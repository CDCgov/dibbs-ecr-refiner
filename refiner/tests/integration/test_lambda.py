import json
from uuid import uuid4

import boto3
import httpx
import pytest
import pytest_asyncio
from botocore.client import Config

from tests.fixtures.loader import load_fixture_str

LAMBDA_BASE_URL = "http://localhost:9000/2015-03-31/functions/function/invocations"


@pytest.fixture
def s3_client():
    s3_client = boto3.client(
        "s3",
        endpoint_url="http://localhost:4566",  # localstack URL
        aws_access_key_id="refiner",
        aws_secret_access_key="refiner",
        region_name="us-east-1",
        config=Config(signature_version="s3v4"),
    )
    return s3_client


@pytest.fixture
def default_setup(s3_client):
    """
    Creates a test configuration in S3 for Lambda to consume.
    Cleans up after the test if needed.
    """
    BUCKET = "local-config-bucket"

    try:
        s3_client.create_bucket(Bucket=BUCKET)
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        pass

    activation_key = "SDDH/840539006/1/active.json"
    activation_content = load_fixture_str("lambda/active.json")

    # Upload activation file to S3
    s3_client.put_object(
        Bucket=BUCKET,
        Key=activation_key,
        Body=activation_content.encode("utf-8"),
        ContentType="application/json",
    )

    current_key = "SDDH/840539006/current.json"
    current_content = {"version": 1}

    # Upload current file to S3
    s3_client.put_object(
        Bucket=BUCKET,
        Key=current_key,
        Body=json.dumps(current_content, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    persistence_id = "persistence/id"
    rr_content = load_fixture_str("eicr_v1_1/mon_mothma_covid_influenza_RR.xml")
    eicr_content = load_fixture_str("eicr_v1_1/mon_mothma_covid_influenza_eICR.xml")

    # Upload RR to S3
    input_rr_key = f"RefinerInput/{persistence_id}"
    s3_client.put_object(
        Bucket=BUCKET,
        Key=input_rr_key,
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

    # Build SQS-style event pointing to S3 object
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
                            "object": {"key": input_rr_key},
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

    yield {
        "rr_key": input_rr_key,
        "eicr_key": eicr_key,
        "current_key": current_key,
        "bucket": BUCKET,
        "event": event,
    }

    # cleanup after test
    s3_client.delete_object(Bucket=BUCKET, Key=activation_key)
    s3_client.delete_object(Bucket=BUCKET, Key=current_key)
    s3_client.delete_object(Bucket=BUCKET, Key=input_rr_key)
    s3_client.delete_object(Bucket=BUCKET, Key=eicr_key)


@pytest_asyncio.fixture
async def http_client():
    async with httpx.AsyncClient() as client:
        yield client


@pytest.mark.integration
@pytest.mark.asyncio
class TestLambda:
    async def test_lambda_successful_refinement(
        self, http_client, s3_client, default_setup
    ):
        bucket = default_setup["bucket"]

        resp = await http_client.post(LAMBDA_BASE_URL, json=default_setup["event"])

        assert resp.status_code == 200

        # Assert refined RR was created
        expected_refined_rr_key = (
            "RefinerOutput/persistence/id/SDDH/840539006/refined_RR.xml"
        )
        rr_response = s3_client.get_object(Bucket=bucket, Key=expected_refined_rr_key)

        assert rr_response["ResponseMetadata"]["HTTPStatusCode"] == 200

        # Assert refined eICR was created
        expected_refined_eicr_key = (
            "RefinerOutput/persistence/id/SDDH/840539006/refined_eICR.xml"
        )
        eicr_response = s3_client.get_object(
            Bucket=bucket, Key=expected_refined_eicr_key
        )
        assert eicr_response["ResponseMetadata"]["HTTPStatusCode"] == 200

    async def test_lambda_current_file_null_version(
        self, http_client, s3_client, default_setup
    ):
        bucket = default_setup["bucket"]

        # Set version to null
        current_file_content = {"version": None}
        s3_client.put_object(
            Bucket=bucket,
            Key=default_setup["current_key"],
            Body=json.dumps(current_file_content, indent=2).encode("utf-8"),
            ContentType="application/json",
        )

        resp = await http_client.post(LAMBDA_BASE_URL, json=default_setup["event"])
        assert resp.status_code == 200

    async def test_lambda_current_file_missing_activation_file(
        self, http_client, s3_client, default_setup
    ):
        bucket = default_setup["bucket"]

        # Set version to null
        current_file_content = {"version": 2}
        s3_client.put_object(
            Bucket=bucket,
            Key=default_setup["current_key"],
            Body=json.dumps(current_file_content, indent=2).encode("utf-8"),
            ContentType="application/json",
        )

        resp = await http_client.post(LAMBDA_BASE_URL, json=default_setup["event"])
        assert resp.status_code == 200

        resp_json = resp.json()
        error_message = resp_json["errorMessage"]
        assert (
            error_message
            == "Activated configuration file could not be read at: SDDH/840539006/2/active.json"
        )

    async def test_lambda_missing_current_file(
        self, http_client, s3_client, default_setup
    ):
        bucket = default_setup["bucket"]

        # Ensure no current key exists
        s3_client.delete_object(Bucket=bucket, Key=default_setup["current_key"])

        resp = await http_client.post(LAMBDA_BASE_URL, json=default_setup["event"])
        assert resp.status_code == 200
