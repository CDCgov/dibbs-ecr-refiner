import re

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

    async def test_export_returns_with_correct_headers(self, setup, authed_client):
        """
        CSV should be returned with correct content type and content-disposition.
        """
        response = await authed_client.get(URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"].startswith("text/csv")

        cd_header = response.headers.get("content-disposition", "")
        assert re.search(
            r'filename="Activity_Log_Export_\d{6}_\d{2}_\d{2}_\d{2}\.csv"',
            cd_header,
        ), f"Unexpected Content-Disposition: {cd_header!r}"
