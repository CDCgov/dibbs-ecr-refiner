import pytest
from lxml import etree

# test with COVID-19 condition code
CONDITION_CODE = "840539006"


@pytest.mark.integration
@pytest.mark.asyncio
class TestHealthAndDocs:
    """
    Basic service health and documentation endpoints
    """

    async def test_health_check(self, setup, authed_client):
        response = await authed_client.get("/api/healthcheck")
        assert response.status_code == 200
        assert response.json() == {"db": "OK", "status": "OK"}

    async def test_openapi_docs(self, setup, authed_client):
        response = await authed_client.get("/api/openapi.json")
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
class TestECREndpoint:
    """
    Tests for /api/v1/ecr endpoint
    """

    async def test_basic_refinement(self, setup, sample_xml_files, authed_client):
        """
        Test basic XML refinement without parameters
        """

        response = await authed_client.post(
            f"/api/v1/ecr?conditions_to_include={CONDITION_CODE}",
            content=sample_xml_files.eicr,
        )
        assert response.status_code == 200
        # we should create a fixture for expected output and verify against that
        assert response.headers["content-type"] == "application/xml"
        # verify basic XML structure is maintained
        root = etree.fromstring(response.content)
        assert root.tag == "{urn:hl7-org:v3}ClinicalDocument"

    @pytest.mark.parametrize(
        "sections",
        [
            # social history
            "29762-2",
            # labs and reason for visit
            "30954-2,29299-5",
        ],
    )
    async def test_section_filtering(
        self, setup, sections, sample_xml_files, authed_client
    ):
        """
        Test section-based filtering
        """

        response = await authed_client.post(
            f"/api/v1/ecr?sections_to_include={sections}&conditions_to_include={CONDITION_CODE}",
            content=sample_xml_files.eicr,
        )
        assert response.status_code == 200
        root = etree.fromstring(response.content)

        # verify only requested sections are present
        namespaces = {"hl7": "urn:hl7-org:v3"}
        section_codes = sections.split(",")
        found_sections = root.findall(".//hl7:section/hl7:code", namespaces)
        found_codes = [s.get("code") for s in found_sections]

        for code in section_codes:
            assert code in found_codes, f"Section {code} not found in response"

    async def test_error_handling(self, setup, sample_xml_files, authed_client):
        """
        Test API error responses
        """

        # invalid xml
        response = await authed_client.post(
            f"/api/v1/ecr?conditions_to_include={CONDITION_CODE}",
            content="invalid xml",
        )
        assert response.status_code == 400
        error = response.json()
        assert "Failed to parse XML" in error["detail"]["message"]

        # invalid section code
        response = await authed_client.post(
            "/api/v1/ecr?sections_to_include=invalid&conditions_to_include={CONDITION_CODE}",
            content=sample_xml_files.eicr,
        )
        assert response.status_code == 422
        error = response.json()
        assert "Invalid section codes" in error["detail"]["message"]


@pytest.mark.integration
@pytest.mark.asyncio
class TestZipUploadEndpoint:
    """
    Tests for /api/v1/ecr/zip-upload endpoint
    """

    async def test_basic_upload(
        self, setup, tmp_path, create_test_zip, test_assets_path, authed_client
    ):
        """
        Test basic ZIP upload processing
        """

        # use paths to the mon-mothma test files
        files = {
            "CDA_eICR.xml": test_assets_path / "mon-mothma-covid-lab-positive_eicr.xml",
            "CDA_RR.xml": test_assets_path / "mon-mothma-covid-lab-positive_RR.xml",
        }
        zip_path = create_test_zip(tmp_path, files)

        with open(zip_path, "rb") as f:
            response = await authed_client.post(
                "/api/v1/ecr/zip-upload",
                files={"file": ("test.zip", f, "application/zip")},
            )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        # Parse JSON to get refined XML
        response_json = response.json()
        assert isinstance(response_json, list)
        assert len(response_json) > 0

        refined_eicr_xml = response_json[0]["refined_eicr"]
        root = etree.fromstring(refined_eicr_xml.encode("utf-8"))

        # Verify expected XML structure
        assert root.tag == "{urn:hl7-org:v3}ClinicalDocument"
        assert root.find(".//{urn:hl7-org:v3}templateId") is not None
        assert root.find(".//{urn:hl7-org:v3}id") is not None

    async def test_upload_with_sections(
        self, setup, tmp_path, create_test_zip, test_assets_path, authed_client
    ):
        """
        Test ZIP upload with section filtering
        """

        files = {
            "CDA_eICR.xml": test_assets_path / "mon-mothma-covid-lab-positive_eicr.xml",
            "CDA_RR.xml": test_assets_path / "mon-mothma-covid-lab-positive_RR.xml",
        }
        zip_path = create_test_zip(tmp_path, files)

        with open(zip_path, "rb") as f:
            response = await authed_client.post(
                "/api/v1/ecr/zip-upload?sections_to_include=30954-2",
                files={"file": ("test.zip", f, "application/zip")},
            )
        assert response.status_code == 200

        response_json = response.json()
        assert isinstance(response_json, list)
        assert len(response_json) > 0

        # Extract and parse the refined XML
        refined_xml = response_json[0]["refined_eicr"]
        root = etree.fromstring(refined_xml.encode("utf-8"))

        # Check that only requested section code is present
        namespaces = {"hl7": "urn:hl7-org:v3"}
        sections = root.findall(".//hl7:section/hl7:code", namespaces)
        section_codes = [s.get("code") for s in sections]

        assert "30954-2" in section_codes
        assert len(section_codes) == 8

    async def test_upload_errors(self, setup, tmp_path, authed_client):
        """
        Test ZIP upload error handling
        """

        # create a ZIP with invalid content
        import io
        import zipfile

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("CDA_eICR.xml", "invalid xml")
            zf.writestr("CDA_RR.xml", "also invalid")

        response = await authed_client.post(
            "/api/v1/ecr/zip-upload",
            files={"file": ("test.zip", zip_buffer.getvalue(), "application/zip")},
        )
        assert response.status_code == 400
        error = response.json()
        assert "Failed to parse XML" in error["detail"]["message"]
