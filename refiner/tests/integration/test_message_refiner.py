import httpx
import pytest


@pytest.mark.integration
def test_health_check(setup):
    """
    Basic test to make sure the message refiner service can communicate with
    other up and running services.
    """
    service_response = httpx.get("http://0.0.0.0:8080/api/v1/healthcheck")
    assert service_response.status_code == 200
