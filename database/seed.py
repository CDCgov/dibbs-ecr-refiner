import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# =============================================================================
#  SEED DATA CONSTANTS--based on ValueSet resources from the TES
# =============================================================================
# this data is a combination of fictional star wars data and manually extracted
# real world data from the real TES FHIR ValueSet JSON to simulate a real-world
# scenarios for testing "Trigger 1" and "Trigger 2" in our new data model
# you can find both in:
# data/
# * condition-grouper.json
# * rs-groupers.json

# a fictional jurisdiction inspired by star wars
JURISDICTION = {
    "id": "SDDH-GC-500",
    "name": "Senate District Health Department",
    "state_code": "GC",
}

# user found from archived web site that wrote from an in-universe pov:
# https://web.archive.org/web/20130728110707/http://www.holonetnews.com/49/life/13328_4.html
USER = {
    "email": "rispi.lacendad@cocotown.clinic.gr.example.com",
    "jurisdiction_id": JURISDICTION["id"],
    "full_name": "Dr. Rispi Lacendad",
}

# this represents the parent "condition grouper" for COVID-19.
# the codes are empty because the trigger is responsible for populating them.
COVID_CONDITION_GROUPER = {
    "url": "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64",
    "version": "2.0.0",
    "display_name": "COVID-19",
    # these start empty; the trigger will fill them
    "loinc_codes": "[]",
    "snomed_codes": "[]",
    "icd10_codes": "[]",
    "rxnorm_codes": "[]",
}

# these represent the two child "reporting specification groupers" that the
# parent condition grouper points to. These contain the actual codes.
COVID_RS_GROUPERS = [
    {
        "url": "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/rs-grouper-840539006",
        "version": "20250328",
        "display_name": "COVID-19",
        "snomed_code": "840539006",
        "loinc_codes": '["615-5", "100156-9", "100157-7", "101289-7", "101928-0"]',
        "snomed_codes": '["119419001", "23141003", "63993003", "10151000132103"]',
        "icd10_codes": '["J15.9", "J16.8", "J17", "F51.1", "F51.11"]',
        "rxnorm_codes": "[]",
    },
    {
        "url": "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/rs-grouper-186747009",
        "version": "20250328",
        "display_name": "COVID-19",
        "snomed_code": "186747009",
        "loinc_codes": '["101289-7", "14458-4", "14459-2", "14460-0", "17975-4"]',
        "snomed_codes": '["248444008", "11833005", "1187591006", "119731000146105"]',
        "icd10_codes": '["R06.02", "R06.03", "R06.09", "R07.0", "R43.0"]',
        "rxnorm_codes": "[]",
    },
]

# a user-defined configuration. This links a jurisdiction to a specific rs grouper
# and adds jurisdiction-specific codes. this is the event that fires "Trigger 2".
CONFIGURATION = {
    "jurisdiction_id": JURISDICTION["id"],
    "child_grouper_url": COVID_RS_GROUPERS[0]["url"],
    "child_grouper_version": COVID_RS_GROUPERS[0]["version"],
    # simulate a local code for this jurisdiction
    "loinc_codes": '["CORUSCANT-LOINC-1"]',
    # one duplicate code to test de-duplication
    "snomed_codes": '["11833005"]',
}


def seed_database() -> None:
    """
    Function to manage connecting, seeding, and wiping the database.

    Connects to the database, wipes all data, and runs a full end-to-end
    test of the trigger-based data pipeline.
    """

    print("🌱 Starting full database seeding and trigger test...")
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
    db_connection_url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@localhost:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    print(f"Connecting to {os.getenv('POSTGRES_DB')}...")

    try:
        with psycopg.connect(db_connection_url) as conn:
            with conn.cursor() as cur:
                print("🗑️  Clearing all tables...")
                tables = [
                    "refinement_cache",
                    "configurations",
                    "users",
                    "jurisdictions",
                    "tes_condition_grouper_references",
                    "tes_reporting_spec_groupers",
                    "tes_condition_groupers",
                ]
                cur.execute(f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE;")

                print("Seeding jurisdictions and users...")
                cur.execute(
                    "INSERT INTO jurisdictions (id, name, state_code) VALUES (%(id)s, %(name)s, %(state_code)s);",
                    JURISDICTION,
                )
                cur.execute(
                    "INSERT INTO users (email, jurisdiction_id, full_name) VALUES (%(email)s, %(jurisdiction_id)s, %(full_name)s);",
                    USER,
                )

                print("Seeding TES grouper data...")
                cur.execute(
                    "INSERT INTO tes_condition_groupers (canonical_url, version, display_name, loinc_codes, snomed_codes, icd10_codes, rxnorm_codes) VALUES (%(url)s, %(version)s, %(display_name)s, %(loinc_codes)s::jsonb, %(snomed_codes)s::jsonb, %(icd10_codes)s::jsonb, %(rxnorm_codes)s::jsonb);",
                    COVID_CONDITION_GROUPER,
                )
                for child in COVID_RS_GROUPERS:
                    cur.execute(
                        "INSERT INTO tes_reporting_spec_groupers (canonical_url, version, display_name, snomed_code, loinc_codes, snomed_codes, icd10_codes, rxnorm_codes) VALUES (%(url)s, %(version)s, %(display_name)s, %(snomed_code)s, %(loinc_codes)s::jsonb, %(snomed_codes)s::jsonb, %(icd10_codes)s::jsonb, %(rxnorm_codes)s::jsonb);",
                        child,
                    )

                print("Linking children to parent... (Firing Trigger 1)")
                refs = [
                    (
                        COVID_CONDITION_GROUPER["url"],
                        COVID_CONDITION_GROUPER["version"],
                        child["url"],
                        child["version"],
                    )
                    for child in COVID_RS_GROUPERS
                ]
                cur.executemany(
                    "INSERT INTO tes_condition_grouper_references (parent_grouper_url, parent_grouper_version, child_grouper_url, child_grouper_version) VALUES (%s, %s, %s, %s);",
                    refs,
                )

                print("Inserting user configuration... (Firing Trigger 2)")
                cur.execute(
                    "INSERT INTO configurations (jurisdiction_id, child_grouper_url, child_grouper_version, loinc_codes, snomed_codes) VALUES (%(jurisdiction_id)s, %(child_grouper_url)s, %(child_grouper_version)s, %(loinc_codes)s::jsonb, %(snomed_codes)s::jsonb);",
                    CONFIGURATION,
                )

                print("\n✅ Initial triggers fired! Verifying the refinement_cache...")
                cur.execute(
                    "SELECT aggregated_codes FROM refinement_cache WHERE snomed_code = %s AND jurisdiction_id = %s;",
                    (COVID_RS_GROUPERS[0]["snomed_code"], JURISDICTION["id"]),
                )
                result = cur.fetchone()
                if not result:
                    raise Exception("Cache verification failed: No record found!")

                # --- VERIFICATION LOGIC ---
                # get the codes that Trigger 1 aggregated into the parent grouper
                cur.execute(
                    "SELECT loinc_codes, snomed_codes, icd10_codes, rxnorm_codes FROM tes_condition_groupers WHERE canonical_url = %s",
                    (COVID_CONDITION_GROUPER["url"],),
                )
                parent_codes_result = cur.fetchone()
                base_codes = (
                    set(parent_codes_result[0])
                    | set(parent_codes_result[1])
                    | set(parent_codes_result[2])
                    | set(parent_codes_result[3])
                )

                # get the codes from the user configuration
                addition_codes = set(
                    json.loads(CONFIGURATION.get("loinc_codes", "[]"))
                ) | set(json.loads(CONFIGURATION.get("snomed_codes", "[]")))

                # the final expected set is the union of the two
                expected_all_codes = base_codes.union(addition_codes)

                if set(result[0]) == expected_all_codes:
                    print("🎉 Success! Initial cache was populated correctly.")
                else:
                    raise Exception(
                        f"Initial cache verification failed! Expected {len(expected_all_codes)} codes, found {len(result[0])}."
                    )

                print(
                    "\n🔥 Simulating an update to base TES data... (Firing Trigger 1 -> Trigger 2)"
                )
                new_snomed_code = "1240411000000107"
                target_rs_grouper = COVID_RS_GROUPERS[1]
                cur.execute(
                    "SELECT snomed_codes FROM tes_reporting_spec_groupers WHERE canonical_url = %s and version = %s",
                    (target_rs_grouper["url"], target_rs_grouper["version"]),
                )
                current_snomeds = cur.fetchone()[0]
                current_snomeds.append(new_snomed_code)
                cur.execute(
                    "UPDATE tes_reporting_spec_groupers SET snomed_codes = %s WHERE canonical_url = %s and version = %s;",
                    (
                        json.dumps(current_snomeds),
                        target_rs_grouper["url"],
                        target_rs_grouper["version"],
                    ),
                )
                expected_all_codes.add(new_snomed_code)

                print("✅ Update applied! Verifying the refinement_cache again...")
                cur.execute(
                    "SELECT aggregated_codes FROM refinement_cache WHERE snomed_code = %s AND jurisdiction_id = %s;",
                    (COVID_RS_GROUPERS[0]["snomed_code"], JURISDICTION["id"]),
                )
                final_result = cur.fetchone()

                if set(final_result[0]) == expected_all_codes:
                    print(
                        "🎉 Success! The cache was correctly updated after a change to the base data"
                    )
                else:
                    raise Exception(
                        f"Final cache verification failed! Expected {len(expected_all_codes)} codes, found {len(final_result[0])}."
                    )

                conn.commit()

    except (psycopg.Error, Exception) as e:
        print(f"❌ Script error: {e}")


if __name__ == "__main__":
    seed_database()
