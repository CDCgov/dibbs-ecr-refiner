import json
import logging
import os
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg import Connection, sql

# configuration
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

SEEDING_DIR = Path(__file__).parent
SCRIPTS_DIR = SEEDING_DIR.parent
DATA_DIR = SCRIPTS_DIR / "data"
TES_DATA_DIR = DATA_DIR / "tes"
SEEDING_DATA_DIR = DATA_DIR / "seeding"
ENV_PATH = SCRIPTS_DIR / ".env"


def get_db_connection(db_url) -> Connection:
    """
    Establishes and returns a connection to the PostgreSQL database.
    """

    try:
        return psycopg.connect(db_url)
    except psycopg.OperationalError as error:
        logging.error(f"❌ Database connection failed: {error}")
        raise


def extract_codes_from_valueset(valueset: dict[str, Any]) -> dict[str, list[dict]]:
    """
    Extracts all code types from a single ValueSet into structured lists.
    """

    codes = {
        "loinc_codes": [],
        "snomed_codes": [],
        "icd10_codes": [],
        "rxnorm_codes": [],
    }
    system_map = {
        "http://loinc.org": "loinc_codes",
        "http://snomed.info/sct": "snomed_codes",
        "http://hl7.org/fhir/sid/icd-10-cm": "icd10_codes",
        "http://www.nlm.nih.gov/research/umls/rxnorm": "rxnorm_codes",
    }
    compose = valueset.get("compose", {})
    for include_item in compose.get("include", []):
        system_url = include_item.get("system")
        code_key = system_map.get(system_url)
        if code_key and "concept" in include_item:
            for concept in include_item["concept"]:
                codes[code_key].append(
                    {"display": concept.get("display"), "code": concept.get("code")}
                )
    return codes


def parse_snomed_from_url(url: str) -> str | None:
    """
    Extracts the SNOMED code from a Reporting Spec Grouper URL.
    """

    if "rs-grouper-" in url:
        return url.split("rs-grouper-")[-1]
    return None


def seed_database(db_url) -> None:
    """
    Orchestrates the entire database seeding process.
    """

    logging.info("🚀 Starting database seeding...")

    # pass 1: prepare condition data from ValueSet files
    all_valuesets_map: dict[tuple, dict] = {}
    json_files = [
        file for file in TES_DATA_DIR.glob("*.json") if file.name != "manifest.json"
    ]
    for file_path in json_files:
        with open(file_path) as file:
            data = json.load(file)
            if "valuesets" in data:
                for valueset in data.get("valuesets", []):
                    key = (valueset.get("url"), valueset.get("version"))
                    all_valuesets_map[key] = valueset

    conditions_to_insert = []
    if all_valuesets_map:
        parent_valuesets = [
            valueset
            for valueset in all_valuesets_map.values()
            if any(
                "valueSet" in item
                for item in valueset.get("compose", {}).get("include", [])
            )
        ]
        for parent in parent_valuesets:
            child_snomed_codes, aggregated_codes = (
                set(),
                {
                    "loinc_codes": [],
                    "snomed_codes": [],
                    "icd10_codes": [],
                    "rxnorm_codes": [],
                },
            )
            for include_item in parent.get("compose", {}).get("include", []):
                for child_reference in include_item.get("valueSet", []):
                    try:
                        child_url, child_version = child_reference.split("|", 1)
                    except ValueError:
                        continue
                    child_valueset = all_valuesets_map.get((child_url, child_version))
                    if not child_valueset:
                        continue
                    snomed_code = parse_snomed_from_url(child_valueset.get("url"))
                    if snomed_code:
                        child_snomed_codes.add(snomed_code)
                    child_extracted = extract_codes_from_valueset(child_valueset)
                    for code_type, codes in child_extracted.items():
                        aggregated_codes[code_type].extend(codes)
            conditions_to_insert.append(
                {
                    "canonical_url": parent.get("url"),
                    "version": parent.get("version"),
                    "display_name": (
                        parent.get("title") or parent.get("name") or ""
                    ).replace("_", " "),
                    "child_rsg_snomed_codes": list(child_snomed_codes),
                    "loinc_codes": json.dumps(aggregated_codes["loinc_codes"]),
                    "snomed_codes": json.dumps(aggregated_codes["snomed_codes"]),
                    "icd10_codes": json.dumps(aggregated_codes["icd10_codes"]),
                    "rxnorm_codes": json.dumps(aggregated_codes["rxnorm_codes"]),
                }
            )

    if conditions_to_insert:
        logging.info(
            f"  ✅ Prepared {len(conditions_to_insert)} condition records to insert."
        )

    # pass 2: connect to db and perform all inserts in a single transaction
    try:
        with get_db_connection(db_url=db_url) as connection:
            with connection.cursor() as cursor:
                logging.info("🧹 Clearing all data tables...")
                tables = [
                    "conditions",
                    "jurisdictions",
                    "configurations",
                    "sessions",
                    "users",
                ]
                for table in tables:
                    try:
                        cursor.execute(
                            f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"
                        )
                    except (
                        psycopg.errors.UndefinedTable,
                        psycopg.errors.InFailedSqlTransaction,
                    ):
                        logging.warning(f"Table {table} does not exist, skipping.")

                if conditions_to_insert:
                    logging.info(
                        f"⏳ Inserting {len(conditions_to_insert)} condition records..."
                    )
                    insert_query = sql.SQL("""
                        INSERT INTO public.conditions (canonical_url, version, display_name, child_rsg_snomed_codes, loinc_codes, snomed_codes, icd10_codes, rxnorm_codes)
                        VALUES (%(canonical_url)s, %(version)s, %(display_name)s, %(child_rsg_snomed_codes)s, %(loinc_codes)s, %(snomed_codes)s, %(icd10_codes)s, %(rxnorm_codes)s)
                    """)
                    cursor.executemany(insert_query, conditions_to_insert)
                    logging.info("  ✅ Conditions insert pass complete.")
                else:
                    logging.warning(
                        "⚠️ No conditions were processed from ValueSet files."
                    )

                connection.commit()
                logging.info("\n🎉 SUCCESS: Database seeding complete!")

    except (psycopg.Error, Exception) as error:
        logging.error(
            "❌ A critical error occurred during the seeding process. The transaction has been rolled back."
        )
        logging.error(f"  Error details: {error}")
        logging.error("🧠 Make sure migrations have been run prior to seeding!")
        raise


if __name__ == "__main__":
    load_dotenv(dotenv_path=ENV_PATH)
    db_url = os.getenv("DB_URL")
    seed_database(db_url=db_url)
