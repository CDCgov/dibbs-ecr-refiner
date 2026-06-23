import csv
import re
import zipfile
from io import BytesIO, StringIO

import pytest
from fastapi import status

from app.db.code_systems.db import get_all_code_systems_db
from app.db.conditions.db import get_condition_codes_by_condition_id_db
from app.db.configurations.model import DbConfigurationCustomCode


def get_csv_from_zip(content: bytes, filename_pattern: str) -> str:
    """Extract a CSV file from a zip response by filename pattern."""
    with zipfile.ZipFile(BytesIO(content)) as zf:
        for name in zf.namelist():
            if re.search(filename_pattern, name):
                return zf.read(name).decode("utf-8")
    raise FileNotFoundError(f"No file matching {filename_pattern!r} found in zip")


@pytest.mark.integration
@pytest.mark.asyncio
class TestConfigurationExport:
    async def test_export_returns_404_for_unknown_id(self, setup, authed_client):
        """
        Endpoint must return 404 for a config ID that does not exist.
        """
        dummy_id = "00000000-0000-0000-0000-000000000000"
        response = await authed_client.get(f"/api/v1/configurations/{dummy_id}/export")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_export_returns_zip_with_correct_headers(
        self, setup, authed_client, get_condition_id, create_config
    ):
        """
        Zip should be returned in correct form when given a valid config.
        """
        condition_id = await get_condition_id("Colorado tick fever")
        config = await create_config(condition_id)
        response = await authed_client.get(
            f"/api/v1/configurations/{config['id']}/export"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"].startswith("application/zip")

        cd_header = response.headers.get("content-disposition", "")
        assert re.search(
            r'filename=".+_Configuration_Export_\d{6}_\d{2}_\d{2}_\d{2}\.zip"',
            cd_header,
        ), f"Unexpected Content-Disposition: {cd_header!r}"

    async def test_export_zip_contains_expected_files(
        self, setup, authed_client, get_condition_id, create_config
    ):
        """
        Zip should contain a codes CSV and a sections CSV.
        """
        condition_id = await get_condition_id("Colorado tick fever")
        config = await create_config(condition_id)
        response = await authed_client.get(
            f"/api/v1/configurations/{config['id']}/export"
        )

        assert response.status_code == status.HTTP_200_OK

        with zipfile.ZipFile(BytesIO(response.content)) as zf:
            names = zf.namelist()
            assert any(re.search(r"Code_Export.+\.csv", n) for n in names)
            assert any(re.search(r"Section_Export.+\.csv", n) for n in names)

    async def test_export_includes_all_codes_from_multiple_codesets(
        self,
        setup,
        authed_client,
        get_condition_id,
        create_config,
        associate_codeset,
        db_pool,
    ):
        """
        CSV export should include all codes from primary and associated code sets.
        """
        amebiasis_id = await get_condition_id("Amebiasis")
        config = await create_config(amebiasis_id)
        config_id = config["id"]

        byssinosis_id = await get_condition_id("Byssinosis")
        await associate_codeset(config_id, byssinosis_id)

        amebiasis_codes = await get_condition_codes_by_condition_id_db(
            id=amebiasis_id, db=db_pool
        )
        byssinosis_codes = await get_condition_codes_by_condition_id_db(
            id=byssinosis_id, db=db_pool
        )
        expected_code_rows = len(amebiasis_codes) + len(byssinosis_codes)

        response = await authed_client.get(f"/api/v1/configurations/{config_id}/export")
        assert response.status_code == status.HTTP_200_OK

        content = get_csv_from_zip(response.content, r"Code_Export")
        lines = [line for line in content.splitlines() if line.strip()]
        assert len(lines) == expected_code_rows + 1  # header + codes

    async def test_export_csv_conditions_column_correct(
        self,
        setup,
        authed_client,
        get_condition_id,
        create_config,
        associate_codeset,
    ):
        """
        CSV "Condition" column should only contain the associated condition names.
        """
        amebiasis_id = await get_condition_id("Amebiasis")
        config = await create_config(amebiasis_id)
        config_id = config["id"]

        byssinosis_id = await get_condition_id("Byssinosis")
        await associate_codeset(config_id, byssinosis_id)

        response = await authed_client.get(f"/api/v1/configurations/{config_id}/export")
        assert response.status_code == status.HTTP_200_OK

        content = get_csv_from_zip(response.content, r"Code_Export")
        reader = csv.DictReader(StringIO(content))
        conditions_in_csv = {row["Condition"] for row in reader if row["Condition"]}

        assert conditions_in_csv == {"Amebiasis", "Byssinosis"}

    async def test_export_csv_code_systems_valid(
        self,
        setup,
        authed_client,
        get_condition_id,
        create_config,
        db_pool,
        add_custom_code,
    ):
        """
        CSV "Code System" column should only contain valid system names.
        """
        condition_id = await get_condition_id("Amebiasis")
        config = await create_config(condition_id)
        config_id = config["id"]

        await add_custom_code(
            config_id,
            DbConfigurationCustomCode(
                code="MOCK-CODE-001",
                system_key="loinc",
                name="Mock custom code",
            ),
        )

        response = await authed_client.get(f"/api/v1/configurations/{config_id}/export")
        assert response.status_code == status.HTTP_200_OK

        content = get_csv_from_zip(response.content, r"Code_Export")
        reader = csv.DictReader(StringIO(content))
        code_systems_in_csv = {
            row["Code System"] for row in reader if row["Code System"]
        }

        code_systems = await get_all_code_systems_db(db=db_pool)
        expected_systems = {cs.display_name for cs in code_systems.values()}

        assert code_systems_in_csv <= expected_systems

    async def test_export_custom_codes_have_blank_condition(
        self,
        setup,
        authed_client,
        get_condition_id,
        create_config,
        add_custom_code,
    ):
        """
        Custom code rows should have a blank "Condition" column.
        """
        condition_id = await get_condition_id("Amebiasis")
        config = await create_config(condition_id)
        config_id = config["id"]

        await add_custom_code(
            config_id,
            DbConfigurationCustomCode(
                code="MOCK-CODE-001",
                system_key="loinc",
                name="Mock custom code",
            ),
        )

        response = await authed_client.get(f"/api/v1/configurations/{config_id}/export")
        assert response.status_code == status.HTTP_200_OK

        content = get_csv_from_zip(response.content, r"Code_Export")
        reader = csv.DictReader(StringIO(content))
        for row in reader:
            if row["Code Type"] == "Custom code":
                assert row["Condition"] == "", (
                    f"Expected blank Condition for custom code, got {row['Condition']!r}"
                )

    async def test_export_csv_body_is_non_empty(
        self, setup, authed_client, get_condition_id, create_config
    ):
        """
        Codes CSV should contain at least a header row.
        """
        condition_id = await get_condition_id("Cholera")
        config = await create_config(condition_id)
        response = await authed_client.get(
            f"/api/v1/configurations/{config['id']}/export"
        )

        assert response.status_code == status.HTTP_200_OK
        content = get_csv_from_zip(response.content, r"Code_Export")
        lines = [line for line in content.splitlines() if line.strip()]
        assert len(lines) >= 1, "Expected at least a CSV header row in the response"
