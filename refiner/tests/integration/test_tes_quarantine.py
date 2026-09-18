import sys
from pathlib import Path

import psycopg
import pytest

from app.core.config import get_db_config
from app.db.conditions.db import get_context_groupers_by_condition_id_db

# `ops/seeding` is run as a script by the ops image, so its modules import each
# other flatly (`from connection import ...`). importing it as a package would
# need that changed, and the entrypoint depends on it, so the path goes on
# sys.path instead
sys.path.insert(0, str(Path(__file__).parents[2] / "ops" / "seeding"))

import load_processed_data as loader  # noqa: E402

PROCESSED_DIR = Path(__file__).parents[2] / "tes" / "data" / "processed"


def _connect() -> psycopg.Connection:
    db_config = get_db_config()
    return psycopg.connect(db_config.DB_URL, password=db_config.DB_PASSWORD)


def _stage_everything(cursor: psycopg.Cursor) -> list[str]:
    """
    Load the processed tables the loader works from, and return the seeding window.
    """

    for table, filename in loader.SOURCE_FILES.items():
        loader._stage(cursor, table, PROCESSED_DIR / filename)
    return loader._versions_to_seed(cursor, False, loader.DEFAULT_VERSIONS_TO_KEEP)


@pytest.mark.integration
class TestQuarantine:
    """
    The seeder moves orphaned valuesets out, and refuses when the input looks wrong.

    Every test here rolls back, so the session's seeded database is unchanged and
    the `absorbed_context_groupers` rows survive for whatever runs next.
    """

    def test_absorbed_groupers_are_quarantined(self, absorbed_context_groupers):
        with _connect() as connection, connection.cursor() as cursor:
            versions = _stage_everything(cursor)
            before = len(absorbed_context_groupers)

            loader._upsert_valuesets(cursor, versions)
            loader._quarantine_stale_valuesets(cursor, versions)

            cursor.execute(
                "SELECT count(*) FROM orphaned_valuesets WHERE valueset_id = ANY(%s)",
                (absorbed_context_groupers,),
            )
            (quarantined,) = cursor.fetchone()
            cursor.execute(
                "SELECT count(*) FROM valuesets WHERE id = ANY(%s)",
                (absorbed_context_groupers,),
            )
            (left_behind,) = cursor.fetchone()

            # the real groupers the processed data does declare stay put
            cursor.execute(
                """
                SELECT count(*) FROM valuesets v
                JOIN conditions c ON c.id = v.condition_id
                JOIN tes t ON t.id = c.tes_id
                WHERE c.display_name = 'Influenza'
                  AND t.version = ANY(%s)
                  AND v.category <> 'reporting_specification_grouper'
                """,
                (versions,),
            )
            (real_groupers,) = cursor.fetchone()

            connection.rollback()

        assert quarantined == before, (
            f"expected all {before} absorbed groupers quarantined, got {quarantined}"
        )
        assert left_behind == 0
        assert real_groupers == 5 * len(versions), (
            "quarantine removed groupers the processed data still declares"
        )

    def test_membership_count_is_recorded_before_the_junction_is_rebuilt(
        self, absorbed_context_groupers
    ):
        """
        Fails if `_quarantine_stale_valuesets` is moved after `_refresh_memberships`.

        `memberships_at_removal` is what separates a row that was already stranded
        from one this release retired, and it can only be read while the junction
        still holds the old rows. Swap the two calls in `load_processed_data` and
        every row records 0 -- silently, since nothing else changes.
        """

        with _connect() as connection, connection.cursor() as cursor:
            versions = _stage_everything(cursor)
            target = absorbed_context_groupers[0]

            # give one absorbed grouper live memberships, as if this release
            # retired it rather than it having been stranded all along
            cursor.execute(
                """
                INSERT INTO conditions_codes_temp (
                    condition_id, code_id, valueset_id, is_child_rsg, is_trigger_code
                )
                SELECT v.condition_id, co.id, v.id, false, false
                FROM valuesets v, (SELECT id FROM codes ORDER BY code LIMIT 3) co
                WHERE v.id = %s
                """,
                (target,),
            )

            loader._upsert_valuesets(cursor, versions)
            loader._quarantine_stale_valuesets(cursor, versions)
            loader._refresh_memberships(cursor, versions)

            cursor.execute(
                "SELECT memberships_at_removal FROM orphaned_valuesets "
                "WHERE valueset_id = %s",
                (target,),
            )
            (memberships,) = cursor.fetchone()
            connection.rollback()

        assert memberships == 3, (
            "membership count was not captured before the junction was rebuilt -- "
            "has the quarantine been moved after `_refresh_memberships`?"
        )

    def test_guardrail_refuses_and_writes_nothing(self, absorbed_context_groupers):
        """
        A processed table that declares almost nothing aborts instead of emptying
        the database.
        """

        with _connect() as connection, connection.cursor() as cursor:
            versions = _stage_everything(cursor)
            loader._upsert_valuesets(cursor, versions)

            cursor.execute("SELECT count(*) FROM valuesets")
            (valuesets_before,) = cursor.fetchone()

            # under-populate the stage table so almost every row in `valuesets`
            # looks undeclared -- the shape a truncated normalize run would have
            cursor.execute(
                "DELETE FROM stage_valuesets WHERE ctid NOT IN "
                "(SELECT ctid FROM stage_valuesets LIMIT 5)"
            )

            with pytest.raises(SystemExit) as excinfo:
                loader._quarantine_stale_valuesets(cursor, versions)

            assert "Refusing to quarantine" in str(excinfo.value)
            assert "Nothing has been written" in str(excinfo.value)

            # the abort happens before any write; the loader's single transaction
            # would roll the rest back anyway
            cursor.execute("SELECT count(*) FROM orphaned_valuesets")
            (quarantined,) = cursor.fetchone()
            cursor.execute("SELECT count(*) FROM valuesets")
            (valuesets_after,) = cursor.fetchone()
            connection.rollback()

        assert quarantined == 0
        assert valuesets_after == valuesets_before

    @pytest.mark.asyncio
    async def test_condition_endpoint_query_skips_orphans(
        self, db_pool, absorbed_context_groupers, get_condition_id
    ):
        """
        The read path ignores a grouper that contributes no codes.

        Belt and braces with the quarantine rather than a duplicate of it: a
        grouper whose codes are all in unsupported code systems is legitimately
        declared, will never be quarantined, and still contributes nothing.
        """

        condition_id = await get_condition_id("Encephalitis")
        groupers = await get_context_groupers_by_condition_id_db(
            condition_id=condition_id, db=db_pool
        )

        served = {grouper.id for grouper in groupers}
        assert not served & set(absorbed_context_groupers), (
            "condition detail query served a grouper with no memberships"
        )

        # Encephalitis has no context groupers of its own, so the absorbed one
        # would invent a symptom category out of nothing
        assert not [g for g in groupers if g.category == "symptom"]
