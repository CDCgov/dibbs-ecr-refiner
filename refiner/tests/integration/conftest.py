import os
from pathlib import Path

import pytest
from lxml import etree
from testcontainers.compose import DockerCompose


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
def base_url():
    """
    Service base URL
    """

    return "http://0.0.0.0:8080/"


def normalize_xml(xml: str) -> str:
    """
    Normalize XML string for comparison.
    """

    return etree.tostring(
        etree.fromstring(xml), pretty_print=True, encoding="unicode"
    ).strip()


@pytest.fixture(scope="session")
def setup(request):
    """
    Use docker compose to run the service and test and then tear down container services.
    """

    print("🚀 Setting up tests...")
    path = Path(__file__).resolve().parent.parent.parent.parent
    compose_file_name = os.path.join(path, "docker-compose.yaml")
    refiner_service = DockerCompose(path, compose_file_name=compose_file_name)

    refiner_service.start()
    refiner_service.wait_for("http://0.0.0.0:8080/api/healthcheck")
    print("✨ Message refiner services ready to test!")

    def teardown():
        print("🧹 Tests finished! Tearing down.")

    request.addfinalizer(teardown)
