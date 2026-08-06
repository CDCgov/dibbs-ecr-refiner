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
