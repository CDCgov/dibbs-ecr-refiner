import json
import os
from datetime import date
from io import BytesIO
from logging import Logger
from typing import Any
from uuid import UUID

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.db.configurations.model import (
    ConfigurationStorageMetadata,
    ConfigurationStoragePayload,
)
from app.services.conditions import ConditionMappingPayload

from ...core.config import ENVIRONMENT
from .s3_keys import (
    get_active_file_key,
    get_metadata_file_key,
    get_parent_directory_key,
    get_rsg_cg_mapping_file_key,
)

S3_CONFIGURATION_BUCKET_NAME = ENVIRONMENT["S3_BUCKET_CONFIG"]


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


def upload_current_version_file(
    directory_keys: list[str], active_version: int | None, logger: Logger
) -> None:
    """
    Writes a new `current.json` file for all directories with new activation files.

    Args:
        directory_keys (list[str]): A list of child RSG code directories in the form: s3://bucket/SDDH/12345
        active_version (int): The newly activated configuration version
        logger (Logger): The standard application logger
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
        logger.debug(
            f"Updating current.json to version {active_version}: {key}/current.json"
        )


def upload_configuration_payload(
    payload: ConfigurationStoragePayload,
    metadata: ConfigurationStorageMetadata,
    logger: Logger,
) -> list[str]:
    """
    Given a payload and metadata, writes this information to JSON files in S3.

    Args:
        payload (ConfigurationStoragePayload): The configuration payload to write to the bucket.
        metadata (ConfigurationStorageMetadata): The configuration metadata to write to the bucket.
        logger (Logger): The standard application logger.

    Returns:
        list[str]: List of keys pointing to the child RSG SNOMED code directories
    """
    s3_condition_code_paths = []

    payload_data = payload.to_dict()
    metadata_data = metadata.to_dict()

    canonical_url = metadata.canonical_url
    jurisdiction_id = metadata.jurisdiction_id

    parent_directory = get_parent_directory_key(
        jurisdiction_id=jurisdiction_id, canonical_url=canonical_url
    )

    # Write active.json
    active_key = get_active_file_key(
        jurisdiction_id=jurisdiction_id,
        canonical_url=canonical_url,
        version=metadata.configuration_version,
    )
    s3_client.put_object(
        Bucket=S3_CONFIGURATION_BUCKET_NAME,
        Key=active_key,
        Body=json.dumps(payload_data, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    # Write metadata.json
    metadata_key = get_metadata_file_key(
        jurisdiction_id=jurisdiction_id,
        canonical_url=canonical_url,
        version=metadata.configuration_version,
    )
    s3_client.put_object(
        Bucket=S3_CONFIGURATION_BUCKET_NAME,
        Key=metadata_key,
        Body=json.dumps(metadata_data, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    s3_condition_code_paths.append(parent_directory)
    logger.debug(f"Writing file to: {active_key}")
    logger.debug(f"Writing file to: {metadata_key}")

    return s3_condition_code_paths


def upload_condition_mapping_payload(
    mapping_payload: ConditionMappingPayload, jurisdiction_id: str, logger: Logger
) -> str:
    """
    Writes the RSG -> CG mapping file to the jurisdiction directory.

    Args:
        mapping_payload (ConditionMappingPayload): The mapping payload to write as JSON
        jurisdiction_id (str): The jurisdiction ID
        logger (Logger): The standard logger

    Returns:
        str: The key where the file was written to.
    """
    condition_mapping_key = get_rsg_cg_mapping_file_key(jurisdiction_id=jurisdiction_id)

    mapping_payload_dict = mapping_payload.to_dict()

    s3_client.put_object(
        Bucket=S3_CONFIGURATION_BUCKET_NAME,
        Key=condition_mapping_key,
        Body=json.dumps(mapping_payload_dict, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    logger.info(
        f"Condition mapping file written to {condition_mapping_key}",
        extra={"jurisdiction_id": jurisdiction_id},
    )

    return condition_mapping_key


def upload_refined_ecr(
    user_id: UUID,
    jurisdiction_id: str,
    file_buffer: BytesIO,
    filename: str,
    logger: Logger,
) -> str:
    """
    Uploads a refined ZIP file to AWS S3.

    Args:
        user_id (UUID): Logged-in user ID
        jurisdiction_id (str): Logged-in user's ID.
        file_buffer (BytesIO): ZIP file in memory
        filename (str): The filename that will be written to S3
        logger (Logger): The standard logger

    Returns:
        str: The S3 key of the uploaded file (or empty string on error)
    """
    key = ""
    try:
        key = get_refined_user_zip_key(
            user_id=user_id, jurisdiction_id=jurisdiction_id, filename=filename
        )

        s3_client.upload_fileobj(file_buffer, S3_CONFIGURATION_BUCKET_NAME, key)

        return key

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


def fetch_zip_from_s3(key: str, logger: Logger) -> dict:
    """
    Fetch file from s3, return botocore response dict.
    """
    resp = s3_client.get_object(
        Bucket=S3_CONFIGURATION_BUCKET_NAME,
        Key=key,
    )
    return resp


def get_refined_user_zip_key(user_id: UUID, jurisdiction_id: str, filename: str) -> str:
    """
    Creates a refiner user zip file key.
    """
    today = date.today().isoformat()
    key = f"test-artifacts/{jurisdiction_id}/{today}/{user_id}/{filename}"
    return key
