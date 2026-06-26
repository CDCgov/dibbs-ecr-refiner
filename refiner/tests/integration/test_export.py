import csv
import re
import zipfile
from io import BytesIO, StringIO

import pytest
from fastapi import status

from app.db.code_systems.db import get_all_code_systems_db
from app.db.conditions.db import get_condition_codes_by_condition_id_db
from app.db.configurations.model import DbConfigurationCustomCode
from app.services.configurations import get_default_sections
from app.services.ecr.policy import NARRATIVE_ONLY_SECTIONS


def _get_csv_from_zip(content: bytes, filename_pattern: str) -> str:
    """
    Helper to extract a CSV file from a zip response by filename pattern.
    """
    with zipfile.ZipFile(BytesIO(content)) as zf:
        for name in zf.namelist():
            if re.search(filename_pattern, name):
                return zf.read(name).decode("utf-8")
    raise FileNotFoundError(f"No file matching {filename_pattern!r} found in zip")


def _get_section_row(content: str, loinc: str) -> dict:
    """
    Helper to get a section row's content by LOINC code.
    """
    reader = csv.DictReader(StringIO(content))
    row = next((r for r in reader if r["LOINC"] == loinc), None)
    assert row is not None, f"No row found for LOINC {loinc!r}"
    return row


@pytest.mark.integration
@pytest.mark.asyncio
class TestConfigurationExportZip:
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
        Zip should be returned with correct content type and content-disposition.
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


@pytest.mark.integration
@pytest.mark.asyncio
class TestConfigurationExportCodesCsv:
    async def test_codes_csv_has_correct_headers(
        self, setup, authed_client, get_condition_id, create_config
    ):
        """
        Codes CSV should have the correct column headers.
        """
        condition_id = await get_condition_id("Amebiasis")
        config = await create_config(condition_id)
        response = await authed_client.get(
            f"/api/v1/configurations/{config['id']}/export"
        )

        assert response.status_code == status.HTTP_200_OK

        content = _get_csv_from_zip(response.content, r"Code_Export")
        reader = csv.DictReader(StringIO(content))
        assert reader.fieldnames == [
            "Code Type",
            "Condition",
            "Code System",
            "Code",
            "Display Name",
        ]

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

        content = _get_csv_from_zip(response.content, r"Code_Export")
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

        content = _get_csv_from_zip(response.content, r"Code_Export")
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

        content = _get_csv_from_zip(response.content, r"Code_Export")
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

        content = _get_csv_from_zip(response.content, r"Code_Export")
        reader = csv.DictReader(StringIO(content))
        for row in reader:
            if row["Code Type"] == "Custom code":
                assert row["Condition"] == "", (
                    f"Expected blank Condition for custom code, got {row['Condition']!r}"
                )

    async def test_export_codes_csv_body_is_non_empty(
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
        content = _get_csv_from_zip(response.content, r"Code_Export")
        lines = [line for line in content.splitlines() if line.strip()]
        assert len(lines) >= 1, "Expected at least a CSV header row in the response"


@pytest.mark.integration
@pytest.mark.asyncio
class TestConfigurationExportSectionsCsv:
    async def test_sections_csv_has_correct_headers(
        self, setup, authed_client, get_condition_id, create_config
    ):
        """
        Sections CSV should have the correct column headers.
        """
        condition_id = await get_condition_id("Colorado tick fever")
        config = await create_config(condition_id)
        response = await authed_client.get(
            f"/api/v1/configurations/{config['id']}/export"
        )

        assert response.status_code == status.HTTP_200_OK

        content = _get_csv_from_zip(response.content, r"Section_Export")
        reader = csv.DictReader(StringIO(content))
        assert reader.fieldnames == [
            "Section Name",
            "LOINC",
            "Include",
            "Coded Data",
            "Narrative Data",
        ]

    async def test_sections_csv_is_sorted_alphabetically(
        self, setup, authed_client, get_condition_id, create_config
    ):
        """
        Sections CSV should be sorted alphabetically by section name.
        """
        condition_id = await get_condition_id("Colorado tick fever")
        config = await create_config(condition_id)
        response = await authed_client.get(
            f"/api/v1/configurations/{config['id']}/export"
        )

        assert response.status_code == status.HTTP_200_OK

        content = _get_csv_from_zip(response.content, r"Section_Export")
        reader = csv.DictReader(StringIO(content))
        names = [row["Section Name"] for row in reader]
        assert names == sorted(names, key=str.lower)

    async def test_sections_csv_include_column_values(
        self,
        setup,
        authed_client,
        get_condition_id,
        create_config,
        update_section_processing,
    ):
        """
        Sections CSV "Include" column should only contain "Yes" or "No".
        """
        condition_id = await get_condition_id("Colorado tick fever")
        config = await create_config(condition_id)

        # Exclude a section
        await update_section_processing(
            config_id=config["id"], current_code="10160-0", include=False
        )

        response = await authed_client.get(
            f"/api/v1/configurations/{config['id']}/export"
        )

        assert response.status_code == status.HTTP_200_OK

        content = _get_csv_from_zip(response.content, r"Section_Export")
        reader = csv.DictReader(StringIO(content))
        include_values = {row["Include"] for row in reader}
        assert include_values <= {"Yes", "No"}

    async def test_sections_csv_refine_action_shows_refine(
        self,
        setup,
        authed_client,
        get_condition_id,
        create_config,
        update_section_processing,
    ):
        """
        A section with action set to `refine` should show "Refine" in the Coded Data column.
        """
        condition_id = await get_condition_id("Colorado tick fever")
        config = await create_config(condition_id)
        config_id = config["id"]

        section_loinc = "10160-0"

        await update_section_processing(
            config_id=config_id, current_code=section_loinc, action="refine"
        )

        response = await authed_client.get(f"/api/v1/configurations/{config_id}/export")
        assert response.status_code == status.HTTP_200_OK

        content = _get_csv_from_zip(response.content, r"Section_Export")
        row = _get_section_row(content=content, loinc=section_loinc)
        assert row["Coded Data"] == "Refine"

    async def test_sections_csv_retain_action_shows_keep_original(
        self,
        setup,
        authed_client,
        get_condition_id,
        create_config,
        update_section_processing,
    ):
        """
        A section with action set to `retain` should show "Keep original" in the Coded Data column.
        """
        condition_id = await get_condition_id("Colorado tick fever")
        config = await create_config(condition_id)
        config_id = config["id"]

        section_loinc = "10160-0"

        await update_section_processing(
            config_id=config_id, current_code=section_loinc, action="retain"
        )

        response = await authed_client.get(f"/api/v1/configurations/{config_id}/export")
        assert response.status_code == status.HTTP_200_OK

        content = _get_csv_from_zip(response.content, r"Section_Export")
        row = _get_section_row(content=content, loinc=section_loinc)
        assert row["Coded Data"] == "Keep original"

    async def test_sections_csv_reconstruct_narrative_shows_reconstruct(
        self,
        setup,
        authed_client,
        get_condition_id,
        create_config,
        update_section_processing,
    ):
        """
        A section with narrative set to `reconstruct` should show "Reconstruct" in the Narrative Data column.
        """
        condition_id = await get_condition_id("Colorado tick fever")
        config = await create_config(condition_id)
        config_id = config["id"]

        section_loinc = "10160-0"

        await update_section_processing(
            config_id=config_id, current_code=section_loinc, narrative="reconstruct"
        )

        response = await authed_client.get(f"/api/v1/configurations/{config_id}/export")
        assert response.status_code == status.HTTP_200_OK

        content = _get_csv_from_zip(response.content, r"Section_Export")
        row = _get_section_row(content=content, loinc=section_loinc)
        assert row["Narrative Data"] == "Reconstruct"

    async def test_sections_csv_remove_narrative_shows_exclude(
        self,
        setup,
        authed_client,
        get_condition_id,
        create_config,
        update_section_processing,
    ):
        """
        A section with narrative set to `remove` should show "Exclude" in the Narrative Data column.
        """
        condition_id = await get_condition_id("Colorado tick fever")
        config = await create_config(condition_id)
        config_id = config["id"]

        section_loinc = "10160-0"

        await update_section_processing(
            config_id=config_id, current_code=section_loinc, narrative="remove"
        )

        response = await authed_client.get(f"/api/v1/configurations/{config_id}/export")
        assert response.status_code == status.HTTP_200_OK

        content = _get_csv_from_zip(response.content, r"Section_Export")
        row = _get_section_row(content=content, loinc=section_loinc)
        assert row["Narrative Data"] == "Exclude"

    async def test_sections_csv_retain_narrative_shows_keep_original(
        self,
        setup,
        authed_client,
        get_condition_id,
        create_config,
        update_section_processing,
    ):
        """
        A section with narrative set to `retain` should show "Keep original" in the Narrative Data column.
        """
        condition_id = await get_condition_id("Colorado tick fever")
        config = await create_config(condition_id)
        config_id = config["id"]

        section_loinc = "10160-0"

        await update_section_processing(
            config_id=config_id, current_code=section_loinc, narrative="retain"
        )

        response = await authed_client.get(f"/api/v1/configurations/{config_id}/export")
        assert response.status_code == status.HTTP_200_OK

        content = _get_csv_from_zip(response.content, r"Section_Export")
        row = _get_section_row(content=content, loinc=section_loinc)
        assert row["Narrative Data"] == "Keep original"

    async def test_sections_csv_excluded_section_shows_no_and_na(
        self,
        setup,
        authed_client,
        get_condition_id,
        create_config,
        update_section_processing,
    ):
        """
        A section with include set to `False` should show "No" and "N/A" for coded and narrative data.
        """
        condition_id = await get_condition_id("Colorado tick fever")
        config = await create_config(condition_id)
        config_id = config["id"]

        section_loinc = "10160-0"

        await update_section_processing(
            config_id=config_id, current_code=section_loinc, include=False
        )

        response = await authed_client.get(f"/api/v1/configurations/{config_id}/export")
        assert response.status_code == status.HTTP_200_OK

        content = _get_csv_from_zip(response.content, r"Section_Export")
        row = _get_section_row(content=content, loinc=section_loinc)
        assert row["Include"] == "No"
        assert row["Coded Data"] == "N/A"
        assert row["Narrative Data"] == "N/A"

    async def test_sections_csv_coded_data_na_for_narrative_only(
        self, authed_client, setup, get_condition_id, create_config
    ):
        """
        Narrative only sections should always show "N/A" for Coded Data.
        """
        condition_id = await get_condition_id("Colorado tick fever")
        config = await create_config(condition_id)
        config_id = config["id"]

        response = await authed_client.get(f"/api/v1/configurations/{config_id}/export")
        assert response.status_code == status.HTTP_200_OK

        content = _get_csv_from_zip(response.content, r"Section_Export")

        for loinc in NARRATIVE_ONLY_SECTIONS:
            row = _get_section_row(content=content, loinc=loinc)
            assert row["Coded Data"] == "N/A"

    async def test_sections_csv_has_all_sections(
        self, setup, authed_client, get_condition_id, create_config
    ):
        """
        Sections CSV should contain a row for each section available.
        """
        condition_id = await get_condition_id("Cholera")
        config = await create_config(condition_id)
        response = await authed_client.get(
            f"/api/v1/configurations/{config['id']}/export"
        )

        assert response.status_code == status.HTTP_200_OK
        content = _get_csv_from_zip(response.content, r"Section_Export")
        lines = [line for line in content.splitlines() if line.strip()]
        expected_lines = len(get_default_sections()) + 1  # adding the heading
        assert len(lines) == expected_lines, (
            "Expected a row in the CSV for each section"
        )
