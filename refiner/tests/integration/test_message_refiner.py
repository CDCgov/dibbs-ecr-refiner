import io
import zipfile

import httpx
import pytest
from lxml import etree

from tests.integration.conftest import normalize_xml


@pytest.mark.integration
def test_health_check(setup):
    """
    Test service health check endpoint
    """

    response = httpx.get("http://0.0.0.0:8080/api/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


@pytest.mark.integration
def test_openapi_docs(setup):
    """
    Test OpenAPI documentation endpoint
    """

    response = httpx.get("http://0.0.0.0:8080/api/openapi.json")
    assert response.status_code == 200
    # verify basic OpenAPI structure
    openapi = response.json()
    assert "openapi" in openapi
    assert "paths" in openapi


@pytest.mark.integration
def test_ecr_refinement(setup, sample_xml_files):
    """
    Test basic eICR refinement
    """

    response = httpx.post(
        "http://0.0.0.0:8080/api/v1/ecr", content=sample_xml_files.eicr
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"

    # verify XML structure is maintained
    response_xml = normalize_xml(response.text)

    # the refined XML should be valid and maintain basic structure
    response_root = etree.fromstring(response_xml)
    assert response_root.tag == "{urn:hl7-org:v3}ClinicalDocument"

    # should maintain key elements
    assert response_root.find(".//{urn:hl7-org:v3}templateId") is not None
    assert response_root.find(".//{urn:hl7-org:v3}id") is not None


@pytest.mark.integration
def test_ecr_section_filtering(setup, sample_xml_files):
    """
    Test eICR refinement with section filtering
    """

    results_section_code = "30954-2"
    response = httpx.post(
        f"http://0.0.0.0:8080/api/v1/ecr?sections_to_include={results_section_code}",
        content=sample_xml_files.eicr,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"

    response_xml = normalize_xml(response.text)
    root = etree.fromstring(response_xml)

    # check that at least one section is minimal
    minimal_sections = root.findall(".//{urn:hl7-org:v3}section[@nullFlavor='NI']")
    assert len(minimal_sections) > 0, "No minimized sections found"

    # find the Results section
    results_section = None
    for section in root.findall(".//{urn:hl7-org:v3}section"):
        code_elem = section.find(".//{urn:hl7-org:v3}code")
        if code_elem is not None and code_elem.get("code") == results_section_code:
            results_section = section
            break

    # verify results section exists and isn't minimal
    assert results_section is not None, "Results section not found"
    assert results_section.get("nullFlavor") is None, (
        "Results section should not be minimal"
    )


@pytest.mark.integration
def test_zip_upload(setup, sample_xml_files):
    """
    Test ZIP file upload and processing
    """

    # create ZIP with both files
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("CDA_eICR.xml", sample_xml_files.eicr)
        zf.writestr("CDA_RR.xml", sample_xml_files.rr)

    files = {"file": ("test.zip", zip_buffer.getvalue(), "application/zip")}
    response = httpx.post("http://0.0.0.0:8080/api/v1/ecr/zip-upload", files=files)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    # Load JSON response
    response_json = response.json()

    assert isinstance(response_json, list)
    assert len(response_json) > 0

    refined_eicr_xml = response_json[0]["refined_eicr"]

    # Parse the XML string
    root = etree.fromstring(refined_eicr_xml.encode("utf-8"))

    # Should still be a ClinicalDocument
    assert root.tag == "{urn:hl7-org:v3}ClinicalDocument"

    # Verify key elements
    assert root.find(".//{urn:hl7-org:v3}templateId") is not None
    assert root.find(".//{urn:hl7-org:v3}id") is not None


@pytest.mark.integration
def test_error_handling(setup, sample_xml_files):
    """
    Test error handling scenarios
    """

    # invalid XML
    response = httpx.post("http://0.0.0.0:8080/api/v1/ecr", content="invalid xml")
    assert response.status_code == 400
    assert "Failed to parse XML" in response.json()["detail"]["message"]

    # invalid section code
    response = httpx.post(
        "http://0.0.0.0:8080/api/v1/ecr?sections_to_include=invalid",
        content=sample_xml_files.eicr,
    )
    assert response.status_code == 422
    assert "Invalid section codes" in response.json()["detail"]["message"]


@pytest.mark.integration
def test_service_interactions(setup, sample_xml_files):
    """
    Test interaction with other services
    """

    # test with COVID-19 condition code
    condition_code = "840539006"
    response = httpx.post(
        f"http://0.0.0.0:8080/api/v1/ecr?conditions_to_include={condition_code}",
        content=sample_xml_files.eicr,
    )
    assert response.status_code == 200

    # verify response xml
    response_xml = normalize_xml(response.text)
    root = etree.fromstring(response_xml)

    # should maintain clinical document structure
    assert root.tag == "{urn:hl7-org:v3}ClinicalDocument"

    # should find relevant clinical observations
    observations = root.findall(".//{urn:hl7-org:v3}observation")
    assert len(observations) > 0
