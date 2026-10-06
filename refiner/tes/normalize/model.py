"""
Types shared across the normalize step.

These are deliberately small and dependency-free: normalize runs in dev and CI
where `fhir.resources` is available for validation, but the row shapes it emits
have to survive a round trip through gzipped CSV and a Postgres `COPY`, so they
stay flat.
"""

from dataclasses import dataclass
from typing import Any

type ValueSetDict = dict[str, Any]
type SystemOid = str
type CanonicalUrl = str
type Version = str

# ValueSet identity is always (url, version) -- never url alone. Two distinct
# groupers can share a title, and the same url is republished every release.
type ValueSetKey = tuple[CanonicalUrl, Version]


# The systems whose codes normalize keeps, as (url, oid) -- what TES publishes
# mapped to what the database stores. Deliberately not the same table as
# `ops/seeding/systems.py`: that one defines the application's vocabulary and
# carries display names and an `Other` bucket for custom codes, which TES has no
# concept of. This one exists only to decide which published codes survive, so it
# holds nothing else. `tes/verify/database.py` asserts every OID here has a row
# in `systems`, which is what keeps the two from drifting apart.
CODE_SYSTEMS: dict[str, dict[str, str]] = {
    "snomed": {
        "oid": "2.16.840.1.113883.6.96",
        "url": "http://snomed.info/sct",
    },
    "loinc": {
        "oid": "2.16.840.1.113883.6.1",
        "url": "http://loinc.org",
    },
    "icd10": {
        "oid": "2.16.840.1.113883.6.90",
        "url": "http://hl7.org/fhir/sid/icd-10-cm",
    },
    "rxnorm": {
        "oid": "2.16.840.1.113883.6.88",
        "url": "http://www.nlm.nih.gov/research/umls/rxnorm",
    },
    "cvx": {
        "oid": "2.16.840.1.113883.12.292",
        "url": "http://hl7.org/fhir/sid/cvx",
    },
}

SNOMED_OID = CODE_SYSTEMS["snomed"]["oid"]

SYSTEM_URL_TO_OID: dict[str, SystemOid] = {
    system["url"]: system["oid"] for system in CODE_SYSTEMS.values()
}

# systems TES publishes that the refiner deliberately does not store: occupational
# and industry coding, HL7 v3 administrative vocabularies, billing codes, retired
# revisions, and local/naming-system variants. The verify step asserts the drop set
# is exactly this -- a new entry means TES started publishing something, and
# somebody has to decide whether it belongs in CODE_SYSTEMS rather than find out
# later that codes went missing.
#
# `http://hl7.org/fhir/sid/icd-10` is plain ICD-10, not the ICD-10-CM clinical
# modification the app supports; it appears only in 2.0.0 and 3.0.0 and TES has
# since stopped publishing it.
KNOWN_UNSUPPORTED_SYSTEMS: frozenset[str] = frozenset(
    {
        "http://hl7.org/fhir/sid/icd-9-cm",
        "http://hl7.org/fhir/sid/icd-10",
        "http://hl7.org/fhir/sid/ndc",
        "http://terminology.hl7.org/CodeSystem/PHIndustryCDCCensus2010",
        "http://terminology.hl7.org/CodeSystem/PHOccupationCDCCensus2010",
        "http://terminology.hl7.org/CodeSystem/PHOccupationalDataForHealthODH",
        "http://terminology.hl7.org/CodeSystem/nddf",
        "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "http://terminology.hl7.org/CodeSystem/v3-ActStatus",
        "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
        "http://terminology.hl7.org/NamingSystem/CDCLocal",
        "http://terminology.hl7.org/NamingSystem/ICD-9CM-diagnosiscodes",
        "http://www.ama-assn.org/go/cpt",
        "https://phinvads.cdc.gov/baseStu3/CodeSystem/2.16.840.1.114222.4.5.274",
        "urn:oid:2.16.840.1.113883.12.112",
        "urn:oid:2.16.840.1.113883.3.1937.98.5.8",
    }
)

KNOWN_CATEGORIES: frozenset[str] = frozenset(
    {
        "clinical_lab_result",
        "diagnosis",
        "immunization",
        "medication",
        "reporting_specification_grouper",
        "specimen_source",
        "symptom",
    }
)


@dataclass(frozen=True, slots=True)
class FhirCodeInfo:
    """
    A single coded concept as published by a leaf grouper.

    `display` is optional in the source for both artifact shapes, so it is
    nullable here rather than coerced to an empty string -- the distinction
    between "no display published" and "published as empty" is preserved until
    the row is written.
    """

    system_url: str
    code: str
    display: str | None
    source_url: str
    source_name: str
