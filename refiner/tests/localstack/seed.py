import json
import os
import sys
from uuid import uuid4

import boto3
from botocore.client import Config

# add Refiner to the sys path so we can import the relevant methods from the
# internal modules when running the script
current_script_dir = os.path.dirname(os.path.abspath(__file__))
refiner_dir = os.path.abspath(os.path.join(current_script_dir, "../.."))
if refiner_dir not in sys.path:
    sys.path.insert(0, refiner_dir)

from app.services.aws.s3_keys import (  # noqa: E402
    get_active_file_key,
    get_current_file_key,
    get_rsg_cg_mapping_file_key,
)
from tests.fixtures.loader import load_fixture_str  # noqa: E402


def create_s3_client():
    """
    Create an S3 client to perform localstack operations with
    """
    return boto3.client(
        "s3",
        endpoint_url="http://localhost:4566",  # localstack URL
        aws_access_key_id="refiner",
        aws_secret_access_key="refiner",
        region_name="us-east-1",
        config=Config(signature_version="s3v4"),
    )


def seed_localstack(s3_client):
    """
    Seed localstack with the relevant infrastructure for manual and integration tests
    """
    BUCKET = "local-config-bucket"

    try:
        s3_client.create_bucket(Bucket=BUCKET)
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        pass

    COVID_CANONICAL_URL = "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64"
    activation_key = get_active_file_key(
        jurisdiction_id="SDDH", canonical_url=COVID_CANONICAL_URL, version=1
    )
    activation_content = load_fixture_str("lambda/active.json")

    # Upload activation file to S3
    s3_client.put_object(
        Bucket=BUCKET,
        Key=activation_key,
        Body=activation_content.encode("utf-8"),
        ContentType="application/json",
    )

    current_key = get_current_file_key(
        jurisdiction_id="SDDH", canonical_url=COVID_CANONICAL_URL
    )
    current_content = {"version": 1}

    # Upload current file to S3
    s3_client.put_object(
        Bucket=BUCKET,
        Key=current_key,
        Body=json.dumps(current_content, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    rsg_cg_mapping_file_key = get_rsg_cg_mapping_file_key(jurisdiction_id="SDDH")
    rsg_cg_content = load_fixture_str("lambda/rsg_cg_mapping.json")

    # Upload current file to S3
    s3_client.put_object(
        Bucket=BUCKET,
        Key=rsg_cg_mapping_file_key,
        Body=rsg_cg_content.encode("utf-8"),
        ContentType="application/json",
    )

    persistence_id = "persistence/id"
    rr_content = load_fixture_str("eicr_v3_1_1/multi-condition-multi-covid-CDA_RR.xml")
    eicr_content = load_fixture_str(
        "eicr_v3_1_1/multi-condition-multi-covid-CDA_eICR.xml"
    )

    # alternative test files with custom code additions
    # rr_content = load_fixture_str("eicr_v3_1_1/all_sections_CDA_RR.xml")
    # eicr_content = load_fixture_str("eicr_v3_1_1/all_sections_CDA_eICR.xml")

    # Upload RR to S3
    rr_key = f"RefinerInput/{persistence_id}"
    s3_client.put_object(
        Bucket=BUCKET,
        Key=rr_key,
        Body=rr_content.encode("utf-8"),
        ContentType="application/xml",
    )

    # Upload eICR to S3
    eicr_key = f"eCRMessageV2/{persistence_id}"
    s3_client.put_object(
        Bucket=BUCKET,
        Key=eicr_key,
        Body=eicr_content.encode("utf-8"),
        ContentType="application/xml",
    )

    # SQS style event pointing to the RR key
    event = {
        "Records": [
            {
                "messageId": str(uuid4()),
                "receiptHandle": str(uuid4()),
                "body": json.dumps(
                    {
                        "version": "0",
                        "id": str(uuid4()),
                        "detail-type": "Object Created",
                        "source": "aws.s3",
                        "account": "123456789012",
                        "time": "2026-01-27T00:00:00Z",
                        "region": "us-east-1",
                        "resources": [f"arn:aws:s3:::{BUCKET}"],
                        "detail": {
                            "version": "0",
                            "bucket": {"name": BUCKET},
                            "object": {"key": rr_key},
                            "size": 123,
                        },
                    }
                ),
                "attributes": {},
                "messageAttributes": {},
                "md5OfBody": "",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:local-queue",
                "awsRegion": "us-east-1",
            }
        ]
    }

    return {
        "rr_key": rr_key,
        "eicr_key": eicr_key,
        "current_key": current_key,
        "activation_key": activation_key,
        "complete_key": f"RefinerComplete/{persistence_id}",
        "bucket": BUCKET,
        "event": event,
    }


def tear_down_seeded_resources(
    s3_client, BUCKET, activation_key, current_key, rr_key, eicr_key
):
    s3_client.delete_object(Bucket=BUCKET, Key=activation_key)
    s3_client.delete_object(Bucket=BUCKET, Key=current_key)
    s3_client.delete_object(Bucket=BUCKET, Key=rr_key)
    s3_client.delete_object(Bucket=BUCKET, Key=eicr_key)


def run() -> None:
    """
    Sets up Localstack infra needed for manual testing.
    """

    s3_client = create_s3_client()
    data = seed_localstack(s3_client=s3_client)

    print(f"Seeding complete. Bucket: {data['bucket']}")
    print("Sample SQS Event to trigger Lambda:")
    print(json.dumps(data["event"], indent=2))


if __name__ == "__main__":
    run()
