from typing import Final

from ..model import EicrVersion

# NOTE:
# VERSION MAPPING
# =============================================================================
# map of templateId extensions to their semantic version strings.
# the extensions are dated according to the eICR Implementation Guide
# release schedule and identify which version of the IG a document
# conforms to

EICR_VERSION_MAP: Final[dict[str, EicrVersion]] = {
    "2016-12-01": "1.1",
    "2021-01-01": "3.1",
    "2022-05-01": "3.1.1",
}


# NOTE:
# CODE SYSTEM OIDS
# =============================================================================
# these OIDs are stable, HL7-registered identifiers that have not changed
# across any version of C-CDA or eICR. inlining them here keeps every
# entry match rule traceable to a named code system without having to
# memorize OIDs

CVX_OID: Final[str] = "2.16.840.1.113883.12.292"
ICD10_OID: Final[str] = "2.16.840.1.113883.6.90"
LOINC_OID: Final[str] = "2.16.840.1.113883.6.1"
RXNORM_OID: Final[str] = "2.16.840.1.113883.6.88"
SNOMED_OID: Final[str] = "2.16.840.1.113883.6.96"


CODE_SYSTEM_LABELS: Final[dict[str, str]] = {
    LOINC_OID: "LOINC",
    SNOMED_OID: "SNOMED",
    RXNORM_OID: "RxNorm",
    ICD10_OID: "ICD-10",
    CVX_OID: "CVX",
}

OID_TO_SYSTEM_KEY_MAP: Final[dict[str, str]] = {
    LOINC_OID: "loinc",
    SNOMED_OID: "snomed",
    RXNORM_OID: "rxnorm",
    ICD10_OID: "icd10",
    CVX_OID: "cvx",
}
