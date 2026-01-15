import json
import os
from datetime import date
from io import BytesIO
from logging import Logger
from uuid import UUID

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.db.configurations.model import (
    ConfigurationStorageMetadata,
    ConfigurationStoragePayload,
)

from ...core.config import ENVIRONMENT

S3_CONFIGURATION_BUCKET_NAME = ENVIRONMENT["S3_BUCKET_CONFIG"]

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


def upload_current_version_file(
    directory_keys: list[str], active_version: int | None
) -> None:
    """
    Writes a new `current.json` file all directories with new activation files.

    Args:
        directory_keys (list[str]): A list of child RSG code directories in the form: s3://bucket/SDDH/12345
        active_version (int): The newly activated configuration version
    """
    data = {
        "version": active_version
        if active_version is not None and active_version > 0
        else None
    }
    for key in directory_keys:
        s3_client.put_object(
            Bucket=S3_CONFIGURATION_BUCKET_NAME,
            Key=f"{key}/current.json",
            Body=json.dumps(data, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        print(f"Updating current.json to version {active_version}: {key}/current.json")


def upload_configuration_payload(
    payload: ConfigurationStoragePayload, metadata: ConfigurationStorageMetadata
) -> list[str]:
    """
    Given a payload and metadata, writes this information to JSON files in S3.

    Args:
        payload (ConfigurationStoragePayload): The configuration payload to write to the bucket.
        metadata: (ConfigurationStorageMetadata): The configuration metadata to write to the bucket.

    Returns:
        str: List of keys pointing to the child RSG SNOMED code directories
    """
    s3_condition_code_paths = []

    payload_data = payload.to_dict()
    metadata_data = metadata.to_dict()

    for child_rsg_code in metadata.child_rsg_snomed_codes:
        parent_directory = f"{metadata.jurisdiction_code}/{child_rsg_code}"

        # Write active.json
        path_with_version = f"{parent_directory}/{metadata.active_version}"
        s3_client.put_object(
            Bucket=S3_CONFIGURATION_BUCKET_NAME,
            Key=f"{path_with_version}/active.json",
            Body=json.dumps(payload_data, indent=2).encode("utf-8"),
            ContentType="application/json",
        )

        # Write metadata.json
        s3_client.put_object(
            Bucket=S3_CONFIGURATION_BUCKET_NAME,
            Key=f"{path_with_version}/metadata.json",
            Body=json.dumps(metadata_data, indent=2).encode("utf-8"),
            ContentType="application/json",
        )

        s3_condition_code_paths.append(parent_directory)
        print(f"Writing file to: {path_with_version}/active.json")
        print(f"Writing file to: {path_with_version}/metadata.json")

    return s3_condition_code_paths


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

        s3_client.upload_fileobj(file_buffer, S3_CONFIGURATION_BUCKET_NAME, key)

        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_CONFIGURATION_BUCKET_NAME, "Key": key},
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
                "bucket": S3_CONFIGURATION_BUCKET_NAME,
                "key": key,
                "user_id": user_id,
            },
        )
        return ""
