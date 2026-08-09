import pytest
from psycopg.rows import dict_row

from app.db.configurations.db import get_configuration_by_id_db
from app.db.configurations.exclusions.db import get_code_exclusions_db
from app.services.configurations import convert_config_to_storage_payload


async def _pick_condition_code(db_pool, condition_id, system_key: str):
    """
    Return one (code_id, code) the condition contributes in `system_key`.

    Reads the normalized `codes` tables, while the projection under test reads
    the `conditions` JSONB columns. Asserting the picked code shows up in the
    projected payload is therefore also a check that the two representations
    still agree.
    """

    async with db_pool.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT c.id, c.code
                FROM conditions_codes cc
                JOIN codes c ON c.id = cc.code_id
                JOIN systems s ON s.id = c.system_id
                WHERE cc.condition_id = %s AND s.key = %s
                ORDER BY c.code
                LIMIT 1
                """,
                (condition_id, system_key),
            )
            row = await cur.fetchone()
            assert row, f"condition {condition_id} contributes no {system_key} codes"
            return row["id"], row["code"]


async def _exclude(db_pool, configuration_id, condition_id, code_id):
    async with db_pool.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO configurations_conditions_code_exclusions
                    (configuration_id, condition_id, code_id)
                VALUES (%s, %s, %s)
                """,
                (configuration_id, condition_id, code_id),
            )


def _codes_for_system(payload, system_key: str) -> set[str]:
    return {c["code"] for c in payload.code_system_sets.get(system_key, [])}


@pytest.mark.integration
@pytest.mark.asyncio
class TestCodeExclusions:
    async def test_excluded_code_is_dropped_from_the_projected_payload(
        self,
        create_config,
        get_condition_id,
        test_user_jurisdiction_id,
        db_pool,
    ):
        condition_id = await get_condition_id("Ophthalmia Neonatorum")
        config_id = (await create_config(condition_id))["id"]

        configuration = await get_configuration_by_id_db(
            id=config_id, jurisdiction_id=test_user_jurisdiction_id, db=db_pool
        )
        assert configuration

        code_id, code = await _pick_condition_code(db_pool, condition_id, "snomed")

        before = await convert_config_to_storage_payload(
            configuration=configuration, db=db_pool
        )
        assert before
        assert code in _codes_for_system(before, "snomed")

        await _exclude(db_pool, config_id, condition_id, code_id)

        after = await convert_config_to_storage_payload(
            configuration=configuration, db=db_pool
        )
        assert after
        assert code not in _codes_for_system(after, "snomed")

        # nothing else moved: the exclusion is surgical, not a wholesale drop
        assert _codes_for_system(before, "snomed") - {code} == _codes_for_system(
            after, "snomed"
        )
        assert _codes_for_system(before, "loinc") == _codes_for_system(after, "loinc")

    async def test_get_code_exclusions_groups_by_condition(
        self,
        create_config,
        get_condition_id,
        db_pool,
    ):
        # a distinct condition from the test above: a configuration is unique
        # per condition, so reusing one returns 409
        condition_id = await get_condition_id("Chlamydia trachomatis infection")
        config_id = (await create_config(condition_id))["id"]

        assert (
            await get_code_exclusions_db(configuration_id=config_id, db=db_pool) == {}
        )

        code_id, code = await _pick_condition_code(db_pool, condition_id, "snomed")
        await _exclude(db_pool, config_id, condition_id, code_id)

        excluded = await get_code_exclusions_db(configuration_id=config_id, db=db_pool)

        assert excluded == {condition_id: {("snomed", code)}}
