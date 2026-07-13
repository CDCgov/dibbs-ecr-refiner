import re
from typing import Final

import pytest
from lxml import etree

from app.api.validation.file_validation import format_refined_document_or_raise
from app.services.ecr.model import RefinedDocument, ReportableCondition
from app.services.format import format_xml_document_for_display

from .conftest import SCENARIOS_BY_NAME, load_scenario_xml_files
from .harness import refine_one

JURISDICTION: Final[str] = "SDDH"

# section LOINCs (from the refined-eICR section table in REPORT.md)
IMMUNIZATIONS_LOINC: Final[str] = "11369-6"
PROBLEMS_LOINC: Final[str] = "11450-4"
MED_ADMIN_LOINC: Final[str] = "29549-3"
MED_USE_LOINC: Final[str] = "10160-0"
PROCEDURES_LOINC: Final[str] = "47519-4"
VITAL_SIGNS_LOINC: Final[str] = "8716-3"
RESULTS_LOINC: Final[str] = "30954-2"

# Specimen Collection Procedure (ID) …4.415: fixed SNOMED code, organizer-scoped
# shared context that must survive the Results component prune
SPECIMEN_COLLECTION_CODE: Final[str] = "17636008"

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
#      `tests/integration/scenarios/conftest.py`, not duplicated here
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


def _refine(scenario, config, *, configuration_version: int | None = None):  # noqa: ANN001 - RefinementResult, avoid import cycle
    """
    Run the production refinement path for a scenario's config.

    Reads rsg_code / canonical_url / configuration_version off the scenario so
    these stay in lockstep with the snapshot suite. `configuration_version` can
    be overridden for the one test that pins an arbitrary version's rendering.

    Augmentation is seeded by JURISDICTION (the live infra jurisdiction, SDDH),
    not the RR's reportable-to jurisdiction--the same bypass the snapshot
    suite documents. None of these explicit tests assert on augmented document
    identifiers, so the jurisdiction only needs to be internally consistent.
    """

    return refine_one(
        xml_files=load_scenario_xml_files(scenario),
        processed_configuration=config,
        jurisdiction_code=JURISDICTION,
        canonical_url=scenario.canonical_url,
        configuration_version=(
            configuration_version
            if configuration_version is not None
            else scenario.configuration_version
        ),
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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_adding_unrelated_condition_codes_does_not_change_refinement(
    setup,
    build_scenario_configuration,
) -> None:
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

    baseline_scenario = SCENARIOS_BY_NAME["covid_baseline"]
    plus_scenario = SCENARIOS_BY_NAME["covid_plus_unrelated_condition"]

    baseline_config, _ = await build_scenario_configuration(baseline_scenario)
    plus_config, _ = await build_scenario_configuration(plus_scenario)

    added = set(plus_config.codes) - set(baseline_config.codes)
    assert added, (
        "covid_plus_unrelated_condition adds no codes beyond covid_baseline; "
        "this test no longer exercises Roll-up Issue #1 (adding unrelated code "
        "sets). Restore the unrelated codes to the configuration or remove "
        "this test."
    )

    baseline = _refine(baseline_scenario, baseline_config)
    plus = _refine(plus_scenario, plus_config)

    # load-bearing assertion (readable headline): identical size reduction
    assert (
        plus.metrics.eicr.size_reduction_percentage
        == baseline.metrics.eicr.size_reduction_percentage
    ), (
        f"Size reduction diverged: baseline="
        f"{baseline.metrics.eicr.size_reduction_percentage}%, "
        f"covid_plus_unrelated_condition="
        f"{plus.metrics.eicr.size_reduction_percentage}%. Roll-up Issue #1 "
        f"regression: adding codes for a condition absent from the eICR "
        f"({sorted(added)}) changed what was removed. The two must be equal."
    )

    # structural truth: the same clinical entries survive in both documents
    # * compares section/entry id roots, not raw bytes--the two scenarios carry
    # different configuration_version values, which legitimately differ in the
    # provenance footnotes but must not touch the clinical payload
    assert _retained_entry_ids(plus.documents.eicr) == _retained_entry_ids(
        baseline.documents.eicr
    ), (
        "Different clinical entries retained between covid_baseline and "
        "covid_plus_unrelated_condition. Roll-up Issue #1 regression: adding "
        "codes for a condition absent from the eICR changed what survived."
    )
    assert _retained_entry_ids(plus.documents.rr) == _retained_entry_ids(
        baseline.documents.rr
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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_immunization_retained_via_cross_oid_custom_code_match(
    setup,
    build_scenario_configuration,
) -> None:
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

    scenario = SCENARIOS_BY_NAME["covid_with_custom_codes"]
    config, _ = await build_scenario_configuration(scenario)
    xml_files = load_scenario_xml_files(scenario)

    assert CROSS_OID_IMMUNIZATION_CODE in config.codes, (
        f"CVX {CROSS_OID_IMMUNIZATION_CODE} is not in covid_with_custom_codes' "
        f"matchable codes; this test no longer exercises Roll-up Issue #2's "
        f"cross-OID match. Restore the custom code or remove this test."
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

    result = _refine(scenario, config)
    refined_root = etree.fromstring(result.documents.eicr.encode("utf-8"))
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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_custom_code_in_problem_entry_relationship_value_retains_entry(
    setup,
    build_scenario_configuration,
) -> None:
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

    scenario = SCENARIOS_BY_NAME["covid_with_custom_codes"]
    config, _ = await build_scenario_configuration(scenario)
    xml_files = load_scenario_xml_files(scenario)

    assert NESTED_PROBLEM_CODE in config.codes, (
        f"Code {NESTED_PROBLEM_CODE} is not in covid_with_custom_codes' "
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

    result = _refine(scenario, config)
    refined_root = etree.fromstring(result.documents.eicr.encode("utf-8"))
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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_substance_admin_custom_code_retains_one_more_medication_entry_each(
    setup,
    build_scenario_configuration,
) -> None:
    """
    Explicit assertion of Roll-up Issue #4 (substanceAdministration half).

    covid_with_substance_admin_custom_code adds a custom code targeting a
    Medications entry's substanceAdministration/consumable that is outside the
    COVID grouper. Relative to covid_baseline, that entry must be retained:
    Medications Administered and History of Medication Use each gain exactly
    one entry.

    Precondition: the substance-admin config adds codes baseline lacks.
    """

    baseline_scenario = SCENARIOS_BY_NAME["covid_baseline"]
    substance_scenario = SCENARIOS_BY_NAME["covid_with_substance_admin_custom_code"]

    baseline_config, _ = await build_scenario_configuration(baseline_scenario)
    substance_config, _ = await build_scenario_configuration(substance_scenario)

    added = set(substance_config.codes) - set(baseline_config.codes)
    assert added, (
        "covid_with_substance_admin_custom_code adds no codes beyond "
        "covid_baseline; this test no longer exercises Roll-up Issue #4's "
        "substanceAdministration half. Restore the custom code or remove this "
        "test."
    )

    baseline = _refine(baseline_scenario, baseline_config)
    substance = _refine(substance_scenario, substance_config)

    base_root = etree.fromstring(baseline.documents.eicr.encode("utf-8"))
    sub_root = etree.fromstring(substance.documents.eicr.encode("utf-8"))

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
# structural precedence: nausea (SNOMED 422587007) is a configured COVID
# matching code, and the fixture's procedure entries each carry Nausea in an
# entryRelationship--but NOT at an entry-level code/value location
# * the matcher must require a match at an entry-level location, so the procedures
# section is stubbed (0 entries) under covid_baseline


@pytest.mark.integration
@pytest.mark.asyncio
async def test_covid_baseline_does_not_retain_procedures_via_entry_relationship_only_match(
    setup,
    build_scenario_configuration,
) -> None:
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

    scenario = SCENARIOS_BY_NAME["covid_baseline"]
    config, _ = await build_scenario_configuration(scenario)
    xml_files = load_scenario_xml_files(scenario)

    assert NAUSEA_SNOMED in config.codes, (
        f"SNOMED {NAUSEA_SNOMED} (Nausea) is not in covid_baseline's matchable "
        f"codes; this test no longer exercises Roll-up Issue #5 -- a "
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

    result = _refine(scenario, config)
    refined_root = etree.fromstring(result.documents.eicr.encode("utf-8"))
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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_single_vital_sign_code_prunes_panel_to_matched_components(
    setup,
    build_scenario_configuration,
) -> None:
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

    scenario = SCENARIOS_BY_NAME["covid_with_custom_codes"]
    config, _ = await build_scenario_configuration(scenario)
    xml_files = load_scenario_xml_files(scenario)

    assert HEART_RATE_LOINC in config.codes, (
        f"LOINC {HEART_RATE_LOINC} is not in covid_with_custom_codes' matchable "
        f"codes; this test no longer exercises Roll-up Issue #6's single-code "
        f"case. Restore the custom code or remove this test."
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

    result = _refine(scenario, config)
    refined_root = etree.fromstring(result.documents.eicr.encode("utf-8"))
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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_vital_sign_codes_prune_panel_to_matched_components(
    setup,
    build_scenario_configuration,
) -> None:
    """
    Explicit assertion of Roll-up Issue #6 (multiple custom codes).

    covid_with_multi_vital_sign_codes adds three vital-sign codes (8867-4,
    8480-6, 9279-1). After refinement the surviving components must be exactly
    the configured-and-present ones -- those three plus body temperature
    (8310-5, a COVID grouper member) -- and strictly fewer than the source.

    Preconditions mirror the single-code test: all three codes configured, and
    the configured-and-present set is a strict subset of the source panel.
    """

    scenario = SCENARIOS_BY_NAME["covid_with_multi_vital_sign_codes"]
    config, _ = await build_scenario_configuration(scenario)
    xml_files = load_scenario_xml_files(scenario)

    assert MULTI_VITAL_CODES <= set(config.codes), (
        f"Not all of {sorted(MULTI_VITAL_CODES)} are in "
        f"covid_with_multi_vital_sign_codes' matchable codes; this test no "
        f"longer exercises Roll-up Issue #6's multi-code case. Restore the "
        f"custom codes or remove this test."
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

    result = _refine(scenario, config)
    refined_root = etree.fromstring(result.documents.eicr.encode("utf-8"))
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
# intentionally, the Scenario docstring in conftest.py and the scenarios README
# must be updated to match


@pytest.mark.integration
@pytest.mark.asyncio
async def test_configuration_version_is_rendered_into_section_provenance_footnotes(
    setup,
    build_scenario_configuration,
) -> None:
    """
    Documents that configuration_version affects the refined XML.

    configuration_version is rendered into each section's provenance footnote
    ('Config Version' column as 'v{n}'). It is therefore NOT a trace-only
    field: bumping a scenario's configuration_version and regenerating
    snapshots rewrites every section footnote in the XML snapshot.
    """

    scenario = SCENARIOS_BY_NAME["covid_baseline"]
    config, _ = await build_scenario_configuration(scenario)

    version = 42
    result = _refine(scenario, config, configuration_version=version)
    root = etree.fromstring(result.documents.eicr.encode("utf-8"))

    rendered = set(
        root.xpath(
            f".//hl7:footnote//hl7:td[text()='v{version}']/text()",
            namespaces=HL7_NS,
        )
    )
    assert rendered == {f"v{version}"}, (
        f"configuration_version v{version} did not render into any section "
        f"provenance footnote 'Config Version' cell. If this is intentional, "
        f"update the Scenario docstring in conftest.py and the scenarios "
        f"README, which would then be wrong to describe configuration_version's "
        f"relationship to the XML."
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reconstruction_reference_pointers_have_no_surrounding_whitespace(
    setup,
    build_scenario_configuration,
) -> None:
    """
    the minted entry->narrative <reference> is a mixed-content element and must
    serialize without surrounding whitespace (Boone, The CDA Book, ch. 6).

    The pipeline emits the raw product unformatted -- the Lambda writes that to
    S3 and never pretty-prints it -- so the only consumer that indents these
    pointers is the web-app display boundary. Pretty-printing re-wraps the
    pointer into indented mixed content, and `format_refined_document_or_raise`
    must collapse it back. This pins that boundary: the eICR the webapp serves
    and zips, not the raw pipeline bytes.
    """

    scenario = SCENARIOS_BY_NAME["immunizations_reconstruction"]
    config, _ = await build_scenario_configuration(scenario)
    result = _refine(scenario, config)

    # precondition: formatting WITHOUT the compaction step indents the minted
    # pointers. if this stops holding, the boundary compaction is a no-op and
    # this test would pass for the wrong reason.
    assert re.search(
        r'<text>\s+<reference value="#ecr-refiner-11369-6-',
        format_xml_document_for_display(result.documents.eicr),
    ), (
        "expected pretty-printing alone to indent the minted reconstruction "
        "pointers; it did not, so this test no longer guards the boundary "
        "compaction"
    )

    doc = RefinedDocument(
        reportable_condition=ReportableCondition(code="", display_name=""),
        refined_eicr=result.documents.eicr,
        refined_rr=result.documents.rr,
        eicr_size_reduction_percentage=0,
    )
    eicr = format_refined_document_or_raise(doc).refined_eicr

    compact = re.findall(
        r'<text><reference value="#ecr-refiner-11369-6-[^"]*"/></text>', eicr
    )
    assert compact, (
        "expected compact reconstruction reference pointers in the eICR the "
        "display boundary produces; found none (did the boundary compaction run?)"
    )
    # no refiner-minted reference survives in the indented mixed-content form
    assert re.search(r'<text>\s+<reference value="#ecr-refiner-', eicr) is None, (
        "a reconstruction reference serialized with surrounding whitespace at "
        "the display boundary"
    )


# NOTE:
# RESULTS SPECIMEN COLLECTION PROCEDURE -- shared-context carve-out
# =============================================================================
# the Specimen Collection Procedure (…4.415) is an organizer-scoped sibling
# component carrying the specimen collection date / body site / source. it has
# no matchable trigger code, so the component-level prune used to drop it even
# when a result in the same organizer was retained -- silently losing the
# context a PHA keys a case to. this asserts, on the real fixture, that a
# retained reportable result keeps its specimen collection procedure


def _results_specimen_procedures(root: etree._Element) -> list[etree._Element]:
    return root.xpath(
        f".//hl7:section[hl7:code/@code='{RESULTS_LOINC}']"
        f"//hl7:organizer/hl7:component/hl7:procedure"
        f"[hl7:code/@code='{SPECIMEN_COLLECTION_CODE}']",
        namespaces=HL7_NS,
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_results_specimen_collection_procedure_survives_refinement(
    setup,
    build_scenario_configuration,
) -> None:
    """
    A retained reportable result keeps its Specimen Collection Procedure.

    covid_baseline's Results section has an organizer with a matched COVID
    result and a sibling Specimen Collection Procedure (…4.415). After
    refinement the procedure -- with its collection date and target site --
    must survive rather than being pruned as non-matching.

    Precondition: the source really carries the specimen procedure inside the
    Results section (else the fixture drifted and the test is vacuous).
    """

    scenario = SCENARIOS_BY_NAME["covid_baseline"]
    config, _ = await build_scenario_configuration(scenario)

    source_root = etree.fromstring(
        load_scenario_xml_files(scenario).eicr.encode("utf-8")
    )
    source_procs = _results_specimen_procedures(source_root)
    assert source_procs, (
        f"covid_baseline's Results section carries no Specimen Collection "
        f"Procedure (code {SPECIMEN_COLLECTION_CODE}); this test no longer "
        f"exercises the shared-context carve-out. Restore the fixture or remove "
        f"this test."
    )

    result = _refine(scenario, config)
    refined_root = etree.fromstring(result.documents.eicr.encode("utf-8"))
    refined_procs = _results_specimen_procedures(refined_root)

    assert refined_procs, (
        "The Specimen Collection Procedure was pruned from the refined Results "
        "section. The component-level prune dropped an organizer-scoped shared "
        "context sibling alongside a retained result -- the specimen data-loss "
        "regression."
    )

    # the procedure's clinical payload--collection date + body site--is what
    # makes it worth keeping; assert it survived intact, not just the shell
    proc = refined_procs[0]
    assert proc.xpath("hl7:effectiveTime/hl7:low/@value", namespaces=HL7_NS), (
        "specimen procedure retained but its collection date was stripped"
    )
    assert proc.xpath("hl7:targetSiteCode/@code", namespaces=HL7_NS), (
        "specimen procedure retained but its target site (body structure) was stripped"
    )
