import os
from pathlib import Path

import pytest
from testcontainers.compose import DockerCompose


@pytest.fixture(scope="session")
def setup(request):
    print("Setting up tests...")
    path = Path(__file__).resolve().parent.parent.parent.parent.parent
    compose_file_name = os.path.join(path, "docker-compose.yaml")
    refiner_service = DockerCompose(path, compose_file_name=compose_file_name)

    refiner_service.start()
    refiner_service.wait_for("http://0.0.0.0:8080")
    print("Message refiner services ready to test!")

    def teardown():
        print("Tests finished! Tearing down.")

    request.addfinalizer(teardown)
