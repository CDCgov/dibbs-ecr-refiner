import json

import httpx
import pytest
import pytest_asyncio

from tests.localstack.seed import (
    create_s3_client,
    seed_localstack,
    tear_down_seeded_resources,
)

LAMBDA_BASE_URL = "http://localhost:9000/2015-03-31/functions/function/invocations"


@pytest.fixture
def s3_client():
    """
    Creates an S3 client for manual interaction with Localstack within the tests.
    """
    return create_s3_client()


@pytest.fixture
def default_setup(s3_client):
    """
    Creates a default test configuration in S3 for Lambda to consume.
    Cleans up after the test if needed.
    """
    metadata = seed_localstack(s3_client)
    yield metadata
    tear_down_seeded_resources(
        s3_client=s3_client,
        BUCKET=metadata["bucket"],
        activation_key=metadata["activation_key"],
        current_key=metadata["current_key"],
        rr_key=metadata["rr_key"],
        eicr_key=metadata["eicr_key"],
    )


@pytest_asyncio.fixture
async def http_client():
    """
    Fixture to get an async client.
    """
    async with httpx.AsyncClient() as client:
        yield client


@pytest.mark.integration
@pytest.mark.asyncio
class TestLambda:
    async def test_lambda_successful_refinement(
        self, http_client, s3_client, default_setup
    ):
        """
        Lambda should be able to successfully refine the RR and eICR when all of the
        required files exist in their expected locations.
        """
        bucket = default_setup["bucket"]

        resp = await http_client.post(LAMBDA_BASE_URL, json=default_setup["event"])

        assert resp.status_code == 200

        # Assert refined RR was created
        expected_refined_rr_key = (
            "RefinerOutput/persistence/id/SDDH/840539006/refined_RR.xml"
        )
        rr_response = s3_client.get_object(Bucket=bucket, Key=expected_refined_rr_key)

        assert rr_response["ResponseMetadata"]["HTTPStatusCode"] == 200
        # Assert shadow refined RR was created
        # TODO: swap this out with the actual value once we get it from APHL
        expected_shadow_rr_key = (
            "RefinerOutput/persistence/id/SDDH/inactive-codes/refined_RR.xml"
        )
        shadow_rr_response = s3_client.get_object(
            Bucket=bucket, Key=expected_shadow_rr_key
        )

        assert shadow_rr_response["ResponseMetadata"]["HTTPStatusCode"] == 200

        # Assert refined eICR was created
        expected_refined_eicr_key = (
            "RefinerOutput/persistence/id/SDDH/840539006/refined_eICR.xml"
        )
        eicr_response = s3_client.get_object(
            Bucket=bucket, Key=expected_refined_eicr_key
        )
        assert eicr_response["ResponseMetadata"]["HTTPStatusCode"] == 200

        # Check generated RefinerComplete file
        complete_response = s3_client.get_object(
            Bucket=bucket, Key=default_setup["complete_key"]
        )
        complete_body = json.loads(complete_response["Body"].read().decode("utf-8"))

        # COVID was refined and the flu was not
        expected_refiner_metadata = {"SDDH": {"840539006": True, "772828001": False}}
        assert complete_body["RefinerMetadata"] == expected_refiner_metadata

        assert expected_refined_eicr_key in complete_body["RefinerOutputFiles"]
        assert expected_refined_rr_key in complete_body["RefinerOutputFiles"]
        assert expected_shadow_rr_key in complete_body["RefinerOutputFiles"]

        assert not complete_body["RefinerSkip"]

    async def test_lambda_current_file_null_version(
        self, http_client, s3_client, default_setup
    ):
        """
        Lambda should properly handle a current file will a `null` version,
        e.g. {"version": null}

        This tells Lambda the config is not active.
        """
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
        """
        Lambda should not perform any processing when it encounters an
        unexpected configuration version. It should report a clear error message
        explaining this.
        """
        bucket = default_setup["bucket"]

        # Set version to a config version that doesn't exist
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
            == "Activated configuration file could not be read at: configurations/SDDH/840539006/2/active.json"
        )

    async def test_lambda_missing_current_file(
        self, http_client, s3_client, default_setup
    ):
        """
        Lambda should skip file processing when no current file exists for a reportable
        condition since this means there is no activated configuration available to use.
        """
        bucket = default_setup["bucket"]

        # Ensure no current key exists
        s3_client.delete_object(Bucket=bucket, Key=default_setup["current_key"])

        resp = await http_client.post(LAMBDA_BASE_URL, json=default_setup["event"])
        assert resp.status_code == 200
