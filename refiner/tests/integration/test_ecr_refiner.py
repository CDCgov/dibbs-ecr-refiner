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
MON_MOTHMA_ZIP_PATH = BASE_DIR / "assets" / "demo" / "mon-mothma-two-conditions.zip"

# define the expected condition codes and their display names that the service
# should identify and process from the MON_MOTHMA_ZIP_PATH file
# -> * these are the two unique conditions that should be pulled out of the RR
EXPECTED_CONDITIONS = {
    "840539006": "Disease caused by severe acute respiratory syndrome coronavirus 2 (disorder)",
    "772828001": "Influenza caused by Influenza A virus subtype H5N1 (disorder)",
}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check(
    setup, authed_client
):  # 'setup' fixture is expected to start the service
    """
    Tests the /api/healthcheck endpoint to ensure the service is responsive.

    Verifies:
    - The endpoint returns a 200 OK status.
    - The response body is a JSON object `{"status": "OK", "db": "OK"}`.
    """

    current_test_name = inspect.currentframe().f_code.co_name
    # define the full URL for the health check endpoint
    service_url = "http://0.0.0.0:8080/api/healthcheck"

    print(f"\n[{current_test_name}] Requesting health check from: {service_url}")

    try:
        # make a get request to the health check endpoint
        response = await authed_client.get(service_url, timeout=10.0)
        # raise an exception for http error codes (4xx or 5xx)
        response.raise_for_status()
    except httpx.RequestError as exc:
        # handle network errors or other issues during the request
        pytest.fail(f"[{current_test_name}] Health check request failed: {exc}")
    except httpx.HTTPStatusError as exc:
        # handle http error responses (e.g., 404, 500)
        pytest.fail(
            f"[{current_test_name}] Health check failed with status {exc.response.status_code}: {exc.response.text}"
        )

    # assert that the status code is 200 OK
    assert response.status_code == 200, (
        f"[{current_test_name}] Expected status code 200, got {response.status_code}. Response: {response.text}"
    )

    try:
        # attempt to parse the response as json
        response_json = response.json()
    # catch broad json parsing errors
    except Exception as e:
        pytest.fail(
            f"[{current_test_name}] Failed to parse health check response as JSON: {e}. Response text: {response.text}"
        )

    # assert that the json response matches the expected {"status": "OK"}
    assert response_json == {"status": "OK", "db": "OK"}, (
        f"[{current_test_name}] Expected JSON response {{'status': 'OK', 'db': 'OK'}}, got {response_json}"
    )

    print(f"[{current_test_name}] Health check successful: {response_json}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_zip_upload_mon_mothma_two_conditions(
    setup, authed_client
):  # 'setup' fixture
    """
    Tests the eICR refinement process via ZIP upload using 'mon-mothma-two-conditions.zip'.

    This test verifies several key aspects of the service's functionality:
    1.  **Correct Number of Outputs:** Ensures the service generates one refined eICR
        for each unique reportable condition found in the input (expected: 2 eICRs).
    2.  **Accurate Condition Identification:** Checks that each generated eICR
        correctly identifies the reportable condition it pertains to (code and display name).
    3.  **Schema Validity:** Validates each refined eICR XML string against the
        official eICR Schematron rules to ensure conformity.
    4.  **XML Well-formedness:** Confirms that each eICR is a well-formed XML document
        and has the correct root tag (`<ClinicalDocument>`).
    """

    # get current test name for logging
    current_test_name = inspect.currentframe().f_code.co_name

    # ensure the test asset (ZIP file) exists before proceeding
    if not MON_MOTHMA_ZIP_PATH.is_file():
        pytest.fail(f"Test ZIP file not found: {MON_MOTHMA_ZIP_PATH}")

    # open the zip file in binary read mode ("rb")
    with open(MON_MOTHMA_ZIP_PATH, "rb") as f_zip:
        # prepare the file for multipart/form-data upload
        files = {"file": (MON_MOTHMA_ZIP_PATH.name, f_zip, "application/zip")}

        # define the service endpoint for zip upload
        service_url = "http://0.0.0.0:8080/api/v1/ecr/zip-upload"
        print(
            f"\n[{current_test_name}] Posting to: {service_url} with file: {MON_MOTHMA_ZIP_PATH.name}"
        )

        # make the post request to the service
        # -> * increased timeout for potentially long processing
        response = await authed_client.post(service_url, files=files, timeout=30.0)

    # initial response assertions
    assert response.status_code == 200, (
        f"[{current_test_name}] Request failed: {response.status_code} - {response.text}"
    )
    assert "application/json" in response.headers["content-type"], (
        f"[{current_test_name}] Unexpected content type: {response.headers['content-type']}"
    )

    # parse the json response from the service
    response_json = response.json()

    # assertions on the structure and content of the json response ---
    assert isinstance(response_json, list), (
        f"[{current_test_name}] Response should be a JSON list, got {type(response_json)}"
    )
    # verify that the number of returned eICR items matches the number of expected conditions
    assert len(response_json) == len(EXPECTED_CONDITIONS), (
        f"[{current_test_name}] Expected {len(EXPECTED_CONDITIONS)} refined eICRs, but got {len(response_json)}. Response: {response_json}"
    )

    # keep track of the condition codes found in the response to ensure all expected ones are present
    found_condition_codes = set()

    # iterate through each eICR item returned in the json array
    for i, eicr_item in enumerate(response_json):
        item_label = f"eICR item #{i + 1}"
        print(f"\n[{current_test_name}] Processing {item_label} from response...")

        # 1. verify the 'reportable_condition' part of the item
        assert "reportable_condition" in eicr_item, (
            f"[{current_test_name}] {item_label} missing 'reportable_condition' key. Item: {eicr_item}"
        )
        condition_data = eicr_item["reportable_condition"]
        assert "code" in condition_data, (
            f"[{current_test_name}] {item_label} 'reportable_condition' missing 'code'. Data: {condition_data}"
        )
        assert "displayName" in condition_data, (
            f"[{current_test_name}] {item_label} 'reportable_condition' missing 'displayName'. Data: {condition_data}"
        )

        condition_code = condition_data["code"]
        condition_display_name = condition_data["displayName"]
        found_condition_codes.add(condition_code)

        # 2. assert that the identified condition is one of the expected conditions
        assert condition_code in EXPECTED_CONDITIONS, (
            f"[{current_test_name}] {item_label} has unexpected condition code '{condition_code}'. Item: {eicr_item}"
        )
        assert condition_display_name == EXPECTED_CONDITIONS[condition_code], (
            f"[{current_test_name}] {item_label} for code '{condition_code}' has unexpected displayName '{condition_display_name}'. Expected: '{EXPECTED_CONDITIONS[condition_code]}'"
        )
        print(
            f"[{current_test_name}] {item_label} is for condition: {condition_code} - {condition_display_name}"
        )

        # 3. verify the 'refined_eicr' (xml string) part of the item
        assert "refined_eicr" in eicr_item, (
            f"[{current_test_name}] {item_label} missing 'refined_eicr' key. Item: {eicr_item}"
        )
        refined_eicr_xml_string = eicr_item["refined_eicr"]
        assert refined_eicr_xml_string and isinstance(refined_eicr_xml_string, str), (
            f"[{current_test_name}] {item_label} 'refined_eicr' XML string is empty or not a string."
        )

        # 4. validate the refined eICR xml string against schematron rules
        print(
            f"[{current_test_name}] Validating {item_label} (Condition: {condition_code}) with Schematron..."
        )
        # we're assuming all outputs are eICR for this test
        # when we start refining RR files we'll need to revist
        # this test
        validation_summary = validate_xml_string(
            refined_eicr_xml_string,
            doc_type_hint="eicr",
        )

        # if schematron validation finds errors, fail the test with detailed information
        if validation_summary["errors"] > 0:
            # format error details for readability in pytest output
            error_details = "\\n".join(
                [
                    f"  - ID: {err.get('id')}, Test: {err.get('test')}, Context: {err.get('context')}, Message: {err.get('message')}"
                    for err in validation_summary["details"]
                    if err["severity"] == "ERROR"
                ]
            )
            # limit how much of the svrl you need to see
            raw_svrl_preview = (validation_summary.get("raw_svrl") or "")[:1000]
            pytest.fail(
                f"[{current_test_name}] Validation failed for {item_label} (Condition: {condition_code}) "
                f"with {validation_summary['errors']} Schematron errors.\\n"
                f"Warnings: {validation_summary['warnings']}, Infos: {validation_summary['infos']}.\\n"
                f"Error Details:\\n{error_details}\\n"
                f"Raw SVRL (first 1KB):\\n{raw_svrl_preview}..."
            )

        print(
            f"[{current_test_name}] {item_label} (Condition: {condition_code}) passed Schematron validation "
            f"({validation_summary['errors']} errors, {validation_summary['warnings']} warnings)."
        )

        # log any schematron warnings found (these do not fail the test)
        if validation_summary["warnings"] > 0:
            print(
                f"[{current_test_name}] INFO: {item_label} (Condition: {condition_code}) "
                f"produced {validation_summary['warnings']} validation warnings."
            )

        # 5. perform a basic xml well-formedness check and verify the root tag
        try:
            # attempt to parse the xml string
            root = etree.fromstring(refined_eicr_xml_string.encode("utf-8"))
            # check if the root tag is <ClinicalDocument> with the correct HL7 v3 namespace
            # this is still an important check beyond just schematron validation
            assert root.tag == "{urn:hl7-org:v3}ClinicalDocument", (
                f"[{current_test_name}] {item_label} (Condition: {condition_code}) root tag is not ClinicalDocument. Got: {root.tag}"
            )
        except (
            etree.XMLSyntaxError
            # handle cases where the XML is not well-formed
        ) as e:
            pytest.fail(
                f"[{current_test_name}] {item_label} (Condition: {condition_code}) is not well-formed XML: {e}. "
                f"Content (first 500 chars): {refined_eicr_xml_string[:500]}"
            )
        print(
            f"[{current_test_name}] {item_label} (Condition: {condition_code}) is well-formed XML with correct root tag."
        )

    # 6. final check: ensure all expected condition codes were found in the response
    assert found_condition_codes == set(EXPECTED_CONDITIONS.keys()), (
        f"[{current_test_name}] Mismatch in processed condition codes. Expected: {set(EXPECTED_CONDITIONS.keys())}, Found: {found_condition_codes}"
    )

    print(
        f"\n[{current_test_name}] Successfully processed and validated eICRs for all {len(EXPECTED_CONDITIONS)} conditions."
    )
