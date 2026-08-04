import pytest

from app.api.v1.tes import get_tes_diff_details


@pytest.mark.integration
@pytest.mark.asyncio
class TestTesDiff:
    async def test_tes_diff_between_conditions(self, db_pool):
        # these values are hardcoded rather than using the fixtures so that
        # TES updates don't change the outcome of the test
        default_and_prev_diff = await get_tes_diff_details(
            cur_version="6.0.0",
            prev_version="5.0.0",
            db=db_pool,
        )

        # these may need to change with new TES releases since the numbers will
        # change
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
