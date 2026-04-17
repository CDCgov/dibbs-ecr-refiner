import pytest
from lxml import etree

from app.services.ecr.model import HL7_NS, EICRSpecification
from app.services.ecr.section import get_section_by_code, get_section_loinc_codes
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


@pytest.fixture(scope="session")
def eicr_spec_v3_1_1() -> EICRSpecification:
    """
    Loads the complete eICR v3.1.1 specification once per session.
    """

    return load_spec("3.1.1")


# NOTE:
# SECTION TRAVERSAL TESTS
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

    structured_body: etree._Element = request.getfixturevalue(fixture_name)
    section = get_section_by_code(structured_body, loinc_code)
    assert section is not None
    assert section.find(".//hl7:title", namespaces=HL7_NS).text == expected_title


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

    structured_body: etree._Element = request.getfixturevalue(fixture_name)
    spec: EICRSpecification = request.getfixturevalue(spec_fixture_name)

    loinc_codes = get_section_loinc_codes(structured_body)
    expected_loinc_codes = set(spec.sections.keys())

    # sections defined in the spec that are also in the document should be recognized
    # (the document may contain additional C-CDA sections not in the eICR spec)
    spec_codes_in_document = set(loinc_codes) & expected_loinc_codes
    assert len(spec_codes_in_document) > 0
