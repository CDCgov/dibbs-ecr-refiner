import json
from typing import Final

from lxml import etree

from app.core.models.types import XMLFiles
from app.services.terminology import ProcessedConfiguration

from ..fixtures.loader import load_fixture_str
from .harness import refine_one

# NOTE:
# SHARED CONTEXT
# =============================================================================

FIXTURE_DIR: Final[str] = "all_sections_COVID_INFLUENZA"

COVID_BASELINE_CONFIG: Final[str] = "covid_baseline.json"
COVID_CUSTOM_CODES_CONFIG: Final[str] = "covid_with_custom_codes.json"
COVID_PLUS_UNRELATED_CONFIG: Final[str] = "covid_plus_unrelated_condition.json"
COVID_SUBSTANCE_ADMIN_CONFIG: Final[str] = "covid_with_substance_admin_custom_code.json"
COVID_MULTI_VITAL_CONFIG: Final[str] = "covid_with_multi_vital_sign_codes.json"

COVID_RSG_CODE: Final[str] = "840539006"
COVID_CANONICAL_URL: Final[str] = (
    "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
    "07221093-b8a1-4b1d-8678-259277bfba64"
)
JURISDICTION: Final[str] = "SDDH"

# configuration_version per scenario, mirroring the SCENARIOS list in
# test_all_sections_covid_influenza.py
# * recorded on the trace AND rendered into the section provenance footnotes
VERSION_BASELINE: Final[int] = 1
VERSION_CUSTOM_CODES: Final[int] = 3
VERSION_PLUS_UNRELATED: Final[int] = 5
VERSION_SUBSTANCE_ADMIN: Final[int] = 6
VERSION_MULTI_VITAL: Final[int] = 7

# section LOINCs (from the refined-eICR section table in REPORT.md)
IMMUNIZATIONS_LOINC: Final[str] = "11369-6"
PROBLEMS_LOINC: Final[str] = "11450-4"
MED_ADMIN_LOINC: Final[str] = "29549-3"
MED_USE_LOINC: Final[str] = "10160-0"
PROCEDURES_LOINC: Final[str] = "47519-4"
VITAL_SIGNS_LOINC: Final[str] = "8716-3"

# codes under test
CROSS_OID_IMMUNIZATION_CODE: Final[str] = (
    "2563008"  # CVX value, RxNorm-tagged in fixture
)
RXNORM_OID: Final[str] = "2.16.840.1.113883.6.88"
NESTED_PROBLEM_CODE: Final[str] = (
    "10628911000119103"  # in problems entryRelationship/value
)
NAUSEA_SNOMED: Final[str] = (
    "422587007"  # COVID-grouper code, present only in entryRelationship
)
HEART_RATE_LOINC: Final[str] = "8867-4"
MULTI_VITAL_CODES: Final[frozenset[str]] = frozenset({"8867-4", "8480-6", "9279-1"})

HL7_NS: Final[dict[str, str]] = {"hl7": "urn:hl7-org:v3"}


# NOTE:
# EXPLICIT ASSERTIONS FOR THE ROLL-UP ISSUES
# =============================================================================
# each test states one behavior in terms a human (Tim) can read, asserts it
# independently of any committed snapshot, and guards its preconditions so it
# fails diagnostically--rather than passing for the wrong reason--if the
# fixture or configuration drifts out from under it
#
# coverage map:
#  *1  adding unrelated code sets must not remove relevant data
#  *2  immunization match across an OID mismatch (CVX value / RxNorm OID)
#  *4a custom code in a nested entryRelationship/value
#  *4b custom code in a substanceAdministration/consumable
#  *5  procedures NOT retained via an entryRelationship-only match
#  *6  vital-sign panel pruned to its matched sub-components (single + multi)
#
#  *3  (validation) is covered by the `validate_refined_document` fixture in
#      `tests/scenarios/conftest.py`, not duplicated here
#
# plus one invariant pin discovered while tightening these:
# * configuration_version is rendered into the section provenance footnotes,
#   so it DOES affect the refined XML (not only the trace)
#
# key learning baked into #6: the surviving vital-sign sub-components are the
# configured-and-present ones, which is NOT the same as the codes a given
# scenario adds. body temperature (LOINC 8310-5) is a member of the COVID
# condition grouper, so it survives alongside any custom vital-sign codes.


# NOTE:
# HELPERS
# =============================================================================


def _load_xml_files() -> XMLFiles:
    return XMLFiles(
        eicr=load_fixture_str(f"{FIXTURE_DIR}/eICR.xml"),
        rr=load_fixture_str(f"{FIXTURE_DIR}/RR.xml"),
    )


def _load_config(filename: str) -> ProcessedConfiguration:
    return ProcessedConfiguration.from_dict(
        json.loads(load_fixture_str(f"{FIXTURE_DIR}/configurations/{filename}"))
    )


def _refine(config: ProcessedConfiguration, *, configuration_version: int):  # noqa: ANN201 - RefinementResult, avoid import cycle
    return refine_one(
        xml_files=_load_xml_files(),
        processed_configuration=config,
        jurisdiction_code=JURISDICTION,
        rsg_code=COVID_RSG_CODE,
        canonical_url=COVID_CANONICAL_URL,
        configuration_version=configuration_version,
    )


def _entry_count(root: etree._Element, section_loinc: str) -> int:
    return len(
        root.xpath(
            f".//hl7:section[hl7:code/@code='{section_loinc}']/hl7:entry",
            namespaces=HL7_NS,
        )
    )


def _vital_component_codes(root: etree._Element) -> set[str]:
    """
    The set of leaf vital-sign observation codes in the Vital Signs panel.

    The Vital Signs Organizer (V3) (templateId 2.16.840.1.113883.10.20.22.4.26)
    SHALL contain one or more `component`, each containing exactly one Vital
    Sign Observation (V2) (...4.27) -- eICR STU 3.1.1 Vol 2, Vital Signs
    Organizer (V3), CONF:1198-7285 / CONF:1198-15946. Scoping to
    component/observation/code therefore enumerates the leaf vital-sign codes
    and excludes the organizer's own panel code (46680005 / 74728-7).
    """

    return set(
        root.xpath(
            f".//hl7:section[hl7:code/@code='{VITAL_SIGNS_LOINC}']"
            f"//hl7:component/hl7:observation/hl7:code/@code",
            namespaces=HL7_NS,
        )
    )


def _retained_entry_ids(xml: str) -> list[str]:
    """
    Sorted id/@root values inside section entries -- the clinical payload.

    Deliberately scoped to section/entry so it excludes the provenance
    footnotes in section/text (where configuration_version is legitimately
    rendered) and the augmented document/header identifiers. Two refinements
    that retain the same clinical content return equal lists even when their
    provenance metadata differs.
    """

    root = etree.fromstring(xml.encode("utf-8"))
    return sorted(
        root.xpath(".//hl7:section/hl7:entry//hl7:id/@root", namespaces=HL7_NS)
    )


# NOTE:
# ROLL-UP ISSUE #1 -- adding unrelated code sets must not remove content
# =============================================================================
# relational assertion: two refinements of the same fixture must retain the
# same clinical content. each snapshot only pins its own absolute size
# reduction, so a regenerate-while-buggy would lock in divergence silently.
# this asserts the relationship directly -- on the clinical payload, NOT on
# raw bytes, because configuration_version differs between the two scenarios
# and is rendered into the provenance footnotes (see the dedicated pin below)


def test_adding_unrelated_condition_codes_does_not_change_refinement() -> None:
    """
    Explicit assertion of Roll-up Issue #1.

    covid_plus_unrelated_condition adds Fertilizer Poisoning codes on top of
    the baseline COVID set. Those codes match nothing in the fixture, so
    refining with them must produce the same size reduction and the same
    retained clinical entries as covid_baseline. A regression manifests as the
    size reduction climbing above baseline -- adding orthogonal codes removing
    COVID-relevant content, the exact bug the Roll-up sheet flagged.

    Precondition: the plus config is a strict superset of baseline (it actually
    adds codes). If it isn't, the test no longer exercises Issue #1.
    """

    baseline_config = _load_config(COVID_BASELINE_CONFIG)
    plus_config = _load_config(COVID_PLUS_UNRELATED_CONFIG)

    added = set(plus_config.codes) - set(baseline_config.codes)
    assert added, (
        f"{COVID_PLUS_UNRELATED_CONFIG} adds no codes beyond "
        f"{COVID_BASELINE_CONFIG}; this test no longer exercises Roll-up "
        f"Issue #1 (adding unrelated code sets). Restore the unrelated codes "
        f"to the configuration or remove this test."
    )

    baseline = _refine(baseline_config, configuration_version=VERSION_BASELINE)
    plus = _refine(plus_config, configuration_version=VERSION_PLUS_UNRELATED)

    # load-bearing assertion (readable headline): identical size reduction
    assert (
        plus.trace.eicr_size_reduction_percentage
        == baseline.trace.eicr_size_reduction_percentage
    ), (
        f"Size reduction diverged: baseline="
        f"{baseline.trace.eicr_size_reduction_percentage}%, "
        f"covid_plus_unrelated_condition="
        f"{plus.trace.eicr_size_reduction_percentage}%. Roll-up Issue #1 "
        f"regression: adding codes for a condition absent from the eICR "
        f"({sorted(added)}) changed what was removed. The two must be equal."
    )

    # structural truth: the same clinical entries survive in both documents
    # * compares section/entry id roots, not raw bytes--the two scenarios carry
    # different configuration_version values, which legitimately differ in the
    # provenance footnotes but must not touch the clinical payload
    assert _retained_entry_ids(plus.refined_eicr) == _retained_entry_ids(
        baseline.refined_eicr
    ), (
        "Different clinical entries retained between covid_baseline and "
        "covid_plus_unrelated_condition. Roll-up Issue #1 regression: adding "
        "codes for a condition absent from the eICR changed what survived."
    )
    assert _retained_entry_ids(plus.refined_rr) == _retained_entry_ids(
        baseline.refined_rr
    ), (
        "Refined RR clinical entries diverged between the two scenarios; see the eICR assertion above."
    )


# NOTE:
# ROLL-UP ISSUE #2 -- immunization match across an OID mismatch
# =============================================================================
# input -> expected: the fixture tags a CVX code value with the RxNorm OID;
# the config adds the bare code; the matcher must accept the match despite the
# OID disagreement (the matcher does not enforce code-system OIDs at runtime)
# and retain the immunization


def test_immunization_retained_via_cross_oid_custom_code_match() -> None:
    """
    Explicit assertion of Roll-up Issue #2.

    The fixture's Immunizations section carries an entry coded 2563008 (a CVX
    value) but tagged with the RxNorm code-system OID -- a real-world tagging
    inconsistency. covid_with_custom_codes adds 2563008 as a bare custom code;
    the matcher must retain the immunization despite the OID mismatch.

    Preconditions:
      1. 2563008 is in the config's matchable codes.
      2. The fixture's Immunizations section has 2563008 tagged with the
         RxNorm OID (not CVX) -- the mismatch the issue is about is present.

    Assertion: the refined Immunizations section retains an element coded
    2563008. A regression that requires OID agreement drops it.
    """

    config = _load_config(COVID_CUSTOM_CODES_CONFIG)
    xml_files = _load_xml_files()

    assert CROSS_OID_IMMUNIZATION_CODE in config.codes, (
        f"CVX {CROSS_OID_IMMUNIZATION_CODE} is not in "
        f"{COVID_CUSTOM_CODES_CONFIG}'s matchable codes; this test no longer "
        f"exercises Roll-up Issue #2's cross-OID match. Restore the custom "
        f"code or remove this test."
    )

    source_root = etree.fromstring(xml_files.eicr.encode("utf-8"))
    rxnorm_tagged = source_root.xpath(
        f".//hl7:section[hl7:code/@code='{IMMUNIZATIONS_LOINC}']"
        f"//hl7:*[@code='{CROSS_OID_IMMUNIZATION_CODE}' "
        f"and @codeSystem='{RXNORM_OID}']",
        namespaces=HL7_NS,
    )
    assert rxnorm_tagged, (
        f"Source fixture's Immunizations section ({IMMUNIZATIONS_LOINC}) no "
        f"longer has code {CROSS_OID_IMMUNIZATION_CODE} tagged with the RxNorm "
        f"OID ({RXNORM_OID}). The OID mismatch Issue #2 depends on is not in "
        f"the data. Restore the fixture or remove this test."
    )

    result = _refine(config, configuration_version=VERSION_CUSTOM_CODES)
    refined_root = etree.fromstring(result.refined_eicr.encode("utf-8"))
    retained = refined_root.xpath(
        f".//hl7:section[hl7:code/@code='{IMMUNIZATIONS_LOINC}']"
        f"//hl7:*[@code='{CROSS_OID_IMMUNIZATION_CODE}']",
        namespaces=HL7_NS,
    )
    assert retained, (
        f"Refined Immunizations section dropped code "
        f"{CROSS_OID_IMMUNIZATION_CODE}. Roll-up Issue #2 regression: the "
        f"matcher is requiring code-system OID agreement and so misses the "
        f"CVX-value/RxNorm-OID match that covid_with_custom_codes adds. "
        f"Expected the immunization to be retained."
    )


# NOTE:
# ROLL-UP ISSUE #4a -- custom code in a nested entryRelationship/value
# =============================================================================
# input -> expected: the matchable code sits below entry level inside a
# Problem List entry's entryRelationship/observation/value; the matcher must
# reach into that nesting and retain the entry


def test_custom_code_in_problem_entry_relationship_value_retains_entry() -> None:
    """
    Explicit assertion of Roll-up Issue #4 (nested entryRelationship/value half).

    Custom code 10628911000119103 lives in the fixture's Problem List inside
    entryRelationship/observation/value. covid_with_custom_codes adds it; the
    Problem List entry containing that nested code must be retained.

    Preconditions:
      1. 10628911000119103 is in the config's matchable codes.
      2. The fixture has it under a Problem List entry's entryRelationship
         (not at entry level) -- the nesting the issue is about.

    Assertion: the refined Problem List retains the entry containing the
    nested code.
    """

    config = _load_config(COVID_CUSTOM_CODES_CONFIG)
    xml_files = _load_xml_files()

    assert NESTED_PROBLEM_CODE in config.codes, (
        f"Code {NESTED_PROBLEM_CODE} is not in {COVID_CUSTOM_CODES_CONFIG}'s "
        f"matchable codes; this test no longer exercises Roll-up Issue #4's "
        f"nested-value half. Restore the custom code or remove this test."
    )

    source_root = etree.fromstring(xml_files.eicr.encode("utf-8"))
    nested = source_root.xpath(
        f".//hl7:section[hl7:code/@code='{PROBLEMS_LOINC}']"
        f"//hl7:entryRelationship//hl7:*[@code='{NESTED_PROBLEM_CODE}']",
        namespaces=HL7_NS,
    )
    assert nested, (
        f"Source fixture's Problem List ({PROBLEMS_LOINC}) no longer has code "
        f"{NESTED_PROBLEM_CODE} in any entryRelationship. The nested-location "
        f"case of Issue #4 is not in the data. Restore the fixture or remove "
        f"this test."
    )

    result = _refine(config, configuration_version=VERSION_CUSTOM_CODES)
    refined_root = etree.fromstring(result.refined_eicr.encode("utf-8"))
    retained_entries = refined_root.xpath(
        f".//hl7:section[hl7:code/@code='{PROBLEMS_LOINC}']"
        f"/hl7:entry[.//hl7:*[@code='{NESTED_PROBLEM_CODE}']]",
        namespaces=HL7_NS,
    )
    assert retained_entries, (
        f"Refined Problem List retains no entry containing nested code "
        f"{NESTED_PROBLEM_CODE}. Roll-up Issue #4 regression: matching is not "
        f"reaching into entryRelationship/observation/value. Expected the "
        f"entry to survive."
    )


# NOTE:
# ROLL-UP ISSUE #4b -- custom code in a substanceAdministration
# =============================================================================
# relational delta: adding the substance-admin custom code must retain exactly
# the one targeted medication entry in each of the two medication sections
# (Medications Administered and History of Medication Use each +1 vs baseline)
# expressed as a delta so the test states the behavior rather than pinning
# absolute counts, and needs no knowledge of the specific custom code value


def test_substance_admin_custom_code_retains_one_more_medication_entry_each() -> None:
    """
    Explicit assertion of Roll-up Issue #4 (substanceAdministration half).

    covid_with_substance_admin_custom_code adds a custom code targeting a
    Medications entry's substanceAdministration/consumable that is outside the
    COVID grouper. Relative to covid_baseline, that entry must be retained:
    Medications Administered and History of Medication Use each gain exactly
    one entry.

    Precondition: the substance-admin config adds codes baseline lacks.
    """

    baseline_config = _load_config(COVID_BASELINE_CONFIG)
    substance_config = _load_config(COVID_SUBSTANCE_ADMIN_CONFIG)

    added = set(substance_config.codes) - set(baseline_config.codes)
    assert added, (
        f"{COVID_SUBSTANCE_ADMIN_CONFIG} adds no codes beyond "
        f"{COVID_BASELINE_CONFIG}; this test no longer exercises Roll-up "
        f"Issue #4's substanceAdministration half. Restore the custom code or "
        f"remove this test."
    )

    baseline = _refine(baseline_config, configuration_version=VERSION_BASELINE)
    substance = _refine(substance_config, configuration_version=VERSION_SUBSTANCE_ADMIN)

    base_root = etree.fromstring(baseline.refined_eicr.encode("utf-8"))
    sub_root = etree.fromstring(substance.refined_eicr.encode("utf-8"))

    for loinc, label in (
        (MED_ADMIN_LOINC, "Medications Administered"),
        (MED_USE_LOINC, "History of Medication Use"),
    ):
        base_n = _entry_count(base_root, loinc)
        sub_n = _entry_count(sub_root, loinc)
        assert sub_n - base_n == 1, (
            f"{label} ({loinc}) entry count changed by {sub_n - base_n} "
            f"(baseline={base_n}, with substance-admin custom code={sub_n}); "
            f"expected exactly +1. Roll-up Issue #4 regression: the custom "
            f"code targeting substanceAdministration/consumable is not "
            f"retaining its one medication entry as expected."
        )


# NOTE:
# ROLL-UP ISSUE #5 -- procedures NOT retained via entryRelationship-only match
# =============================================================================
# RECONSTRUCTED FROM README -- this block restates the behavior the README
# attributes to `test_covid_baseline_does_not_retain_procedures_via_entry_
# relationship_only_match`. Reconcile with the committed version: if your file
# already defines this test, keep yours and delete this block (or vice versa)
# * the XPaths below encode the README's description of the fixture; adjust if
# the fixture's Procedures statements nest Nausea differently.
#
# structural precedence: nausea (SNOMED 422587007) is a configured COVID
# matching code, and the fixture's procedure entries each carry Nausea in an
# entryRelationship--but NOT at an entry-level code/value location
# * the matcher must require a match at an entry-level location, so the procedures
# section is stubbed (0 entries) under covid_baseline


def test_covid_baseline_does_not_retain_procedures_via_entry_relationship_only_match() -> (
    None
):
    """
    Explicit assertion of Roll-up Issue #5 (negative case).

    The fixture's Procedures section entries carry Nausea (SNOMED 422587007),
    a configured COVID matching code, only inside an entryRelationship -- never
    as the procedure's own entry-level code/value. covid_baseline must stub the
    Procedures section at 0 entries: an entryRelationship-only match does not
    justify retaining the entry.

    Preconditions:
      1. 422587007 is in covid_baseline's matchable codes (so a buggy
         entry-anywhere matcher WOULD retain the procedures).
      2. The fixture's Procedures section has at least one entry carrying
         422587007 in an entryRelationship.
      3. No Procedures entry carries 422587007 at an entry-level code/value
         location -- otherwise the test isn't exercising the entryRelationship-
         only case.

    Assertion: the refined Procedures section has 0 entries.
    """

    config = _load_config(COVID_BASELINE_CONFIG)
    xml_files = _load_xml_files()

    assert NAUSEA_SNOMED in config.codes, (
        f"SNOMED {NAUSEA_SNOMED} (Nausea) is not in {COVID_BASELINE_CONFIG}'s "
        f"matchable codes; this test no longer exercises Roll-up Issue #5 -- a "
        f"non-configured code cannot demonstrate the entryRelationship-only "
        f"guard. Restore the code or remove this test."
    )

    source_root = etree.fromstring(xml_files.eicr.encode("utf-8"))

    proc_entries = source_root.xpath(
        f".//hl7:section[hl7:code/@code='{PROCEDURES_LOINC}']/hl7:entry",
        namespaces=HL7_NS,
    )
    assert proc_entries, (
        f"Source fixture's Procedures section ({PROCEDURES_LOINC}) has no "
        f"entries; there is nothing for the entryRelationship-only guard to act "
        f"on. Restore the fixture or remove this test."
    )

    nausea_in_entry_relationship = source_root.xpath(
        f".//hl7:section[hl7:code/@code='{PROCEDURES_LOINC}']"
        f"/hl7:entry[.//hl7:entryRelationship//hl7:*[@code='{NAUSEA_SNOMED}']]",
        namespaces=HL7_NS,
    )
    assert nausea_in_entry_relationship, (
        f"No Procedures entry carries {NAUSEA_SNOMED} in an entryRelationship. "
        f"The entryRelationship-only case Issue #5 depends on is not in the "
        f"data, so a passing test would be vacuous. Restore the fixture or "
        f"remove this test."
    )

    nausea_at_entry_level = source_root.xpath(
        f".//hl7:section[hl7:code/@code='{PROCEDURES_LOINC}']"
        f"/hl7:entry/*[hl7:code/@code='{NAUSEA_SNOMED}' "
        f"or hl7:value/@code='{NAUSEA_SNOMED}']",
        namespaces=HL7_NS,
    )
    assert not nausea_at_entry_level, (
        f"A Procedures entry carries {NAUSEA_SNOMED} at an entry-level "
        f"code/value location. That is a legitimate match, so retaining the "
        f"entry would be correct and this test would not be exercising the "
        f"entryRelationship-only guard. Fix the fixture or remove this test."
    )

    result = _refine(config, configuration_version=VERSION_BASELINE)
    refined_root = etree.fromstring(result.refined_eicr.encode("utf-8"))
    assert _entry_count(refined_root, PROCEDURES_LOINC) == 0, (
        f"Refined Procedures section ({PROCEDURES_LOINC}) retained "
        f"{_entry_count(refined_root, PROCEDURES_LOINC)} entries; expected 0. "
        f"Roll-up Issue #5 regression: a match found only in an "
        f"entryRelationship is being treated as an entry-level match, so "
        f"procedures with no condition-specific code are retained."
    )


# NOTE:
# ROLL-UP ISSUE #6 -- vital-sign panel pruned to matched sub-components
# =============================================================================
# input -> expected. the EXPECTED retained component set is derived from the
# configuration, NOT hard-coded: it is the configured codes that are actually
# present in the source panel. this matters because body temperature
# (LOINC 8310-5) is a member of the COVID condition grouper, so it survives
# alongside any custom vital-sign codes -- the panel-pruning property is "keep
# the configured-and-present components, drop the rest", not "keep only the
# custom code". the strict-subset assertion guards the original bug: a "whole
# panel returned on any match" regression would leave all nine components.


def test_single_vital_sign_code_prunes_panel_to_matched_components() -> None:
    """
    Explicit assertion of Roll-up Issue #6 (single custom code).

    covid_with_custom_codes adds Heart Rate (LOINC 8867-4) as the only custom
    vital-sign code. The fixture's Vital Signs panel has several sub-component
    observations; after refinement the surviving components must be exactly the
    configured-and-present ones -- Heart Rate plus body temperature (8310-5,
    already a COVID grouper member) -- and strictly fewer than the source.

    Preconditions:
      1. 8867-4 is in the config's matchable codes.
      2. The configured-and-present set is a strict subset of the source panel
         (i.e. there is a panel to prune) and includes 8867-4.
    """

    config = _load_config(COVID_CUSTOM_CODES_CONFIG)
    xml_files = _load_xml_files()

    assert HEART_RATE_LOINC in config.codes, (
        f"LOINC {HEART_RATE_LOINC} is not in {COVID_CUSTOM_CODES_CONFIG}'s "
        f"matchable codes; this test no longer exercises Roll-up Issue #6's "
        f"single-code case. Restore the custom code or remove this test."
    )

    source_root = etree.fromstring(xml_files.eicr.encode("utf-8"))
    source_codes = _vital_component_codes(source_root)

    # expected survivors = configured codes that are actually in the panel.
    # NOTE: this is intentionally NOT {8867-4}. Body temperature (8310-5) is a
    # COVID condition-grouper member, so it survives too.
    expected = source_codes & set(config.codes)
    assert HEART_RATE_LOINC in expected and len(expected) < len(source_codes), (
        f"Fixture/config no longer set up to exercise panel pruning: source="
        f"{sorted(source_codes)}, configured-and-present={sorted(expected)}. "
        f"Need the custom code present and at least one component to prune. "
        f"Restore the fixture/config or remove this test."
    )

    result = _refine(config, configuration_version=VERSION_CUSTOM_CODES)
    refined_root = etree.fromstring(result.refined_eicr.encode("utf-8"))
    retained = _vital_component_codes(refined_root)

    assert retained == expected, (
        f"Refined Vital Signs panel retained {sorted(retained)}; expected "
        f"{sorted(expected)} (configured codes present in the source panel). "
        f"Roll-up Issue #6 regression: the panel is not pruned to its matched "
        f"sub-components (source panel had {len(source_codes)})."
    )
    assert retained < source_codes, (
        f"No pruning occurred -- retained == source ({sorted(retained)}). A "
        f"'whole panel returned on any match' regression looks exactly like "
        f"this."
    )


def test_multiple_vital_sign_codes_prune_panel_to_matched_components() -> None:
    """
    Explicit assertion of Roll-up Issue #6 (multiple custom codes).

    covid_with_multi_vital_sign_codes adds three vital-sign codes (8867-4,
    8480-6, 9279-1). After refinement the surviving components must be exactly
    the configured-and-present ones -- those three plus body temperature
    (8310-5, a COVID grouper member) -- and strictly fewer than the source.

    Preconditions mirror the single-code test: all three codes configured, and
    the configured-and-present set is a strict subset of the source panel.
    """

    config = _load_config(COVID_MULTI_VITAL_CONFIG)
    xml_files = _load_xml_files()

    assert MULTI_VITAL_CODES <= set(config.codes), (
        f"Not all of {sorted(MULTI_VITAL_CODES)} are in "
        f"{COVID_MULTI_VITAL_CONFIG}'s matchable codes; this test no longer "
        f"exercises Roll-up Issue #6's multi-code case. Restore the custom "
        f"codes or remove this test."
    )

    source_root = etree.fromstring(xml_files.eicr.encode("utf-8"))
    source_codes = _vital_component_codes(source_root)

    expected = source_codes & set(config.codes)
    assert MULTI_VITAL_CODES <= expected and len(expected) < len(source_codes), (
        f"Fixture/config no longer set up to exercise panel pruning: source="
        f"{sorted(source_codes)}, configured-and-present={sorted(expected)}. "
        f"Need all custom codes present and at least one component to prune. "
        f"Restore the fixture/config or remove this test."
    )

    result = _refine(config, configuration_version=VERSION_MULTI_VITAL)
    refined_root = etree.fromstring(result.refined_eicr.encode("utf-8"))
    retained = _vital_component_codes(refined_root)

    assert retained == expected, (
        f"Refined Vital Signs panel retained {sorted(retained)}; expected "
        f"{sorted(expected)} (configured codes present in the source panel). "
        f"Roll-up Issue #6 regression: the panel is not pruned to its matched "
        f"sub-components (source panel had {len(source_codes)})."
    )
    assert retained < source_codes, (
        f"No pruning occurred -- retained == source ({sorted(retained)}). A "
        f"'whole panel returned on any match' regression looks exactly like "
        f"this."
    )


# NOTE:
# INVARIANT PIN -- configuration_version is rendered into the refined XML
# =============================================================================
# discovered while tightening Issue #1: configuration_version appears in each
# section's provenance footnote ('Config Version' column), so it affects the
# refined XML, not only the trace. pinning it converts the surprise into a
# readable failure: a future change to footnote rendering fails here with a
# clear message rather than as an opaque XML snapshot diff. if this ever fails
# intentionally, the Scenario docstring in test_all_sections_covid_influenza.py
# and the scenarios README must be updated to match


def test_configuration_version_is_rendered_into_section_provenance_footnotes() -> None:
    """
    Documents that configuration_version affects the refined XML.

    configuration_version is rendered into each section's provenance footnote
    ('Config Version' column as 'v{n}'). It is therefore NOT a trace-only
    field: bumping a scenario's configuration_version and regenerating
    snapshots rewrites every section footnote in the XML snapshot.
    """

    version = 42
    result = _refine(_load_config(COVID_BASELINE_CONFIG), configuration_version=version)
    root = etree.fromstring(result.refined_eicr.encode("utf-8"))

    rendered = set(
        root.xpath(
            f".//hl7:footnote//hl7:td[text()='v{version}']/text()",
            namespaces=HL7_NS,
        )
    )
    assert rendered == {f"v{version}"}, (
        f"configuration_version v{version} did not render into any section "
        f"provenance footnote 'Config Version' cell. If this is intentional, "
        f"update the Scenario docstring in test_all_sections_covid_influenza.py "
        f"and the scenarios README, which would then be wrong to describe "
        f"configuration_version's relationship to the XML."
    )
