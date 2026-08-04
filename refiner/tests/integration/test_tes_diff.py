import pytest

from app.api.v1.tes import get_tes_diff_details


@pytest.mark.integration
@pytest.mark.asyncio
class TestTesDiff:
    async def test_tes_diff_between_conditions(
        self, default_tes_version, previous_tes_version, db_pool
    ):
        # check some topline numbers between known quantities
        default_and_prev_diff = await get_tes_diff_details(
            cur_version=default_tes_version,
            prev_version=previous_tes_version,
            db=db_pool,
        )

        expected_acanthamoeba = default_and_prev_diff[0]
        assert expected_acanthamoeba.display_name == "Acanthamoeba"
        assert expected_acanthamoeba.added_code_total == 6
        assert expected_acanthamoeba.removed_code_total == 0

        expected_rubella = [
            c for c in default_and_prev_diff if c.display_name == "Rubella"
        ][0]
        assert expected_rubella
        assert expected_rubella.added_code_total == 1156
        assert expected_rubella.removed_code_total == 3
