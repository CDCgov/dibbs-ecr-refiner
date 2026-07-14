import pytest
from fastapi import status

TIMEZONE = "America/New_York"
URL = f"/api/v1/events/export?timezone={TIMEZONE}"


@pytest.mark.integration
@pytest.mark.asyncio
class TestEventsCsvExport:
    async def test_export_returns_200(self, setup, authed_client):
        """
        Endpoint returns a 200.
        """
        response = await authed_client.get(URL)
        assert response.status_code == status.HTTP_200_OK
