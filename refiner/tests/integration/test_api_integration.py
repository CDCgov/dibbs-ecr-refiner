import pytest

# test with COVID-19 condition code
CONDITION_CODE = "840539006"


@pytest.mark.integration
@pytest.mark.asyncio
class TestHealthAndDocs:
    """
    Basic service health and documentation endpoints
    """

    async def test_health_check(self, setup, authed_client):
        response = await authed_client.get("/api/healthcheck")
        assert response.status_code == 200
        assert response.json() == {"db": "OK", "status": "OK"}

    async def test_openapi_docs(self, setup, authed_client):
        response = await authed_client.get("/api/openapi.json")
        assert response.status_code == 200
