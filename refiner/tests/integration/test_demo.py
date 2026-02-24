from pathlib import Path
from typing import Any

import pytest

api_route_base = "/api/v1/demo"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_demo_upload_smoke(
    covid_influenza_v1_1_zip_path: Path, authed_client
) -> None:
    """
    Smoke test for the /api/v1/demo/upload endpoint.
    Verifies that the endpoint processes a demo ZIP file and returns a 200 with expected top-level fields.
    """

    uploaded_file = covid_influenza_v1_1_zip_path
    with open(uploaded_file, "rb") as file_data:
        response = await authed_client.post(
            f"{api_route_base}/upload",
            files={
                "uploaded_file": (
                    "mon_mothma_covid_influenza_1.1.zip",
                    file_data,
                    "application/zip",
                )
            },
        )
    assert response.status_code == 200
    data: dict[str, Any] = response.json()
    assert "refined_conditions" in data
    assert "conditions_without_matching_configs" in data
    assert "unrefined_eicr" in data
    assert "refined_download_key" in data
