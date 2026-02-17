import pytest

from tests.integration.conftest import assert_schematron_valid, validate_refined_xml

EXPECTED_COVID_INFLUENZA_CONDITIONS: dict[str, str] = {
    "840539006": "COVID-19",
    "772828001": "Influenza",
}

EXPECTED_ZIKA_CONDITIONS: dict[str, str] = {
    "3928002": "Zika Virus Disease",
}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check(setup, authed_client):
    """
    Tests the /api/healthcheck endpoint to ensure the service is responsive.
    """

    response = await authed_client.get(
        "http://0.0.0.0:8080/api/healthcheck",
        timeout=10.0,
    )
    assert response.status_code == 200
    assert response.json() == {"status": "OK", "db": "OK"}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_zip_upload_covid_influenza_v1_1(
    setup,
    authed_client,
    covid_influenza_v1_1_zip_path,
    validate_xml_string,
):
    """
    Integration test for /api/v1/demo/upload using Mon Mothma COVID+Influenza v1.1.
    """

    test_name = "test_zip_upload_covid_influenza_v1_1"

    with open(covid_influenza_v1_1_zip_path, "rb") as f:
        files = {
            "uploaded_file": (covid_influenza_v1_1_zip_path.name, f, "application/zip")
        }
        response = await authed_client.post(
            "http://0.0.0.0:8080/api/v1/demo/upload",
            files=files,
            timeout=30.0,
        )

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]

    conditions = response.json()["refined_conditions"]
    found_codes = {item["code"]: item["display_name"] for item in conditions}
    assert found_codes == EXPECTED_COVID_INFLUENZA_CONDITIONS

    for index, condition in enumerate(conditions):
        item_label = f"Condition #{index + 1} (Code:  {condition['code']})"

        # validate RR is well-formed
        validate_refined_xml(condition["refined_rr"], "RR", item_label, test_name)
        rr_result = validate_xml_string(condition["refined_rr"], "rr")
        assert_schematron_valid(rr_result, f"{item_label} RR", test_name)

        # validate eICR is well-formed and passes Schematron
        validate_refined_xml(condition["refined_eicr"], "eICR", item_label, test_name)
        eicr_result = validate_xml_string(condition["refined_eicr"], "eicr")
        assert_schematron_valid(eicr_result, f"{item_label} eICR", test_name)

        print(
            f"[{test_name}] ✅ {item_label} passed ({eicr_result['warnings']} warnings)"
        )

    print(f"[{test_name}] 🎉 All {len(conditions)} conditions validated!")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_zip_upload_zika_v3_1_1(
    setup,
    authed_client,
    zika_v3_1_1_zip_path,
    validate_xml_string,
):
    """
    Integration test for /api/v1/demo/upload using Mon Mothma Zika v3.1.1.
    """

    test_name = "test_zip_upload_zika_v3_1_1"

    with open(zika_v3_1_1_zip_path, "rb") as f:
        files = {"uploaded_file": (zika_v3_1_1_zip_path.name, f, "application/zip")}
        response = await authed_client.post(
            "http://0.0.0.0:8080/api/v1/demo/upload",
            files=files,
            timeout=30.0,
        )

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]

    conditions = response.json()["refined_conditions"]
    found_codes = {item["code"]: item["display_name"] for item in conditions}
    assert found_codes == EXPECTED_ZIKA_CONDITIONS

    for index, condition in enumerate(conditions):
        item_label = f"Condition #{index + 1} (Code: {condition['code']})"

        # validate RR is well-formed
        validate_refined_xml(condition["refined_rr"], "RR", item_label, test_name)
        rr_result = validate_xml_string(condition["refined_rr"], "rr")
        assert_schematron_valid(rr_result, f"{item_label} RR", test_name)

        # validate eICR is well-formed
        validate_refined_xml(condition["refined_eicr"], "eICR", item_label, test_name)
        eicr_result = validate_xml_string(condition["refined_eicr"], "eicr")
        assert_schematron_valid(eicr_result, f"{item_label} eICR", test_name)

        print(f"[{test_name}] ✅ {item_label} passed well-formedness checks")

    print(f"[{test_name}] 🎉 Zika v3.1.1 test completed!")
