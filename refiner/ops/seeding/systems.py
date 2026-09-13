"""
The code systems the refiner recognizes, and the upsert that seeds them.

This is app vocabulary, not TES content. TES publishes codes in many systems the
refiner does not match against; these are the ones it does, plus an `Other`
bucket that only ever holds user-supplied custom codes -- TES has no concept of
it.

`tes/normalize` keeps its own url-to-OID map for deciding which published codes
to keep. The overlap is the five real systems below, and it is deliberate rather
than shared: normalize filters TES content, while this defines what the
application can store. The verify step asserts every OID in the processed data
exists here, so the two cannot drift apart silently.
"""

from config import logger
from psycopg import Cursor

CODE_SYSTEMS: dict[str, dict[str, str]] = {
    "snomed": {
        "oid": "2.16.840.1.113883.6.96",
        "display_name": "SNOMED",
        "url": "http://snomed.info/sct",
    },
    "loinc": {
        "oid": "2.16.840.1.113883.6.1",
        "display_name": "LOINC",
        "url": "http://loinc.org",
    },
    "icd10": {
        "oid": "2.16.840.1.113883.6.90",
        "display_name": "ICD-10",
        "url": "http://hl7.org/fhir/sid/icd-10-cm",
    },
    "rxnorm": {
        "oid": "2.16.840.1.113883.6.88",
        "display_name": "RxNorm",
        "url": "http://www.nlm.nih.gov/research/umls/rxnorm",
    },
    "cvx": {
        "oid": "2.16.840.1.113883.12.292",
        "display_name": "CVX",
        "url": "http://hl7.org/fhir/sid/cvx",
    },
    "other": {"oid": "Other", "display_name": "Other", "url": ""},
}


def upsert_systems(cursor: Cursor) -> None:
    """
    Seed or update the `systems` table.

    Matching on either key or OID keeps the row stable if one of the two is ever
    corrected, and only touching changed columns keeps `updated_at` honest.

    Args:
        cursor: A database cursor.
    """

    logger.info("⏳ Upserting system data...")

    # conflict handling here is matched by a trigger that maintains updated_at;
    # changing which columns this touches needs a migration to match
    statement = """
        MERGE INTO systems s
        USING (VALUES (%(key)s, %(display_name)s, %(oid)s)) AS v(key, display_name, oid)
        ON s.key = v.key OR s.oid = v.oid
        WHEN MATCHED THEN
            UPDATE SET display_name = v.display_name, oid = v.oid
        WHEN NOT MATCHED THEN
            INSERT (key, display_name, oid) VALUES (v.key, v.display_name, v.oid)
    """

    cursor.executemany(
        statement,
        [
            {"key": key, "oid": system["oid"], "display_name": system["display_name"]}
            for key, system in CODE_SYSTEMS.items()
        ],
    )
    logger.info(f"✨ {len(CODE_SYSTEMS)} code systems seeded.")
