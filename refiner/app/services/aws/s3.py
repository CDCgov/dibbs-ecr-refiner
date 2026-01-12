import os
from datetime import date
from io import BytesIO
from logging import Logger
from uuid import UUID

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from ...core.config import ENVIRONMENT

uploaded_artifact_bucket_name = ENVIRONMENT["S3_BUCKET_CONFIG"]

config = Config(signature_version="s3v4")

if ENVIRONMENT["ENV"] == "local":
    s3_client = boto3.client(
        "s3",
        # use mock access keys needed for localstack
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=ENVIRONMENT["AWS_REGION"],
        endpoint_url=os.getenv("S3_ENDPOINT_URL"),
        config=config,
    )
elif ENVIRONMENT["ENV"] == "demo":
    s3_client = boto3.client(
        "s3",
        region_name=ENVIRONMENT["AWS_REGION"],
        # get these directly rather than from the loaded config file so the
        # app doesn't crash in envs where they're missing
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        endpoint_url=os.getenv("S3_ENDPOINT_URL"),
        config=config,
    )
else:
    s3_client = boto3.client(
        "s3",
        region_name=ENVIRONMENT["AWS_REGION"],
        config=config,
    )


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
