import json
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

    # activated config
    covid_condition_id = await get_condition_id("COVID-19")
    covid_config = await create_config(covid_condition_id)
    await activate_config(covid_config["id"])

    # draft config
    flu_condition_id = await get_condition_id("Influenza")
    flu_config = await create_config(flu_condition_id)

    uploaded_file = covid_influenza_v1_1_zip_path
    with open(uploaded_file, "rb") as file_data:
        response = await authed_client.post(
            f"{api_route_base}/discover-configurations",
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

    # Both config IDs should be present
    groups_by_name = {group["name"]: group for group in data["groups"]}

    assert groups_by_name["COVID-19"]["condition_id"] == str(covid_condition_id)
    assert groups_by_name["COVID-19"]["versions"][0]["status"] == "active"
    assert groups_by_name["COVID-19"]["versions"][0]["id"] == str(covid_config["id"])

    assert groups_by_name["Influenza"]["condition_id"] == str(flu_condition_id)
    assert groups_by_name["Influenza"]["versions"][0]["status"] == "draft"
    assert groups_by_name["Influenza"]["versions"][0]["id"] == str(flu_config["id"])

    payload = {
        "configuration_ids": [covid_config["id"], flu_config["id"]],
        "unconfigured_condition_ids": [],
    }
    with open(uploaded_file, "rb") as file_data:
        response = await authed_client.post(
            f"{api_route_base}/upload",
            data={"body": json.dumps(payload)},
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

    expected_keys = {
        "message",
        "refined_conditions_found",
        "refined_conditions",
        "unrefined_eicr",
        "refined_download_key",
        "file_info_response",
    }

    assert set(data.keys()) == expected_keys

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
