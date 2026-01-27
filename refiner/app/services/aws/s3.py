import os
from datetime import date
from io import BytesIO
from logging import Logger
from typing import Any
from uuid import UUID

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from ...core.config import ENVIRONMENT

uploaded_artifact_bucket_name = ENVIRONMENT["S3_BUCKET_CONFIG"]


def _build_s3_client_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "region_name": ENVIRONMENT["AWS_REGION"],
        "config": Config(signature_version="s3v4"),
    }

    if ENVIRONMENT["ENV"] in {"local", "demo"}:
        kwargs["aws_access_key_id"] = os.getenv("AWS_ACCESS_KEY_ID")
        kwargs["aws_secret_access_key"] = os.getenv("AWS_SECRET_ACCESS_KEY")
        kwargs["endpoint_url"] = os.getenv("S3_ENDPOINT_URL")

    return kwargs


s3_client = boto3.client("s3", **_build_s3_client_kwargs())


def upload_refined_ecr(
    user_id: UUID, file_buffer: BytesIO, filename: str, logger: Logger
) -> str:
    """
    Uploads a refined ZIP file to AWS S3 and provides the uploader with a pre-signed link.

    Args:
        user_id (UUID): Logged-in user ID
        file_buffer (BytesIO): ZIP file in memory
        filename (str): The filename that will be written to S3
        logger (Logger): The standard logger

    Returns:
        str: The pre-signed S3 URL to download the uploaded file
    """

    expires = 3600  # 1 hour

    try:
        today = date.today().isoformat()  # YYYY-MM-DD
        key = f"refiner-test-suite/{today}/{user_id}/{filename}"

        s3_client.upload_fileobj(file_buffer, uploaded_artifact_bucket_name, key)

        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": uploaded_artifact_bucket_name, "Key": key},
            ExpiresIn=expires,
        )

        # for local dev, boto3 creates a URL with the internal hostname ('localstack')
        # We must replace it with the public hostname ('localhost') before sending it
        # to the browser
        if ENVIRONMENT["ENV"] == "local":
            presigned_url = presigned_url.replace("localstack:4566", "localhost:4566")

        return presigned_url

    except ClientError as e:
        logger.error(
            "Attempted refined file upload to S3 failed",
            extra={
                "error": str(e),
                "bucket": uploaded_artifact_bucket_name,
                "key": key,
                "user_id": user_id,
            },
        )
        return ""
