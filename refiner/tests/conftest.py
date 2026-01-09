import os
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile

import pytest
from lxml import etree
from lxml.etree import _Element

from app.core.models.types import XMLFiles
from tests.fixtures.loader import load_fixture_str, load_fixture_xml

os.environ["ENV"] = "mock-env"
os.environ["DB_URL"] = "postgresql://mock@fakedb:5432/refiner"
os.environ["PASSWORD"] = "mock"
os.environ["AUTH_PROVIDER"] = "mock-oauth-provider"
os.environ["AUTH_CLIENT_ID"] = "mock-refiner-client"
os.environ["AUTH_CLIENT_SECRET"] = "mock-secret"
os.environ["AUTH_ISSUER"] = "http://mock.com"
os.environ["SESSION_SECRET_KEY"] = "mock-session-secret"

os.environ["AWS_REGION"] = "us-east-1"
os.environ["S3_ENDPOINT_URL"] = "http://localhost:4566"
os.environ["S3_UPLOADED_FILES_BUCKET_NAME"] = "mock-bucket"


type NamespaceMap = dict[str, str]
NAMESPACES: NamespaceMap = {"hl7": "urn:hl7-org:v3"}


@pytest.fixture(scope="session")
def fixtures_path() -> Path:
    """
    Returns the absolute path to the test fixtures directory.
    """

    return Path(__file__).parent / "fixtures"


@pytest.fixture
def create_test_zip(tmp_path: Path):
    """
    Utility to create a temporary zip file for testing purposes.

    Takes a dict of {zip_arc_name: source_content_path}.
    """

    def _create_zip(files: dict[str, Path]) -> Path:
        zip_path = tmp_path / "test.zip"
        with ZipFile(zip_path, "w") as zf:
            for zip_name, source_path in files.items():
                zf.write(source_path, zip_name)
        return zip_path

    return _create_zip


def normalize_xml(xml: str) -> str:
    """
    Normalizes an XML string for consistent comparison in tests.
    """

    parser = etree.XMLParser(remove_blank_text=True)
    return etree.tostring(
        etree.fromstring(xml.encode("utf-8"), parser),
        pretty_print=True,
        encoding="unicode",
    ).strip()


@pytest.fixture(scope="session")
def eicr_v1_1_covid_influenza() -> etree._Element:
    """
    Loads the Mon Mothma v1.1 COVID+Influenza eICR document once per session.
    """

    return load_fixture_xml("eicr_v1_1/mon_mothma_covid_influenza_eICR.xml")


@pytest.fixture(scope="session")
def eicr_v3_1_1_zika() -> etree._Element:
    """
    Loads the Mon Mothma v3.1.1 Zika eICR document once per session.
    """

    return load_fixture_xml("eicr_v3_1_1/mon_mothma_zika_eICR.xml")


@pytest.fixture
def covid_influenza_v1_1_files() -> XMLFiles:
    """
    Provides an XMLFiles object for the v1.1 COVID+Influenza test data.
    """

    return XMLFiles(
        eicr=load_fixture_str("eicr_v1_1/mon_mothma_covid_influenza_eICR.xml"),
        rr=load_fixture_str("eicr_v1_1/mon_mothma_covid_influenza_RR.xml"),
    )


@pytest.fixture
def zika_v3_1_1_files() -> XMLFiles:
    """
    Provides an XMLFiles object for the v3.1.1 Zika test data.
    """

    return XMLFiles(
        eicr=load_fixture_str("eicr_v3_1_1/mon_mothma_zika_eICR.xml"),
        rr=load_fixture_str("eicr_v3_1_1/mon_mothma_zika_RR.xml"),
    )


@pytest.fixture
def covid_influenza_v1_1_zip_path(fixtures_path: Path) -> Path:
    """
    Returns the Path to the packaged v1.1 COVID+Influenza zip file.
    """

    if (
        path := fixtures_path / "eicr_v1_1/mon_mothma_covid_influenza_1.1.zip"
    ) and path.exists():
        return path
    else:
        pytest.fail(f"Fixture ZIP file not found: {path}")


@pytest.fixture
def zika_v3_1_1_zip_path(fixtures_path: Path) -> Path:
    """
    Returns the Path to the packaged v3.1.1 Zika zip file.
    """

    if (
        path := fixtures_path / "eicr_v3_1_1/mon_mothma_zika_3.1.1.zip"
    ) and path.exists():
        return path
    else:
        pytest.fail(f"Fixture ZIP file not found: {path}")


@pytest.fixture
def structured_body_v1_1(eicr_v1_1_covid_influenza: _Element) -> _Element:
    """
    Provides a mutable copy of the <structuredBody> from the v1.1 eICR fixture.
    """

    if (
        body := eicr_v1_1_covid_influenza.find(
            path=".//hl7:structuredBody", namespaces=NAMESPACES
        )
    ) is not None:
        return deepcopy(body)
    else:
        pytest.fail("No <structuredBody> found in v1.1 eICR fixture.")


@pytest.fixture
def structured_body_v3_1_1(eicr_v3_1_1_zika: _Element) -> _Element:
    """
    Provides a mutable copy of the <structuredBody> from the v3.1.1 eICR fixture.
    """

    if (
        body := eicr_v3_1_1_zika.find(
            path=".//hl7:structuredBody", namespaces=NAMESPACES
        )
    ) is not None:
        return deepcopy(body)
    else:
        pytest.fail("No <structuredBody> found in v3.1.1 eICR fixture.")
