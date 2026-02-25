import pytest
from lxml import etree
from lxml.etree import _Element

from app.services.ecr.models import EICRSpecification
from app.services.ecr.process_eicr import (
    _analyze_trigger_codes_in_context,
    _preserve_relevant_entries_and_generate_summary,
    get_section_by_code,
    get_section_loinc_codes,
    process_section,
)
from app.services.ecr.specification import load_spec

from .conftest import NAMESPACES

# NOTE:
# TEST FIXTURES
# =============================================================================


@pytest.fixture(scope="session")
def eicr_spec_v1_1() -> EICRSpecification:
    """
    Loads the complete eICR v1.1 specification once per session.
    """

    return load_spec("1.1")


@pytest.fixture(scope="session")
def eicr_spec_v3_1_1() -> EICRSpecification:
    """
    Loads the complete eICR v3.1.1 specification once per session.
    """

    return load_spec("3.1.1")


# fixtures for eICR v1.1
@pytest.fixture
def results_section_v1_1(structured_body_v1_1: _Element) -> _Element:
    """
    Provides the 'Results' section from the v1.1 eICR fixture.
    """

    return get_section_by_code(structured_body_v1_1, "30954-2")


@pytest.fixture
def clinical_elements_v1_1(results_section_v1_1: _Element) -> list[_Element]:
    """
    Provides specific clinical elements from the v1.1 'Results' section.
    """

    xpath = './/hl7:observation[hl7:code[@code="94310-0"]]'
    return results_section_v1_1.xpath(xpath, namespaces=NAMESPACES)


# fixtures for eICR v3.1.1
@pytest.fixture
def results_section_v3_1_1(structured_body_v3_1_1: _Element) -> _Element:
    """
    Provides the 'Results' section from the v3.1.1 eICR fixture.
    """

    return get_section_by_code(structured_body_v3_1_1, "30954-2")


# NOTE:
# SECTION PROCESSING TESTS
# =============================================================================


@pytest.mark.parametrize(
    "fixture_name, loinc_code, expected_title",
    [
        ("structured_body_v1_1", "11450-4", "Problem List"),
        ("structured_body_v1_1", "30954-2", "Results"),
        ("structured_body_v3_1_1", "11450-4", "Problems"),
        ("structured_body_v3_1_1", "30954-2", "Results"),
    ],
)
def test_get_section_by_code(
    request, fixture_name: str, loinc_code: str, expected_title: str
):
    """
    Tests that a section can be retrieved by its LOINC code for different eICR versions.
    """

    structured_body: _Element = request.getfixturevalue(fixture_name)
    section = get_section_by_code(structured_body, loinc_code)
    assert section is not None
    assert section.find(".//hl7:title", namespaces=NAMESPACES).text == expected_title


@pytest.mark.parametrize(
    "fixture_name, spec_fixture_name",
    [
        ("structured_body_v1_1", "eicr_spec_v1_1"),
        ("structured_body_v3_1_1", "eicr_spec_v3_1_1"),
    ],
)
def test_get_section_loinc_codes(request, fixture_name: str, spec_fixture_name: str):
    """
    Tests that `get_section_loinc_codes` extracts all expected top-level section codes.
    """

    structured_body: _Element = request.getfixturevalue(fixture_name)
    spec: EICRSpecification = request.getfixturevalue(spec_fixture_name)

    loinc_codes = get_section_loinc_codes(structured_body)
    expected_loinc_codes = set(spec.sections.keys())

    # we only test for codes present in the spec that are also in the document
    assert set(loinc_codes).issubset(expected_loinc_codes)


def test_process_section_no_clinical_elements() -> None:
    """
    Test `process_section` when no matches are found, creating a minimal section.
    """

    section: _Element = etree.fromstring(
        '<section xmlns="urn:hl7-org:v3"><code code="30954-2"/></section>'
    )
    process_section(section=section, combined_xpath="", namespaces=NAMESPACES)
    assert section.get("nullFlavor") == "NI"


def test_process_section_with_matches_v1_1(
    results_section_v1_1: _Element, eicr_spec_v1_1: EICRSpecification
):
    """
    Test the complete `process_section` workflow for v1.1 using a real spec.
    """

    xpath = './/hl7:observation[hl7:code[@code="94310-0"]]'
    results_spec = eicr_spec_v1_1.sections.get("30954-2")

    process_section(
        section=results_section_v1_1,
        combined_xpath=xpath,
        namespaces=NAMESPACES,
        section_specification=results_spec,
        version="1.1",
    )

    assert results_section_v1_1.get("nullFlavor") is None
    final_text = results_section_v1_1.find(".//hl7:text", namespaces=NAMESPACES)
    assert final_text is not None
    assert final_text.find("table") is not None


def test_analyze_trigger_codes_in_context_positive_match_v1_1(
    eicr_spec_v1_1: EICRSpecification,
):
    """
    Test that a real trigger code from the v1.1 spec is correctly identified.
    """

    results_spec = eicr_spec_v1_1.sections["30954-2"]
    trigger_oid = results_spec.trigger_codes[0].oid

    trigger_element = etree.fromstring(
        f'<observation xmlns="urn:hl7-org:v3"><templateId root="{trigger_oid}"/></observation>'
    )
    non_trigger_element = etree.fromstring(
        '<observation xmlns="urn:hl7-org:v3"><code code="regular"/></observation>'
    )

    result = _analyze_trigger_codes_in_context(
        [trigger_element, non_trigger_element], results_spec
    )
    assert result[id(trigger_element)] is True
    assert result[id(non_trigger_element)] is False


def test_preserve_relevant_entries_and_generate_summary(
    results_section_v1_1: _Element, clinical_elements_v1_1: list[_Element]
):
    """
    Test the `_preserve_relevant_entries_and_generate_summary` workflow for v1.1.
    """

    initial_entry_count = len(
        results_section_v1_1.xpath(".//hl7:entry", namespaces=NAMESPACES)
    )
    trigger_analysis = {id(elem): False for elem in clinical_elements_v1_1}

    _preserve_relevant_entries_and_generate_summary(
        section=results_section_v1_1,
        contextual_matches=clinical_elements_v1_1,
        trigger_analysis=trigger_analysis,
        namespaces=NAMESPACES,
    )

    final_entry_count = len(
        results_section_v1_1.xpath(".//hl7:entry", namespaces=NAMESPACES)
    )
    # some entries should be pruned, but not all
    assert 0 < final_entry_count < initial_entry_count
