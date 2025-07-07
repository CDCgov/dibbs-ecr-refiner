import os
from pathlib import Path

import pytest
from testcontainers.compose import DockerCompose

os.environ["DB_URL"] = "postgres://postgres:refiner@db:5432/refiner"


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

    def teardown():
        """
        Registered finalizer to stop Docker Compose services.
        """

        print("🧹 Tests finished! Tearing down.")

    request.addfinalizer(teardown)
