import pytest
from lxml import etree

from app.services.ecr.model import HL7_NS, EICRSpecification
from app.services.ecr.section import get_section_by_code, process_section
from app.services.ecr.section.generic_matching import _preserve_relevant_entries
from app.services.ecr.specification import load_spec

# NOTE:
# SESSION-SCOPED SPEC FIXTURES
# =============================================================================
# load_spec assembles dicts from in-memory data, so re-loading per test is
# cheap, but session scope keeps the test output free of repeated setup.


@pytest.fixture(scope="session")
def eicr_spec_v1_1() -> EICRSpecification:
    """
    Loads the complete eICR v1.1 specification once per session.
    """

    return load_spec("1.1")


# NOTE:
# FUNCTION-SCOPED SECTION FIXTURES
# =============================================================================
# pulled from the v1.1 structured body so each test gets a fresh mutable
# section to work with.


@pytest.fixture
def results_section_v1_1(structured_body_v1_1: etree._Element) -> etree._Element:
    """
    Provides the 'Results' section from the v1.1 eICR fixture.
    """

    return get_section_by_code(structured_body_v1_1, "30954-2")


@pytest.fixture
def clinical_elements_v1_1(
    results_section_v1_1: etree._Element,
) -> list[etree._Element]:
    """
    Provides specific clinical elements from the v1.1 'Results' section.

    Returns observations carrying LOINC code 94533-7, used to exercise
    entry preservation logic.
    """

    xpath = './/hl7:observation[hl7:code[@code="94533-7"]]'
    return results_section_v1_1.xpath(xpath, namespaces=HL7_NS)


# NOTE:
# GENERIC MATCHING TESTS
# =============================================================================
# the generic engine is the unscoped fallback path. tests here exercise it
# directly via process_section without supplying code_system_sets — the
# dispatcher routes to the generic engine when code_system_sets is None or
# when the section has no entry match rules.


def test_process_section_no_clinical_elements() -> None:
    """
    Test `process_section` when no matches are found, creating a minimal section.

    Builds a tiny synthetic section so the test doesn't depend on fixture
    contents — useful as a smoke test of the no-match policy override:
    when codes_to_match is empty, the generic engine stubs the section
    with nullFlavor="NI" regardless of the section's contents.
    """

    section: etree._Element = etree.fromstring(
        '<section xmlns="urn:hl7-org:v3"><code code="30954-2"/></section>'
    )
    process_section(
        section=section,
        codes_to_match=set(),
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    assert section.get("nullFlavor") == "NI"


def test_process_section_routes_to_generic_when_code_system_sets_missing_v1_1(
    results_section_v1_1: etree._Element, eicr_spec_v1_1: EICRSpecification
):
    """
    Test that the dispatcher routes to the generic engine when
    code_system_sets is None, even for sections with entry match rules.

    The Results section has entry_match_rules in the spec, but without
    code_system_sets the dispatcher cannot use the section-aware engine
    and falls back to generic matching. With a non-matching code set,
    the section is reduced to nullFlavor="NI".
    """

    results_spec = eicr_spec_v1_1.sections.get("30954-2")

    process_section(
        section=results_section_v1_1,
        codes_to_match={"94310-0"},
        namespaces=HL7_NS,
        section_specification=results_spec,
        code_system_sets=None,
    )

    assert results_section_v1_1.get("nullFlavor") == "NI"


def test_preserve_relevant_entries(
    results_section_v1_1: etree._Element,
    clinical_elements_v1_1: list[etree._Element],
):
    """
    Test the `_preserve_relevant_entries` workflow for v1.1.

    Given a real Results section and a set of contextual matches,
    `_preserve_relevant_entries` should keep the entries that contain
    the matched elements and remove the rest. Tests the engine's
    private helper directly because the entry preservation logic is
    independent of the rest of the matching pipeline.
    """

    initial_entry_count = len(
        results_section_v1_1.xpath(".//hl7:entry", namespaces=HL7_NS)
    )

    _preserve_relevant_entries(
        section=results_section_v1_1,
        contextual_matches=clinical_elements_v1_1,
    )

    final_entry_count = len(
        results_section_v1_1.xpath(".//hl7:entry", namespaces=HL7_NS)
    )
    # some entries should be pruned, but not all
    assert 0 < final_entry_count < initial_entry_count
