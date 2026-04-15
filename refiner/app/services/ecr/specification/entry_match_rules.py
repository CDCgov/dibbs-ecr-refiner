from typing import Final

from ..model import EntryMatchRule
from .constants import CVX_OID, ICD10_OID, LOINC_OID, RXNORM_OID, SNOMED_OID

# NOTE:
# =============================================================================
# DESIGN NOTES FOR THIS FILE
# =============================================================================
#
# -----------------------------------------------
# OID fields are documentation, not enforcement
# -----------------------------------------------
#
# Each EntryMatchRule carries `code_system_oid` and (when applicable)
# `translation_code_system_oid` fields that describe the code system the IG
# expects at each location. The matcher in section/entry_matching.py does
# NOT use these fields to constrain lookups — it calls find_match with
# `None` as the system and trusts the rule's XPath template scoping to
# keep the match structurally safe. The OID fields are retained as
# IG-traceable documentation: a reader of this file should be able to
# see which code system the IG says belongs at each location, even
# though the matcher is deliberately more permissive than the IG's
# strict reading.
#
# The reason for the permissiveness is real-world data variability:
# EHRs mislabel code systems, nullFlavor their primaries and carry the
# actual code in translation, use ICD-10 where the IG expects SNOMED,
# and so on. The PHA's configuration is the source of truth for "which
# codes we care about"; the XPath scoping is the source of truth for
# "which structural positions in the document count as matches"; the
# code system is not part of either story.


# NOTE:
# ADMISSION DIAGNOSIS (46241-6)
# =============================================================================
# IG template: Hospital Admission Diagnosis (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ'] (CONF:1198-7674, CONF:1198-7675)
# prune level: act/entryRelationship[@typeCode='SUBJ'] (individual diagnoses)
#   typeCode='SUBJ' is a SHALL constraint (CONF:1198-7675) — safe to filter on
#
# the single rule here catches both the IG-conformant shape (SNOMED
# primary on value, ICD-10-CM optional translation, per CONF:1198-9058
# and CONF:1198-16750) and the observed real-world variant (ICD-10-CM
# primary, SNOMED translation, seen in EHRs whose internal problem
# list is indexed on ICD-10-CM)
_ADMISSION_DIAGNOSIS_MATCH_RULES: Final[list[EntryMatchRule]] = [
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
]


# NOTE:
# ADMISSION MEDICATIONS (42346-7)
# =============================================================================
# IG template: Admission Medication (V2) uses Medication Information (V2)
# primary code: manufacturedMaterial/code SHALL be RxNorm (CONF:1098-7412)
# translation:  manufacturedMaterial/code/translation MAY have NDC (CONF:1098-31884)
#
# * single rule, matcher-unscoped. the rule will catch RxNorm on primary,
#   RxNorm on translation, NDC on translation (if NDC codes are ever in
#   a configured set), and the nullFlavor-primary-with-translation
#   pattern where an EHR can't supply the expected primary and puts the
#   real code in translation
# * all of these are structurally constrained to the Medication
#   Information template via the XPath scoping
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
]


# NOTE:
# ENCOUNTERS (46240-8)
# =============================================================================
# IG template: Encounter Diagnosis (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ'] (CONF:1198-14892, CONF:1198-14898)
# prune level: encounter/entryRelationship scoped by Encounter Diagnosis templateId
#   CONF:1198-15492 does NOT constrain @typeCode on the entryRelationship
#   that wraps Encounter Diagnosis (V3). Real-world data uses a mix of
#   SUBJ, RSON, and COMP for this typeCode, and scoping by the child
#   act's templateId (CONF:1198-14896, SHALL) is reliable regardless
#   of which typeCode the document chose.
_ENCOUNTERS_MATCH_RULES: Final[list[EntryMatchRule]] = [
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
]


# NOTE:
# IMMUNIZATIONS (11369-6)
# =============================================================================
# IG template: Immunization Activity (V3) uses Immunization Medication Information (V2)
# primary code: manufacturedMaterial/code SHALL be CVX (CONF:1098-9007)
# translation:  manufacturedMaterial/code/translation MAY be RxNorm (CONF:1098-31543)
# single rule. Under the new matcher semantics, this rule now
# correctly handles several real-world shapes that the old
# OID-enforcing matcher would have silently dropped:
#
#   1. CVX on primary, no translation — the IG-conformant shape.
#   2. CVX mislabeled as RxNorm on primary — EHRs that index vaccines
#      on RxNorm internally often tag the CVX code as RxNorm. The
#      unscoped lookup catches this.
#   3. nullFlavor'd primary with translation — EHRs that can't supply
#      CVX will sometimes set @nullFlavor on the primary and put an
#      RxNorm (or other) translation underneath. The primary loop in
#      _try_match_entry skips nullFlavor'd elements (no @code
#      attribute), and the translation branch catches the real code.
#   4. CVX on primary with RxNorm translation — both would match
#      against a configured set containing either code.
#
# the common thread is that the code system the document claims is
# not part of the match decision; only the code value is
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
]


# NOTE:
# PLAN OF TREATMENT (18776-5)
# =============================================================================
# heterogeneous entry types — multiple rules with structural precedence.
# Each rule's xpath is scoped to a specific C-CDA template so that
# structural precedence correctly separates medication entries from
# immunization entries (both share manufacturedMaterial/code but use
# different templateIds).
# rule 1 — Planned Observation / Lab Test Order (SHOULD code binding)
#   IG template: Planned Observation (V2) (2.16.840.1.113883.10.20.22.4.44)
#   primary code: observation/code SHOULD be LOINC (CONF:1098-31030)
#   eICR trigger: SHALL be from RCTC lab test orders (CONF:3284-336)
# * this is a SHOULD constraint, not SHALL, so real-world documents
#   may carry a non-LOINC primary (local lab panel codes) with LOINC
#   in translation. The `translation_xpath` on this rule catches that
#   shape.
# rule 2 — Medication Activity
#   IG template: Medication Activity (V2) (2.16.840.1.113883.10.20.22.4.16)
#   note: Planned Medication Activity (4.42) conforms to Medication Activity
#     (4.16), so targeting 4.16 catches both planned and non-planned
#     medication entries
#   inner template: Medication Information (V2) (2.16.840.1.113883.10.20.22.4.23)
#   primary code: manufacturedMaterial/code SHALL be RxNorm (CONF:1098-7412)
#   translation:  manufacturedMaterial/code/translation MAY have NDC (CONF:1098-31884)
# rule 3 — Immunization Activity
#   IG template: Immunization Activity (V3) (2.16.840.1.113883.10.20.22.4.52)
#   note: Planned Immunization Activity (4.120) conforms to Immunization
#     Activity (4.52), so targeting 4.52 catches both planned and
#     non-planned immunization entries
#   inner template: Immunization Medication Information (V2)
#     (2.16.840.1.113883.10.20.22.4.54)
#   primary code: manufacturedMaterial/code SHALL be CVX (CONF:1098-9007)
#   translation:  manufacturedMaterial/code/translation MAY be RxNorm (CONF:1098-31543)
# rule 4 — Indication (fallback)
#   IG template: Indication (V2) (2.16.840.1.113883.10.20.22.4.19)
#   primary code: observation/value MAY be SNOMED
#   note: catches entries indicated for a matching condition
#     (e.g., Remdesivir for COVID-19)
# structural precedence: rule 1 claims observation entries, rules 2-3 claim
# medication/immunization entries respectively (template-scoped so they
# don't interfere), rule 4 catches unclaimed entries only
_PLAN_OF_TREATMENT_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # rule 1 — planned observation / lab test order code (SHOULD LOINC),
    # with translation_xpath to catch non-LOINC-primary documents
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.44']]"
            "/hl7:code"
        ),
        code_system_oid=LOINC_OID,
        translation_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.44']]"
            "/hl7:code/hl7:translation"
        ),
        translation_code_system_oid=LOINC_OID,
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
]


# NOTE:
# RESULTS (30954-2)
# =============================================================================
# three rules targeting Result Observation V3 (2.16.840.1.113883.10.20.22.4.2):
# rule 1 — test code (primary, SHOULD LOINC)
#   primary code: observation/code
#   IG guidance: CONF:1198-7133 SHOULD be LOINC (note: SHOULD, not SHALL)
#   prune level:  organizer/component (individual result observations)
# rule 2 — result value
#   primary code: observation/value[@xsi:type='CD']
#   IG guidance: CONF:1198-32610 SHOULD be SNOMED Findings value set
#   prune level:  organizer/component
# rule 3 — test code via translation (real-world SHOULD variant)
#   primary code: observation/code/translation
#   Catches Result Observations where the primary `code` is a local
#   lab system identifier and the LOINC appears as a translation.
#   This is IG-conformant under the SHOULD binding in CONF:1198-7133.
#   prune level:  organizer/component
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
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.2']]"
            "/hl7:code/hl7:translation"
        ),
        code_system_oid=LOINC_OID,
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
#
# unlike Results, the Vital Sign Result Type value set is small and
# tightly bound by a SHALL, so no SHOULD-variant rule is needed
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
