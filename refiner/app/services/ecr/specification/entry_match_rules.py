from typing import Final

from ..model import EntryMatchRule
from .constants import ICD10_OID, LOINC_OID, SNOMED_OID

# NOTE:
# RULE TIER CONVENTION
# =============================================================================
# Rules within each section are ordered by specificity and IG conformance.
# The tier label in each rule comment describes its provenance:
#
#   TIER 1 — SHALL: directly mandated by the IG. The primary conformant
#             path. If a sender follows the spec, this rule matches.
#
#   TIER 2 — SHOULD/MAY: permitted by the IG but not required. Handles
#             optional patterns (translations, alternate code locations)
#             that conformant senders may or may not use.
#
#   TIER 3 — HEURISTIC: not IG-conformant but observed in real EHR output.
#             Labeled explicitly so future maintainers know these rules
#             exist to accommodate vendor variance, not spec patterns.
#             Each TIER 3 rule carries a note describing what real-world
#             pattern it was written for.
#
# structural precedence (enforced in entry_matching._try_match_entry):
# * rules are evaluated in order; the first rule whose xpath finds any
#   code-bearing elements in an entry claims that entry, regardless of
#   whether those elements produced code set matches. This prevents
#   lower-tier rules from running on entries already evaluated by a
#   higher-tier rule
#
# OID convention:
# OIDs are retained when they encode semantic meaning — i.e. when the
# OID constrains *what kind of code* is meaningful at that xpath location,
#   not just *which system* the code nominally came from. See EntryMatchRule
#   docstring for the full rationale. Rules where OID is set to None carry
#   a comment explaining the intent


# NOTE:
# ADMISSION DIAGNOSIS (46241-6)
# =============================================================================
# IG template: Hospital Admission Diagnosis (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ'] (CONF:1198-7674, CONF:1198-7675)
# * prune level: act/entryRelationship[@typeCode='SUBJ'] (individual diagnoses)
#   typeCode='SUBJ' is a SHALL constraint (CONF:1198-7675) — safe to filter on
_ADMISSION_DIAGNOSIS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # TIER 1 — SHALL: SNOMED on value (CONF:1198-9058)
    # ICD-10-CM in translation is MAY (CONF:1198-16750)
    # OID: SNOMED_OID retained — observation/value in a Problem Observation
    # SHALL be SNOMED; the OID scopes the rule to condition-name codes
    # specifically, distinguishing them from ICD-10 in the reversed pattern
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
        tier=1,
    ),
    # TIER 3 — HEURISTIC: ICD-10-CM on value, SNOMED in translation
    # Not IG-conformant; observed in real EHR output where senders place
    # the billing code (ICD-10) as the primary value and the clinical
    # concept (SNOMED) in translation, reversing the spec's intent.
    # Structural precedence ensures this only fires when TIER 1 found
    # no SNOMED-coded value — i.e., the entry doesn't follow the spec.
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
        tier=3,
    ),
]


# NOTE:
# ADMISSION MEDICATIONS (42346-7)
# =============================================================================
# IG template: Admission Medication (V2) uses Medication Information (V2)
# primary code: manufacturedMaterial/code SHALL be RxNorm (CONF:1098-7412)
# translation:  manufacturedMaterial/code/translation MAY have NDC (CONF:1098-31884)
_ADMISSION_MEDICATIONS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # TIER 1 — SHALL: RxNorm on manufacturedMaterial/code (CONF:1098-7412)
    # OID: None — manufacturedMaterial/code is structurally unambiguous;
    # vendor coding practice varies enough that strict OID checking would
    # produce false negatives on real documents. The xpath location alone
    # is sufficient to scope the match.
    EntryMatchRule(
        code_xpath=".//hl7:manufacturedMaterial/hl7:code",
        code_system_oid=None,  # intentional — see note above
        translation_xpath=".//hl7:manufacturedMaterial/hl7:code/hl7:translation",
        tier=1,
        preserve_whole_entry=True,
    ),
]


# NOTE:
# DISCHARGE DIAGNOSIS (11535-2)
# =============================================================================
# IG template: Hospital Discharge Diagnosis (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ']
#   (CONF:1198-7666, CONF:1198-7667, CONF:1198-15536)
# * prune level: act/entryRelationship[@typeCode='SUBJ'] (individual diagnoses)
#   typeCode='SUBJ' is a SHALL constraint (CONF:1198-7667) — safe to filter on
_DISCHARGE_DIAGNOSIS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # TIER 1 — SHALL: SNOMED on value (CONF:1198-9058)
    # ICD-10-CM in translation is MAY (CONF:1198-16750)
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
        tier=1,
    ),
    # TIER 3 — HEURISTIC: ICD-10-CM on value, SNOMED in translation
    # same rationale as admission diagnosis TIER 3 rule above
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
        tier=3,
    ),
]


# NOTE:
# ENCOUNTERS (46240-8)
# =============================================================================
# IG template: Encounter Diagnosis (V3) wraps Problem Observation (V3)
#   via entryRelationship (CONF:1198-14892, CONF:1198-14898)
# * prune level: encounter/entryRelationship scoped by Encounter Diagnosis templateId
#   CONF:1198-15492 does NOT constrain @typeCode on the entryRelationship
#   that wraps Encounter Diagnosis (V3) — testing has shown a mix of
#   SUBJ, RSON, and COMP entries. Scoping by the child act's templateId
#   (CONF:1198-14896, SHALL) is reliable regardless of typeCode.
_ENCOUNTERS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # TIER 1 — SHALL: SNOMED on value (CONF:1198-9058)
    # ICD-10-CM in translation is MAY (CONF:1198-16750)
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
        tier=1,
    ),
    # TIER 3 — HEURISTIC: ICD-10-CM on value, SNOMED in translation
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
        tier=3,
    ),
]


# NOTE:
# IMMUNIZATIONS (11369-6)
# =============================================================================
# IG template: Immunization Activity (V3) uses Immunization Medication Information (V2)
# primary code: manufacturedMaterial/code SHALL be CVX (CONF:1098-9007)
# translation:  manufacturedMaterial/code/translation MAY be RxNorm (CONF:1098-31543)
#
# * single rule, code_system_oid=None — rationale:
#   The IG says CVX SHALL on manufacturedMaterial/code, but real senders use
#   RxNorm, NDC, and local codes as the primary vaccine code. Earlier attempts
#   to express CVX/RxNorm/NDC as separate tiered rules failed because
#   structural precedence is based on the xpath returning candidates, not on
#   whether any candidate matched the expected OID. Rules 1–3 all targeted
#   .//hl7:manufacturedMaterial/hl7:code — so rule 1 (CVX) would claim every
#   entry that had any code at that location, preventing rules 2 and 3 from
#   ever firing.
# * the fix is the same pattern used for medications: accept any code system
#   at this structurally unambiguous location. The configured condition code
#   set provides the semantic constraint — only configured vaccine codes match,
#   regardless of which code system the sender used. The translation path
#   handles the nullFlavor-primary pattern (CONF:1098-31543) where the primary
#   carries nullFlavor and the RxNorm or NDC code is in translation.
_IMMUNIZATIONS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # TIER 1: any code system on manufacturedMaterial/code
    # translation catches nullFlavor-primary / code-in-translation senders
    # OID: None — see note above; structural location is sufficient constraint
    EntryMatchRule(
        code_xpath=".//hl7:manufacturedMaterial/hl7:code",
        code_system_oid=None,  # intentional — see note above
        translation_xpath=".//hl7:manufacturedMaterial/hl7:code/hl7:translation",
        tier=1,
        preserve_whole_entry=True,
    ),
]


# NOTE:
# MEDICATIONS ADMINISTERED (29549-3)
# =============================================================================
# IG template: Medication Activity (V2) uses Medication Information (V2)
# primary code: manufacturedMaterial/code SHALL be RxNorm (CONF:1098-7412)
# translation:  manufacturedMaterial/code/translation MAY have NDC (CONF:1098-31884)
_MEDICATIONS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # TIER 1 — SHALL: RxNorm on manufacturedMaterial/code (CONF:1098-7412)
    # OID: None — structurally unambiguous location; vendor OID variance
    # is high enough that strict OID checking causes false negatives
    EntryMatchRule(
        code_xpath=".//hl7:manufacturedMaterial/hl7:code",
        code_system_oid=None,  # intentional — see note above
        translation_xpath=".//hl7:manufacturedMaterial/hl7:code/hl7:translation",
        tier=1,
        preserve_whole_entry=True,
    ),
]


# NOTE:
# MEDICATIONS — HOME (10160-0)
# =============================================================================
# IG template: Medication Activity (V2) uses Medication Information (V2)
# primary code: manufacturedMaterial/code SHALL be RxNorm (CONF:1098-7412)
# translation:  manufacturedMaterial/code/translation MAY have NDC (CONF:1098-31884)
_MEDICATIONS_HOME_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # TIER 1 — SHALL: RxNorm on manufacturedMaterial/code (CONF:1098-7412)
    # OID: None — same rationale as MEDICATIONS ADMINISTERED above
    EntryMatchRule(
        code_xpath=".//hl7:manufacturedMaterial/hl7:code",
        code_system_oid=None,  # intentional — see note above
        translation_xpath=".//hl7:manufacturedMaterial/hl7:code/hl7:translation",
        tier=1,
        preserve_whole_entry=True,
    ),
]


# NOTE:
# PAST MEDICAL HISTORY (11348-0)
# =============================================================================
# IG template: Problem Concern Act (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ']
# * prune level: act/entryRelationship[@typeCode='SUBJ'] (individual problems)
#   typeCode='SUBJ' is a SHALL constraint — safe to filter on
_PAST_MEDICAL_HISTORY_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # TIER 1 — SHALL: SNOMED on value (CONF:1198-9058)
    # ICD-10-CM in translation is MAY (CONF:1198-16750)
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
        tier=1,
    ),
    # TIER 3 — HEURISTIC: ICD-10-CM on value, SNOMED in translation
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
        tier=3,
    ),
]


# NOTE:
# PLAN OF TREATMENT (18776-5)
# =============================================================================
# Heterogeneous entry types — multiple rules with structural precedence.
# Each rule's xpath is scoped to a specific C-CDA templateId so that
# structural precedence correctly separates entry types (observation,
# medication, immunization, procedure) that otherwise share element names.
#
# rule 1 — TIER 1: Planned Observation / Lab Test Order
#   IG template: Planned Observation (V2) (2.16.840.1.113883.10.20.22.4.44)
#   primary code: observation/code SHOULD be LOINC (CONF:1098-31030)
#   eICR trigger: SHALL be from RCTC lab test orders (CONF:3284-336)
#   OID: None — the IG says SHOULD not SHALL, and senders frequently
#   use local/proprietary codes as the primary with no LOINC translation.
#   Accepting any code system here lets the configured code set drive
#   matching rather than enforcing a code system the sender may not use.
#
# rule 2 — TIER 1: Medication Activity
#   IG template: Medication Activity (V2) (2.16.840.1.113883.10.20.22.4.16)
#   Planned Medication Activity (4.42) conforms to 4.16, so this catches both.
#   primary code: manufacturedMaterial/code SHALL be RxNorm (CONF:1098-7412)
#   OID: None — vendor OID variance on this location is high in real documents
#
# rule 3 — TIER 1: Immunization Activity
#   IG template: Immunization Activity (V3) (2.16.840.1.113883.10.20.22.4.52)
#   Planned Immunization Activity (4.120) conforms to 4.52, so this catches both.
#   primary code: manufacturedMaterial/code SHALL be CVX (CONF:1098-9007)
#   translation:  MAY be RxNorm (CONF:1098-31543)
#
# rule 4 — TIER 1: Planned Procedure Activity
#   IG template: Procedure Activity Procedure (V2) (2.16.840.1.113883.10.20.22.4.14)
#   Planned Procedure Activity (4.39) conforms to 4.14.
#   primary code: procedure/code — SNOMED or CPT-4 in practice
#   OID: None — procedure code systems vary widely (SNOMED, CPT-4, local)
#   Note: structural precedence means this only fires on entries that have
#   a procedure/code element but were not claimed by rules 1–3.
#
# rule 5 — TIER 2: Indication (fallback for unclaimed entries)
#   IG template: Indication (V2) (2.16.840.1.113883.10.20.22.4.19)
#   primary code: observation/value — condition name driving the planned item
#   OID: None — indication values appear in SNOMED, ICD-9, and ICD-10 in
#   real documents; restricting to SNOMED_OID caused false negatives
_PLAN_OF_TREATMENT_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # rule 1 — TIER 1: planned observation / lab test order
    # OID: None — see note above; local codes are common as primary
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.44']]"
            "/hl7:code"
        ),
        code_system_oid=None,  # intentional — see note above
        tier=1,
    ),
    # rule 2 — TIER 1: medication activity
    # OID: None — vendor OID variance; see note above
    EntryMatchRule(
        code_xpath=(
            ".//hl7:substanceAdministration"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.16']]"
            "//hl7:manufacturedMaterial/hl7:code"
        ),
        code_system_oid=None,  # intentional — vendor OID variance
        translation_xpath=(
            ".//hl7:substanceAdministration"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.16']]"
            "//hl7:manufacturedMaterial/hl7:code/hl7:translation"
        ),
        tier=1,
    ),
    # rule 3 — TIER 1: immunization activity
    # OID: None — same rationale as standalone immunizations section;
    # code_system_oid=CVX_OID would cause structural precedence to claim
    # the entry and block matching when the sender uses RxNorm as primary
    EntryMatchRule(
        code_xpath=(
            ".//hl7:substanceAdministration"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.52']]"
            "//hl7:manufacturedMaterial/hl7:code"
        ),
        code_system_oid=None,  # intentional — see note above
        translation_xpath=(
            ".//hl7:substanceAdministration"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.52']]"
            "//hl7:manufacturedMaterial/hl7:code/hl7:translation"
        ),
        tier=1,
    ),
    # rule 4 — TIER 1: planned procedure activity procedure
    # targets the Procedure Activity Procedure base template (4.14)
    # which Planned Procedure Activity (4.39) conforms to
    # OID: None — procedure codes use SNOMED or CPT-4 depending on sender
    EntryMatchRule(
        code_xpath=(
            ".//hl7:procedure"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.14']"
            " or hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.39']]"
            "/hl7:code"
        ),
        code_system_oid=None,  # intentional — SNOMED and CPT-4 both observed
        tier=1,
    ),
    # rule 5 — TIER 2: indication value (condition name on Indication observation)
    # catches entries indicated for a matching condition (e.g. a planned
    # procedure or medication ordered because of COVID-19).
    # OID: None — indication values appear in SNOMED, ICD-9, and ICD-10
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.19']]"
            "/hl7:value"
        ),
        code_system_oid=None,  # intentional — multiple code systems observed
        tier=2,
    ),
]


# NOTE:
# PROBLEMS (11450-4)
# =============================================================================
# IG template: Problem Concern Act (V3) wraps Problem Observation (V3)
#   via entryRelationship[@typeCode='SUBJ']
# * prune level: act/entryRelationship[@typeCode='SUBJ'] (individual problems)
#   typeCode='SUBJ' is a SHALL constraint — safe to filter on
_PROBLEM_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # TIER 1 — SHALL: SNOMED on value (CONF:1198-9058)
    # ICD-10-CM in translation is MAY (CONF:1198-16750)
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
        tier=1,
    ),
    # TIER 3 — HEURISTIC: ICD-10-CM on value, SNOMED in translation
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
        tier=3,
    ),
]


# NOTE:
# RESULTS (30954-2)
# =============================================================================
# The Results section has three rules reflecting two distinct RCTC subsets
# defined in the eICR IG for resulted laboratory reports:
#   Lab Obs Test Name subset: trigger is on observation/code (LOINC)
#     — the test name identifies the reportable condition
#   Organism_Substance subset: trigger is on observation/value (SNOMED)
#     — a non-specific test (e.g. general culture) where the result
#       organism/substance name identifies the reportable condition
#
# * these correspond to STU 1.1 Tables 107/108 and STU 3.1.1 Tables 266/267
# * both subsets are valid trigger patterns and both are handled here
#
# > the LOINC-in-translation rule (rule 2) handles the additional pattern
# > where a sender uses a local/proprietary code as the primary code and
# > puts the LOINC trigger code in translation, per CONF:4527-466/467.
#
# rule 1 — TIER 1: LOINC test name on observation/code
#   primary code: observation/code SHOULD be LOINC (CONF:1198-7133)
#   prune level:  organizer/component (individual result observations)
#
# rule 2 — TIER 2: LOINC trigger code in translation
#   IG: code/translation SHOULD carry RCTC trigger when local code
#     used as primary (CONF:4527-466, CONF:4527-467)
#   prune level:  organizer/component
#   note: structural precedence ensures this only fires on entries
#     where rule 1 found no LOINC at the primary code location
#
# rule 3 — TIER 2: organism/substance SNOMED on observation/value
#   IG: value SHOULD be SNOMED for organism/substance triggers
#     (CONF:1198-32610 / STU 3.1.1 Table 267)
#   prune level: organizer/component
#   OID: SNOMED_OID intentionally retained — SNOMED here means
#     organism/substance codes specifically, not generic SNOMED
#     qualifiers (e.g. 260373001 "Detected (qualifier value)")
#   require_value_set_attr: sdtc:valueSet SHALL be present on genuine
#     RCTC trigger code values (CONF:4527-443). Elements without it
#     are plain clinical finding values, not trigger codes. This guard
#     prevents 260373001 "Detected" (no sdtc:valueSet) from matching
#     while still matching 5247005 "Bordetella pertussis" (has
#     sdtc:valueSet when placed as an RCTC trigger value).
_RESULTS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # rule 1 — TIER 1: LOINC test name on observation/code
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.2']]"
            "/hl7:code"
        ),
        code_system_oid=LOINC_OID,
        prune_container_xpath="hl7:organizer/hl7:component",
        tier=1,
    ),
    # rule 2 — TIER 2: LOINC trigger code in translation
    # handles local-code-primary / LOINC-in-translation sender pattern
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.2']]"
            "/hl7:code/hl7:translation"
        ),
        code_system_oid=LOINC_OID,
        prune_container_xpath="hl7:organizer/hl7:component",
        tier=2,
    ),
    # rule 3 — TIER 2: organism/substance SNOMED on observation/value
    # OID and require_value_set_attr both intentional — see note above
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.2']]"
            "/hl7:value[@xsi:type='CD']"
        ),
        code_system_oid=SNOMED_OID,
        require_value_set_attr=True,
        prune_container_xpath="hl7:organizer/hl7:component",
        tier=2,
    ),
]


# NOTE:
# VITAL SIGNS (8716-3)
# =============================================================================
# IG template: Vital Signs Organizer (V3) wraps Vital Sign Observation (V2)
#   via component (CONF:1198-7285, CONF:1198-15946)
# primary code: observation/code SHALL be LOINC from Vital Sign Result Type
#   value set (CONF:1098-7301)
# * prune level:  organizer/component (individual vital sign observations)
_VITAL_SIGNS_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # TIER 1 — SHALL: LOINC on Vital Sign Observation code (CONF:1098-7301)
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.27']]"
            "/hl7:code"
        ),
        code_system_oid=LOINC_OID,
        prune_container_xpath="hl7:organizer/hl7:component",
        tier=1,
    ),
]


# NOTE:
# PROCEDURES (47519-4)
# =============================================================================
# eICR IG defines three trigger code procedure templates, each a specialisation
# of a base C-CDA template:
#   Initial Case Report Trigger Code Procedure Activity Procedure
#     templateId: 2.16.840.1.113883.10.20.15.2.3.44 (eICR, extends 4.14)
#   Initial Case Report Trigger Code Procedure Activity Act
#     templateId: 2.16.840.1.113883.10.20.15.2.3.45 (eICR, extends 4.12)
#   Initial Case Report Trigger Code Procedure Activity Observation
#     templateId: 2.16.840.1.113883.10.20.15.2.3.46 (eICR, extends 4.13)
#
# * all three carry trigger codes on the primary <code> element with
#   sdtc:valueSet present (trigger codes are RCTC-bound per CONF:4482-869).
#   SNOMED is the predominant code system for procedure codes (4.14),
#   though LOINC appears on procedure observations (4.13).
# * preserve_whole_entry=True on all rules: Procedure Activity Procedure (V2)
#   MAY contain Reaction Observation (V2) via entryRelationship[@typeCode='COMP']
#   (CONF:1098-32475) and Medication Activity (V2) via entryRelationship
#   (CONF:1098-7887). Stripping these would lose adverse event and medication
#   context that is clinically meaningful to PHAs.
#
# rule 1 — TIER 1: SNOMED on procedure/code (Procedure Activity Procedure)
#   templateId 2.16.840.1.113883.10.20.15.2.3.44 (eICR trigger code variant)
#   falls back to base template 2.16.840.1.113883.10.20.22.4.14
#
# rule 2 — TIER 1: SNOMED/LOINC on act/code (Procedure Activity Act)
#   templateId 2.16.840.1.113883.10.20.15.2.3.45 (eICR trigger code variant)
#   falls back to base template 2.16.840.1.113883.10.20.22.4.12
#
# rule 3 — TIER 1: LOINC on observation/code (Procedure Activity Observation)
#   templateId 2.16.840.1.113883.10.20.15.2.3.46 (eICR trigger code variant)
#   falls back to base template 2.16.840.1.113883.10.20.22.4.13
#
# OID: None on all rules — the trigger code eICR templates do not mandate
# a single code system for the primary code beyond the sdtc:valueSet binding.
# SNOMED dominates for procedure and act codes; LOINC for observation codes.
# Accepting any code system and letting the configured code set constrain
# matching is safer than guessing OID values that real senders may vary.
_PROCEDURES_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # rule 1 — TIER 1: procedure activity procedure code
    # eICR trigger template (CONF:4482-869 — sdtc:valueSet SHALL be present)
    # falls back to C-CDA base template when eICR template absent
    EntryMatchRule(
        code_xpath=(
            ".//hl7:procedure"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.15.2.3.44']"
            " or hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.14']]"
            "/hl7:code"
        ),
        code_system_oid=None,  # intentional — SNOMED expected but not OID-enforced
        tier=1,
        preserve_whole_entry=True,
    ),
    # rule 2 — TIER 1: procedure activity act code
    EntryMatchRule(
        code_xpath=(
            ".//hl7:act"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.15.2.3.45']"
            " or hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.12']]"
            "/hl7:code"
        ),
        code_system_oid=None,  # intentional — SNOMED/LOINC both observed
        tier=1,
        preserve_whole_entry=True,
    ),
    # rule 3 — TIER 1: procedure activity observation code
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.15.2.3.46']"
            " or hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.13']]"
            "/hl7:code"
        ),
        code_system_oid=None,  # intentional — LOINC expected but not OID-enforced
        tier=1,
        preserve_whole_entry=True,
    ),
]


# NOTE:
# SOCIAL HISTORY (29762-2)
# =============================================================================
# Social History uses T3 heuristic rules — the only section in the catalog
# that does. This is intentional and worth explaining.
#
# Every other section with entry_match_rules has at least one SHALL or SHOULD
# binding in the IG that anchors the rule to a specific templateId and element:
#
#   Problems:      SHALL SNOMED on Problem Observation/value (CONF:1098-31526)
#   Results:       SHOULD LOINC on Result Observation/code (CONF:1198-7133)
#   Immunizations: SHALL CVX on manufacturedMaterial/code (CONF:1098-9007)
#   Vital Signs:   SHALL LOINC on Vital Sign Observation/code (CONF:1098-7301)
#
# Social History has no equivalent anchor. It is a heterogeneous container
# for C-CDA demographic templates, ODH occupational templates, and eICR-specific
# exposure/travel templates. Code systems vary across entries (SNOMED, LOINC,
# PHIN VS, Census, ISO 3166, HL7ActCode). The clinically meaningful code can
# be on observation/code (panel header), observation/value (clinical content),
# or act/code (travel/exposure type) depending entirely on which template the
# entry uses. No single structural pattern covers the section, and no CONF
# citation justifies preferring one xpath over another.
#
# A previous version of these rules used templateId-scoped T1 rules for each
# known Social History template (Travel History, Exposure/Contact, Occupation,
# Country of Residence, Pregnancy). That approach had two problems:
#
# 1. Structural precedence blocking. The templateId-scoped rules claimed
#    entries before the fallback rule could run. A jurisdiction configuring
#    a LOINC panel code (e.g. 21843-8 "Usual Occupation" on observation/code)
#    would get no match because the T1 rule for that template targeted
#    observation/value — found a candidate there, claimed the entry, and
#    the fallback never evaluated observation/code.
#
# 2. No output difference. Every Social History rule uses preserve_whole_entry=True
#    with no prune_container_xpath. Whether the match landed on observation/code,
#    observation/value, or act/code, the output is always the same: the entire
#    entry survives intact. If intra-entry pruning is never performed, there is
#    no benefit to structural precision — the templateId-scoped rules added
#    complexity without adding any value to the output.
#
# Given those two problems, the right model is to scan broadly and let the
# configured code set be the constraint: if any configured code appears
# anywhere in the entry — panel header, clinical content, travel type,
# exposure agent — the whole entry is retained. That is what T3 rules do.
#
# Rule 1 covers observation/code and act/code (structural/panel codes and
# type codes like Travel 420008001). Rule 2 covers observation/value and
# act/value (clinical content codes like Homeless 32911000, country codes
# like GB, occupation codes like Census 3600). Rule 1 will claim most entries
# since code elements are nearly universal; rule 2 fires on entries where
# the only configured code is on a value element and nothing on code matched.
#
# A jurisdiction can configure either the structural panel code or the clinical
# content code and get the same result. This is intentional — the refiner does
# not distinguish between "I want this type of SDH data always" and "I want
# entries with this specific clinical value." Both are valid reasons to retain
# a Social History entry and both produce identical output.
#
# OID: None on both rules. Code system diversity in Social History is too
# broad for OID constraints to be meaningful, and no EHR vendor is consistent
# enough in Social History encoding for OID scoping to be reliable.
_SOCIAL_HISTORY_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # rule 1 — TIER 3: any observation or act code
    EntryMatchRule(
        code_xpath=".//hl7:observation/hl7:code | .//hl7:act/hl7:code",
        code_system_oid=None,
        tier=3,
        preserve_whole_entry=True,
    ),
    # rule 2 — TIER 3: any observation or act value
    # Fallback for entries where the configured code lives on value rather
    # than code — clinical content codes, country codes, occupation codes, etc.
    EntryMatchRule(
        code_xpath=".//hl7:observation/hl7:value | .//hl7:act/hl7:value",
        code_system_oid=None,
        tier=3,
        preserve_whole_entry=True,
    ),
]


# NOTE:
# PREGNANCY SECTION (90767-5)
# =============================================================================
# The dedicated Pregnancy Section was added in eICR STU 3.1.1.
# In STU 1.1 documents pregnancy is recorded in Social History (see rule 6
# in _SOCIAL_HISTORY_MATCH_RULES above). In 3.1.1 it moves here.
#
# rule 1 — TIER 1: Pregnancy Observation (SUPPLEMENTAL PREGNANCY)
#   templateId: 2.16.840.1.113883.10.20.22.4.293 (C-CDA Supplemental Pregnancy)
#   The eICR STU 1.1 base template (15.3.8) is also matched as a fallback
#   for documents that carry the older templateId in this section.
#   match on observation/value — the pregnancy status code lives on value
#   (e.g. 77386006 "Pregnant", 60001007 "Not pregnant", nullFlavor for unknown).
#   observation/code carries ASSERTION which has no condition-grouper relevance.
#
#   preserve_whole_entry=True — the Pregnancy Observation (SUPPLEMENTAL
#   PREGNANCY) template can contain:
#     - Estimated Gestational Age of Pregnancy (CONF:3368 component)
#     - Pregnancy Outcome (CONF:3368 component)
#     - Estimated Date of Delivery (CONF:3368 component)
#     - First Prenatal Visit for this Pregnancy (CONF:3368)
#     - Total Number of Prenatal Care Visits (CONF:3368)
#   All of these are clinically meaningful context that must survive with
#   the matched observation.
#
# OID: None — pregnancy status codes are SNOMED but no OID enforcement needed
# given the templateId scoping already constrains the match location.
_PREGNANCY_MATCH_RULES: Final[list[EntryMatchRule]] = [
    # rule 1 — TIER 1: Pregnancy Observation value
    # targets 3.1.1 SUPPLEMENTAL PREGNANCY templateId with 1.1 base as fallback
    EntryMatchRule(
        code_xpath=(
            ".//hl7:observation"
            "[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.293']"
            " or hl7:templateId[@root='2.16.840.1.113883.10.20.15.3.8']]"
            "/hl7:value"
        ),
        code_system_oid=None,  # intentional — SNOMED pregnancy status codes
        tier=1,
        preserve_whole_entry=True,
    ),
]
