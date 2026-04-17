from typing import Final

from ..model import EntryMatchRule
from .constants import CVX_OID, ICD10_OID, LOINC_OID, RXNORM_OID, SNOMED_OID

# NOTE:
# ADMISSION DIAGNOSIS (46241-6)
# =============================================================================
# IG template: Hospital Admission Diagnosis (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ'] (CONF:1198-7674, CONF:1198-7675)
# prune level: act/entryRelationship[@typeCode='SUBJ'] (individual diagnoses)
#   typeCode='SUBJ' is a SHALL constraint (CONF:1198-7675) -> safe to filter on

_ADMISSION_DIAGNOSIS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # rule 1 — IG-conformant: SNOMED on value, ICD-10-CM on translation
    # primary code: observation/value SHALL be SNOMED (CONF:1198-9058)
    # translation: observation/value/translation MAY be ICD-10-CM (CONF:1198-16750)
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value"
        ),
        code_system_oid=SNOMED_OID,
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value/hl7:translation"
        ),
        translation_code_system_oid=ICD10_OID,
        prune_container_xpath="hl7:act/hl7:entryRelationship[@typeCode='SUBJ']",
    ),
    # rule 2 — reversed: ICD-10-CM on value, SNOMED on translation
    # not IG-conformant but observed in real data; structural precedence
    # ensures this only fires when rule 1 finds no SNOMED on value
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value"
        ),
        code_system_oid=ICD10_OID,
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value/hl7:translation"
        ),
        translation_code_system_oid=SNOMED_OID,
        prune_container_xpath="hl7:act/hl7:entryRelationship[@typeCode='SUBJ']",
    ),
]


# NOTE:
# ADMISSION MEDICATIONS (42346-7)
# =============================================================================
# IG template: Admission Medication (V2) uses Medication Information (V2)
# primary code: manufacturedMaterial/code SHALL be RxNorm (CONF:1098-7412)
# translation:  manufacturedMaterial/code/translation MAY have NDC (CONF:1098-31884)

_ADMISSION_MEDICATIONS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=".//hl7:manufacturedMaterial/hl7:code",
        code_system_oid=RXNORM_OID,
        translation_xpath=".//hl7:manufacturedMaterial/hl7:code/hl7:translation",
    ),
]


# NOTE:
# DISCHARGE DIAGNOSIS (11535-2)
# =============================================================================
# IG template: Hospital Discharge Diagnosis (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ']
#   (CONF:1198-7666, CONF:1198-7667, CONF:1198-15536)
# prune level: act/entryRelationship[@typeCode='SUBJ'] (individual diagnoses)
#   typeCode='SUBJ' is a SHALL constraint (CONF:1198-7667) — safe to filter on

_DISCHARGE_DIAGNOSIS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # rule 1 — IG-conformant: SNOMED on value, ICD-10-CM on translation
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value"
        ),
        code_system_oid=SNOMED_OID,
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value/hl7:translation"
        ),
        translation_code_system_oid=ICD10_OID,
        prune_container_xpath="hl7:act/hl7:entryRelationship[@typeCode='SUBJ']",
    ),
    # rule 2 — reversed: ICD-10-CM on value, SNOMED on translation
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value"
        ),
        code_system_oid=ICD10_OID,
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value/hl7:translation"
        ),
        translation_code_system_oid=SNOMED_OID,
        prune_container_xpath="hl7:act/hl7:entryRelationship[@typeCode='SUBJ']",
    ),
]


# NOTE:
# ENCOUNTERS (46240-8)
# =============================================================================
# IG template: Encounter Diagnosis (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ'] (CONF:1198-14892, CONF:1198-14898)
#
# prune level: encounter/entryRelationship scoped by Encounter Diagnosis templateId
#   CONF:1198-15492 does NOT constrain @typeCode on the entryRelationship
#   that wraps Encounter Diagnosis (V3)
#   * testing has shown a mix of SUBJ, RSON, and COMP entries
#   scoping by the child act's templateId (CONF:1198-14896, SHALL) is
#   reliable regardless of typeCode

_ENCOUNTERS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # rule 1 — IG-conformant: SNOMED on value, ICD-10-CM on translation
    # primary code: observation/value SHALL be SNOMED (CONF:1198-9058)
    # translation: observation/value/translation MAY be ICD-10-CM (CONF:1198-16750)
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value"
        ),
        code_system_oid=SNOMED_OID,
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value/hl7:translation"
        ),
        translation_code_system_oid=ICD10_OID,
        prune_container_xpath=(
            "hl7:encounter/hl7:entryRelationship"
            "[hl7:act/hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.80']]"
        ),
    ),
    # rule 2 — reversed: ICD-10-CM on value, SNOMED on translation
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value"
        ),
        code_system_oid=ICD10_OID,
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value/hl7:translation"
        ),
        translation_code_system_oid=SNOMED_OID,
        prune_container_xpath=(
            "hl7:encounter/hl7:entryRelationship"
            "[hl7:act/hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.80']]"
        ),
    ),
]


# NOTE:
# IMMUNIZATIONS (11369-6)
# =============================================================================
# IG template: Immunization Activity (V3) uses Immunization Medication Information (V2)
# primary code: manufacturedMaterial/code SHALL be CVX (CONF:1098-9007)
# translation:  manufacturedMaterial/code/translation MAY be RxNorm (CONF:1098-31543)

_IMMUNIZATIONS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=".//hl7:manufacturedMaterial/hl7:code",
        code_system_oid=CVX_OID,
        translation_xpath=".//hl7:manufacturedMaterial/hl7:code/hl7:translation",
        translation_code_system_oid=RXNORM_OID,
    ),
]


# NOTE:
# MEDICATIONS ADMINISTERED (29549-3)
# =============================================================================
# IG template: Medication Activity (V2) uses Medication Information (V2)
# primary code: manufacturedMaterial/code SHALL be RxNorm (CONF:1098-7412)
# translation:  manufacturedMaterial/code/translation MAY have NDC (CONF:1098-31884)

_MEDICATIONS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=".//hl7:manufacturedMaterial/hl7:code",
        code_system_oid=RXNORM_OID,
        translation_xpath=".//hl7:manufacturedMaterial/hl7:code/hl7:translation",
    ),
]


# NOTE:
# MEDICATIONS — HOME (10160-0)
# =============================================================================
# IG template: Medication Activity (V2) uses Medication Information (V2)
# primary code: manufacturedMaterial/code SHALL be RxNorm (CONF:1098-7412)
# translation:  manufacturedMaterial/code/translation MAY have NDC (CONF:1098-31884)

_MEDICATIONS_HOME_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=".//hl7:manufacturedMaterial/hl7:code",
        code_system_oid=RXNORM_OID,
        translation_xpath=".//hl7:manufacturedMaterial/hl7:code/hl7:translation",
    ),
]


# NOTE:
# PAST MEDICAL HISTORY (11348-0)
# =============================================================================
# IG template: Problem Concern Act (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ']
# prune level: act/entryRelationship[@typeCode='SUBJ'] (individual problems)
#   typeCode='SUBJ' is a SHALL constraint — safe to filter on

_PAST_MEDICAL_HISTORY_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # rule 1 — IG-conformant: SNOMED on value, ICD-10-CM on translation
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value"
        ),
        code_system_oid=SNOMED_OID,
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value/hl7:translation"
        ),
        translation_code_system_oid=ICD10_OID,
        prune_container_xpath="hl7:act/hl7:entryRelationship[@typeCode='SUBJ']",
    ),
    # rule 2 — reversed: ICD-10-CM on value, SNOMED on translation
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value"
        ),
        code_system_oid=ICD10_OID,
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value/hl7:translation"
        ),
        translation_code_system_oid=SNOMED_OID,
        prune_container_xpath="hl7:act/hl7:entryRelationship[@typeCode='SUBJ']",
    ),
]


# NOTE:
# PLAN OF TREATMENT (18776-5)
# =============================================================================
# Heterogeneous entry types — multiple rules with structural precedence.
# Each rule's xpath is scoped to a specific C-CDA template so that
# structural precedence correctly separates medication entries from
# immunization entries (both share manufacturedMaterial/code but use
# different templateIds).
#
# rule 1 — Planned Observation / Lab Test Order
#   IG template: Planned Observation (V2) (2.16.840.1.113883.10.20.22.4.44)
#   primary code: observation/code SHOULD be LOINC (CONF:1098-31030)
#   eICR trigger: SHALL be from RCTC lab test orders (CONF:3284-336)
#
# rule 2 — Medication Activity
#   IG template: Medication Activity (V2) (2.16.840.1.113883.10.20.22.4.16)
#   note: Planned Medication Activity (4.42) conforms to Medication Activity
#     (4.16), so targeting 4.16 catches both planned and non-planned
#     medication entries
#   inner template: Medication Information (V2) (2.16.840.1.113883.10.20.22.4.23)
#   primary code: manufacturedMaterial/code SHALL be RxNorm (CONF:1098-7412)
#   translation:  manufacturedMaterial/code/translation MAY have NDC (CONF:1098-31884)
#
# rule 3 — Immunization Activity
#   IG template: Immunization Activity (V3) (2.16.840.1.113883.10.20.22.4.52)
#   note: Planned Immunization Activity (4.120) conforms to Immunization
#     Activity (4.52), so targeting 4.52 catches both planned and
#     non-planned immunization entries
#   inner template: Immunization Medication Information (V2)
#     (2.16.840.1.113883.10.20.22.4.54)
#   primary code: manufacturedMaterial/code SHALL be CVX (CONF:1098-9007)
#   translation:  manufacturedMaterial/code/translation MAY be RxNorm (CONF:1098-31543)
#
# rule 4 — Indication (fallback)
#   IG template: Indication (V2) (2.16.840.1.113883.10.20.22.4.19)
#   primary code: observation/value MAY be SNOMED
#   note: catches entries indicated for a matching condition
#     (e.g., Remdesivir for COVID-19)
#
# structural precedence: rule 1 claims observation entries, rules 2-3 claim
# medication/immunization entries respectively (template-scoped so they
# don't interfere), rule 4 catches unclaimed entries only

_PLAN_OF_TREATMENT_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # rule 1 — planned observation / lab test order code
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.44']]"
            "/hl7:code"
        ),
        code_system_oid=LOINC_OID,
    ),
    # rule 2 — medication activity (scoped to base Medication Activity template)
    EntryMatchRule(
        code_xpath=(
            ".//hl7:substanceAdministration"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.16']]"
            "//hl7:manufacturedMaterial/hl7:code"
        ),
        code_system_oid=RXNORM_OID,
        translation_xpath=(
            ".//hl7:substanceAdministration"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.16']]"
            "//hl7:manufacturedMaterial/hl7:code/hl7:translation"
        ),
    ),
    # rule 3 — immunization activity (scoped to base Immunization Activity template)
    EntryMatchRule(
        code_xpath=(
            ".//hl7:substanceAdministration"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.52']]"
            "//hl7:manufacturedMaterial/hl7:code"
        ),
        code_system_oid=CVX_OID,
        translation_xpath=(
            ".//hl7:substanceAdministration"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.52']]"
            "//hl7:manufacturedMaterial/hl7:code/hl7:translation"
        ),
        translation_code_system_oid=RXNORM_OID,
    ),
    # rule 4 — indication value (reason for medication/procedure) — SNOMED fallback
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.19']]"
            "/hl7:value"
        ),
        code_system_oid=SNOMED_OID,
    ),
]


# NOTE:
# PROBLEMS (11450-4)
# =============================================================================
# IG template: Problem Concern Act (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ']
# prune level: act/entryRelationship[@typeCode='SUBJ'] (individual problems)
#   typeCode='SUBJ' is a SHALL constraint — safe to filter on

_PROBLEM_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # rule 1 — IG-conformant: SNOMED on value, ICD-10-CM on translation
    # primary code: observation/value SHALL be SNOMED (CONF:1198-9058)
    # translation: observation/value/translation MAY be ICD-10-CM (CONF:1198-16750)
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value"
        ),
        code_system_oid=SNOMED_OID,
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value/hl7:translation"
        ),
        translation_code_system_oid=ICD10_OID,
        prune_container_xpath="hl7:act/hl7:entryRelationship[@typeCode='SUBJ']",
    ),
    # rule 2 — reversed: ICD-10-CM on value, SNOMED on translation
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value"
        ),
        code_system_oid=ICD10_OID,
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value/hl7:translation"
        ),
        translation_code_system_oid=SNOMED_OID,
        prune_container_xpath="hl7:act/hl7:entryRelationship[@typeCode='SUBJ']",
    ),
]


# NOTE:
# RESULTS (30954-2)
# =============================================================================
# rule 1 — test code
#   IG template: Result Observation (V3) (2.16.840.1.113883.10.20.22.4.2)
#   primary code: observation/code SHOULD be LOINC (CONF:1198-7133)
#   prune level:  organizer/component (individual result observations)
#
# rule 2 — result value (structural precedence fallback)
#   primary code: observation/value[@xsi:type='CD'] SHOULD be SNOMED
#     (CONF:1198-32610)
#   prune level:  organizer/component (individual result observations)

_RESULTS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.2']]"
            "/hl7:code"
        ),
        code_system_oid=LOINC_OID,
        prune_container_xpath="hl7:organizer/hl7:component",
    ),
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.2']]"
            "/hl7:value[@xsi:type='CD']"
        ),
        code_system_oid=SNOMED_OID,
        prune_container_xpath="hl7:organizer/hl7:component",
    ),
]


# NOTE:
# VITAL SIGNS (8716-3)
# =============================================================================
# IG template: Vital Signs Organizer (V3) wraps Vital Sign Observation (V2)
#   via component (CONF:1198-7285, CONF:1198-15946)
# primary code: observation/code SHALL be LOINC from Vital Sign Result Type
#   value set (CONF:1098-7301)
# prune level:  organizer/component (individual vital sign observations)

_VITAL_SIGNS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.27']]"
            "/hl7:code"
        ),
        code_system_oid=LOINC_OID,
        prune_container_xpath="hl7:organizer/hl7:component",
    ),
]
