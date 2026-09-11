import csv
import io

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
class TestTesDiff:
    async def test_tes_diff_between_conditions(
        self, authed_client, default_tes_version, previous_tes_version
    ):
        response = await authed_client.get(
            f"/api/v1/tes/?cur_version={default_tes_version}&prev_version={previous_tes_version}"
        )
        assert response.status_code == 200
        diff_cur_and_prev = response.json()

        # these may need to change with new TES releases since the numbers will
        # change
        expected_acanthamoeba = diff_cur_and_prev[0]
        assert expected_acanthamoeba["display_name"] == "Acanthamoeba"
        assert expected_acanthamoeba["added_code_total"] == 27
        assert expected_acanthamoeba["removed_code_total"] == 0

        expected_rubella = [
            c for c in diff_cur_and_prev if c["display_name"] == "Rubella"
        ][0]
        assert expected_rubella
        assert expected_rubella["added_code_total"] == 3
        assert expected_rubella["removed_code_total"] == 13
        assert not expected_rubella["is_new"]

        expected_zika = diff_cur_and_prev[-1]
        assert expected_zika["display_name"] == "Zika Virus Disease"
        assert expected_zika["added_code_total"] == 8480
        assert expected_zika["removed_code_total"] == 0
        assert not expected_zika["is_new"]

    async def test_tes_diff_csv_export(
        self, authed_client, default_tes_version, previous_tes_version
    ):
        COVID_CANONICAL_URL = "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64"

        response = await authed_client.get(
            f"/api/v1/tes/export?cur_version={default_tes_version}&prev_version={previous_tes_version}&canonical_url={COVID_CANONICAL_URL}"
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        assert (
            f"COVID-19_TES_v{default_tes_version}_change_summary.csv"
            in response.headers["content-disposition"]
        )

        # Decode response string into structured dictionary rows
        csv_file = io.StringIO(response.text)
        reader = list(csv.DictReader(csv_file))

        assert len(reader) == 54

        # spot check some values
        assert "105909-6" in (row["Code"] for row in reader)
        assert "SARS-CoV-2 (COVID-19) RNA [Presence] in Specimen" in (
            row["Display Name"] for row in reader
        )
        assert "371045000" in (row["Code"] for row in reader)
        assert "Removed" in (row["Change"] for row in reader)
