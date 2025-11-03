import inspect
from pathlib import Path

import httpx
import pytest
from lxml import etree

from ..validation_utils import validate_xml_string

# -> Test Configuration & Constants

# define the base directory of the 'refiner' project to help locate assets
# -> * __file__ is the path to this test file (test_ecr_refiner.py)
# -> * .resolve() makes the path absolute
# -> * .parent.parent.parent navigates up three levels:
#   -> * integration -> tests -> refiner (assuming 'tests' is a direct child of 'refiner')
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MON_MOTHMA_ZIP_PATH = BASE_DIR / "assets" / "demo" / "mon-mothma-covid-influenza.zip"

# define the expected condition codes and their display names that the service
# should identify and process from the MON_MOTHMA_ZIP_PATH file
# -> * these are the two unique conditions that should be connected from:
#      the RR -> jurisdiction specific configurations
EXPECTED_REPORTABLE_CONDITIONS = {
    "840539006": "COVID-19",
    "772828001": "Influenza",
}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check(setup, authed_client):
    """
    Tests the /api/healthcheck endpoint to ensure the service is responsive.

    Verifies:
    - The endpoint returns a 200 OK status.
    - The response body is a JSON object `{"status": "OK", "db": "OK"}`.
    """

    current_test_name = inspect.currentframe().f_code.co_name
    service_url = "http://0.0.0.0:8080/api/healthcheck"

    print(f"\n[{current_test_name}] Requesting health check from: {service_url}")

    try:
        response = await authed_client.get(service_url, timeout=10.0)
        response.raise_for_status()
    except httpx.RequestError as exc:
        pytest.fail(
            f"[{current_test_name}] Expected successful health check request, got RequestError: {exc}"
        )
    except httpx.HTTPStatusError as exc:
        pytest.fail(
            f"[{current_test_name}] Expected status code 200 for health check, got {exc.response.status_code}: {exc.response.text}"
        )

    assert response.status_code == 200, (
        f"[{current_test_name}] Expected status code 200, got {response.status_code}. Response: {response.text}"
    )

    try:
        response_json = response.json()
    except Exception as e:
        pytest.fail(
            f"[{current_test_name}] Expected valid JSON response for health check, got exception: {e}. Response text: {response.text}"
        )

    assert response_json == {"status": "OK", "db": "OK"}, (
        f"[{current_test_name}] Expected JSON response {{'status': 'OK', 'db': 'OK'}}, got {response_json}"
    )

    print(f"[{current_test_name}] Health check successful: {response_json}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_zip_upload_mon_mothma_two_conditions(setup, authed_client):
    """
    Integration test for the /api/v1/demo/upload endpoint using the 'mon-mothma-covid-influenza.zip' demo file.

    This test verifies:
    - The endpoint successfully processes a demo ZIP containing eICR and RR XML files.
    - The response includes exactly the expected reportable conditions (codes and display names) as defined in the test constants.
    - Each condition in the response includes a non-empty, well-formed refined eICR XML string that validates against the expected schema.
    - The overall workflow (file upload, processing, and response structure) functions as intended.

    Steps:
    1. Open and upload the demo ZIP file to the /api/v1/demo/upload endpoint.
    2. Assert the response status and content type.
    3. Assert the correct mapping of reportable condition codes to display names in the response.
    4. Validate that each returned refined eICR:
        - Exists and is a non-empty string,
        - Is well-formed XML with the expected root tag,
        - Passes Schematron validation checks.

    Fails with informative messages if any assertion does not hold.
    """

    current_test_name = inspect.currentframe().f_code.co_name

    if not MON_MOTHMA_ZIP_PATH.is_file():
        pytest.fail(
            f"[{current_test_name}] Expected test ZIP file at {MON_MOTHMA_ZIP_PATH}, got file not found."
        )

    with open(MON_MOTHMA_ZIP_PATH, "rb") as f_zip:
        files = {"uploaded_file": (MON_MOTHMA_ZIP_PATH.name, f_zip, "application/zip")}
        service_url = "http://0.0.0.0:8080/api/v1/demo/upload"
        response = await authed_client.post(service_url, files=files, timeout=30.0)

    assert response.status_code == 200, (
        f"[{current_test_name}] Expected status code 200, got {response.status_code}. Response: {response.text}"
    )
    assert "application/json" in response.headers["content-type"], (
        f"[{current_test_name}] Expected content type containing 'application/json', got {response.headers['content-type']}"
    )

    response_json = response.json()
    conditions = response_json["refined_conditions"]

    # STEP 1
    # only check for reportable codes/display_names from RR
    found_codes = {item["code"]: item["display_name"] for item in conditions}
    assert found_codes == EXPECTED_REPORTABLE_CONDITIONS, (
        f"[{current_test_name}] Expected reportable conditions {EXPECTED_REPORTABLE_CONDITIONS}, got {found_codes}"
    )

    # STEP 2
    # validate refined eICR and RR for each condition
    for index, eicr_item in enumerate(conditions):
        item_label = f"eICR item #{index + 1}"

        assert "refined_rr" in eicr_item, (
            f"[{current_test_name}] Expected key 'refined_eicr' in {item_label}, got keys {list(eicr_item.keys())}. Item: {eicr_item}"
        )
        refined_rr_xml_string = eicr_item["refined_rr"]
        assert refined_rr_xml_string and isinstance(refined_rr_xml_string, str), (
            f"[{current_test_name}] Expected non-empty string for {item_label} 'refined_eicr', got {type(refined_rr_xml_string)} with value: {refined_rr_xml_string!r}"
        )
        validation_summary = validate_xml_string(
            refined_rr_xml_string, doc_type_hint="rr"
        )
        if validation_summary["errors"] > 0:
            pytest.fail(
                f"[{current_test_name}] Expected 0 Schematron errors for {item_label} (Condition: {eicr_item['code']}), got {validation_summary['errors']}."
            )
        try:
            root = etree.fromstring(refined_rr_xml_string.encode("utf-8"))
            assert root.tag == "{urn:hl7-org:v3}ClinicalDocument", (
                f"[{current_test_name}] Expected root tag '{{urn:hl7-org:v3}}ClinicalDocument' for {item_label}, got {root.tag}"
            )
        except etree.XMLSyntaxError as e:
            pytest.fail(
                f"[{current_test_name}] Expected well-formed XML for {item_label} (Condition: {eicr_item['code']}), got XMLSyntaxError: {e}. Content (first 500 chars): {refined_rr_xml_string[:500]}"
            )

        assert "refined_eicr" in eicr_item, (
            f"[{current_test_name}] Expected key 'refined_eicr' in {item_label}, got keys {list(eicr_item.keys())}. Item: {eicr_item}"
        )
        refined_eicr_xml_string = eicr_item["refined_eicr"]
        assert refined_eicr_xml_string and isinstance(refined_eicr_xml_string, str), (
            f"[{current_test_name}] Expected non-empty string for {item_label} 'refined_eicr', got {type(refined_eicr_xml_string)} with value: {refined_eicr_xml_string!r}"
        )
        validation_summary = validate_xml_string(
            refined_eicr_xml_string,
            doc_type_hint="eicr",
        )
        if validation_summary["errors"] > 0:
            pytest.fail(
                f"[{current_test_name}] Expected 0 Schematron errors for {item_label} (Condition: {eicr_item['code']}), got {validation_summary['errors']}."
            )
        try:
            root = etree.fromstring(refined_eicr_xml_string.encode("utf-8"))
            assert root.tag == "{urn:hl7-org:v3}ClinicalDocument", (
                f"[{current_test_name}] Expected root tag '{{urn:hl7-org:v3}}ClinicalDocument' for {item_label}, got {root.tag}"
            )
        except etree.XMLSyntaxError as e:
            pytest.fail(
                f"[{current_test_name}] Expected well-formed XML for {item_label} (Condition: {eicr_item['code']}), got XMLSyntaxError: {e}. Content (first 500 chars): {refined_eicr_xml_string[:500]}"
            )
