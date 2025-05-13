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

from .conftest import EICR_FILENAME


class MockFileUpload:
    def __init__(self, content: bytes):
        self._content = content

    async def read(self) -> bytes:
        return self._content


def test_parse_xml_valid(read_test_file):
    """
    Test parsing valid XML.
    """

    xml_content = read_test_file(
        "mon-mothma-covid-lab-positive_eicr.xml"
    )  # Updated to match
    root = file_io.parse_xml(xml_content)
    assert root is not None
    assert root.tag.endswith("ClinicalDocument")


def test_parse_xml_invalid():
    """
    Test parsing invalid XML raises appropriate error.
    """

    with pytest.raises(XMLValidationError):
        file_io.parse_xml("<not>valid</xml>")


@pytest.mark.asyncio
async def test_read_xml_zip(test_assets_path, tmp_path):
    """
    Test reading XMLFiles from a zip file.
    """

    # create a new zip with proper file names
    test_zip = tmp_path / "test.zip"
    with ZipFile(test_zip, "w") as zf:
        # copy the existing files with the expected names
        with open(
            test_assets_path / "mon-mothma-covid-lab-positive_eicr.xml", "rb"
        ) as src:
            zf.writestr("CDA_eICR.xml", src.read())
        with open(
            test_assets_path / "mon-mothma-covid-lab-positive_RR.xml", "rb"
        ) as src:
            zf.writestr("CDA_RR.xml", src.read())

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


def test_xml_files_container(read_test_file):
    """
    Test XMLFiles container functionality.
    """

    xml_files = XMLFiles(
        eicr=read_test_file("mon-mothma-covid-lab-positive_eicr.xml"),  # Updated
        rr=read_test_file("mon-mothma-covid-lab-positive_RR.xml"),  # Updated
    )

    eicr_root = xml_files.parse_eicr()
    assert isinstance(eicr_root, etree._Element)
    assert eicr_root.tag.endswith("ClinicalDocument")

    rr_root = xml_files.parse_rr()
    assert isinstance(rr_root, etree._Element)
    assert rr_root.tag.endswith("ClinicalDocument")


@pytest.mark.asyncio
async def test_zip_missing_eicr(test_assets_path, tmp_path):
    """
    Test validation when eICR file is missing.
    """

    # create zip with only RR file
    test_zip = tmp_path / "test.zip"
    with ZipFile(test_zip, "w") as zf:
        # Copy the existing RR file but use the expected name
        with open(
            test_assets_path / "mon-mothma-covid-lab-positive_RR.xml", "rb"
        ) as src:
            zf.writestr("CDA_RR.xml", src.read())

    with open(test_zip, "rb") as f:
        mock_file = MockFileUpload(f.read())

    with pytest.raises(ZipValidationError) as exc_info:
        await file_io.read_xml_zip(mock_file)

    error = exc_info.value
    assert "CDA_eICR.xml not found" in str(error)


@pytest.mark.asyncio
async def test_zip_with_only_eicr(test_assets_path, tmp_path):
    """
    Test that zip with only eICR file is valid.
    """

    # create zip with only eICR file
    test_zip = tmp_path / "test.zip"
    with ZipFile(test_zip, "w") as zf:
        zf.write(test_assets_path / "CDA_eICR.xml", EICR_FILENAME)

    with open(test_zip, "rb") as f:
        mock_file = MockFileUpload(f.read())

    # should not raise an error since RR is optional
    xml_files = await file_io.read_xml_zip(mock_file)
    assert isinstance(xml_files, XMLFiles)
    assert xml_files.eicr is not None
    assert xml_files.rr is None


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
