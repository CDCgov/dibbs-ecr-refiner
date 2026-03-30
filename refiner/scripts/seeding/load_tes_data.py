import os
import time
from typing import Any, TypedDict

from config import ENV_PATH, logger
from dotenv import load_dotenv
from lib import (
    ConditionData,
    get_db_connection,
    is_condition_grouper,
    load_valuesets_from_all_files,
)


class ConditionRow(TypedDict):
    """
    A condition row to upsert into the DB.
    """

    canonical_url: str
    version: str
    display_name: str
    child_rsg_snomed_codes: list[str] | None
    loinc_codes: list[str] | None
    snomed_codes: list[str] | None
    icd10_codes: list[str] | None
    rxnorm_codes: list[str] | None
    cvx_codes: list[str] | None


def _build_condition_upsert_rows(
    condition_groupers: list[dict],
    valuesets_map: dict[tuple[str, str], dict],
) -> list[ConditionRow]:
    conditions: list[ConditionRow] = []

    for parent in condition_groupers:
        conditions.append(ConditionData(parent, valuesets_map).payload)

    logger.info(f"🛠️  Total condition rows processed: {len(conditions)}")
    return conditions


def _upsert_processed_conditions(
    db_url: str, db_password: str, conditions: list[dict[str, Any]]
) -> None:
    try:
        with get_db_connection(db_url, db_password) as conn, conn.cursor() as cursor:
            logger.info("⏳ Upserting condition records...")

            upsert_query = """
                INSERT INTO conditions (
                    canonical_url,
                    version,
                    display_name,
                    child_rsg_snomed_codes,
                    loinc_codes,
                    snomed_codes,
                    icd10_codes,
                    rxnorm_codes,
                    cvx_codes
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
                    %(cvx_codes)s
                )
                ON CONFLICT (canonical_url, version)
                DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    child_rsg_snomed_codes = EXCLUDED.child_rsg_snomed_codes,
                    loinc_codes = EXCLUDED.loinc_codes,
                    snomed_codes = EXCLUDED.snomed_codes,
                    icd10_codes = EXCLUDED.icd10_codes,
                    rxnorm_codes = EXCLUDED.rxnorm_codes,
                    cvx_codes = EXCLUDED.cvx_codes
                WHERE
                    conditions.display_name IS DISTINCT FROM EXCLUDED.display_name
                    OR conditions.child_rsg_snomed_codes IS DISTINCT FROM EXCLUDED.child_rsg_snomed_codes
                    OR conditions.loinc_codes IS DISTINCT FROM EXCLUDED.loinc_codes
                    OR conditions.snomed_codes IS DISTINCT FROM EXCLUDED.snomed_codes
                    OR conditions.icd10_codes IS DISTINCT FROM EXCLUDED.icd10_codes
                    OR conditions.rxnorm_codes IS DISTINCT FROM EXCLUDED.rxnorm_codes
                    OR conditions.cvx_codes IS DISTINCT FROM EXCLUDED.cvx_codes
            """

            cursor.executemany(upsert_query, conditions)
            conn.commit()

    except Exception:
        logger.error(
            "❌ A critical error occurred during the condition upsert process.",
            exc_info=True,
        )
        logger.error("Make sure migrations have been run prior to seeding!")
        raise


def _build_condition_groupers(valuesets_map: dict[tuple[str, str], dict]) -> list[dict]:
    groupers = [vs for vs in valuesets_map.values() if is_condition_grouper(vs)]
    logger.info(f"🔎 Identified {len(groupers)} condition groupers to process.")
    return groupers


def load_tes_data(db_url: str, db_password: str) -> None:
    """
    Loads condition grouper data from the TES and upserts condition rows into the database.

    New rows are inserted. Existing rows with the same (canonical_url, version)
    are updated only when relevant fields have changed.

    Args:
        db_url (str): The database URL
        db_password (str): The database password
    """

    all_valuesets_map = load_valuesets_from_all_files()

    condition_groupers = _build_condition_groupers(valuesets_map=all_valuesets_map)

    upsertable_condition_rows = _build_condition_upsert_rows(
        condition_groupers=condition_groupers,
        valuesets_map=all_valuesets_map,
    )

    if not upsertable_condition_rows:
        logger.info("⚠️  No conditions found to upsert.")
        return

    logger.info(f"⬆️  Total conditions to upsert: {len(upsertable_condition_rows)}")
    _upsert_processed_conditions(
        db_url=db_url, db_password=db_password, conditions=upsertable_condition_rows
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
