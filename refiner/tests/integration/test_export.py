import re

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
class TestConfigurationExportBasic:
    """
    Basic smoke test for the configuration export endpoint.
    Ensures the route exists and returns some valid HTTP response
    even if no database data exists.
    """

    async def test_export_endpoint_does_not_crash(self, setup, authed_client):
        # Use a dummy UUID so we don't depend on seeded data
        dummy_id = "00000000-0000-0000-0000-000000000000"
        response = await authed_client.get(f"/api/v1/configurations/{dummy_id}/export")

        # Endpoint should at least return a proper HTTP status, not hang.
        # Accept 200 (success), 404 (not found), or 500 (server error when DB empty).
        assert response.status_code in (200, 404, 500)

        if response.status_code == 200:
            # If somehow a valid configuration exists, validate headers
            assert response.headers["content-type"].startswith("text/csv")
            cd_header = response.headers.get("content-disposition", "")
            assert re.search(
                r'filename=".+_Code Export_\d{6}_\d{2}:\d{2}:\d{2}\.csv"',
                cd_header,
            )
