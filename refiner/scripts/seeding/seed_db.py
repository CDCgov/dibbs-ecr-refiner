import os
import time

import psycopg
from config import ENV_PATH, logger
from dotenv import load_dotenv
from lib import (
    get_db_connection,
)
from tes_update import run_tes_update


def seed_database(db_url: str, db_password: str) -> None:
    """
    Orchestrates the entire database seeding process.
    """

    logger.info("🚀 Starting database seeding...")
    try:
        with get_db_connection(db_url, db_password) as conn, conn.cursor() as cursor:
            logger.info("🧹 Clearing specified data tables...")

            for table in [
                "conditions",
                "jurisdictions",
                "configurations",
                "sessions",
                "users",
            ]:
                try:
                    cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                except psycopg.errors.UndefinedTable:
                    logger.warning(f"Table '{table}' not found, skipping truncation.")
    except Exception:
        logger.error(
            "❌ A critical error occurred during the existing data cleanup process.",
            exc_info=True,
        )
        logger.error("Make sure migrations have been run prior to seeding!")
        raise
    # all_vs_map = load_valuesets_from_all_files()

    # condition_groupers = [vs for vs in all_vs_map.values() if is_condition_grouper(vs)]
    # logger.info(
    #     f"🔎 Identified {len(condition_groupers)} condition groupers to process."
    # )

    # processed_conditions = [
    #     ConditionData(parent, all_vs_map) for parent in condition_groupers
    # ]
    # conditions_to_insert = [cond.payload for cond in processed_conditions]

    # if not conditions_to_insert:
    #     logger.warning("⚠️ No conditions were processed. Aborting database write.")
    #     return

    # logger.info(f"✅ Prepared {len(conditions_to_insert)} records for insertion.")
    run_tes_update(db_url=db_url, db_password=db_password, skip_existing_versions=False)


if __name__ == "__main__":
    load_dotenv(dotenv_path=ENV_PATH)

    db_url = os.getenv("DB_URL")
    db_password = os.getenv("DB_PASSWORD")

    if not db_url or not db_password:
        logger.critical("DB_URL and DB_PASSWORD environment variables must be set.")
    else:
        start = time.perf_counter()
        seed_database(db_url=db_url, db_password=db_password)
        end = time.perf_counter()
        print(f"Took {end - start:.3f} seconds")
