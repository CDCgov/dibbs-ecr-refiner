from datetime import date
from io import BytesIO
from logging import Logger

import boto3
from botocore.exceptions import ClientError

from ...core.config import ENVIRONMENT

s3_client = boto3.client(
    "s3",
    region_name=ENVIRONMENT["AWS_REGION"],
    aws_access_key_id=ENVIRONMENT["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=ENVIRONMENT["AWS_SECRET_ACCESS_KEY"],
    endpoint_url=ENVIRONMENT["S3_ENDPOINT_URL"],
)


def upload_refined_ecr(
    user_id: str, file_buffer: BytesIO, filename: str, logger: Logger
) -> str:
    """
    Uploads a refined ZIP file to AWS S3 and provides the uploader with a pre-signed link.

    Args:
        user_id (str): Logged-in user ID
        file_buffer (BytesIO): ZIP file in memory
        filename (str): The filename that will be written to S3
        logger (Logger): The standard logger

    Returns:
        str: The pre-signed S3 URL to download the uploaded file
    """

    bucket_name = "refiner-app"
    expires = 3600  # 1 hour

    try:
        today = date.today().isoformat()  # YYYY-MM-DD
        key = f"refiner-test-suite/{today}/{user_id}/{filename}"

        s3_client.upload_fileobj(file_buffer, bucket_name, key)

        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": key},
            ExpiresIn=expires,
        )

        return presigned_url

    except ClientError as e:
        logger.error(
            "Attempted refined file upload to S3 failed",
            extra={
                "error": str(e),
                "bucket": bucket_name,
                "key": key,
                "user_id": user_id,
            },
        )
        return ""
