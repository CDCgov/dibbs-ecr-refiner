import os
from unittest.mock import AsyncMock, MagicMock

os.environ["ENV"] = "local"
os.environ["DB_URL"] = "postgresql://mock@fakedb:5432/refiner"
os.environ["DB_PASSWORD"] = "mock"
os.environ["AUTH_PROVIDER"] = "mock-oauth-provider"
os.environ["AUTH_CLIENT_ID"] = "mock-refiner-client"
os.environ["AUTH_CLIENT_SECRET"] = "mock-secret"
os.environ["AUTH_ISSUER"] = "http://mock.com"
os.environ["SESSION_SECRET_KEY"] = "super-secret-key"

os.environ["AWS_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "refiner"
os.environ["AWS_SECRET_ACCESS_KEY"] = "refiner"
os.environ["S3_ENDPOINT_URL"] = "http://localhost:4566"
os.environ["S3_BUCKET_CONFIG"] = "mock-bucket"
os.environ["LOG_LEVEL"] = "debug"

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4
from zipfile import ZipFile

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from lxml import etree
from lxml.etree import _Element

from app.api.auth.middleware import get_logged_in_user
from app.core.models.types import XMLFiles
from app.db.conditions.model import DbCondition, DbConditionCoding
from app.db.configurations.model import DbConfiguration, DbConfigurationCondition
from app.db.pool import get_db
from app.db.users.model import DbUser
from app.main import create_fastapi_app
from tests.fixtures.loader import load_fixture_str, load_fixture_xml

type NamespaceMap = dict[str, str]
NAMESPACES: NamespaceMap = {"hl7": "urn:hl7-org:v3"}

# User info
TEST_SESSION_TOKEN = "test-token"
MOCK_CONFIGURATION_ID = UUID("11111111-1111-1111-1111-111111111111")
MOCK_CONDITION_ID = UUID("22222222-2222-2222-2222-222222222222")
MOCK_NEW_CONFIGURATION_ID = UUID("33333333-3333-3333-3333-333333333333")


class AsyncContextManagerMock:
    """Helper to create async context manager mocks."""

    def __init__(self, return_value=None):
        self.return_value = return_value or AsyncMock()

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, *args):
        return None


@pytest.fixture
def mock_db():
    """Create a mock database with proper async support."""
    db = MagicMock()

    # Create mock cursor
    mock_cursor = AsyncMock()
    mock_cursor.fetchone = AsyncMock(return_value=None)
    mock_cursor.fetchall = AsyncMock(return_value=[])
    mock_cursor.execute = AsyncMock()

    # Create mock connection
    mock_conn = AsyncMock()
    mock_conn.cursor = MagicMock(return_value=AsyncContextManagerMock(mock_cursor))

    # Setup get_connection with proper async context manager
    db.get_connection = MagicMock(return_value=AsyncContextManagerMock(mock_conn))

    # Store references for easy access in tests
    db._mock_conn = mock_conn
    db._mock_cursor = mock_cursor

    return db


@pytest.fixture
def test_app(mock_db):
    """Create a test app with mocked dependencies."""
    # Create app without lifespan (no real DB connection)
    app = create_fastapi_app(lifespan=None)

    # Override the get_db dependency with mock
    app.dependency_overrides[get_db] = lambda: mock_db

    return app


@pytest.fixture
def mock_user():
    return DbUser(
        id="5deb43c2-6a82-4052-9918-616e01d255c7",
        username="tester",
        email="tester@test.com",
        jurisdiction_id="JD-1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_condition():
    return DbCondition(
        id=uuid4(),
        display_name="Hypertension",
        canonical_url="http://url.com",
        version="3.0.0",
        child_rsg_snomed_codes=["11111"],
        snomed_codes=[DbConditionCoding("11111", "Hypertension SNOMED")],
        loinc_codes=[DbConditionCoding("22222", "Hypertension LOINC")],
        icd10_codes=[DbConditionCoding("I10", "Essential hypertension")],
        rxnorm_codes=[DbConditionCoding("33333", "Hypertension RXNORM")],
    )


@pytest.fixture
def mock_configuration(mock_user):
    return DbConfiguration(
        id=MOCK_CONFIGURATION_ID,
        name="test config",
        jurisdiction_id="SDDH",
        condition_id=MOCK_CONDITION_ID,
        included_conditions=[DbConfigurationCondition(id=MOCK_CONDITION_ID)],
        custom_codes=[],
        local_codes=[],
        section_processing=[],
        version=1,
        status="draft",
        last_activated_at=None,
        last_activated_by=None,
        created_by=mock_user.id,
        condition_canonical_url="url-1",
        s3_urls=[],
    )


@pytest_asyncio.fixture
async def authed_client(mock_logged_in_user, test_app):
    """
    Mock an authenticated client.
    """

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        client.cookies.update({"refiner-session": TEST_SESSION_TOKEN})
        yield client


@pytest.fixture
def mock_logged_in_user(mock_user, test_app):
    """
    Mock the logged-in user dependency
    """

    test_app.dependency_overrides[get_logged_in_user] = lambda: mock_user
    yield
    test_app.dependency_overrides.pop(get_logged_in_user, None)


@pytest.fixture(scope="session")
def fixtures_path() -> Path:
    """
    Returns the absolute path to the test fixtures directory.
    """

    return Path(__file__).parent.parent / "fixtures"


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
