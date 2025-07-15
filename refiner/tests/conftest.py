import os
from pathlib import Path
from zipfile import ZipFile

import pytest
from lxml import etree

from app.core.models.types import XMLFiles

NAMESPACES: dict[str, str] = {"hl7": "urn:hl7-org:v3"}


# file names that read_xml_zip looks for
EICR_FILENAME = "CDA_eICR.xml"
RR_FILENAME = "CDA_RR.xml"

os.environ["DB_URL"] = "postgresql://mock:mock@fakedb:5432/refiner"
os.environ["AUTH_PROVIDER"] = "mock-oauth-provider"
os.environ["AUTH_CLIENT_ID"] = "mock-refiner-client"
os.environ["AUTH_CLIENT_SECRET"] = "mock-secret"
os.environ["AUTH_ISSUER"] = "http://mock.com"


@pytest.fixture(scope="session")
def test_assets_path() -> Path:
    """
    Return the path to the test assets directory.
    """

    return Path(__file__).parent / "assets"


@pytest.fixture(scope="session")
def read_test_file():
    """
    Fixture to read file contents from test assets.
    """

    def _read_file(filename: str) -> str:
        """Read a file from the test assets directory.

        Args:
            filename: Name of the file in the test assets directory

        Returns:
            str: Contents of the file
        """

        with open(
            Path(__file__).parent / "assets" / filename, encoding="utf-8"
        ) as file:
            return file.read()

    return _read_file


@pytest.fixture(scope="session")
def read_test_xml():
    """
    Fixture to read and parse XML files from test assets.
    """

    def _read_xml(filename: str) -> etree.Element:
        """
        Read and parse an XML file from test assets.

        Args:
            filename: Name of the XML file in test assets directory

        Returns:
            etree.Element: Parsed XML root element
        """

        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(Path(__file__).parent / "assets" / filename, parser)
        return tree.getroot()

    return _read_xml


@pytest.fixture
def create_test_zip():
    def _create_zip(tmp_path: Path, files: dict[str, str]) -> Path:
        """
        Create a test ZIP file with given content.

        Args:
            tmp_path: Path to create ZIP in
            files: Dict of {zip_path: source_path} for files to include

        Returns:
            Path to created ZIP file
        """

        zip_path = tmp_path / "test.zip"
        with ZipFile(zip_path, "w") as zf:
            for zip_name, source_path in files.items():
                zf.write(source_path, zip_name)
        return zip_path

    return _create_zip


@pytest.fixture(scope="session")
def sample_xml_files(read_test_file) -> XMLFiles:
    """
    Fixture to provide sample eICR and RR XML files.

    Returns:
        XMLFiles: Container with sample eICR and RR content
    """

    return XMLFiles(
        eicr=read_test_file("mon-mothma-covid-lab-positive_eicr.xml"),
        rr=read_test_file("mon-mothma-covid-lab-positive_RR.xml"),
    )


def normalize_xml(xml: str) -> str:
    """
    Normalize XML string for comparison.
    """

    return etree.tostring(
        etree.fromstring(xml), pretty_print=True, encoding="unicode"
    ).strip()
