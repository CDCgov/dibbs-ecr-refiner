import os
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient
from testcontainers.compose import DockerCompose


@pytest.fixture
def auth_cookie():
    return {"refiner-session": "test-token"}


@pytest_asyncio.fixture
async def authed_client(auth_cookie, base_url):
    async with AsyncClient(base_url=base_url) as client:
        client.cookies.update(auth_cookie)
        yield client


@pytest.fixture(scope="session")
def test_assets_path() -> Path:
    """
    Return the path to the test assets directory.
    """
    return Path(__file__).parent.parent / "assets"


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
      1. Start the Docker services defined in `docker-compose.yaml`
      2. Wait for the main application service to become healthy (via its healthcheck endpoint)
      3. Yield control to the test session
      4. After all tests in the session complete, it will tear down (stop) the Docker services

    Args:
        request: The pytest request object, used to add a finalizer for teardown
    """

    print("🚀 Setting up tests...")
    path = Path(__file__).resolve().parent.parent.parent.parent
    compose_file_name = os.path.join(path, "docker-compose.yaml")
    refiner_service = DockerCompose(path, compose_file_name=compose_file_name)

    refiner_service.start()
    refiner_service.wait_for("http://0.0.0.0:8080/api/healthcheck")
    print("✨ Message refiner services ready to test!")

    # Set up database schema
    print("Applying database schema...")
    refiner_service.exec_in_container(
        [
            "psql",
            "-U",
            "postgres",
            "-d",
            "refiner",
            "-f",
            "/app/db/schema.sql",
        ],
        "db",
    )
    print("✅ Schema applied")

    print("🧠 Seeding database with TES data...")
    refiner_service.exec_in_container(
        [
            "psql",
            "-U",
            "postgres",
            "refiner",
            "-f",
            "/docker-entrypoint-initdb.d/seed-data.sql",
        ],
        "db",
    )
    print("🧠 Seeding database with test user...")
    seed_user = """
    DO $$
    BEGIN
        INSERT INTO users (id, username, email)
        VALUES ('test-user', 'test-user', 'test@example.com')
        ON CONFLICT DO NOTHING;

        INSERT INTO sessions (token, user_id, expires_at)
        VALUES ('test-token', 'test-user', NOW() + INTERVAL '1 hour')
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
    print("Database is ready!")

    def teardown():
        """
        Registered finalizer to stop Docker Compose services.
        """

        print("🧹 Tests finished! Tearing down.")

    request.addfinalizer(teardown)
