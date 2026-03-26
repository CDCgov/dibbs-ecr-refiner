from collections import defaultdict
from typing import Final

from lxml.etree import _Element

from .model import (
    HL7_NS,
    EICRSpecification,
    EicrVersion,
    EntryMatchRule,
    SectionSpecification,
    TriggerCode,
)

# NOTE:
# CONSTANTS
# =============================================================================

# map of templateId extensions to their semantic version strings
EICR_VERSION_MAP: Final[dict[str, EicrVersion]] = {
    "2016-12-01": "1.1",
    "2021-01-01": "3.1",
    "2022-05-01": "3.1.1",
}

# for CDA sections that we should not refine; in the future we may
# decide to implement new ways to handle these sections but for now;
# skipping them is easier and produces valid (based on schematron) output
SECTION_PROCESSING_SKIP: Final[set[str]] = {
    "83910-0",  # emergency outbreak information section
    "88085-6",  # reportability response information section
}


# NOTE:
# ENTRY MATCH RULES
# =============================================================================
# these encode IG-verified knowledge about where matchable codes live in each
# section's entries and which code system to expect. they target C-CDA templates
# (not eICR-specific ones) and are version-independent
#
# source references verified against:
# - CDAR2_IG_PHCASERPT_R2_STU1_1_2017JAN Vol2
# - CDAR2_IG_PHCASERPT_R2_STU3_1_1_Vol2_2022JUL_2024OCT


# Admission Diagnosis (46241-6)
# IG template: Hospital Admission Diagnosis (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ'] (CONF:1198-7674, CONF:1198-7675)
# primary code: observation/value SHALL be SNOMED (CONF:1198-9058)
# translation:  observation/value/translation MAY be ICD-10-CM (CONF:1198-16750)
# prune level:  act/entryRelationship[@typeCode='SUBJ'] (individual diagnoses)
_ADMISSION_DIAGNOSIS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value"
        ),
        code_system_oid="2.16.840.1.113883.6.96",
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value/hl7:translation"
        ),
        translation_code_system_oid="2.16.840.1.113883.6.90",
        prune_container_xpath="hl7:act/hl7:entryRelationship[@typeCode='SUBJ']",
    ),
]

# Admission Medications (42346-7)
# IG template: Admission Medication (V2) uses Medication Information (V2)
# primary code: manufacturedMaterial/code SHALL be RxNorm (CONF:1098-7412)
# translation:  manufacturedMaterial/code/translation MAY have NDC (CONF:1098-31884)
_ADMISSION_MEDICATIONS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=".//hl7:manufacturedMaterial/hl7:code",
        code_system_oid="2.16.840.1.113883.6.88",  # RxNorm
        translation_xpath=".//hl7:manufacturedMaterial/hl7:code/hl7:translation",
    ),
]

# Discharge Diagnosis (11535-2)
# IG template: Hospital Discharge Diagnosis (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ'] (CONF:1198-7680, CONF:1198-7681, CONF:1198-15536)
# primary code: observation/value SHALL be SNOMED (CONF:1198-9058)
# translation:  observation/value/translation MAY be ICD-10-CM (CONF:1198-16750)
# prune level:  act/entryRelationship[@typeCode='SUBJ'] (individual diagnoses)
_DISCHARGE_DIAGNOSIS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value"
        ),
        code_system_oid="2.16.840.1.113883.6.96",
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value/hl7:translation"
        ),
        translation_code_system_oid="2.16.840.1.113883.6.90",
        prune_container_xpath="hl7:act/hl7:entryRelationship[@typeCode='SUBJ']",
    ),
]

# Encounters (46240-8)
# IG template: Encounter Diagnosis (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ'] (CONF:1198-14892, CONF:1198-14898)
# primary code: observation/value SHALL be SNOMED (CONF:1198-9058)
# translation:  observation/value/translation MAY be ICD-10-CM (CONF:1198-16750)
# prune level:  encounter/entryRelationship[@typeCode='COMP'] (individual diagnoses)
_ENCOUNTERS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value"
        ),
        code_system_oid="2.16.840.1.113883.6.96",
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value/hl7:translation"
        ),
        translation_code_system_oid="2.16.840.1.113883.6.90",
        prune_container_xpath="hl7:encounter/hl7:entryRelationship[@typeCode='COMP']",
    ),
]

# Immunizations (11369-6)
# IG template: Immunization Activity (V3) uses Immunization Medication Information (V2)
# primary code: manufacturedMaterial/code SHALL be CVX (CONF:1098-9007)
# translation:  manufacturedMaterial/code/translation MAY be RxNorm (CONF:1098-31543)
_IMMUNIZATIONS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=".//hl7:manufacturedMaterial/hl7:code",
        code_system_oid="2.16.840.1.113883.12.292",  # CVX
        translation_xpath=".//hl7:manufacturedMaterial/hl7:code/hl7:translation",
        translation_code_system_oid="2.16.840.1.113883.6.88",  # RxNorm
    ),
]

# Medications Administered (29549-3)
# IG template: Medication Activity (V2) uses Medication Information (V2)
# primary code: manufacturedMaterial/code SHALL be RxNorm (CONF:1098-7412)
# translation:  manufacturedMaterial/code/translation MAY have NDC (CONF:1098-31884)
_MEDICATIONS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=".//hl7:manufacturedMaterial/hl7:code",
        code_system_oid="2.16.840.1.113883.6.88",  # RxNorm
        translation_xpath=".//hl7:manufacturedMaterial/hl7:code/hl7:translation",
    ),
]

# Medications (home) (10160-0)
# IG template: Medication Activity (V2) uses Medication Information (V2)
# primary code: manufacturedMaterial/code SHALL be RxNorm (CONF:1098-7412)
# translation:  manufacturedMaterial/code/translation MAY have NDC (CONF:1098-31884)
_MEDICATIONS_HOME_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=".//hl7:manufacturedMaterial/hl7:code",
        code_system_oid="2.16.840.1.113883.6.88",  # RxNorm
        translation_xpath=".//hl7:manufacturedMaterial/hl7:code/hl7:translation",
    ),
]

# Past Medical History (11348-0)
# IG template: Problem Concern Act (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ']
# primary code: observation/value SHALL be SNOMED (CONF:1198-9058)
# translation:  observation/value/translation MAY be ICD-10-CM (CONF:1198-16750)
# prune level:  act/entryRelationship[@typeCode='SUBJ'] (individual problems)
_PAST_MEDICAL_HISTORY_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value"
        ),
        code_system_oid="2.16.840.1.113883.6.96",
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value/hl7:translation"
        ),
        translation_code_system_oid="2.16.840.1.113883.6.90",
        prune_container_xpath="hl7:act/hl7:entryRelationship[@typeCode='SUBJ']",
    ),
]

# Plan of Treatment (18776-5)
# Heterogeneous entry types — multiple rules with structural precedence.
# Each rule's xpath is scoped to a specific C-CDA template so that structural
# precedence correctly separates medication entries from immunization entries
# (both share manufacturedMaterial/code but use different templateIds).
#
# rule 1 — Planned Observation / Lab Test Order
#   IG template: Planned Observation (V2) (2.16.840.1.113883.10.20.22.4.44)
#   primary code: observation/code SHOULD be LOINC (CONF:1098-31030)
#   eICR trigger: SHALL be from RCTC lab test orders (CONF:3284-336)
#
# rule 2 — Medication Activity
#   IG template: Medication Activity (V2) (2.16.840.1.113883.10.20.22.4.16)
#   note: Planned Medication Activity (4.42) conforms to Medication Activity (4.16),
#     so targeting 4.16 catches both planned and non-planned medication entries
#   inner template: Medication Information (V2) (2.16.840.1.113883.10.20.22.4.23)
#   primary code: manufacturedMaterial/code SHALL be RxNorm (CONF:1098-7412)
#   translation:  manufacturedMaterial/code/translation MAY have NDC (CONF:1098-31884)
#
# rule 3 — Immunization Activity
#   IG template: Immunization Activity (V3) (2.16.840.1.113883.10.20.22.4.52)
#   note: Planned Immunization Activity (4.120) conforms to Immunization Activity (4.52),
#     so targeting 4.52 catches both planned and non-planned immunization entries
#   inner template: Immunization Medication Information (V2) (2.16.840.1.113883.10.20.22.4.54)
#   primary code: manufacturedMaterial/code SHALL be CVX (CONF:1098-9007)
#   translation:  manufacturedMaterial/code/translation MAY be RxNorm (CONF:1098-31543)
#
# rule 4 — Indication (fallback)
#   IG template: Indication (V2) (2.16.840.1.113883.10.20.22.4.19)
#   primary code: observation/value MAY be SNOMED
#   note: catches entries indicated for a matching condition (e.g., Remdesivir for COVID-19)
#
# structural precedence: rule 1 claims observation entries, rules 2-3 claim
# medication/immunization entries respectively (template-scoped so they don't
# interfere), rule 4 catches unclaimed entries only
_PLAN_OF_TREATMENT_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # rule 1 — planned observation / lab test order code
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.44']]"
            "/hl7:code"
        ),
        code_system_oid="2.16.840.1.113883.6.1",  # LOINC
    ),
    # rule 2 — medication activity (scoped to base Medication Activity template)
    EntryMatchRule(
        code_xpath=(
            ".//hl7:substanceAdministration"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.16']]"
            "//hl7:manufacturedMaterial/hl7:code"
        ),
        code_system_oid="2.16.840.1.113883.6.88",  # RxNorm
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
        code_system_oid="2.16.840.1.113883.12.292",  # CVX
        translation_xpath=(
            ".//hl7:substanceAdministration"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.52']]"
            "//hl7:manufacturedMaterial/hl7:code/hl7:translation"
        ),
        translation_code_system_oid="2.16.840.1.113883.6.88",  # RxNorm
    ),
    # rule 4 — indication value (reason for medication/procedure) — SNOMED fallback
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.19']]"
            "/hl7:value"
        ),
        code_system_oid="2.16.840.1.113883.6.96",  # SNOMED
    ),
]

# Problems (11450-4)
# IG template: Problem Concern Act (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ']
# primary code: observation/value SHALL be SNOMED (CONF:1198-9058)
# translation:  observation/value/translation MAY be ICD-10-CM (CONF:1198-16750)
# prune level:  act/entryRelationship[@typeCode='SUBJ'] (individual problems)
_PROBLEM_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value"
        ),
        code_system_oid="2.16.840.1.113883.6.96",
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]"
            "/hl7:value/hl7:translation"
        ),
        translation_code_system_oid="2.16.840.1.113883.6.90",
        prune_container_xpath="hl7:act/hl7:entryRelationship[@typeCode='SUBJ']",
    ),
]

# Results (30954-2)
# rule 1 — test code
#   IG template: Result Observation (V3) (2.16.840.1.113883.10.20.22.4.2)
#   primary code: observation/code SHOULD be LOINC (CONF:1198-7133)
#   prune level:  organizer/component (individual result observations)
#
# rule 2 — result value (structural precedence fallback)
#   primary code: observation/value[@xsi:type='CD'] SHOULD be SNOMED (CONF:1198-32610)
#   prune level:  organizer/component (individual result observations)
_RESULTS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.2']]"
            "/hl7:code"
        ),
        code_system_oid="2.16.840.1.113883.6.1",  # LOINC
        prune_container_xpath="hl7:organizer/hl7:component",
    ),
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.2']]"
            "/hl7:value[@xsi:type='CD']"
        ),
        code_system_oid="2.16.840.1.113883.6.96",  # SNOMED
        prune_container_xpath="hl7:organizer/hl7:component",
    ),
]

# Vital Signs (8716-3)
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
        code_system_oid="2.16.840.1.113883.6.1",  # LOINC
        prune_container_xpath="hl7:organizer/hl7:component",
    ),
]


# NOTE:
# SECTION CATALOG
# =============================================================================
# one entry per section LOINC code. Contains C-CDA structural information that
# is stable across all eICR versions: display name, section templateId, and
# entry match rules
#
# trigger codes are NOT here — they vary by eICR version and live in the
# version manifests below.

_SECTION_CATALOG: Final[dict[str, SectionSpecification]] = {
    # sections present in all versions (1.1, 3.1, 3.1.1)
    "46240-8": SectionSpecification(
        loinc_code="46240-8",
        display_name="Encounters Section",
        template_id="2.16.840.1.113883.10.20.22.2.22.1:2015-08-01",
        entry_match_rules=_ENCOUNTERS_MATCH_RULES,
    ),
    "10164-2": SectionSpecification(
        loinc_code="10164-2",
        display_name="History of Present Illness Section",
        template_id="1.3.6.1.4.1.19376.1.5.3.1.3.4",
    ),
    "11369-6": SectionSpecification(
        loinc_code="11369-6",
        display_name="Immunizations Section",
        template_id="2.16.840.1.113883.10.20.22.2.2.1:2015-08-01",
        entry_match_rules=_IMMUNIZATIONS_MATCH_RULES,
    ),
    "29549-3": SectionSpecification(
        loinc_code="29549-3",
        display_name="Medications Administered Section",
        template_id="2.16.840.1.113883.10.20.22.2.38:2014-06-09",
        entry_match_rules=_MEDICATIONS_MATCH_RULES,
    ),
    "18776-5": SectionSpecification(
        loinc_code="18776-5",
        display_name="Plan of Treatment Section",
        template_id="2.16.840.1.113883.10.20.22.2.10:2014-06-09",
        entry_match_rules=_PLAN_OF_TREATMENT_MATCH_RULES,
    ),
    "11450-4": SectionSpecification(
        loinc_code="11450-4",
        display_name="Problem Section",
        template_id="2.16.840.1.113883.10.20.22.2.5.1:2015-08-01",
        entry_match_rules=_PROBLEM_MATCH_RULES,
    ),
    "29299-5": SectionSpecification(
        loinc_code="29299-5",
        display_name="Reason for Visit Section",
        template_id="2.16.840.1.113883.10.20.22.2.12",
    ),
    "30954-2": SectionSpecification(
        loinc_code="30954-2",
        display_name="Results Section",
        template_id="2.16.840.1.113883.10.20.22.2.3.1:2015-08-01",
        entry_match_rules=_RESULTS_MATCH_RULES,
    ),
    "29762-2": SectionSpecification(
        loinc_code="29762-2",
        display_name="Social History Section",
        template_id="2.16.840.1.113883.10.20.22.2.17:2015-08-01",
    ),
    # sections added in 3.1+
    "10187-3": SectionSpecification(
        loinc_code="10187-3",
        display_name="Review of Systems Section",
        template_id="1.3.6.1.4.1.19376.1.5.3.1.3.18",
    ),
    "10154-3": SectionSpecification(
        loinc_code="10154-3",
        display_name="Chief Complaint Section",
        template_id="1.3.6.1.4.1.19376.1.5.3.1.1.13.2.1",
    ),
    "10160-0": SectionSpecification(
        loinc_code="10160-0",
        display_name="Medications Section",
        template_id="2.16.840.1.113883.10.20.22.2.1.1:2014-06-09",
        entry_match_rules=_MEDICATIONS_HOME_MATCH_RULES,
    ),
    "47519-4": SectionSpecification(
        loinc_code="47519-4",
        display_name="Procedures Section",
        template_id="2.16.840.1.113883.10.20.22.2.7.1:2014-06-09",
    ),
    "46241-6": SectionSpecification(
        loinc_code="46241-6",
        display_name="Admission Diagnosis Section",
        template_id="2.16.840.1.113883.10.20.22.2.43:2015-08-01",
        entry_match_rules=_ADMISSION_DIAGNOSIS_MATCH_RULES,
    ),
    "11535-2": SectionSpecification(
        loinc_code="11535-2",
        display_name="Discharge Diagnosis Section",
        template_id="2.16.840.1.113883.10.20.22.2.24:2015-08-01",
        entry_match_rules=_DISCHARGE_DIAGNOSIS_MATCH_RULES,
    ),
    "42346-7": SectionSpecification(
        loinc_code="42346-7",
        display_name="Admission Medications Section",
        template_id="2.16.840.1.113883.10.20.22.2.44:2015-08-01",
        entry_match_rules=_ADMISSION_MEDICATIONS_MATCH_RULES,
    ),
    "11348-0": SectionSpecification(
        loinc_code="11348-0",
        display_name="Past Medical History",
        template_id="2.16.840.1.113883.10.20.22.2.20:2015-08-01",
        entry_match_rules=_PAST_MEDICAL_HISTORY_MATCH_RULES,
    ),
    "8716-3": SectionSpecification(
        loinc_code="8716-3",
        display_name="Vital Signs Section",
        template_id="2.16.840.1.113883.10.20.22.2.4.1:2015-08-01",
        entry_match_rules=_VITAL_SIGNS_MATCH_RULES,
    ),
    "90767-5": SectionSpecification(
        loinc_code="90767-5",
        display_name="Pregnancy Section",
        template_id="2.16.840.1.113883.10.20.22.2.80:2018-04-01",
    ),
    "83910-0": SectionSpecification(
        loinc_code="83910-0",
        display_name="Emergency Outbreak Information Section",
        template_id="2.16.840.1.113883.10.20.15.2.2.4:2021-01-01",
    ),
    "88085-6": SectionSpecification(
        loinc_code="88085-6",
        display_name="Reportability Response Information Section",
        template_id="2.16.840.1.113883.10.20.15.2.2.5:2021-01-01",
    ),
}


# NOTE:
# VERSION MANIFESTS
# =============================================================================
# * each manifest lists the sections present in that eICR version and the
# trigger code templateIds (with version-dated extensions) for each section
# * this is the ONLY thing that varies by version. section definitions,
# entry match rules, display names, and C-CDA templateIds come from the
# catalog above

# format: dict of section LOINC -> dict of trigger OID -> TriggerCode
type TriggerMap = dict[str, list[TriggerCode]]

_VERSION_1_1_TRIGGERS: Final[TriggerMap] = {
    "46240-8": [
        TriggerCode(
            oid="2.16.840.1.113883.10.20.15.2.3.5:2016-12-01",
            display_name="Initial Case Report Manual Initiation Reason Observation",
            element_tag="observation",
        ),
        TriggerCode(
            oid="2.16.840.1.113883.10.20.15.2.3.3:2016-12-01",
            display_name="Initial Case Report Trigger Code Problem Observation",
            element_tag="observation",
        ),
    ],
    "18776-5": [
        TriggerCode(
            oid="2.16.840.1.113883.10.20.15.2.3.4:2016-12-01",
            display_name="Initial Case Report Trigger Code Lab Test Order",
            element_tag="observation",
        ),
    ],
    "30954-2": [
        TriggerCode(
            oid="2.16.840.1.113883.10.20.15.2.3.2:2016-12-01",
            display_name="Initial Case Report Trigger Code Result Observation",
            element_tag="observation",
        ),
    ],
}

# 3.1 trigger codes (shared by 3.1.1 — they are parsed identically)
_trigger_code_problem_obs_v3 = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.3:2021-01-01",
    display_name="Initial Case Report Trigger Code Problem Observation",
    element_tag="observation",
)
_trigger_code_med_info = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.36:2019-04-01",
    display_name="Initial Case Report Trigger Code Medication Information",
    element_tag="manufacturedProduct",
)
_trigger_code_immunization_info = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.38:2019-04-01",
    display_name="Initial Case Report Trigger Code Immunization Medication Information",
    element_tag="manufacturedProduct",
)
_trigger_code_result_obs_v2 = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.2:2019-04-01",
    display_name="Initial Case Report Trigger Code Result Observation",
    element_tag="observation",
)
_trigger_code_result_organizer = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.35:2022-05-01",
    display_name="Initial Case Report Trigger Code Result Organizer",
    element_tag="organizer",
)
_trigger_code_lab_test_order_v2 = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.4:2019-04-01",
    display_name="Initial Case Report Trigger Code Lab Test Order",
    element_tag="observation",
)
_trigger_code_planned_act = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.41:2021-01-01",
    display_name="Initial Case Report Trigger Code Planned Act",
    element_tag="act",
)
_trigger_code_planned_procedure = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.42:2021-01-01",
    display_name="Initial Case Report Trigger Code Planned Procedure",
    element_tag="procedure",
)
_trigger_code_planned_observation = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.43:2021-01-01",
    display_name="Initial Case Report Trigger Code Planned Observation",
    element_tag="observation",
)
_trigger_code_procedure_act = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.45:2021-01-01",
    display_name="Initial Case Report Trigger Code Procedure Activity Act",
    element_tag="act",
)
_trigger_code_procedure_obs = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.46:2021-01-01",
    display_name="Initial Case Report Trigger Code Procedure Activity Observation",
    element_tag="observation",
)
_trigger_code_procedure_procedure = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.44:2021-01-01",
    display_name="Initial Case Report Trigger Code Procedure Activity Procedure",
    element_tag="procedure",
)

_VERSION_3X_TRIGGERS: Final[TriggerMap] = {
    "10160-0": [_trigger_code_med_info],
    "18776-5": [
        _trigger_code_lab_test_order_v2,
        _trigger_code_planned_act,
        _trigger_code_planned_procedure,
        _trigger_code_planned_observation,
        _trigger_code_med_info,
    ],
    "29549-3": [_trigger_code_med_info],
    "47519-4": [
        _trigger_code_med_info,
        _trigger_code_procedure_act,
        _trigger_code_procedure_obs,
        _trigger_code_procedure_procedure,
    ],
    "11369-6": [_trigger_code_immunization_info, _trigger_code_med_info],
    "30954-2": [_trigger_code_result_organizer, _trigger_code_result_obs_v2],
    "42346-7": [_trigger_code_med_info],
    "11450-4": [_trigger_code_problem_obs_v3],
    "46240-8": [_trigger_code_problem_obs_v3],
}


# which sections exist in each version (by LOINC code)
_VERSION_SECTIONS: Final[dict[EicrVersion, list[str]]] = {
    "1.1": [
        "46240-8",  # Encounters
        "10164-2",  # History of Present Illness
        "11369-6",  # Immunizations
        "29549-3",  # Medications Administered
        "18776-5",  # Plan of Treatment
        "11450-4",  # Problem
        "29299-5",  # Reason for Visit
        "30954-2",  # Results
        "29762-2",  # Social History
    ],
    # 3.1 and 3.1.1 have identical section sets and trigger codes
    "3.1": [
        # all 1.1 sections
        "46240-8",
        "10164-2",
        "11369-6",
        "29549-3",
        "18776-5",
        "11450-4",
        "29299-5",
        "30954-2",
        "29762-2",
        # added in 3.1+
        "10187-3",  # Review of Systems
        "10154-3",  # Chief Complaint
        "10160-0",  # Medications (home)
        "47519-4",  # Procedures
        "46241-6",  # Admission Diagnosis
        "11535-2",  # Discharge Diagnosis
        "42346-7",  # Admission Medications
        "11348-0",  # Past Medical History
        "8716-3",  # Vital Signs
        "90767-5",  # Pregnancy
        "83910-0",  # Emergency Outbreak Information
        "88085-6",  # Reportability Response Information
    ],
}
# 3.1.1 is parsed identically to 3.1
_VERSION_SECTIONS["3.1.1"] = _VERSION_SECTIONS["3.1"]

# version → trigger map
_VERSION_TRIGGERS: Final[dict[EicrVersion, TriggerMap]] = {
    "1.1": _VERSION_1_1_TRIGGERS,
    "3.1": _VERSION_3X_TRIGGERS,
    "3.1.1": _VERSION_3X_TRIGGERS,
}


# NOTE:
# SERVICE FUNCTIONS
# =============================================================================


def detect_eicr_version(xml_root: _Element) -> EicrVersion:
    """
    Inspects the XML header to determine the eICR version (e.g. "1.1", "3.1").

    Defaults to "1.1" if detection fails.
    """

    template_id = xml_root.find(
        'hl7:templateId[@root="2.16.840.1.113883.10.20.15.2"]',
        namespaces=HL7_NS,
    )

    if template_id is not None:
        version_date = template_id.get("extension")
        if version_date and version_date in EICR_VERSION_MAP:
            return EICR_VERSION_MAP[version_date]

    return "1.1"


def load_spec(version: EicrVersion) -> EICRSpecification:
    """
    Assemble the specification for a specific eICR version by merging the section catalog with version-specific trigger codes.

    The catalog provides stable C-CDA structural data (templateIds, display names,
    entry match rules). The version manifest provides which sections exist and
    which trigger code OIDs apply.
    """

    # resolve version — fall back to 1.1 for unknown versions
    if version not in _VERSION_SECTIONS:
        version = "1.1"

    section_codes = _VERSION_SECTIONS[version]
    trigger_map = _VERSION_TRIGGERS.get(version, {})

    sections: dict[str, SectionSpecification] = {}

    for loinc_code in section_codes:
        catalog_entry = _SECTION_CATALOG.get(loinc_code)
        if catalog_entry is None:
            continue  # section not in catalog — skip gracefully

        # overlay version-specific trigger codes onto the catalog entry
        version_triggers = trigger_map.get(loinc_code, [])

        if version_triggers:
            # create a new SectionSpecification with the trigger codes added
            # (SectionSpecification is frozen, so we rebuild rather than mutate)
            spec = SectionSpecification(
                loinc_code=catalog_entry.loinc_code,
                display_name=catalog_entry.display_name,
                template_id=catalog_entry.template_id,
                trigger_codes=version_triggers,
                entry_match_rules=catalog_entry.entry_match_rules,
            )
        else:
            # no trigger codes for this section in this version — use catalog as-is
            spec = catalog_entry

        sections[loinc_code] = spec

    return EICRSpecification(version=version, sections=sections)


def get_section_version_map() -> dict[str, list[str]]:
    """
    Returns a mapping of section LOINC code → sorted list of eICR versions that include that section.

    Used by the configuration service to tag sections with their version
    availability.
    """

    loinc_version_map: dict[str, set[str]] = defaultdict(set)
    for version, section_codes in _VERSION_SECTIONS.items():
        for loinc in section_codes:
            loinc_version_map[loinc].add(version)

    return {k: sorted(v) for k, v in loinc_version_map.items()}
