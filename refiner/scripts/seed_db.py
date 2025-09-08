import json
import logging
import os
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg import Connection, Cursor, sql

# configuration
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

current_dir = Path(__file__).parent

DATA_DIR = current_dir / "data"
# correct path for the test configuration and jurisdiction data file inside the container
TEST_DATA_FILE = current_dir / "sample_configuration_seed_data.json"

filters_data_path = Path(DATA_DIR / "filters_data.sql")
groupers_data_path = Path(DATA_DIR / "groupers_data.sql")


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


def seed_test_data_from_json(cursor: Cursor, test_data: dict[str, Any]) -> None:
    """
    Seeds jurisdictions, users, labels, configurations, and activations from a JSON object.
    """

    logging.info("🌱 Seeding test data from JSON file...")

    # labels
    # labels_to_insert = test_data.get("labels", [])
    # label_id_map = {}
    # if labels_to_insert:
    #     logging.info(f"  - Inserting {len(labels_to_insert)} label(s)...")
    #     for label in labels_to_insert:
    #         cursor.execute(
    #             "INSERT INTO labels (name, color, description) VALUES (%s, %s, %s) RETURNING id, name",
    #             (label["name"], label["color"], label["description"]),
    #         )
    #         label_id, label_name = cursor.fetchone()
    #         label_id_map[label_name] = label_id

    # configurations
    # configs_to_insert = test_data.get("configurations", [])
    # config_uuid_map = {}  # Maps "1001_V1" -> actual UUID
    # if configs_to_insert:
    #     logging.info(f"  - Inserting {len(configs_to_insert)} configuration(s)...")
    #     for config in configs_to_insert:
    #         # Handle cloned_from_configuration_id placeholder resolution
    #         cloned_from_id = config.get("cloned_from_configuration_id")
    #         if cloned_from_id and cloned_from_id.startswith("PLACEHOLDER_UUID_"):
    #             placeholder_key = cloned_from_id.replace("PLACEHOLDER_UUID_", "")
    #             cloned_from_id = config_uuid_map.get(placeholder_key)
    #         elif cloned_from_id == "null":
    #             cloned_from_id = None

    #         cursor.execute(
    #             """
    # INSERT INTO configurations (
    #     family_id, version, jurisdiction_id, name, description,
    #     included_conditions, loinc_codes_additions, snomed_codes_additions,
    #     icd10_codes_additions, rxnorm_codes_additions, custom_codes,
    #     sections_to_include, cloned_from_configuration_id
    # ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
    #             """,
    #             (
    #                 config["family_id"],
    #                 config["version"],
    #                 config["jurisdiction_id"],
    #                 config["name"],
    #                 config["description"],
    #                 json.dumps(config.get("included_conditions", [])),
    #                 json.dumps(config.get("loinc_codes_additions", [])),
    #                 json.dumps(config.get("snomed_codes_additions", [])),
    #                 json.dumps(config.get("icd10_codes_additions", [])),
    #                 json.dumps(config.get("rxnorm_codes_additions", [])),
    #                 json.dumps(config.get("custom_codes", [])),
    #                 config.get("sections_to_include", []),
    #                 cloned_from_id,
    #             ),
    #         )
    #         config_uuid = cursor.fetchone()[0]
    #         # store mapping for placeholder resolution
    #         config_key = f"{config['family_id']}_V{config['version']}"
    #         config_uuid_map[config_key] = config_uuid

    # activations
    # activations_to_insert = test_data.get("activations", [])
    # if activations_to_insert:
    #     logging.info(
    #         f"  - Inserting {len(activations_to_insert)} activation record(s)..."
    #     )
    #     for activation in activations_to_insert:
    #         # look up configuration UUID by family_id + version
    #         family_id = activation.get("configuration_family_id")
    #         version = activation.get("configuration_version")

    #         if family_id and version:
    #             config_key = f"{family_id}_V{version}"
    #             config_uuid = config_uuid_map.get(config_key)

    #             if config_uuid:
    #                 cursor.execute(
    #                     """INSERT INTO activations
    #                     (jurisdiction_id, snomed_code, configuration_id, computed_codes, s3_synced_at, s3_object_key)
    #                     VALUES (%s, %s, %s, %s, %s, %s)""",
    #                     (
    #                         activation["jurisdiction_id"],
    #                         activation["snomed_code"],
    #                         config_uuid,
    #                         json.dumps(activation["computed_codes"]),
    #                         activation["s3_synced_at"],
    #                         activation["s3_object_key"],
    #                     ),
    #                 )
    #             else:
    #                 logging.warning(
    #                     f"⚠️ Could not find configuration UUID for family {family_id} v{version}"
    #                 )
    #         else:
    #             logging.warning(
    #                 f"⚠️ Skipping activation with missing family_id/version: {activation}"
    #             )

    # configuration labels
    # config_labels_to_insert = test_data.get("configuration_labels", [])
    # if config_labels_to_insert:
    #     logging.info(
    #         f"  - Applying {len(config_labels_to_insert)} label(s) to configurations..."
    #     )
    #     for config_label in config_labels_to_insert:
    #         # resolve placeholder UUID to actual UUID
    #         config_id_placeholder = config_label.get("configuration_id", "")
    #         if config_id_placeholder.startswith("PLACEHOLDER_UUID_"):
    #             config_key = config_id_placeholder.replace("PLACEHOLDER_UUID_", "")
    #             config_uuid = config_uuid_map.get(config_key)
    #         else:
    #             config_uuid = config_id_placeholder

    #         label_id = label_id_map.get(config_label["label_name"])

    #         if config_uuid and label_id:
    #             cursor.execute(
    #                 "INSERT INTO configuration_labels (configuration_id, label_id) VALUES (%s, %s)",
    #                 (config_uuid, label_id),
    #             )
    #         else:
    #             logging.warning(
    #                 f"⚠️ Skipping label join for missing config UUID ({config_uuid}) or label ('{config_label['label_name']}')"
    #             )

    # logging.info("  ✅ Test data seeding complete.")


def seed_filters_data(cursor) -> None:
    """
    Seeds filters data used by the Refiner.
    """
    try:
        cursor.execute(filters_data_path.read_text())
    except (psycopg.Error, Exception) as error:
        logging.error(
            "❌ Unable to seed filters data. The transaction has been rolled back."
        )
        logging.error(f"  Error details: {error}")
        raise


def seed_groupers_data(cursor) -> None:
    """
    Seeds groupers data used by the Refiner.
    """
    try:
        cursor.execute(groupers_data_path.read_text())
    except (psycopg.Error, Exception) as error:
        logging.error(
            "❌ Unable to seed groupers data. The transaction has been rolled back."
        )
        logging.error(f"  Error details: {error}")
        raise


def seed_database(db_url) -> None:
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
                    "activations",
                    "conditions",
                    "configuration_labels",
                    "filters",
                    "groupers",
                    "jurisdictions",
                    "configurations",
                    "labels",
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

                # seed filters and groupers from .sql files
                seed_filters_data(cursor)
                seed_groupers_data(cursor)

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

                # load and seed test data from the sample configuration file
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
        logging.error("🧠 Make sure migrations have been run prior to seeding!")
        raise


if __name__ == "__main__":
    load_dotenv()
    db_url = os.getenv("DB_URL")
    seed_database(db_url=db_url)
