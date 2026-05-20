import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from fastapi import status

api_route_base = "/api/v1/simulator"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_independent_test_flow_smoke(
    covid_influenza_v1_1_zip_path: Path,
    authed_client,
    get_condition_id,
    create_config,
    activate_config,
) -> None:
    """
    Smoke test for the simulate test flow.
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
    sets_by_name = {set["name"]: set for set in data["sets"]}

    assert sets_by_name["COVID-19"]["condition_id"] == str(covid_condition_id)
    assert sets_by_name["COVID-19"]["versions"][0]["status"] == "active"
    assert sets_by_name["COVID-19"]["versions"][0]["id"] == str(covid_config["id"])

    assert sets_by_name["Influenza"]["condition_id"] == str(flu_condition_id)
    assert sets_by_name["Influenza"]["versions"][0]["status"] == "draft"
    assert sets_by_name["Influenza"]["versions"][0]["id"] == str(flu_config["id"])

    payload = {
        "configuration_ids": [covid_config["id"], flu_config["id"]],
        "unconfigured_condition_ids": [],
        "unused_condition_ids": [],
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

    # no shadow RR should exist
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


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize(
    "unconfigured_condition_ids_fixture, unused_condition_ids_fixture",
    [
        ("flu", []),  # only unconfigured
        ([], "flu"),  # only unused
        ("flu", "flu"),  # both
    ],
)
async def test_shadow_rr_is_produced(
    covid_influenza_v1_1_zip_path: Path,
    authed_client,
    get_condition_id,
    create_config,
    unconfigured_condition_ids_fixture,
    unused_condition_ids_fixture,
) -> None:
    """
    Tests that the shadow RR is produced during the test run in the following situations:
    1. `unconfigured_condition_ids` has associated condition IDs
    2. `unused_condition_ids` has associated condition IDs
    3. Both fields have associated condition IDs
    """

    # draft config
    covid_condition_id = await get_condition_id("COVID-19")
    covid_config = await create_config(covid_condition_id)

    # draft config
    flu_condition_id = await get_condition_id("Influenza")

    uploaded_file = covid_influenza_v1_1_zip_path

    # helper function to get the actual ID
    def resolve(fixture):
        return [str(flu_condition_id)] if fixture == "flu" else []

    payload = {
        "configuration_ids": [covid_config["id"]],
        "unconfigured_condition_ids": resolve(unconfigured_condition_ids_fixture),
        "unused_condition_ids": resolve(unused_condition_ids_fixture),
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

    # Check zip download and contents
    file_key = data["refined_download_key"]
    download_response = await authed_client.get(
        f"{api_route_base}/download/{file_key}",
    )

    assert download_response.status_code == status.HTTP_200_OK
    zip_bytes = download_response.content
    assert zip_bytes

    # no influenza files should exist, only shadow RR
    expected_file_names = [
        "CDA_eICR_COVID19.xml",
        "CDA_RR_COVID19.xml",
        "CDA_eICR_COVID19.html",
        "CDA_eICR.xml",
        "CDA_RR.xml",
        "CDA_RR_unrefined_rr.xml",
    ]

    with ZipFile(BytesIO(zip_bytes), "r") as zf:
        names = zf.namelist()
        assert set(names) == set(expected_file_names)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_discovers_configs_across_all_tes_versions(
    get_condition_id,
    create_config,
    activate_config,
    covid_influenza_v1_1_zip_path,
    authed_client,
):
    """
    Test that the discovery feature will find all configurations for a reportable condition
    regardless of their TES version. The app should be able to handle multiple versions at the
    same time.

    NOTE: The `condition_id` of the set will be the latest TES version's condition ID.
    """
    current_covid_id = await get_condition_id("COVID-19", "5.0.0")
    current_flu_id = await get_condition_id("Influenza", "5.0.0")

    old_covid_id = await get_condition_id("COVID-19", "3.0.0")
    old_flu_id = await get_condition_id("Influenza", "4.0.0")

    # create a bunch of 3.0.0 COVID configs
    for _ in range(21):
        config = await create_config(old_covid_id)
        await activate_config(config["id"])

    # create a 5.0.0 COVID draft
    await create_config(current_covid_id)

    # create a bunch of 4.0.0 influenza configs
    for _ in range(27):
        config = await create_config(old_flu_id)
        await activate_config(config["id"])

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

    sets_by_name = {set["name"]: set for set in data["sets"]}
    assert len(sets_by_name["COVID-19"]["versions"]) == 22
    assert sets_by_name["COVID-19"]["condition_id"] == str(current_covid_id)

    assert len(sets_by_name["Influenza"]["versions"]) == 27
    assert sets_by_name["Influenza"]["condition_id"] == str(current_flu_id)
