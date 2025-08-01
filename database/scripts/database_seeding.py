import json
import logging
from pathlib import Path
from typing import Any

import psycopg
from psycopg import Connection, sql

# configuration
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# this path is correct for running inside the Docker container
DATA_DIR = Path("/app/data")


def get_db_connection() -> Connection:
    """
    Establishes and returns a connection to the PostgreSQL database.
    """

    try:
        return psycopg.connect("")
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


def seed_database() -> None:
    """
    Orchestrates the entire database seeding process.
    """

    logging.info("🚀 Starting database seeding...")

    # pass 1: prepare all data in memory
    all_valuesets_map: dict[tuple, dict] = {}
    json_files = [
        file for file in DATA_DIR.glob("*.json") if file.name != "manifest.json"
    ]
    for file_path in json_files:
        with open(file_path) as file:
            data = json.load(file)
            for valueset in data.get("valuesets", []):
                key = (valueset.get("url"), valueset.get("version"))
                all_valuesets_map[key] = valueset

    conditions_to_insert = []
    parent_valuesets = [
        valueset
        for valueset in all_valuesets_map.values()
        if any(
            "valueSet" in item
            for item in valueset.get("compose", {}).get("include", [])
        )
    ]

    for parent in parent_valuesets:
        child_snomed_codes = set()
        aggregated_codes = {
            "loinc_codes": [],
            "snomed_codes": [],
            "icd10_codes": [],
            "rxnorm_codes": [],
        }

        for include_item in parent.get("compose", {}).get("include", []):
            for child_ref in include_item.get("valueSet", []):
                try:
                    child_url, child_version = child_ref.split("|", 1)
                except ValueError:
                    continue

                child_valueset = all_valuesets_map.get((child_url, child_version))
                if not child_valueset:
                    continue

                snomed_code = parse_snomed_from_url(child_valueset.get("url"))
                if snomed_code:
                    child_snomed_codes.add(snomed_code)

                child_extracted_codes = extract_codes_from_valueset(child_valueset)
                for code_type, codes in child_extracted_codes.items():
                    aggregated_codes[code_type].extend(codes)

        conditions_to_insert.append(
            {
                "canonical_url": parent.get("url"),
                "version": parent.get("version"),
                "display_name": parent.get("name") or parent.get("title"),
                "child_rsg_snomed_codes": list(child_snomed_codes),
                "loinc_codes": json.dumps(aggregated_codes["loinc_codes"]),
                "snomed_codes": json.dumps(aggregated_codes["snomed_codes"]),
                "icd10_codes": json.dumps(aggregated_codes["icd10_codes"]),
                "rxnorm_codes": json.dumps(aggregated_codes["rxnorm_codes"]),
            }
        )
    logging.info(
        f"  ✅ Prepared {len(conditions_to_insert)} condition records to insert."
    )

    # pass 2: connect to db and perform all inserts in a single transaction
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                logging.info("🧹 Clearing all data tables...")
                tables = [
                    "configuration_labels",
                    "labels",
                    "configuration_versions",
                    "configurations",
                    "conditions",
                    "users",
                    "jurisdictions",
                ]
                cursor.execute(
                    f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE;"
                )

                if not conditions_to_insert:
                    logging.warning("⚠️ No conditions were processed. Halting seed.")
                    return

                logging.info(
                    f"⏳ Inserting {len(conditions_to_insert)} condition records..."
                )
                insert_query = sql.SQL("""
                    INSERT INTO conditions (canonical_url, version, display_name, child_rsg_snomed_codes, loinc_codes, snomed_codes, icd10_codes, rxnorm_codes)
                    VALUES (%(canonical_url)s, %(version)s, %(display_name)s, %(child_rsg_snomed_codes)s, %(loinc_codes)s, %(snomed_codes)s, %(icd10_codes)s, %(rxnorm_codes)s)
                """)
                cursor.executemany(insert_query, conditions_to_insert)
                logging.info("  ✅ Conditions insert pass complete.")

                logging.info("➕ Inserting test data (Jurisdiction, User, Labels)...")
                cursor.execute(
                    "INSERT INTO jurisdictions (id, name, state_code) VALUES ('TEST_JUR', 'Test Jurisdiction', 'TJ');"
                )
                cursor.execute(
                    "INSERT INTO users (email, jurisdiction_id, full_name) VALUES ('test.user@example.com', 'TEST_JUR', 'Dr. Test User');"
                )
                cursor.execute(
                    "INSERT INTO labels (name, description, color) VALUES ('Production Ready', 'Approved for production use', '#28a745') RETURNING id;"
                )
                prod_label_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO labels (name, description, color) VALUES ('Needs Review', 'Requires review by an epidemiologist', '#ffc107');"
                )

                logging.info(
                    "➕ Creating sample Configuration using the first available condition..."
                )
                first_condition = conditions_to_insert[0]
                sample_condition_url = first_condition["canonical_url"]
                sample_condition_version = first_condition["version"]
                sample_condition_name = first_condition["display_name"]

                cursor.execute(
                    "INSERT INTO configurations (jurisdiction_id, name, description) VALUES ('TEST_JUR', %s, %s) RETURNING id;",
                    (
                        f"Default {sample_condition_name} Config",
                        f"Tracks the latest codes for {sample_condition_name}.",
                    ),
                )
                config_id = cursor.fetchone()[0]

                logging.info("➕ Creating sample Configuration Version (v1)...")
                included_conditions_json = json.dumps(
                    [{"url": sample_condition_url, "version": sample_condition_version}]
                )
                cursor.execute(
                    """
                    INSERT INTO configuration_versions (configuration_id, version, is_active, notes, included_conditions)
                    VALUES (%s, 1, true, %s, %s);
                    """,
                    (
                        config_id,
                        f"Initial version, linked to {sample_condition_name} v{sample_condition_version}.",
                        included_conditions_json,
                    ),
                )

                logging.info(
                    "➕ Applying 'Production Ready' label to the new configuration..."
                )
                cursor.execute(
                    "INSERT INTO configuration_labels (configuration_id, label_id) VALUES (%s, %s);",
                    (config_id, prod_label_id),
                )

                connection.commit()
                logging.info("\n🎉 SUCCESS: Database seeding complete!")

    except (psycopg.Error, Exception) as error:
        logging.error(
            "❌ A critical error occurred during the seeding process. The transaction has been rolled back."
        )
        logging.error(f"  Error details: {error}")
        raise


if __name__ == "__main__":
    seed_database()
