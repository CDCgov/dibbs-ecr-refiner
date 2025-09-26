import os
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient
from testcontainers.compose import DockerCompose

# Ensure session secret is set before this file gets imported
os.environ["SESSION_SECRET_KEY"] = "super-secret-key"
from app.api.auth.session import get_hashed_token

# Session info
TEST_SESSION_TOKEN = "test-token"
TEST_SESSION_TOKEN_HASH = get_hashed_token(TEST_SESSION_TOKEN)

# User info
TEST_USERNAME = "test-user"
TEST_USER_ID = "112569a2-315a-47b7-be57-f7f3b87734f8"

# Jurisdiction info
TEST_JD_ID = "TEST"
TEST_JD_NAME = "Test Jurisdiction"
TEST_JD_STATE_CODE = "TT"


@pytest.fixture
def test_user_id():
    return TEST_USER_ID


@pytest.fixture
def test_username():
    return TEST_USERNAME


@pytest.fixture
def auth_cookie():
    return {"refiner-session": TEST_SESSION_TOKEN}


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
            "migrate -path /app/refiner/migrations -database $(./.justscripts/sh/get_db_url.sh local) up",
        ],
        "migrate",
    )

    print("🩺 Seeding conditions...")
    refiner_service.exec_in_container(
        ["python", "/app/scripts/seeding/seed_db.py"],
        "refiner-service",
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

    print("🧠 Seeding database with test user...")
    seed_user = f"""
    DO $$
    BEGIN
        INSERT INTO jurisdictions (id, name, state_code)
        VALUES ('{TEST_JD_ID}', '{TEST_JD_NAME}', '{TEST_JD_STATE_CODE}')
        ON CONFLICT DO NOTHING;

        INSERT INTO users (id, username, email, jurisdiction_id)
        VALUES ('{TEST_USER_ID}', '{TEST_USER_ID}', 'test@example.com', '{TEST_JD_ID}')
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
