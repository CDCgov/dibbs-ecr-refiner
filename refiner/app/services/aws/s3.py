from datetime import date
from io import BytesIO

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
bucket_name = "refiner-app"


def upload_refined_ecr(
    user_id: str, file_buffer: BytesIO, filename: str, expires: int = 3600
) -> str:
    """
    Uploads a refined ZIP file to AWS S3 and provides the uploader with a pre-signed link.

    Args:
        user_id (str): _description_
        file_buffer (BytesIO): _description_
        filename (str): _description_
        expires (int, optional): _description_. Defaults to 3600.

    Returns:
        str: _description_
    """
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

    except ClientError:
        print("Upload to S3 failed.")
        return ""
