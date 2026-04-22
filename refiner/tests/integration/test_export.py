import re

import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.asyncio
class TestConfigurationExport:
    async def test_export_returns_404_for_unknown_id(self, setup, authed_client):
        """Endpoint must return 404 for a config ID that does not exist."""
        dummy_id = "00000000-0000-0000-0000-000000000000"
        response = await authed_client.get(f"/api/v1/configurations/{dummy_id}/export")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_export_returns_csv_with_correct_headers(
        self, setup, authed_client, get_condition_id, create_config
    ):
        """
        CSV should be returned in correct form when given a valid config.
        """
        condition_id = await get_condition_id("Colorado tick fever")
        config = await create_config(condition_id)
        response = await authed_client.get(
            f"/api/v1/configurations/{config['id']}/export"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"].startswith("text/csv")

        cd_header = response.headers.get("content-disposition", "")
        assert re.search(
            r'filename=".+_Code Export_\d{6}_\d{2}:\d{2}:\d{2}\.csv"',
            cd_header,
        ), f"Unexpected Content-Disposition: {cd_header!r}"

    async def test_export_csv_body_is_non_empty(
        self, setup, authed_client, get_condition_id, create_config
    ):
        """
        CSV should contain at least a header row.
        """
        condition_id = await get_condition_id("Cholera")
        config = await create_config(condition_id)
        response = await authed_client.get(
            f"/api/v1/configurations/{config['id']}/export"
        )

        assert response.status_code == status.HTTP_200_OK
        content = response.text
        lines = [line for line in content.splitlines() if line.strip()]
        assert len(lines) >= 1, "Expected at least a CSV header row in the response"
