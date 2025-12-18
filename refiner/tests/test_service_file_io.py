import zipfile
from pathlib import Path
from zipfile import ZipFile

import pytest
from lxml import etree

from app.core.exceptions import (
    FileProcessingError,
    XMLValidationError,
    ZipValidationError,
)
from app.core.models.types import XMLFiles
from app.services import file_io


class MockFileUpload:
    def __init__(self, content: bytes):
        self._content = content

    async def read(self) -> bytes:
        return self._content


def test_parse_xml_valid(covid_influenza_v1_1_files: XMLFiles):
    """
    Test parsing valid XML.
    """

    root = file_io.parse_xml(covid_influenza_v1_1_files.eicr.encode("utf-8"))
    assert root is not None
    assert root.tag.endswith("ClinicalDocument")


def test_parse_xml_invalid():
    """
    Test parsing invalid XML raises appropriate error.
    """

    with pytest.raises(XMLValidationError):
        file_io.parse_xml(b"<not>valid</xml>")


@pytest.mark.asyncio
async def test_read_xml_zip(create_test_zip, fixtures_path: Path):
    """
    Test reading XMLFiles from a zip file.
    """

    # create a new zip with proper file names
    test_zip = create_test_zip(
        {
            "CDA_eICR.xml": fixtures_path
            / "eicr_v1_1/mon_mothma_covid_influenza_eICR.xml",
            "CDA_RR.xml": fixtures_path / "eicr_v1_1/mon_mothma_covid_influenza_RR.xml",
        }
    )

    with open(test_zip, "rb") as f:
        zip_bytes = f.read()

    mock_file = MockFileUpload(zip_bytes)
    xml_files = await file_io.read_xml_zip(mock_file)

    assert isinstance(xml_files, XMLFiles)
    assert xml_files.eicr is not None

    eicr_root = xml_files.parse_eicr()
    assert isinstance(eicr_root, etree._Element)
    assert eicr_root.tag.endswith("ClinicalDocument")


@pytest.mark.asyncio
async def test_read_invalid_zip():
    """
    Test reading invalid zip file raises appropriate error.
    """

    mock_file = MockFileUpload(b"not a zip file")

    with pytest.raises(ZipValidationError) as exc_info:
        await file_io.read_xml_zip(mock_file)
    assert "Invalid ZIP file" in str(exc_info.value)


@pytest.mark.asyncio
async def test_uncompressed_zip_size_too_large(create_test_zip, fixtures_path: Path):
    # Create a valid ZIP that contains a document that is too large to process
    big_content = b"x" * (file_io.MAX_UNCOMPRESSED_SIZE + 1)

    # Use the create_test_zip fixture to handle temp paths
    zip_path = create_test_zip(
        {
            "CDA_eICR.xml": fixtures_path
            / "eicr_v1_1/mon_mothma_covid_influenza_eICR.xml",
            "CDA_RR.xml": fixtures_path / "eicr_v1_1/mon_mothma_covid_influenza_RR.xml",
        }
    )

    # Add the large file to the existing zip
    with ZipFile(zip_path, "a") as zf:
        zf.writestr("large.xml", big_content)

    with open(zip_path, "rb") as f:
        zip_bytes = f.read()

    mock_file = MockFileUpload(zip_bytes)
    with pytest.raises(ZipValidationError) as exc:
        await file_io.read_xml_zip(mock_file)
    assert "Uncompressed .zip file must not exceed" in exc.value.message


def test_xml_files_container(covid_influenza_v1_1_files: XMLFiles):
    """
    Test XMLFiles container functionality.
    """

    eicr_root = covid_influenza_v1_1_files.parse_eicr()
    assert isinstance(eicr_root, etree._Element)
    assert eicr_root.tag.endswith("ClinicalDocument")

    rr_root = covid_influenza_v1_1_files.parse_rr()
    assert isinstance(rr_root, etree._Element)
    assert rr_root.tag.endswith("ClinicalDocument")


@pytest.mark.asyncio
async def test_zip_missing_eicr(create_test_zip, fixtures_path: Path):
    """
    Test validation when eICR file is missing.
    """

    # create zip with only RR file
    test_zip = create_test_zip(
        {
            "CDA_RR.xml": fixtures_path / "eicr_v1_1/mon_mothma_covid_influenza_RR.xml",
        }
    )

    with open(test_zip, "rb") as f:
        mock_file = MockFileUpload(f.read())

    with pytest.raises(ZipValidationError) as exc_info:
        await file_io.read_xml_zip(mock_file)

    error = exc_info.value
    assert "CDA_eICR.xml not found" in str(error)


@pytest.mark.asyncio
async def test_zip_missing_rr(create_test_zip, fixtures_path: Path):
    """
    Test validation when RR file is missing.
    """

    # create zip with only eICR file
    test_zip = create_test_zip(
        {
            "CDA_eICR.xml": fixtures_path
            / "eicr_v1_1/mon_mothma_covid_influenza_eICR.xml",
        }
    )

    with open(test_zip, "rb") as f:
        mock_file = MockFileUpload(f.read())

    with pytest.raises(ZipValidationError) as exc_info:
        await file_io.read_xml_zip(mock_file)

    error = exc_info.value
    assert "CDA_RR.xml not found" in str(error)


@pytest.mark.asyncio
async def test_read_xml_zip_processing_error():
    """
    Test general error handling in read_xml_zip.
    """

    mock_file = MockFileUpload(b"not a zip but also won't raise BadZipFile")
    with pytest.raises(ZipValidationError) as exc_info:
        await file_io.read_xml_zip(mock_file)
    assert "Invalid ZIP file provided" in str(exc_info.value)


@pytest.mark.asyncio
async def test_read_xml_zip_general_error():
    """
    Test general exception handling in read_xml_zip.
    """

    class BrokenFileUpload:
        async def read(self):
            raise Exception("Simulated error")

    with pytest.raises(FileProcessingError) as exc_info:
        await file_io.read_xml_zip(BrokenFileUpload())
    assert "Failed to process ZIP file" in str(exc_info.value)


def test_get_asset_path_single():
    """
    Test getting asset path with single filename.
    """

    path = file_io.get_asset_path("refiner_details.json")
    assert path.name == "refiner_details.json"
    assert path.parent.name == "assets"
    assert isinstance(path, Path)


def test_get_asset_path_nested():
    """
    Test getting asset path with nested directory structure.
    """

    path = file_io.get_asset_path("demo", "monmothma.zip")
    assert path.name == "monmothma.zip"
    assert path.parent.name == "demo"
    assert path.parent.parent.name == "assets"
    assert isinstance(path, Path)


def test_get_asset_path_empty():
    """
    Test getting base assets directory path.
    """

    path = file_io.get_asset_path()
    assert path.name == "assets"
    assert isinstance(path, Path)


@pytest.mark.integration
def test_zip_contains_only_xml_when_html_fails() -> None:
    """
    Integration test: ZIP contains only XML if HTML transformation fails for a condition.

    Simulate by omitting HTML file for ConditionC and including for ConditionD.
    """
    files: list[tuple[str, str | bytes]] = [
        ("ConditionC-321.xml", "<xml>TestC</xml>"),  # HTML intentionally omitted for C
        ("ConditionD-654.xml", "<xml>TestD</xml>"),
        ("ConditionD-654.html", b"<html><body>HTML D</body></html>"),
    ]
    zip_name, zip_buf = file_io.create_refined_ecr_zip_in_memory(files=files)
    with zipfile.ZipFile(zip_buf, "r") as zf:
        namelist = zf.namelist()
        assert "ConditionC-321.xml" in namelist
        assert "ConditionD-654.xml" in namelist
        assert "ConditionD-654.html" in namelist
        assert "ConditionC-321.html" not in namelist  # HTML missing for C, correct
        # Verify contents
        assert zf.read("ConditionD-654.html").startswith(b"<html")
        assert zf.read("ConditionC-321.xml").decode("utf-8").startswith("<xml>")
