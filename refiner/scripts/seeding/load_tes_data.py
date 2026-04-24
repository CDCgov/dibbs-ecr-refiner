import os
import time
from datetime import datetime
from typing import TypedDict

from config import ENV_PATH, logger
from dotenv import load_dotenv
from lib import (
    ConditionData,
    VsCanonicalUrl,
    VsDict,
    VsVersion,
    get_db_connection,
    is_condition_grouper,
    load_valuesets_from_all_files,
)


class Code(TypedDict):
    """
    A code object in a condition's code set.
    """

    code: str
    display: str


class ConditionRow(TypedDict):
    """
    A condition row to upsert into the DB.
    """

    canonical_url: str
    version: str
    display_name: str
    child_rsg_snomed_codes: list[str] | None
    loinc_codes: list[Code] | None
    snomed_codes: list[Code] | None
    icd10_codes: list[Code] | None
    rxnorm_codes: list[Code] | None
    cvx_codes: list[Code] | None
    coverage_level: str | None
    coverage_level_reason: str | None
    coverage_level_date: datetime | None


class ContextGrouperRow(TypedDict):
    """
    A context grouper row to upsert into the DB.
    """

    name: str
    category: str
    canonical_url: str
    code_count: int


class ProcessedCondition(TypedDict):
    """
    A fully processed condition with its associated context grouper rows.
    """

    condition: ConditionRow
    context_groupers: list[ContextGrouperRow]


def _build_processed_conditions(
    condition_groupers: list[VsDict],
    valuesets_map: dict[tuple[VsCanonicalUrl, VsVersion], VsDict],
) -> list[ProcessedCondition]:
    results: list[ProcessedCondition] = []

    for parent in condition_groupers:
        data = ConditionData(parent, valuesets_map)
        results.append(
            {
                "condition": data.payload,
                "context_groupers": data.context_grouper_payloads,
            }
        )

    logger.info(f"🛠️  Total condition rows processed: {len(results)}")
    return results


def _upsert_conditions_and_groupers(
    db_url: str,
    db_password: str,
    processed: list[ProcessedCondition],
) -> None:
    """
    Upserts condition rows and their associated context grouper rows.

    Each condition is upserted using a CTE that returns the row's id
    regardless of whether the row was inserted, updated, or unchanged.
    Context grouper rows are then upserted as children of that condition.

    Both upserts use IS DISTINCT FROM to avoid touching rows where
    nothing has changed, preventing spurious updated_at timestamps.
    """

    try:
        with get_db_connection(db_url, db_password) as conn, conn.cursor() as cursor:
            logger.info("⏳ Upserting condition records...")

            condition_upsert_query = """
                WITH upsert_condition AS (
                    INSERT INTO conditions (
                        canonical_url,
                        version,
                        display_name,
                        child_rsg_snomed_codes,
                        loinc_codes,
                        snomed_codes,
                        icd10_codes,
                        rxnorm_codes,
                        cvx_codes,
                        coverage_level,
                        coverage_level_reason,
                        coverage_level_date
                    )
                    VALUES (
                        %(canonical_url)s,
                        %(version)s,
                        %(display_name)s,
                        %(child_rsg_snomed_codes)s,
                        %(loinc_codes)s,
                        %(snomed_codes)s,
                        %(icd10_codes)s,
                        %(rxnorm_codes)s,
                        %(cvx_codes)s,
                        %(coverage_level)s,
                        %(coverage_level_reason)s,
                        %(coverage_level_date)s
                    )
                    ON CONFLICT (canonical_url, version)
                    DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        child_rsg_snomed_codes = EXCLUDED.child_rsg_snomed_codes,
                        loinc_codes = EXCLUDED.loinc_codes,
                        snomed_codes = EXCLUDED.snomed_codes,
                        icd10_codes = EXCLUDED.icd10_codes,
                        rxnorm_codes = EXCLUDED.rxnorm_codes,
                        cvx_codes = EXCLUDED.cvx_codes,
                        coverage_level = EXCLUDED.coverage_level,
                        coverage_level_reason = EXCLUDED.coverage_level_reason,
                        coverage_level_date = EXCLUDED.coverage_level_date
                    WHERE
                        conditions.display_name IS DISTINCT FROM EXCLUDED.display_name
                        OR conditions.child_rsg_snomed_codes IS DISTINCT FROM EXCLUDED.child_rsg_snomed_codes
                        OR conditions.loinc_codes IS DISTINCT FROM EXCLUDED.loinc_codes
                        OR conditions.snomed_codes IS DISTINCT FROM EXCLUDED.snomed_codes
                        OR conditions.icd10_codes IS DISTINCT FROM EXCLUDED.icd10_codes
                        OR conditions.rxnorm_codes IS DISTINCT FROM EXCLUDED.rxnorm_codes
                        OR conditions.cvx_codes IS DISTINCT FROM EXCLUDED.cvx_codes
                        OR conditions.coverage_level IS DISTINCT FROM EXCLUDED.coverage_level
                        OR conditions.coverage_level_reason IS DISTINCT FROM EXCLUDED.coverage_level_reason
                        OR conditions.coverage_level_date IS DISTINCT FROM EXCLUDED.coverage_level_date
                    RETURNING id
                )
                SELECT id FROM upsert_condition

                UNION ALL

                SELECT id
                FROM conditions
                WHERE canonical_url = %(canonical_url)s
                  AND version = %(version)s
                  AND NOT EXISTS (SELECT 1 FROM upsert_condition)

                LIMIT 1
            """

            context_grouper_upsert_query = """
                INSERT INTO conditions_context_groupers (
                    condition_id,
                    name,
                    category,
                    canonical_url,
                    code_count
                )
                VALUES (
                    %(condition_id)s,
                    %(name)s,
                    %(category)s,
                    %(canonical_url)s,
                    %(code_count)s
                )
                ON CONFLICT (condition_id, canonical_url)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    category = EXCLUDED.category,
                    code_count = EXCLUDED.code_count
                WHERE
                    conditions_context_groupers.name IS DISTINCT FROM EXCLUDED.name
                    OR conditions_context_groupers.category IS DISTINCT FROM EXCLUDED.category
                    OR conditions_context_groupers.code_count IS DISTINCT FROM EXCLUDED.code_count
            """

            for item in processed:
                cond = item["condition"]

                cursor.execute(condition_upsert_query, cond)
                condition_id = cursor.fetchone()[0]

                groupers = item.get("context_groupers", [])
                if not groupers:
                    continue

                grouper_params = [
                    {
                        "condition_id": condition_id,
                        "name": cg["name"],
                        "category": cg["category"],
                        "canonical_url": cg["canonical_url"],
                        "code_count": cg["code_count"],
                    }
                    for cg in groupers
                ]

                cursor.executemany(context_grouper_upsert_query, grouper_params)

            conn.commit()

    except Exception:
        logger.error(
            "❌ A critical error occurred during the condition upsert process.",
            exc_info=True,
        )
        logger.error("Make sure migrations have been run prior to seeding!")
        raise


def _build_condition_groupers(
    valuesets_map: dict[tuple[VsCanonicalUrl, VsVersion], VsDict],
) -> list[VsDict]:
    groupers = [vs for vs in valuesets_map.values() if is_condition_grouper(vs)]
    logger.info(f"🔎 Identified {len(groupers)} condition groupers to process.")
    return groupers


def load_tes_data(db_url: str, db_password: str) -> None:
    """
    Loads condition grouper data from the TES and upserts condition rows and their associated context grouper rows into the database.

    New rows are inserted. Existing rows with the same (canonical_url, version)
    are updated only when relevant fields have changed.

    Args:
        db_url (str): The database URL
        db_password (str): The database password
    """

    all_valuesets_map = load_valuesets_from_all_files()

    condition_groupers = _build_condition_groupers(valuesets_map=all_valuesets_map)

    processed = _build_processed_conditions(
        condition_groupers=condition_groupers,
        valuesets_map=all_valuesets_map,
    )

    if not processed:
        logger.info("⚠️  No conditions found to upsert.")
        return

    logger.info(f"⬆️  Total conditions to upsert: {len(processed)}")
    _upsert_conditions_and_groupers(
        db_url=db_url, db_password=db_password, processed=processed
    )

    logger.info("🏁 Done!")


if __name__ == "__main__":
    load_dotenv(dotenv_path=ENV_PATH)

    db_url = os.getenv("DB_URL")
    db_password = os.getenv("DB_PASSWORD")

    if not db_url or not db_password:
        logger.critical("DB_URL and DB_PASSWORD environment variables must be set.")
    else:
        start = time.perf_counter()
        load_tes_data(db_url=db_url, db_password=db_password)
        end = time.perf_counter()
        logger.info(f"⏱️  Took {end - start:.3f} seconds")
