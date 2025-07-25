import json

import pytest

# these constants will simulate what typical data might look like in the db
# the goal is to add data to a table and check the triggers are working correctly
JURISDICTION = {
    "id": "SDDH",
    "name": "Senate District Health Department",
    "state_code": "GC",
}
USER = {
    "email": "rispi.lacendad@cocotown.clinic.gr.example.com",
    "jurisdiction_id": JURISDICTION["id"],
    "full_name": "Dr. Rispi Lacendad",
}
COVID_CONDITION_GROUPER = {
    "url": "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64",
    "version": "2.0.0",
    "display_name": "COVID-19",
    "loinc_codes": "[]",
    "snomed_codes": "[]",
    "icd10_codes": "[]",
    "rxnorm_codes": "[]",
}
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
CONFIGURATION = {
    "jurisdiction_id": JURISDICTION["id"],
    "child_grouper_url": COVID_RS_GROUPERS[0]["url"],
    "child_grouper_version": COVID_RS_GROUPERS[0]["version"],
    "loinc_codes": '["CORUSCANT-LOINC-1"]',
    "snomed_codes": '["11833005"]',
}


@pytest.mark.integration
def test_triggers_end_to_end(db_cursor):
    """
    Runs a full end-to-end test of the trigger-based data pipeline.

    The `db_cursor` fixture provides a clean, ready-to-use database cursor.
    """

    cursor = db_cursor

    # 1: seed initial data
    cursor.execute(
        "INSERT INTO jurisdictions (id, name, state_code) VALUES (%(id)s, %(name)s, %(state_code)s);",
        JURISDICTION,
    )
    cursor.execute(
        "INSERT INTO users (email, jurisdiction_id, full_name) VALUES (%(email)s, %(jurisdiction_id)s, %(full_name)s);",
        USER,
    )
    cursor.execute(
        "INSERT INTO tes_condition_groupers (canonical_url, version, display_name, loinc_codes, snomed_codes, icd10_codes, rxnorm_codes) VALUES (%(url)s, %(version)s, %(display_name)s, %(loinc_codes)s::jsonb, %(snomed_codes)s::jsonb, %(icd10_codes)s::jsonb, %(rxnorm_codes)s::jsonb);",
        COVID_CONDITION_GROUPER,
    )
    for child in COVID_RS_GROUPERS:
        cursor.execute(
            "INSERT INTO tes_reporting_spec_groupers (canonical_url, version, display_name, snomed_code, loinc_codes, snomed_codes, icd10_codes, rxnorm_codes) VALUES (%(url)s, %(version)s, %(display_name)s, %(snomed_code)s, %(loinc_codes)s::jsonb, %(snomed_codes)s::jsonb, %(icd10_codes)s::jsonb, %(rxnorm_codes)s::jsonb);",
            child,
        )

    # 2: fire Trigger 1
    references = [
        (
            COVID_CONDITION_GROUPER["url"],
            COVID_CONDITION_GROUPER["version"],
            child["url"],
            child["version"],
        )
        for child in COVID_RS_GROUPERS
    ]
    cursor.executemany(
        "INSERT INTO tes_condition_grouper_references (parent_grouper_url, parent_grouper_version, child_grouper_url, child_grouper_version) VALUES (%s, %s, %s, %s);",
        references,
    )

    # 3: fire Trigger 2
    cursor.execute(
        "INSERT INTO configurations (jurisdiction_id, child_grouper_url, child_grouper_version, loinc_codes, snomed_codes) VALUES (%(jurisdiction_id)s, %(child_grouper_url)s, %(child_grouper_version)s, %(loinc_codes)s::jsonb, %(snomed_codes)s::jsonb);",
        CONFIGURATION,
    )

    # 4: verify initial cache population
    cursor.execute(
        "SELECT aggregated_codes FROM refinement_cache WHERE snomed_code = %s AND jurisdiction_id = %s;",
        (COVID_RS_GROUPERS[0]["snomed_code"], JURISDICTION["id"]),
    )
    result = cursor.fetchone()
    assert result is not None, "Cache verification failed: No record found!"

    cursor.execute(
        "SELECT loinc_codes, snomed_codes, icd10_codes, rxnorm_codes FROM tes_condition_groupers WHERE canonical_url = %s",
        (COVID_CONDITION_GROUPER["url"],),
    )
    parent_codes_result = cursor.fetchone()
    base_codes = set().union(*parent_codes_result)
    addition_codes = set(json.loads(CONFIGURATION["loinc_codes"])) | set(
        json.loads(CONFIGURATION["snomed_codes"])
    )
    expected_all_codes = base_codes.union(addition_codes)

    assert set(result[0]) == expected_all_codes, (
        f"Initial cache verification failed! Expected {len(expected_all_codes)} codes, found {len(result[0])}."
    )

    # 5: simulate an update to base data (fires Trigger 1 -> Trigger 2)
    new_snomed_code = "1240411000000107"
    target_rs_grouper = COVID_RS_GROUPERS[1]
    cursor.execute(
        "SELECT snomed_codes FROM tes_reporting_spec_groupers WHERE canonical_url = %s and version = %s",
        (target_rs_grouper["url"], target_rs_grouper["version"]),
    )
    current_snomeds = cursor.fetchone()[0]
    current_snomeds.append(new_snomed_code)
    cursor.execute(
        "UPDATE tes_reporting_spec_groupers SET snomed_codes = %s WHERE canonical_url = %s and version = %s;",
        (
            json.dumps(current_snomeds),
            target_rs_grouper["url"],
            target_rs_grouper["version"],
        ),
    )
    expected_all_codes.add(new_snomed_code)

    # 6: verify final cache state
    cursor.execute(
        "SELECT aggregated_codes FROM refinement_cache WHERE snomed_code = %s AND jurisdiction_id = %s;",
        (COVID_RS_GROUPERS[0]["snomed_code"], JURISDICTION["id"]),
    )
    final_result = cursor.fetchone()
    assert final_result is not None, (
        "Final cache verification failed: No record found after update!"
    )
    assert set(final_result[0]) == expected_all_codes, (
        f"Final cache verification failed! Expected {len(expected_all_codes)} codes, found {len(final_result[0])}."
    )
