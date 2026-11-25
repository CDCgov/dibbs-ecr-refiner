from typing import Final

from dibbs_ecr.vocab import (
    CODE_SYSTEM_DISPLAY_NAMES,
    CPT4_OID,
    CVX_OID,
    ICD10_OID,
    LOINC_OID,
    NCI_OID,
    NDC_OID,
    OBSERVATION_INTERPRETATION_DISPLAY,
    OID_TO_SYSTEM_KEY_MAP,
    OTHER_OID,
    RXNORM_OID,
    SNOMED_OID,
)

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

__all__ = [
    "CODE_SYSTEM_DISPLAY_NAMES",
    "CPT4_OID",
    "CVX_OID",
    "ICD10_OID",
    "LOINC_OID",
    "NCI_OID",
    "NDC_OID",
    "OBSERVATION_INTERPRETATION_DISPLAY",
    "OID_TO_SYSTEM_KEY_MAP",
    "OTHER_OID",
    "RXNORM_OID",
    "SNOMED_OID",
]
