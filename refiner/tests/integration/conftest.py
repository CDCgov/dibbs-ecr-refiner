import os
from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import AsyncClient
from lxml import etree
from psycopg.rows import dict_row
from saxonche import PySaxonProcessor
from testcontainers.compose import DockerCompose

os.environ["ENV"] = "local"
os.environ["VERSION"] = "integration-test"
os.environ["DB_URL"] = "postgresql://postgres@localhost:5432/refiner"
os.environ["DB_PASSWORD"] = "refiner"
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

# ensure session secret is set before `app` imports
os.environ["SESSION_SECRET_KEY"] = "super-secret-key"

from fastapi import status
from rich.console import Console

from app.api.auth.session import get_hashed_token
from app.core.config import ENVIRONMENT
from app.db.pool import create_db
from scripts.validation.validate_document_schematron import (
    STANDARDS_MAP,
    display_svrl_results,
    get_document_template_info,
    parse_svrl,
)
from scripts.validation.validate_document_xsd import build_schema, display_xsd_results

# Session info
TEST_SESSION_TOKEN = "test-token"
TEST_SESSION_TOKEN_HASH = get_hashed_token(TEST_SESSION_TOKEN)

# User info
TEST_USERNAME = "refiner"
TEST_EMAIL = "refiner@refiner.com"
TEST_USER_ID = "673da667-6f92-4a50-a40d-f44c5bc6a2d8"

# Jurisdiction info
TEST_JD_ID = "SDDH"
TEST_JD_NAME = "Senate District Health Department"
TEST_JD_STATE_CODE = "GC"


@pytest_asyncio.fixture
async def activate_config(authed_client):
    async def _get(id: UUID):
        response = await authed_client.patch(f"/api/v1/configurations/{id}/activate")
        assert response.status_code == status.HTTP_200_OK
        return response.json()

    return _get


@pytest_asyncio.fixture
async def create_config(authed_client):
    async def _get(condition_id: UUID):
        payload = {"condition_id": str(condition_id)}
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        assert response.status_code == status.HTTP_200_OK
        return response.json()

    return _get


@pytest_asyncio.fixture(scope="session")
async def get_config_by_id(db_pool):
    async def _get(id: UUID):
        async with db_pool.get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT *
                    FROM configurations
                    WHERE id = %s
                    """,
                    (id,),
                )
                result = await cur.fetchone()
                assert result, f"Configuration with ID '{id}' not found."
                return result

    return _get


@pytest_asyncio.fixture(scope="session")
async def get_condition_by_id(db_pool):
    async def _get(id: UUID):
        async with db_pool.get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT *
                    FROM conditions
                    WHERE id = %s
                    """,
                    (id,),
                )
                result = await cur.fetchone()
                assert result, f"Condition with ID '{id}' not found."
                return result

    return _get


@pytest_asyncio.fixture(scope="session")
async def get_condition_id(db_pool):
    async def _get(name: str, version: str = "4.0.0") -> UUID:
        async with db_pool.get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT id
                    FROM conditions
                    WHERE display_name = %s
                    AND version = %s
                    """,
                    (name, version),
                )
                result = await cur.fetchone()
                assert result, f"Condition '{name}' version '{version}' not found"
                return result["id"]

    return _get


@pytest_asyncio.fixture(autouse=True)
async def reset_db(db_pool):
    yield
    # run after each test
    async with db_pool.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM configurations")


@pytest_asyncio.fixture(scope="session")
async def db_pool(setup):
    # setup as a dependency guarantees that the pool isn't created until migrations have run
    db = create_db(
        db_url=ENVIRONMENT["DB_URL"],
        db_password=ENVIRONMENT["DB_PASSWORD"],
        prepare_threshold=None,
    )
    await db.connect()

    # wait for pool to be ready
    await db.pool.wait()

    yield db
    await db.close()


@pytest.fixture
def test_user_id():
    return TEST_USER_ID


@pytest.fixture
def test_username():
    return TEST_USERNAME


@pytest.fixture
def test_user_jurisdiction_id():
    return TEST_JD_ID


@pytest.fixture
def test_session_token():
    return TEST_SESSION_TOKEN


@pytest.fixture
def auth_cookie():
    return {"refiner-session": TEST_SESSION_TOKEN}


@pytest_asyncio.fixture
async def authed_client(auth_cookie, base_url):
    async with AsyncClient(base_url=base_url) as client:
        client.cookies.update(auth_cookie)
        yield client


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


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """
    Configure logging for integration tests
    """

    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Setting up integration test logging")


@pytest.fixture(scope="session")
def base_url() -> str:
    """
    Provides the base URL for the service under test.

    Returns:
        str: The base URL (e.g., "http://0.0.0.0:8080/")
    """

    return "http://0.0.0.0:8080/"


@pytest.fixture(scope="session")
def setup(request):
    """
    Manages the lifecycle of the service running via Docker Compose

    This fixture will:
      1. Start the Docker services defined in `docker-compose.yml`
      2. Wait for the main application service to become healthy (via its healthcheck endpoint)
      3. Yield control to the test session
      4. After all tests in the session complete, it will tear down (stop) the Docker services

    Args:
        request: The pytest request object, used to add a finalizer for teardown
    """

    print("🚀 Setting up tests...")
    path = Path(__file__).resolve().parent.parent.parent.parent
    refiner_service = DockerCompose(
        path,
        compose_file_name=["docker-compose.yml", "docker-compose.override.yml"],
    )

    # restart the environment if it's already running
    # this will clear the DB volume and prevent caching issues
    refiner_service.stop()
    refiner_service.start()

    refiner_service.wait_for("http://0.0.0.0:8080/api/healthcheck")
    print("✨ Message refiner services ready to test!")

    print("☄️ Clearing data...")
    refiner_service.exec_in_container(
        [
            "psql",
            "-U",
            "postgres",
            "refiner",
            "-f",
            "/drop-all.sql",
        ],
        "db",
    )

    print("🧠 Running database migrations...")
    refiner_service.exec_in_container(
        [
            "sh",
            "-c",
            "dbmate --no-dump-schema --migrations-dir /app/refiner/migrations --url $(./.justscripts/sh/get_db_url.sh local) migrate",
        ],
        "migrate",
    )

    print("🩺 Seeding conditions...")
    refiner_service.exec_in_container(
        ["python", "/app/scripts/seeding/seed_db.py"],
        "server",
    )

    print("⏳ Waiting for conditions seeding...")
    refiner_service.exec_in_container(
        [
            "psql",
            "-U",
            "postgres",
            "-d",
            "refiner",
            "-c",
            "SELECT 1 FROM conditions LIMIT 1;",
        ],
        "db",
    )

    print("🧠 Seeding database with test user and jurisdiction...")
    seed_user = f"""
    DO $$
    BEGIN
        INSERT INTO jurisdictions (id, name, state_code)
        VALUES ('{TEST_JD_ID}', '{TEST_JD_NAME}', '{TEST_JD_STATE_CODE}')
        ON CONFLICT DO NOTHING;

        INSERT INTO users (id, username, email, jurisdiction_id)
        VALUES ('{TEST_USER_ID}', '{TEST_USERNAME}', '{TEST_EMAIL}', '{TEST_JD_ID}')
        ON CONFLICT DO NOTHING;

        INSERT INTO sessions (token_hash, user_id, expires_at)
        VALUES ('{TEST_SESSION_TOKEN_HASH}', '{TEST_USER_ID}', NOW() + INTERVAL '1 hour')
        ON CONFLICT DO NOTHING;
    END $$;
    """
    refiner_service.exec_in_container(
        [
            "psql",
            "-U",
            "postgres",
            "-d",
            "refiner",
            "-c",
            seed_user,
        ],
        "db",
    )

    print("🏃‍♀️ Database is ready!")

    def teardown():
        """
        Registered finalizer to stop Docker Compose services.
        """

        print("🧹 Tests finished! Tearing down.")

    request.addfinalizer(teardown)


@pytest.fixture(scope="session")
def fixtures_path() -> Path:
    """
    Return the path to the test fixtures directory.
    """

    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def validate_xml_string():
    """
    Fixture providing XML validation against Schematron rules.
    Delegates to the canonical validation logic in scripts/validation/.
    """

    def _validate(xml_string: str, doc_type_hint: str) -> dict:
        # parse and detect version (same logic as determine_validation_path, but for strings)
        root = etree.fromstring(xml_string.encode("utf-8"))
        nsmap = {"hl7": "urn:hl7-org:v3"}
        root_oid, extension = get_document_template_info(root, nsmap)

        if not root_oid or root_oid not in STANDARDS_MAP:
            raise ValueError(f"Could not detect document type.  OID: {root_oid}")

        standard_family = STANDARDS_MAP[root_oid]
        if extension not in standard_family["versions"]:
            raise ValueError(
                f"Unknown version extension: {extension} for OID: {root_oid}"
            )

        xslt_path = standard_family["versions"][extension]["path"]
        if not xslt_path.exists():
            raise FileNotFoundError(f"XSLT not found: {xslt_path}")

        # run schematron validation (same as validate_xml_with_schematron)
        with PySaxonProcessor(license=False) as processor:
            xslt_processor = processor.new_xslt30_processor()
            executable = xslt_processor.compile_stylesheet(
                stylesheet_file=str(xslt_path)
            )
            xdm_node = processor.parse_xml(xml_text=xml_string)
            svrl_output = executable.transform_to_string(xdm_node=xdm_node)

            if not svrl_output:
                return {"errors": 0, "warnings": 0, "details": []}

            # parse svrl using the canonical parser
            results = parse_svrl(svrl_output)
            errors = [r for r in results if r["severity"] in ("ERROR", "FATAL")]
            warnings = [r for r in results if r["severity"] == "WARNING"]

            return {
                "errors": len(errors),
                "warnings": len(warnings),
                "details": results,
            }

    return _validate


@pytest.fixture(scope="session")
def xsd_schema():
    """
    Build the CDA R2 XMLSchema once per session — compilation is expensive.
    All tests share this single compiled schema instance.
    """
    console = Console()
    schema = build_schema(console)
    if schema is None:
        pytest.fail(
            "Could not compile CDA R2 XSD schema — check cda-r2-schema/ layout."
        )
    return schema


@pytest.fixture
def validate_xml_string_xsd(xsd_schema):
    """
    Fixture providing CDA R2 XSD validation for an XML string.

    Returns {"errors": int, "details": list[dict]} matching the schematron
    fixture shape so assert_xsd_valid mirrors assert_schematron_valid exactly.
    """

    def _validate(xml_string: str) -> dict:
        try:
            doc = etree.fromstring(xml_string.encode("utf-8"))
        except etree.XMLSyntaxError as e:
            raise ValueError(f"XML parse error before XSD validation: {e}")

        xsd_schema.validate(etree.ElementTree(doc))
        details = [
            {
                "severity": "ERROR",
                "message": err.message,
                "location": f"line {err.line}, col {err.column}",
                "path": err.path or "unknown",
            }
            for err in xsd_schema.error_log
        ]
        return {"errors": len(details), "details": details}

    return _validate


def validate_refined_xml(
    xml_string: str,
    doc_type: str,
    item_label: str,
    test_name: str,
) -> etree._Element:
    """
    Validate that an XML string is well-formed and has the expected CDA root tag.

    Raises AssertionError with detailed message if validation fails.
    Returns the parsed root element for further inspection if needed.
    """
    assert xml_string and isinstance(xml_string, str), (
        f"[{test_name}] Expected non-empty string for {item_label} '{doc_type}', "
        f"got {type(xml_string)}"
    )

    try:
        root = etree.fromstring(xml_string.encode("utf-8"))
    except etree.XMLSyntaxError as e:
        pytest.fail(
            f"[{test_name}] Expected well-formed XML for {item_label} {doc_type}, "
            f"got XMLSyntaxError: {e}.  Content (first 500 chars): {xml_string[:500]}"
        )

    assert root.tag == "{urn:hl7-org:v3}ClinicalDocument", (
        f"[{test_name}] Expected root tag '{{urn:hl7-org:v3}}ClinicalDocument' "
        f"for {item_label} {doc_type}, got {root.tag}"
    )

    return root


def assert_schematron_valid(
    validation_result: dict,
    item_label: str,
    test_name: str,
) -> None:
    """
    Assert that a Schematron validation result has no errors.

    Fails with detailed error messages if validation errors are present.
    """

    if validation_result["errors"] == 0:
        return

    console = Console()

    # filter to just errors
    errors_only = [
        row
        for row in validation_result["details"]
        if row["severity"] in ("ERROR", "FATAL")
    ]

    console.print(f"\n[bold red]Validation Failed:[/bold red] {item_label}\n")
    display_svrl_results(errors_only, console)

    pytest.fail(
        f"[{test_name}] Expected 0 Schematron errors for {item_label}, "
        f"got {validation_result['errors']} errors (see above for details)"
    )


def assert_xsd_valid(
    validation_result: dict,
    item_label: str,
    test_name: str,
) -> None:
    """
    Assert that a CDA R2 XSD validation result has no errors.

    Fails with detailed error messages if validation errors are present.
    Mirrors assert_schematron_valid in structure and output style.
    """

    if validation_result["errors"] == 0:
        return

    console = Console()
    console.print(f"\n[bold red]XSD Validation Failed:[/bold red] {item_label}\n")
    display_xsd_results(validation_result["details"], console)

    pytest.fail(
        f"[{test_name}] Expected 0 XSD errors for {item_label}, "
        f"got {validation_result['errors']} errors (see above for details)"
    )
