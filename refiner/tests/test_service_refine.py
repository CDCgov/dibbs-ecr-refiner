from typing import Any

import pytest
from lxml import etree

from app.core.exceptions import (
    SectionValidationError,
    StructureValidationError,
    XMLValidationError,
)
from app.core.models.types import XMLFiles
from app.services.refine import (
    _create_or_update_text_element,
    _extract_observation_data,
    _find_path_to_entry,
    _get_section_by_code,
    _get_template_id_xpath,
    _process_section,
    _prune_unwanted_siblings,
    get_reportable_conditions,
    refine_eicr,
    validate_sections_to_include,
)

from .conftest import NAMESPACES, TRIGGER_CODE_TEMPLATE_IDS


@pytest.fixture(scope="session")
def xml_test_setup(read_test_xml):
    """
    Setup XML elements for testing section processing."""
    test_message = read_test_xml("mon-mothma-covid-lab-positive_eicr.xml")
    structured_body = test_message.find(".//{urn:hl7-org:v3}structuredBody", NAMESPACES)

    return {
        "structured_body": structured_body,
        "results_section": _get_section_by_code(structured_body, "30954-2"),
        "encounters_section": _get_section_by_code(structured_body, "46240-8"),
        "social_history_section": _get_section_by_code(structured_body, "29762-2"),
    }


@pytest.fixture(scope="session")
def observation_test_data(xml_test_setup) -> dict[str, str | Any | None]:
    """
    Setup observation test data for section processing.
    """

    observation_xpath = (
        # covid test code
        './/hl7:observation[hl7:templateId[@root="2.16.840.1.113883.10.20.15.2.3.2"]] | '
        './/hl7:observation[hl7:code[@code="94310-0"]]'
    )

    # Use direct XPath instead of _get_observations
    observations = xml_test_setup["results_section"].xpath(
        observation_xpath, namespaces=NAMESPACES
    )

    return {
        "xpath": observation_xpath,
        "observations": observations,
        "single_observation": observations[0] if observations else None,
    }


def test_xml_files_container(sample_xml_files: XMLFiles) -> None:
    """
    Verify XMLFiles container has required content.
    """

    assert sample_xml_files.eicr is not None
    assert sample_xml_files.rr is not None


def _get_entries_for_section(
    section: etree.Element,
    namespaces: dict = NAMESPACES,
) -> list[etree.Element]:
    """
    Gets the entries of a section of an eICR.

    Args:
        section: The <section> element to retrieve entries from
        namespaces: The namespaces to use when searching for elements

    Returns:
        list[etree.Element]: List of <entry> elements in the section
    """

    entries = section.xpath(".//hl7:entry", namespaces=namespaces)
    return entries if entries is not None else []


@pytest.mark.parametrize(
    "observation_index,expected_path_length",
    [
        # in the new implementation, _find_path_to_entry returns only the entry element
        (0, 1),
    ],
)
def test_find_path_to_entry(
    observation_test_data, observation_index, expected_path_length
):
    """
    Test finding path from observation to its containing entry.
    """

    observation = observation_test_data["observations"][observation_index]
    entry_element = _find_path_to_entry(observation)

    # verify we got an entry element
    assert entry_element.tag.endswith("entry")

    # instead of checking path length, just verify we got an element
    assert entry_element is not None


@pytest.mark.parametrize(
    "xml_content,xpath,expected_entry_count",
    [
        (
            """
            <section xmlns="urn:hl7-org:v3">
              <entry>
                <organizer>
                  <component>
                    <observation>
                      <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                      <code code="94310-0"/>
                    </observation>
                  </component>
                </organizer>
              </entry>
              <entry>
                <organizer>
                  <component>
                    <observation>
                      <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                      <code code="67890-1"/>
                    </observation>
                  </component>
                </organizer>
              </entry>
            </section>
            """,
            './/hl7:observation[hl7:code/@code="94310-0"]',
            1,
        ),
    ],
)
def test_prune_unwanted_siblings(xml_content, xpath, expected_entry_count):
    """
    Test removal of non-matching sibling entries.
    """

    # parse the XML string into an element
    element = etree.fromstring(xml_content)

    # find matching observations using XPath
    matching_observations = element.xpath(xpath, namespaces=NAMESPACES)
    paths = [_find_path_to_entry(obs) for obs in matching_observations]

    # call with the section element (element is the section in this case)
    _prune_unwanted_siblings(paths, matching_observations, element)

    # verify the result
    remaining_entries = _get_entries_for_section(element)
    assert len(remaining_entries) == expected_entry_count


@pytest.mark.parametrize(
    "observation_index,expected_data",
    [
        (
            0,
            {
                "display_text": "SARS-like Coronavirus N gene [Presence] in Unspecified specimen by NAA with probe detection",
                "code": "94310-0",
                "code_system": "LOINC",
                "is_trigger_code": True,
            },
        ),
    ],
)
def test_extract_observation_data(
    observation_test_data, observation_index, expected_data
):
    """
    Test extraction of observation metadata.
    """

    observation = observation_test_data["observations"][observation_index]
    data = _extract_observation_data(observation)
    assert data == expected_data


def test_create_or_update_text_element(observation_test_data):
    """
    Test creation of text element from observations.
    """

    text_element = _create_or_update_text_element(observation_test_data["observations"])

    # verify basic structure
    assert text_element.tag.endswith("text")
    assert text_element.find(".//table") is not None
    assert text_element.find(".//title") is not None

    # verify content
    table = text_element.find(".//table")
    rows = table.findall(".//tr")
    assert len(rows) > 1  # Header row plus at least one data row

    # verify header
    header = rows[0].findall(".//th")
    expected_headers = [
        "Display Text",
        "Code",
        "Code System",
        "Trigger Code Observation",
    ]
    assert [h.text for h in header] == expected_headers


@pytest.mark.parametrize(
    "sections_to_include,condition_codes,expected_in_results",
    [
        # base case - templateId matching
        (None, None, True),
        # covid-19
        (None, "840539006", True),
        # covid-19 with social history section preserved
        (["29762-2"], "840539006", True),
        # covid-19 with results section preserved
        (["30954-2"], "840539006", True),
    ],
)
def test_refine_eicr(
    sample_xml_files: XMLFiles,
    sections_to_include: list[str] | None,
    condition_codes: str | None,
    expected_in_results: bool,
) -> None:
    """
    Test eICR refinement with various parameters.
    """

    refined_output = refine_eicr(
        xml_files=sample_xml_files,
        sections_to_include=sections_to_include,
        condition_codes=condition_codes,
    )

    refined_doc = etree.fromstring(refined_output)
    refined_structured_body = refined_doc.find(
        ".//{urn:hl7-org:v3}structuredBody", NAMESPACES
    )
    refined_results_section = _get_section_by_code(refined_structured_body, "30954-2")

    xpath_query = ".//hl7:code"
    result = bool(refined_results_section.xpath(xpath_query, namespaces=NAMESPACES))
    assert result == expected_in_results


@pytest.mark.parametrize(
    "xml_files,sections_to_include,condition_codes,expected_error",
    [
        # test 1: invalid section should raise SectionValidationError
        (
            XMLFiles(
                eicr="""
                <ClinicalDocument xmlns="urn:hl7-org:v3">
                    <component>
                        <structuredBody>
                            <component>
                                <section>
                                    <code code="30954-2"/>
                                </section>
                            </component>
                        </structuredBody>
                    </component>
                </ClinicalDocument>
                """,
                rr=None,
            ),
            "invalid-section",  # Pass as string to trigger validate_sections_to_include
            None,
            SectionValidationError,
        ),
        # test 2: invalid XML should raise XMLValidationError
        (
            XMLFiles(eicr="<invalid", rr=None),  # Malformed XML
            None,
            None,
            XMLValidationError,
        ),
        # test 3: empty xml should raise XMLValidationError
        (
            XMLFiles(eicr="", rr=None),  # Empty string
            None,
            None,
            XMLValidationError,
        ),
        # test 4: none xml should raise XMLValidationError
        (
            XMLFiles(eicr=None, rr="<valid/>"),
            None,
            None,
            XMLValidationError,
        ),
    ],
)
def test_refine_eicr_errors(
    xml_files: XMLFiles,
    sections_to_include: str | None,
    condition_codes: str | None,
    expected_error: type[Exception],
) -> None:
    """
    Test error handling in refine_eicr.
    """

    with pytest.raises(expected_error):
        # handle section validation first if needed
        validated_sections = None
        if sections_to_include is not None:
            validated_sections = validate_sections_to_include(sections_to_include)

        # call refine_eicr with validated sections
        refine_eicr(
            xml_files=xml_files,
            sections_to_include=validated_sections,
            condition_codes=condition_codes,
        )


def test_get_reportable_conditions_no_codes():
    """
    Test get_reportable_conditions when no codes are found.
    """

    root = etree.fromstring("""
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <component>
                <section>
                    <code code="55112-7"/>
                </section>
            </component>
        </ClinicalDocument>
    """)
    assert get_reportable_conditions(root) is None


def test_process_section_no_observations():
    """
    Test _process_section when no observations are found.
    """

    section = etree.fromstring("""
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
        </section>
    """)

    # we need to pass a valid XPath expression and template IDs
    _process_section(
        section=section,
        combined_xpath=".//hl7:observation",  # Valid XPath expression
        namespaces={"hl7": "urn:hl7-org:v3"},
    )

    # verify that a text element was created (minimal section)
    text_elem = section.find(".//hl7:text", {"hl7": "urn:hl7-org:v3"})
    assert text_elem is not None

    # verify table with message exists
    table = text_elem.find("table")
    assert table is not None
    assert "Section details have been removed as requested" in table.findtext(".//td")


def test_process_section_with_error():
    """
    Test error handling in _process_section.
    """

    section = etree.fromstring("""
        <section xmlns="urn:hl7-org:v3">
            <code code="invalid"/>
            <entry>
                <observation>
                    <code code="nonexistent"/>
                </observation>
            </entry>
        </section>
    """)

    template_xpath = " | ".join(
        [
            f'.//hl7:observation[hl7:templateId[@root="{tid}"]]'
            for tid in TRIGGER_CODE_TEMPLATE_IDS
        ]
    )

    # Add xpath for the test code if needed
    code_xpath = './/hl7:observation[hl7:code[@code="nonexistent-code"]]'

    # combine them
    combined_xpath = f"{template_xpath} | {code_xpath}"

    _process_section(
        section=section,
        combined_xpath=combined_xpath,
        namespaces=NAMESPACES,
    )

    # verify section still exists and has a text element
    assert section.find("{urn:hl7-org:v3}code") is not None
    assert section.find("{urn:hl7-org:v3}text") is not None

    xpath_query = './/hl7:code[@code="nonexistent-code"]'
    result = section.xpath(xpath_query, namespaces=NAMESPACES)
    assert not result  # Empty list means no elements found


def test_create_or_update_text_invalid_section():
    """
    Test creating text element with invalid section.
    """

    observations = [
        etree.fromstring("""
            <observation xmlns="urn:hl7-org:v3">
                <templateId root="2.16.840.1.113883.10.20.15.2.3.3"/>
                <code code="test" displayName="Test Code" codeSystemName="Test System"/>
            </observation>
        """)
    ]

    text_element = _create_or_update_text_element(observations)
    assert text_element is not None
    assert text_element.tag == "{urn:hl7-org:v3}text"
    assert text_element.find("table") is not None


def test_find_path_to_entry_no_match():
    """
    Test finding path when no match exists.
    """

    observation = etree.fromstring("""
        <observation xmlns="urn:hl7-org:v3">
            <code code="different"/>
        </observation>
    """)

    with pytest.raises(StructureValidationError) as exc_info:
        _find_path_to_entry(observation)
    assert "Parent <entry> element not found" in str(exc_info.value)


def test_get_template_id_xpath():
    """Test generation of XPath for template IDs."""
    template_ids = ["2.16.840.1.113883.10.20.15.2.3.2"]
    xpath = _get_template_id_xpath(template_ids)
    assert (
        './/hl7:observation[hl7:templateId[@root="2.16.840.1.113883.10.20.15.2.3.2"]]'
        == xpath
    )

    # Test with multiple template IDs
    template_ids = [
        "2.16.840.1.113883.10.20.15.2.3.2",
        "2.16.840.1.113883.10.20.15.2.3.3",
    ]
    xpath = _get_template_id_xpath(template_ids)
    assert " | " in xpath
    assert len(xpath.split(" | ")) == 2
