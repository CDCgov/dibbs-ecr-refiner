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

CPT4_OID: Final[str] = "2.16.840.1.113883.6.12"
CVX_OID: Final[str] = "2.16.840.1.113883.12.292"
ICD10_OID: Final[str] = "2.16.840.1.113883.6.90"
LOINC_OID: Final[str] = "2.16.840.1.113883.6.1"
NCI_OID: Final[str] = "2.16.840.1.113883.3.26.1.1"
NDC_OID: Final[str] = "2.16.840.1.113883.6.69"
RXNORM_OID: Final[str] = "2.16.840.1.113883.6.88"
SNOMED_OID: Final[str] = "2.16.840.1.113883.6.96"
OTHER_OID: Final[str] = "Other"

# human-readable names resolved from the codeSystem OID, never the source
# codeSystemName attribute, which is unreliable and inconsistently populated
# (missing, or "SNOMED-CT" vs "SNOMED CT"). used both for PHA-facing narrative
# display and for the internal entry-match provenance comments--one OID->name
# map, using the technically correct names (e.g. "SNOMED CT", "ICD-10-CM")
CODE_SYSTEM_DISPLAY_NAMES: Final[dict[str, str]] = {
    LOINC_OID: "LOINC",
    SNOMED_OID: "SNOMED CT",
    RXNORM_OID: "RxNorm",
    CVX_OID: "CVX",
    NDC_OID: "NDC",
    NCI_OID: "NCI Thesaurus",
    ICD10_OID: "ICD-10-CM",
    CPT4_OID: "CPT-4",
}

# HL7 ObservationInterpretation (codeSystem 2.16.840.1.113883.5.83): the
# result-flag vocabulary a lab stamps on an observation (and on a reference
# range). Senders often carry only the bare @code ("A", "H", "L") with no
# @displayName, which reads as a cryptic letter to a PHA. This maps the clinical
# subset that actually shows up in eICR lab results to its canonical display;
# unknown codes fall back to the raw @code (see render_interpretation).
OBSERVATION_INTERPRETATION_DISPLAY: Final[dict[str, str]] = {
    "N": "Normal",
    "A": "Abnormal",
    "AA": "Critically abnormal",
    "H": "High",
    "HH": "Critically high",
    "L": "Low",
    "LL": "Critically low",
    "HU": "Significantly high",
    "LU": "Significantly low",
    "I": "Intermediate",
    "R": "Resistant",
    "S": "Susceptible",
    "POS": "Positive",
    "NEG": "Negative",
    "IND": "Indeterminate",
    "E": "Equivocal",
}

OID_TO_SYSTEM_KEY_MAP: Final[dict[str, str]] = {
    LOINC_OID: "loinc",
    SNOMED_OID: "snomed",
    RXNORM_OID: "rxnorm",
    ICD10_OID: "icd10",
    CVX_OID: "cvx",
    OTHER_OID: "other",
}
