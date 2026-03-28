import json

import httpx
import pytest
import pytest_asyncio
from lxml import etree

from tests.integration.conftest import assert_schematron_valid, validate_refined_xml
from tests.localstack.seed import (
    create_s3_client,
    seed_localstack,
    tear_down_seeded_resources,
)

LAMBDA_BASE_URL = "http://localhost:9000/2015-03-31/functions/function/invocations"
COVID_CANONICAL_URL_UUID = "07221093-b8a1-4b1d-8678-259277bfba64"
REFINER_OUTPUT_PREFIX = "RefinerOutput/"

# Condition SNOMED codes
COVID_CODE = "840539006"
COVID_DUPE_CODE = "186747009"
INFLUENZA_CODE = "772828001"

# RR namespaces for content assertions
RR_NAMESPACES = {"cda": "urn:hl7-org:v3"}


def get_rr_condition_codes(rr_xml: str) -> set[str]:
    """
    Extract all reportable condition SNOMED codes from the RR11 organizer.
    """
    root = etree.fromstring(rr_xml.encode("utf-8"))
    codes = root.xpath(
        ".//cda:observation"
        "[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12']]"
        "/cda:value/@code",
        namespaces=RR_NAMESPACES,
    )
    return set(codes)


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
        self, http_client, s3_client, default_setup, validate_xml_string
    ):
        """
        Lambda should be able to successfully refine the RR and eICR when all of the
        required files exist in their expected locations. Refined outputs should be
        well-formed XML that passes Schematron validation.
        """
        test_name = "test_lambda_successful_refinement"
        bucket = default_setup["bucket"]

        resp = await http_client.post(LAMBDA_BASE_URL, json=default_setup["event"])

        assert resp.status_code == 200

        # --- File existence assertions ---

        # Assert refined RR was created
        expected_refined_covid_rr_key = (
            f"{REFINER_OUTPUT_PREFIX}persistence/id/SDDH/COVID19/refined_RR.xml"
        )
        rr_response = s3_client.get_object(
            Bucket=bucket, Key=expected_refined_covid_rr_key
        )
        assert rr_response["ResponseMetadata"]["HTTPStatusCode"] == 200

        # Assert unrefined conditions RR was created
        expected_unrefined_rr_key = (
            f"{REFINER_OUTPUT_PREFIX}persistence/id/SDDH/unrefined_rr/refined_RR.xml"
        )
        unrefined_rr_response = s3_client.get_object(
            Bucket=bucket, Key=expected_unrefined_rr_key
        )
        assert unrefined_rr_response["ResponseMetadata"]["HTTPStatusCode"] == 200

        # Assert refined eICR was created
        expected_refined_covid_eicr_key = (
            f"{REFINER_OUTPUT_PREFIX}persistence/id/SDDH/COVID19/refined_eICR.xml"
        )
        eicr_covid_response = s3_client.get_object(
            Bucket=bucket, Key=expected_refined_covid_eicr_key
        )
        assert eicr_covid_response["ResponseMetadata"]["HTTPStatusCode"] == 200

        # --- RefinerComplete assertions ---

        complete_response = s3_client.get_object(
            Bucket=bucket, Key=default_setup["complete_key"]
        )
        complete_body = json.loads(complete_response["Body"].read().decode("utf-8"))

        # COVID was refined and the flu was not
        expected_refiner_metadata = {
            "SDDH": {
                COVID_CODE: True,
                COVID_DUPE_CODE: True,
                INFLUENZA_CODE: False,
            },
            "JDDH": {INFLUENZA_CODE: False},
        }
        assert complete_body["RefinerMetadata"] == expected_refiner_metadata

        assert expected_refined_covid_eicr_key in complete_body["RefinerOutputFiles"]

        # COVID has two codes, but should only have one instance of the output key
        # for both files
        assert (
            complete_body["RefinerOutputFiles"].count(expected_refined_covid_eicr_key)
            == 1
        )
        assert (
            complete_body["RefinerOutputFiles"].count(expected_refined_covid_rr_key)
            == 1
        )

        assert expected_unrefined_rr_key in complete_body["RefinerOutputFiles"]
        assert not complete_body["RefinerSkip"]

        # --- Content and Schematron validation for refined eICR ---

        refined_eicr_xml = eicr_covid_response["Body"].read().decode("utf-8")

        validate_refined_xml(
            refined_eicr_xml, "eICR", "COVID19 refined eICR", test_name
        )
        eicr_result = validate_xml_string(refined_eicr_xml, "eicr")
        assert_schematron_valid(eicr_result, "COVID19 refined eICR", test_name)

        # Refined eICR should be smaller than the original
        original_eicr = s3_client.get_object(
            Bucket=bucket, Key=default_setup["eicr_key"]
        )
        original_eicr_xml = original_eicr["Body"].read().decode("utf-8")
        assert len(refined_eicr_xml) < len(original_eicr_xml), (
            "Refined eICR should be smaller than the original"
        )

        # --- Content and Schematron validation for refined RR ---

        refined_rr_xml = rr_response["Body"].read().decode("utf-8")

        validate_refined_xml(refined_rr_xml, "RR", "COVID19 refined RR", test_name)
        rr_result = validate_xml_string(refined_rr_xml, "rr")
        assert_schematron_valid(rr_result, "COVID19 refined RR", test_name)

        # Refined RR should contain only the COVID condition
        refined_rr_codes = get_rr_condition_codes(refined_rr_xml)
        assert COVID_CODE in refined_rr_codes, "Refined RR should contain COVID"
        assert INFLUENZA_CODE not in refined_rr_codes, (
            "Refined RR should not contain Influenza"
        )

        # --- Content validation for unrefined conditions RR ---

        unrefined_rr_xml = unrefined_rr_response["Body"].read().decode("utf-8")

        validate_refined_xml(
            unrefined_rr_xml, "RR", "Unrefined conditions RR", test_name
        )
        unrefined_rr_result = validate_xml_string(unrefined_rr_xml, "rr")
        assert_schematron_valid(
            unrefined_rr_result, "Unrefined conditions RR", test_name
        )

        # Unrefined conditions RR should contain only Influenza
        unrefined_rr_codes = get_rr_condition_codes(unrefined_rr_xml)
        assert INFLUENZA_CODE in unrefined_rr_codes, (
            "Unrefined conditions RR should contain Influenza"
        )
        assert COVID_CODE not in unrefined_rr_codes, (
            "Unrefined conditions RR should not contain COVID"
        )

        print(f"[{test_name}] ✅ All refined outputs passed Schematron validation")

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
            == f"Activated configuration file could not be read at: configurations/SDDH/{COVID_CANONICAL_URL_UUID}/2/active.json"
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
