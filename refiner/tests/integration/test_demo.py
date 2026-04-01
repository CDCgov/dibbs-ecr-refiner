from io import BytesIO
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import pytest
from fastapi import status

api_route_base = "/api/v1/demo"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_demo_upload_smoke(
    covid_influenza_v1_1_zip_path: Path, authed_client, test_user_jurisdiction_id
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
    assert response.status_code == status.HTTP_200_OK
    data: dict[str, Any] = response.json()
    assert "refined_conditions" in data
    assert "conditions_without_matching_configs" in data
    assert "unrefined_eicr" in data
    assert "refined_download_key" in data

    # Check zip download and contents
    file_key = data["refined_download_key"]
    download_response = await authed_client.get(
        f"{api_route_base}/download/{file_key}",
    )
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] in {
        "application/zip",
        "application/x-zip-compressed",
        "application/octet-stream",
    }

    zip_bytes = download_response.content
    assert zip_bytes

    jd = test_user_jurisdiction_id
    expected_file_names = [
        f"{jd}/Influenza/refined_eICR.xml",
        f"{jd}/Influenza/refined_RR.xml",
        f"{jd}/Influenza/refined_eICR.html",
        f"{jd}/COVID19/refined_eICR.xml",
        f"{jd}/COVID19/refined_RR.xml",
        f"{jd}/COVID19/refined_eICR.html",
        "CDA_eICR.xml",
        "CDA_RR.xml",
    ]

    with ZipFile(BytesIO(zip_bytes), "r") as zf:
        names = zf.namelist()
        assert set(names) == set(expected_file_names)
