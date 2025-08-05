import json
import logging
from pathlib import Path
from typing import Any

import psycopg
from psycopg import Connection, Cursor, sql

# configuration
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# this path is correct for running inside the Docker container
DATA_DIR = Path("/app/data")
# correct path for the test configuration and jurisdiction data file inside the container
TEST_DATA_FILE = Path("/app/scripts/sample_configuration_seed_data.json")


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


def seed_test_data_from_json(cursor: Cursor, test_data: dict[str, Any]) -> None:
    """
    Seeds jurisdictions, users, labels, configurations, and activations from a JSON object.
    """

    logging.info("🌱 Seeding test data from JSON file...")

    # jurisdictions
    jurisdictions = test_data.get("jurisdictions", [])
    if jurisdictions:
        logging.info(f"  - Inserting {len(jurisdictions)} jurisdiction(s)...")
        insert_query = sql.SQL(
            "INSERT INTO jurisdictions (id, name, state_code) VALUES (%(id)s, %(name)s, %(state_code)s)"
        )
        cursor.executemany(insert_query, jurisdictions)

    # users
    users = test_data.get("users", [])
    if users:
        logging.info(f"  - Inserting {len(users)} user(s)...")
        insert_query = sql.SQL(
            "INSERT INTO users (email, jurisdiction_id, full_name) VALUES (%(email)s, %(jurisdiction_id)s, %(full_name)s)"
        )
        cursor.executemany(insert_query, users)

    # labels
    labels_to_insert = test_data.get("labels", [])
    label_id_map = {}
    if labels_to_insert:
        logging.info(f"  - Inserting {len(labels_to_insert)} label(s)...")
        for label in labels_to_insert:
            cursor.execute(
                "INSERT INTO labels (name, color, description) VALUES (%s, %s, %s) RETURNING id, name",
                (label["name"], label["color"], label["description"]),
            )
            label_id, label_name = cursor.fetchone()
            label_id_map[label_name] = label_id

    # configurations
    configs_to_insert = test_data.get("configurations", [])
    config_id_map = {}
    if configs_to_insert:
        logging.info(f"  - Inserting {len(configs_to_insert)} configuration(s)...")
        for config in configs_to_insert:
            cursor.execute(
                "INSERT INTO configurations (jurisdiction_id, name, description) VALUES (%s, %s, %s) RETURNING id, name",
                (config["jurisdiction_id"], config["name"], config["description"]),
            )
            config_id, config_name = cursor.fetchone()
            config_id_map[config_name] = config_id

    # configuration versions
    versions_to_insert = test_data.get("configuration_versions", [])
    version_id_map = {}  # To link activations to the correct version ID
    if versions_to_insert:
        logging.info(
            f"  - Inserting {len(versions_to_insert)} configuration version(s)..."
        )
        for version in versions_to_insert:
            config_id = config_id_map.get(version["configuration_name"])
            if not config_id:
                logging.warning(
                    f"⚠️ Skipping version for unknown configuration '{version['configuration_name']}'"
                )
                continue
            cursor.execute(
                """
                INSERT INTO configuration_versions (
                    configuration_id, version, status, notes, included_conditions,
                    loinc_codes_additions, snomed_codes_additions, icd10_codes_additions, rxnorm_codes_additions
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """,
                (
                    config_id,
                    version["version"],
                    version["status"],
                    version.get("notes"),
                    json.dumps(version.get("included_conditions")),
                    json.dumps(version.get("loinc_codes_additions")),
                    json.dumps(version.get("snomed_codes_additions")),
                    json.dumps(version.get("icd10_codes_additions")),
                    json.dumps(version.get("rxnorm_codes_additions")),
                ),
            )
            version_id = cursor.fetchone()[0]
            version_key = (version["configuration_name"], version["version"])
            version_id_map[version_key] = version_id

    # activations
    activations_to_insert = test_data.get("activations", [])
    if activations_to_insert:
        logging.info(
            f"  - Inserting {len(activations_to_insert)} activation record(s)..."
        )
        for activation in activations_to_insert:
            version_key = (
                activation["configuration_name"],
                activation["configuration_version"],
            )
            version_id = version_id_map.get(version_key)
            if version_id:
                cursor.execute(
                    "INSERT INTO activations (snomed_code, configuration_version_id) VALUES (%s, %s)",
                    (activation["snomed_code"], version_id),
                )
            else:
                logging.warning(
                    f"⚠️ Skipping activation for unknown version: {version_key}"
                )

    # configuration labels (join table)
    config_labels_to_insert = test_data.get("configuration_labels", [])
    if config_labels_to_insert:
        logging.info(
            f"  - Applying {len(config_labels_to_insert)} label(s) to configurations..."
        )
        for config_label in config_labels_to_insert:
            config_id = config_id_map.get(config_label["configuration_name"])
            label_id = label_id_map.get(config_label["label_name"])
            if config_id and label_id:
                cursor.execute(
                    "INSERT INTO configuration_labels (configuration_id, label_id) VALUES (%s, %s)",
                    (config_id, label_id),
                )
            else:
                logging.warning(
                    f"⚠️ Skipping label join for missing config ('{config_label['configuration_name']}') or label ('{config_label['label_name']}')"
                )

    logging.info("  ✅ Test data seeding complete.")


def seed_database() -> None:
    """
    Orchestrates the entire database seeding process.
    """

    logging.info("🚀 Starting database seeding...")

    # pass 1: prepare condition data from ValueSet files
    all_valuesets_map: dict[tuple, dict] = {}
    json_files = [
        file for file in DATA_DIR.glob("*.json") if file.name != "manifest.json"
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
                    "display_name": parent.get("name") or parent.get("title"),
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
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                logging.info("🧹 Clearing all data tables...")
                tables = [
                    "activations",
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

                if conditions_to_insert:
                    logging.info(
                        f"⏳ Inserting {len(conditions_to_insert)} condition records..."
                    )
                    insert_query = sql.SQL("""
                        INSERT INTO conditions (canonical_url, version, display_name, child_rsg_snomed_codes, loinc_codes, snomed_codes, icd10_codes, rxnorm_codes)
                        VALUES (%(canonical_url)s, %(version)s, %(display_name)s, %(child_rsg_snomed_codes)s, %(loinc_codes)s, %(snomed_codes)s, %(icd10_codes)s, %(rxnorm_codes)s)
                    """)
                    cursor.executemany(insert_query, conditions_to_insert)
                    logging.info("  ✅ Conditions insert pass complete.")
                else:
                    logging.warning(
                        "⚠️ No conditions were processed from ValueSet files."
                    )

                # Load and seed test data from the sample configuration file
                if TEST_DATA_FILE.exists():
                    with open(TEST_DATA_FILE) as f:
                        test_data = json.load(f)
                    seed_test_data_from_json(cursor, test_data)
                else:
                    logging.warning(
                        f"⚠️ Test data file not found at {TEST_DATA_FILE}. Skipping test data seeding."
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
