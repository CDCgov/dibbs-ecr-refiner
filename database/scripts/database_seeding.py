import json
import logging
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg import Connection

# configuration
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
load_dotenv()

DATA_DIR = Path("/app/data")

# NOTE: this map intentionally omits 'additional_context_grouper'
# * our current schema only allows references to `tes_reporting_spec_groupers`;
#   to keep the initial implementation simple, we are only seeding the data
#   required for the core functionality. when we need to incorporate other
#   grouper types, the schema and this script will need to be updated
TABLE_MAP = {
    "condition_grouper": "tes_condition_groupers",
    "reporting_spec_grouper": "tes_reporting_spec_groupers",
}


def get_db_connection() -> Connection:
    """
    Establishes and returns a connection to the PostgreSQL database.

    Connection parameters are automatically sourced from environment variables
    (e.g., PGHOST, PGUSER, PGPASSWORD, PGDATABASE) by psycopg.

    Raises:
        psycopg.OperationalError: If the database connection fails.

    Returns:
        Connection: The active database connection object.
    """

    try:
        logging.info("🔌 Connecting to database using environment variables...")
        return psycopg.connect("")
    except psycopg.OperationalError as error:
        logging.error(f"❌ Database connection failed: {error}")
        raise


def extract_codes(valueset: dict[str, Any], code_system_url: str) -> str:
    """
    Extracts concept codes from a FHIR ValueSet for a specific code system.

    Args:
        valueset: A dictionary representing a single FHIR ValueSet resource.
        code_system_url: The canonical URL for the code system to extract
                         (e.g., 'http://snomed.info/sct').

    Returns:
        str: A JSON string representing a list of the extracted codes.
             Returns an empty JSON list '[]' if no codes are found.
    """

    codes = []
    compose = valueset.get("compose", {})
    for include_item in compose.get("include", []):
        if "valueSet" in include_item:
            continue
        if include_item.get("system") == code_system_url:
            if "concept" in include_item:
                codes.extend([concept["code"] for concept in include_item["concept"]])
    return json.dumps(codes)


def parse_child_url(url_with_version: str) -> tuple[str, str] | None:
    """
    Parses a versioned FHIR ValueSet URL into its components.

    The FHIR standard often represents versioned ValueSet references in a
    single string, delimited by a pipe character '|'.

    Args:
        url_with_version: The URL string, expected in the format
                          'canonical_url|version'.

    Returns:
        A tuple containing the (canonical_url, version) if parsing is
        successful, otherwise None.
    """

    if "|" in url_with_version:
        return tuple(url_with_version.split("|", 1))
    return None


def populate_refinement_cache(connection: Connection) -> None:
    """
    Manually populates the refinement_cache after the main seeding is complete.

    This function executes a single, powerful query to calculate the aggregated
    code sets for every grouper and insert them into the cache. This is more
    reliable and efficient for a bulk-seeding operation than relying on
    row-level triggers.

    Args:
        connection: The active database connection.
    """

    logging.info("🧮 Populating the refinement_cache...")
    with connection.cursor() as cursor:
        try:
            # this query correctly populates the cache by combining the base
            # codes from the parent grouper with any overrides from the
            # jurisdiction-specific configuration. It performs the logic
            # directly instead of calling a potentially mismatched function
            cursor.execute(
                """
                INSERT INTO refinement_cache (
                    snomed_code,
                    jurisdiction_id,
                    aggregated_codes,
                    source_details
                )
                SELECT
                    rsg.snomed_code,
                    conf.jurisdiction_id,
                    -- Combine the parent's SNOMED codes with the override codes
                    ARRAY(
                        SELECT DISTINCT code
                        FROM (
                            SELECT jsonb_array_elements_text(cg.snomed_codes) AS code FROM tes_condition_groupers cg
                            WHERE cg.canonical_url = ref.parent_grouper_url AND cg.version = ref.parent_grouper_version
                            UNION ALL
                            SELECT jsonb_array_elements_text(conf.snomed_codes) AS code
                        ) AS combined_codes
                    ),
                    jsonb_build_object(
                        'source', 'Seeded Configuration',
                        'parent_grouper_url', ref.parent_grouper_url,
                        'configuration_id', conf.id
                    )
                FROM
                    configurations conf
                JOIN
                    tes_reporting_spec_groupers rsg ON conf.child_grouper_url = rsg.canonical_url AND conf.child_grouper_version = rsg.version
                JOIN
                    tes_condition_grouper_references ref ON rsg.canonical_url = ref.child_grouper_url AND rsg.version = ref.child_grouper_version
                ON CONFLICT (snomed_code, jurisdiction_id) DO NOTHING;
                """
            )
            logging.info(
                f"  ✨ Successfully populated refinement cache. {cursor.rowcount} rows affected."
            )
            connection.commit()
        except psycopg.Error as e:
            logging.error(f"❌ Failed to populate refinement cache: {e}")
            connection.rollback()
            raise


# main seeding logic
def seed_database() -> None:
    """
    Orchestrates the entire database seeding process.

    This function performs a full refresh of the terminology tables based on
    the JSON ValueSet files located in the /app/data directory. It follows
    a three-pass strategy to handle dependencies between tables.

    The process is as follows:
    1.  TRUNCATE: All relevant tables are cleared to ensure a clean slate.
    2.  PASS 1 (Seeding Groupers): It reads all JSON files, identifies them
        by category (e.g., 'condition_grouper'), and inserts the ValueSet
        data into the corresponding tables (`tes_condition_groupers`,
        `tes_reporting_spec_groupers`). It intentionally skips files that
        are not part of the core requirement, like 'additional_context_grouper'.
        During this pass, it also collects the primary keys of all
        `tes_reporting_spec_groupers` to use for validation in the next step.
    3.  PASS 2 (Seeding References): It iterates through all the parsed
        ValueSets again. For parent groupers, it attempts to create links
        to their children. A link is only created if the child is a valid
        `tes_reporting_spec_grouper` (verified against the keys collected
        in Pass 1), thus preventing foreign key constraint violations.
    4.  The high-speed `COPY` command is used for inserting references for
        optimal performance.
    5.  PASS 3 (Populate the refinement cache): The transaction management
        within the seeding script prevents the triggers from firing in the
        expected sequence. Our solution here is to not just rely on the triggers
        _during the seed_; rather, will run a single command at the end of
        the seed to populate the cache table.

    Raises:
        psycopg.Error: If any database operation fails.
        Exception: For any other unexpected errors during the process.
    """

    logging.info("🚀 Starting database seeding from pipeline data...")

    # collect all ValueSets
    all_valuesets = []

    # set to store keys of valid RS groupers
    rs_grouper_keys = set()

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                # 1. clear all tables
                logging.info("🧹 Clearing all data tables...")
                tables = [
                    "refinement_cache",
                    "configurations",
                    "users",
                    "jurisdictions",
                    "tes_condition_grouper_references",
                    "tes_reporting_spec_groupers",
                    "tes_condition_groupers",
                ]
                cursor.execute(
                    f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE;"
                )

                # insert test jurisdiction and user data
                # * this is required in order for the cache table triggers to work
                logging.info("➕ Inserting test data (Jurisdiction, User)...")
                # insert jurisdiction
                cursor.execute(
                    """
                    INSERT INTO jurisdictions (id, name, state_code)
                    VALUES (%(id)s, %(name)s, %(state_code)s) ON CONFLICT DO NOTHING;
                    """,
                    {
                        "id": "SDDH",
                        "name": "Senate District Health Department",
                        "state_code": "GC",
                    },
                )
                # insert user
                cursor.execute(
                    """
                    INSERT INTO users (email, jurisdiction_id, full_name)
                    VALUES (%(email)s, %(jurisdiction_id)s, %(full_name)s) ON CONFLICT DO NOTHING;
                    """,
                    {
                        "email": "rispi.lacendad@cocotown.clinic.gr.example.com",
                        "jurisdiction_id": "SDDH",
                        "full_name": "Dr. Rispi Lacendad",
                    },
                )

                # NOTE: this script uses a two-pass approach:
                # * PASS 1: insert all individual grouper records. we must insert all potential
                #   parents and children before we can create references between them
                logging.info("📦 PASS 1: Seeding all relevant grouper tables...")
                json_files = [
                    file
                    for file in DATA_DIR.glob("*.json")
                    if file.name != "manifest.json"
                ]
                for file_path in json_files:
                    file_category = file_path.stem.rsplit("_", 1)[0]
                    table_name = TABLE_MAP.get(file_category)

                    if not table_name:
                        logging.info(
                            f"⏩ Skipping file of ignored category: {file_path.name}"
                        )
                        continue

                    with open(file_path) as file:
                        json_data = json.load(file)

                    if "valuesets" not in json_data:
                        continue

                    for valueset in json_data["valuesets"]:
                        all_valuesets.append(valueset)
                        record = {
                            "canonical_url": valueset.get("url"),
                            "version": valueset.get("version"),
                            "display_name": valueset.get("name")
                            or valueset.get("title"),
                            "loinc_codes": extract_codes(valueset, "http://loinc.org"),
                            "snomed_codes": extract_codes(
                                valueset, "http://snomed.info/sct"
                            ),
                            "icd10_codes": extract_codes(
                                valueset, "http://hl7.org/fhir/sid/icd-10-cm"
                            ),
                            "rxnorm_codes": extract_codes(
                                valueset, "http://www.nlm.nih.gov/research/umls/rxnorm"
                            ),
                        }
                        if table_name == "tes_reporting_spec_groupers":
                            record["snomed_code"] = valueset.get("id", "").split("-")[
                                -1
                            ]
                            # NOTE: we build a set of all valid RS grouper keys here:
                            # * this is crucial for the second pass to prevent foreign key violations
                            rs_grouper_keys.add(
                                (record["canonical_url"], record["version"])
                            )

                        columns = ", ".join(record.keys())
                        placeholders = ", ".join(
                            [f"%({key})s" for key in record.keys()]
                        )
                        cursor.execute(
                            f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                            record,
                        )

                logging.info(
                    f"  🌱 Seeded {len(all_valuesets)} total relevant groupers."
                )

                # NOTE:
                # PASS 2: now that all groupers are in the DB, we create the links:
                # * we iterate through all parent groupers and create references **only** for
                #   children that we've confirmed are valid RS groupers
                logging.info(
                    "🔗 PASS 2: Seeding the relationships (references) table..."
                )
                references_to_insert = []
                for parent_valueset in all_valuesets:
                    if "compose" in parent_valueset and any(
                        "valueSet" in item
                        for item in parent_valueset["compose"].get("include", [])
                    ):
                        parent_url = parent_valueset.get("url")
                        parent_version = parent_valueset.get("version")
                        if not (parent_url and parent_version):
                            continue

                        for include_item in parent_valueset["compose"].get(
                            "include", []
                        ):
                            for child_url_with_version in include_item.get(
                                "valueSet", []
                            ):
                                parsed = parse_child_url(child_url_with_version)
                                # only add the reference if the child key exists in our set
                                if parsed and parsed in rs_grouper_keys:
                                    child_url, child_version = parsed
                                    references_to_insert.append(
                                        {
                                            "parent_grouper_url": parent_url,
                                            "parent_grouper_version": parent_version,
                                            "child_grouper_url": child_url,
                                            "child_grouper_version": child_version,
                                        }
                                    )

                if references_to_insert:
                    with cursor.copy(
                        "COPY tes_condition_grouper_references (parent_grouper_url, parent_grouper_version, child_grouper_url, child_grouper_version) FROM STDIN"
                    ) as copy:
                        for reference in references_to_insert:
                            # NOTE: we must convert the dictionary values to a tuple:
                            # * the psycopg `copy.write_row` function expects a subscriptable sequence
                            #   (like a list or tuple), and `dict.values()` is not subscriptable
                            copy.write_row(tuple(reference.values()))
                    logging.info(
                        f"  ✨ Inserted {len(references_to_insert)} valid references. Triggers will now fire."
                    )

                # insert jurisdiction-specific configuration
                logging.info("⚙️ Inserting jurisdiction-specific configuration...")
                cursor.execute(
                    """
                    INSERT INTO configurations (jurisdiction_id, child_grouper_url, child_grouper_version, loinc_codes, snomed_codes)
                    VALUES (%(jurisdiction_id)s, %(child_grouper_url)s, %(child_grouper_version)s, %(loinc_codes)s::jsonb, %(snomed_codes)s::jsonb)
                    ON CONFLICT DO NOTHING;
                    """,
                    {
                        "jurisdiction_id": "SDDH",
                        "child_grouper_url": "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/rs-grouper-840539006",
                        "child_grouper_version": "20250328",
                        "loinc_codes": '["CORUSCANT-LOINC-1"]',
                        "snomed_codes": '["11833005"]',
                    },
                )

                connection.commit()
                logging.info("\n🎉 SUCCESS: Database seeding and linking complete!")

            # PASS 3: Populate the refinement cache
            populate_refinement_cache(connection)
            logging.info(
                "\n🏁 SUCCESS: Database seeding and cache population complete!"
            )

    except (psycopg.Error, Exception) as error:
        logging.error(f"❌ Script error: {error}")
        raise


if __name__ == "__main__":
    seed_database()
