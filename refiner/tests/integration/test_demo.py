from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from fastapi import status

api_route_base = "/api/v1/demo"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_demo_upload_smoke(
    covid_influenza_v1_1_zip_path: Path,
    authed_client,
    get_condition_id,
    create_config,
    activate_config,
) -> None:
    """
    Smoke test for the /api/v1/demo/upload endpoint.
    Verifies that the endpoint processes a demo ZIP file and returns a 200 with expected top-level fields.
    """

    covid_id = await get_condition_id("COVID-19")
    flu_id = await get_condition_id("Influenza")

    covid_config = await create_config(covid_id)
    await activate_config(covid_config["id"])
    flu_config = await create_config(flu_id)
    await activate_config(flu_config["id"])

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
    data = response.json()
    assert "refined_conditions" in data
    assert "conditions_without_matching_configs" in data
    assert "unrefined_eicr" in data
    assert "refined_download_key" in data

    # Check zip download and contents
    file_key = data["refined_download_key"]
    download_response = await authed_client.get(
        f"{api_route_base}/download/{file_key}",
    )

    assert download_response.status_code == status.HTTP_200_OK
    assert download_response.headers["content-type"] in {
        "application/zip",
        "application/x-zip-compressed",
        "application/octet-stream",
    }

    zip_bytes = download_response.content
    assert zip_bytes

    expected_file_names = [
        "CDA_eICR_Influenza.xml",
        "CDA_RR_Influenza.xml",
        "CDA_eICR_Influenza.html",
        "CDA_eICR_COVID19.xml",
        "CDA_RR_COVID19.xml",
        "CDA_eICR_COVID19.html",
        "CDA_eICR.xml",
        "CDA_RR.xml",
    ]

    with ZipFile(BytesIO(zip_bytes), "r") as zf:
        names = zf.namelist()
        assert set(names) == set(expected_file_names)
