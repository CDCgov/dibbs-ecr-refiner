import os
import time
from typing import Any

from config import ENV_PATH, logger
from dotenv import load_dotenv
from lib import (
    ConditionData,
    get_db_connection,
    is_condition_grouper,
    load_valuesets_from_all_files,
)
from psycopg import sql


def _get_existing_versions(db_url: str, db_password: str) -> set[str]:
    """
    Returns a list of TES versions already present in the database.
    """

    query = """
    SELECT DISTINCT(version)
    FROM conditions
    """
    try:
        with get_db_connection(db_url, db_password) as conn, conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return {row[0] for row in rows}
    except Exception:
        logger.critical(
            "Could not connect to the DB while getting existing TES versions"
        )


def _build_processed_conditions(
    condition_groupers: list[dict],
    valuesets_map: dict[tuple[str, str], dict],
    versions_to_skip: set[str] = {},
) -> list[ConditionData]:
    conditions: list[ConditionData] = []

    versions_seen: set[str] = set()
    skipped_count = 0
    for parent in condition_groupers:
        version = parent.get("version")
        if version in versions_to_skip:
            versions_seen.add(version)
            skipped_count += 1
            continue

        conditions.append(ConditionData(parent, valuesets_map))

    for v in versions_seen:
        logger.info(f"💡 TES version {v} data already found in DB, skipping import...")

    logger.info(f"⏭️  Total condition rows skipped during processing: {skipped_count}")
    return conditions


def _insert_processed_conditions(
    db_url: str, db_password: str, conditions: list[ConditionData]
) -> None:
    try:
        with get_db_connection(db_url, db_password) as conn, conn.cursor() as cursor:
            logger.info("⏳ Inserting condition records...")
            insert_query = sql.SQL(
                """
                INSERT INTO public.conditions (
                    canonical_url,
                    version,
                    display_name,
                    child_rsg_snomed_codes,
                    loinc_codes,
                    snomed_codes,
                    icd10_codes,
                    rxnorm_codes
                )
                VALUES (
                    %(canonical_url)s,
                    %(version)s,
                    %(display_name)s,
                    %(child_rsg_snomed_codes)s,
                    %(loinc_codes)s,
                    %(snomed_codes)s,
                    %(icd10_codes)s,
                    %(rxnorm_codes)s
                )
                """
            )

            cursor.executemany(insert_query, conditions)
            conn.commit()
    except Exception:
        logger.error(
            "❌ A critical error occurred during the condition insert process.",
            exc_info=True,
        )
        logger.error("Make sure migrations have been run prior to seeding!")
        raise


def _build_insertable_conditions(
    processed_conditions: list[ConditionData],
) -> list[dict[str, Any]]:
    return [cond.payload for cond in processed_conditions]


def _build_condition_groupers(valuesets_map: dict[tuple[str, str], dict]) -> list[dict]:
    groupers = [vs for vs in valuesets_map.values() if is_condition_grouper(vs)]
    logger.info(f"🔎 Identified {len(groupers)} condition groupers to process.")
    return groupers


def load_tes_data(db_url: str, db_password: str) -> None:
    """
    Determines which condition groupers from the TES need to be inserted into the database and performs the insert.

    It will skip any data that has already been found in the database by default.

    Args:
        db_url (str): The database URL
        db_password (str): The database password
    """
    # Get versions that already exist in DB
    versions_in_db: set[str] = set()
    versions_in_db = _get_existing_versions(db_url=db_url, db_password=db_password)
    logger.info("🏃 Previously loaded TES condition data will be skipped.")

    all_vs_map = load_valuesets_from_all_files()

    condition_groupers = _build_condition_groupers(valuesets_map=all_vs_map)

    processed_conditions = _build_processed_conditions(
        condition_groupers=condition_groupers,
        valuesets_map=all_vs_map,
        versions_to_skip=versions_in_db,
    )

    insertable_conditions = _build_insertable_conditions(processed_conditions)
    if not insertable_conditions:
        logger.info("⚠️  All conditions found already exist. Skipping insert step.")
        return

    logger.info(f"⬆️  Total conditions to insert: {len(insertable_conditions)}")
    _insert_processed_conditions(
        db_url=db_url, db_password=db_password, conditions=insertable_conditions
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
