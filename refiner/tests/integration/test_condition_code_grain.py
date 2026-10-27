import pytest

from app.db.conditions.db import (
    get_condition_by_id_db,
    get_condition_codes_by_condition_id_db,
)


async def _worst_fanout_condition(db_pool):
    """
    Returns the condition whose codes span the most valuesets, with its real counts.

    A code reaching a condition through several sibling groupers is several rows in
    `conditions_codes_temp` -- its grain is `(condition_id, code_id, valueset_id)`.
    Picking the worst fan-out means these assertions actually have duplicates to
    collapse; on a condition with one valueset they would pass either way.
    """

    async with db_pool.get_connection() as conn, conn.cursor() as cur:
        await cur.execute("""
            SELECT c.id,
                   COUNT(*) AS memberships,
                   COUNT(DISTINCT (codes.system_id, codes.code)) AS distinct_codes
            FROM conditions c
            JOIN conditions_codes_temp cc ON cc.condition_id = c.id
            JOIN codes ON codes.id = cc.code_id
            GROUP BY c.id
            HAVING COUNT(*) > COUNT(DISTINCT (codes.system_id, codes.code))
            ORDER BY COUNT(*) - COUNT(DISTINCT (codes.system_id, codes.code)) DESC
            LIMIT 1
        """)
        return await cur.fetchone()


@pytest.mark.integration
@pytest.mark.asyncio
class TestConditionCodeGrain:
    """
    Pins read-time deduplication over the `conditions_codes_temp` junction.

    PR #1661 replaced `conditions_codes` -- `PRIMARY KEY (condition_id, code_id)`,
    one row per code -- with a membership junction, and added `DISTINCT` to one of
    the 36 migrated references. Nothing then enforced the guarantee the dropped
    primary key had been providing, so later readers inherited the omission and
    `events.code_count` drifted up to 2.58x on 17.4% of conditions.

    These fail if a `DISTINCT` is dropped again.
    """

    async def test_condition_codes_are_deduplicated(self, db_pool):
        row = await _worst_fanout_condition(db_pool)
        assert row, "no condition in the corpus has a fan-out to exercise"
        condition_id, memberships, distinct_codes = row

        condition = await get_condition_by_id_db(id=condition_id, db=db_pool)
        assert condition

        assert len(condition.codes) == distinct_codes, (
            f"DbCondition.codes carries {len(condition.codes)} entries for "
            f"{distinct_codes} distinct codes -- the JSONB_AGG lost its DISTINCT, "
            f"or JSONB_BUILD_OBJECT regressed to JSON_BUILD_OBJECT (`json` has no "
            f"equality operator, so DISTINCT silently cannot apply)"
        )
        assert memberships > distinct_codes, "fixture no longer exercises a fan-out"

    async def test_code_count_counts_codes_not_memberships(self, db_pool):
        """`events.code_count` is persisted from here and shown in the activity log."""

        row = await _worst_fanout_condition(db_pool)
        condition_id, _, distinct_codes = row

        condition = await get_condition_by_id_db(id=condition_id, db=db_pool)
        assert condition
        assert condition.get_code_count() == distinct_codes

    async def test_csv_export_agrees_with_the_event_count(self, db_pool):
        """
        The export and the stored count have to stay equal.

        They agreed before this fix only because both were inflated identically, so
        deduplicating one without the other would have broken the invariant the
        export's own docstring promises.
        """

        row = await _worst_fanout_condition(db_pool)
        condition_id, _, distinct_codes = row

        condition = await get_condition_by_id_db(id=condition_id, db=db_pool)
        exported = await get_condition_codes_by_condition_id_db(
            condition_id=condition_id, db=db_pool
        )
        assert condition
        assert len(exported) == condition.get_code_count() == distinct_codes

    async def test_system_id_is_a_uuid_on_the_jsonb_path(self, db_pool):
        """
        `JSONB_BUILD_OBJECT` renders a uuid as a JSON string.

        Without coercion `DbConditionCode.system_id` is a `str`, while the annotation
        says `UUID`. It used to differ from a `class_row` path that handed back a real
        `UUID`, so a `dict[UUID, ...]` lookup on this one missed every key.
        """

        from uuid import UUID

        row = await _worst_fanout_condition(db_pool)
        condition = await get_condition_by_id_db(id=row[0], db=db_pool)
        assert condition
        assert all(isinstance(c.system_id, UUID) for c in condition.codes)
