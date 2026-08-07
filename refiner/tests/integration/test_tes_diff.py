import csv
import io

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
class TestTesDiff:
    async def test_tes_diff_between_conditions(self, authed_client):
        response = await authed_client.get(
            "/api/v1/tes/?cur_version=6.0.0&prev_version=5.0.0"
        )
        assert response.status_code == 200
        diff_6_and_5 = response.json()

        # these may need to change with new TES releases since the numbers will
        # change
        expected_acanthamoeba = diff_6_and_5[0]
        assert expected_acanthamoeba["display_name"] == "Acanthamoeba"
        assert expected_acanthamoeba["added_code_total"] == 6
        assert expected_acanthamoeba["removed_code_total"] == 0

        expected_rubella = [c for c in diff_6_and_5 if c["display_name"] == "Rubella"][
            0
        ]
        assert expected_rubella
        assert expected_rubella["added_code_total"] == 1156
        assert expected_rubella["removed_code_total"] == 3
        assert not expected_rubella["is_new"]

        expected_zika = diff_6_and_5[-1]
        assert expected_zika["display_name"] == "Zika Virus Disease"
        assert expected_zika["added_code_total"] == 32
        assert expected_zika["removed_code_total"] == 0
        assert not expected_zika["is_new"]

    async def test_tes_diff_csv_export(self, authed_client):
        COVID_CANONICAL_URL = "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64"

        response = await authed_client.get(
            f"/api/v1/tes/export?cur_version=6.0.0&prev_version=5.0.0&cond_canonical_url={COVID_CANONICAL_URL}"
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        assert (
            "COVID-19_TES_v6.0.0_change_summary.csv"
            in response.headers["content-disposition"]
        )

        # Decode response string into structured dictionary rows
        csv_file = io.StringIO(response.text)
        reader = list(csv.DictReader(csv_file))

        assert len(reader) == 12648

        # spot check some values
        assert "1003863006" in (row["Code"] for row in reader)
        assert (
            "15 ML atezolizumab-tqjs 125 MG/ML / hyaluronidase-tqjs 2000 UNT/ML Injection"
            in (row["Display Name"] for row in reader)
        )
        assert "Removed" in (row["Change"] for row in reader)
