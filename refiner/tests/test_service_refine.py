from typing import Any

import pytest
from lxml import etree

from app.core.exceptions import (
    ConditionCodeError,
    StructureValidationError,
)
from app.core.models.types import XMLFiles
from app.services.refine import (
    MINIMAL_SECTION_MESSAGE,
    OBSERVATION_TABLE_HEADERS,
    REFINER_OUTPUT_TITLE,
    _create_or_update_text_element,
    _extract_observation_data,
    _find_path_to_entry,
    _get_section_by_code,
    _process_section,
    _prune_unwanted_siblings,
    build_condition_eicr_pairs,
    get_reportable_conditions,
    refine_eicr,
)

from .conftest import NAMESPACES


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

    # Use a simple XPath to find observations with specific codes
    observation_xpath = './/hl7:observation[hl7:code[@code="94310-0"]]'

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
                      <code code="94310-0"/>
                    </observation>
                  </component>
                </organizer>
              </entry>
              <entry>
                <organizer>
                  <component>
                    <observation>
                      <code code="67890-1"/>
                    </observation>
                  </component>
                </organizer>
              </entry>
            </section>
            """,
            './/hl7:observation[hl7:code[@code="94310-0"]]',
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
                "is_trigger_code": False,  # Always False now
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

    # verify title contains expected text
    title = text_element.find(".//title")
    assert title.text == REFINER_OUTPUT_TITLE

    # verify content
    table = text_element.find(".//table")
    rows = table.findall(".//tr")
    assert len(rows) > 1  # Header row plus at least one data row

    # verify header uses new constants
    header = rows[0].findall(".//th")
    assert [h.text for h in header] == OBSERVATION_TABLE_HEADERS


@pytest.mark.parametrize(
    "sections_to_include,condition_codes,expected_in_results",
    [
        # happy-path: must always provide condition_codes
        (None, "840539006", True),
        (["29762-2"], "840539006", True),
        (["30954-2"], "840539006", True),
    ],
)
def test_refine_eicr(
    sample_xml_files: XMLFiles,
    sections_to_include,
    condition_codes,
    expected_in_results,
):
    """
    Test eICR refinement with required condition_codes.
    """
    refined_output = refine_eicr(
        xml_files=sample_xml_files,
        sections_to_include=sections_to_include,
        condition_codes=condition_codes,
    )

    refined_doc = etree.fromstring(refined_output)
    refined_structured_body = refined_doc.find(
        ".//{urn:hl7-org:v3}structuredBody", {"hl7": "urn:hl7-org:v3"}
    )
    refined_results_section = _get_section_by_code(refined_structured_body, "30954-2")

    xpath_query = ".//hl7:code"
    result = bool(
        refined_results_section.xpath(xpath_query, namespaces={"hl7": "urn:hl7-org:v3"})
    )
    assert result == expected_in_results


def test_refine_eicr_requires_condition_codes(sample_xml_files: XMLFiles):
    """
    Test that refine_eicr raises ConditionCodeError if condition_codes is not provided.
    """
    with pytest.raises(ConditionCodeError) as excinfo:
        refine_eicr(
            xml_files=sample_xml_files,
            sections_to_include=None,
            condition_codes=None,
        )
    assert "No condition codes provided" in str(excinfo.value)


def test_refine_eicr_empty_condition_codes(sample_xml_files: XMLFiles):
    """
    Test that refine_eicr raises ConditionCodeError if condition_codes is empty string.
    """
    with pytest.raises(ConditionCodeError) as excinfo:
        refine_eicr(
            xml_files=sample_xml_files,
            sections_to_include=None,
            condition_codes="",
        )
    assert "No condition codes provided" in str(excinfo.value)


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

    with pytest.raises(StructureValidationError) as exc_info:
        get_reportable_conditions(root)

    assert "Missing required RR11 Coded Information Organizer" in str(exc_info.value)


def test_get_reportable_conditions_uniqueness():
    """
    Test that get_reportable_conditions returns unique conditions only.
    Uses sample RR with duplicate reportable conditions to verify deduplication.
    """

    root = etree.fromstring("""
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <component>
                <section>
                    <code code="55112-7"/>
                    <entry>
                        <organizer>
                            <code code="RR11"/>
                            <!-- First occurrence of condition -->
                            <component>
                                <observation>
                                    <templateId root="2.16.840.1.113883.10.20.15.2.3.12"/>
                                    <value codeSystem="2.16.840.1.113883.6.96"
                                          code="840539006"
                                          displayName="COVID-19"/>
                                    <entryRelationship>
                                        <observation>
                                            <code code="RR1"/>
                                            <value code="RRVS1"/>
                                        </observation>
                                    </entryRelationship>
                                </observation>
                            </component>
                            <!-- Duplicate condition -->
                            <component>
                                <observation>
                                    <templateId root="2.16.840.1.113883.10.20.15.2.3.12"/>
                                    <value codeSystem="2.16.840.1.113883.6.96"
                                          code="840539006"
                                          displayName="COVID-19"/>
                                    <entryRelationship>
                                        <observation>
                                            <code code="RR1"/>
                                            <value code="RRVS1"/>
                                        </observation>
                                    </entryRelationship>
                                </observation>
                            </component>
                            <!-- Different condition -->
                            <component>
                                <observation>
                                    <templateId root="2.16.840.1.113883.10.20.15.2.3.12"/>
                                    <value codeSystem="2.16.840.1.113883.6.96"
                                          code="27836007"
                                          displayName="Pertussis"/>
                                    <entryRelationship>
                                        <observation>
                                            <code code="RR1"/>
                                            <value code="RRVS1"/>
                                        </observation>
                                    </entryRelationship>
                                </observation>
                            </component>
                        </organizer>
                    </entry>
                </section>
            </component>
        </ClinicalDocument>
    """)

    result = get_reportable_conditions(root)

    # verify we get exactly 2 unique conditions
    assert len(result) == 2

    # verify the specific conditions are present
    expected_conditions = [
        {"code": "840539006", "displayName": "COVID-19"},
        {"code": "27836007", "displayName": "Pertussis"},
    ]
    assert result == expected_conditions


def test_get_reportable_conditions_empty_rr11():
    """
    Test that RR11 organizer with no qualifying observations returns None.
    """

    root = etree.fromstring("""
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <component>
                <section>
                    <code code="55112-7"/>
                    <entry>
                        <organizer>
                            <code code="RR11"/>
                            <!-- Empty RR11 organizer -->
                        </organizer>
                    </entry>
                </section>
            </component>
        </ClinicalDocument>
    """)

    result = get_reportable_conditions(root)
    assert result is None


def test_process_section_no_observations():
    """
    Test _process_section when no observations are found.
    """

    section = etree.fromstring("""
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
        </section>
    """)

    # Pass empty XPath since no condition codes provided
    _process_section(
        section=section,
        combined_xpath="",  # Empty XPath means no condition codes
        namespaces={"hl7": "urn:hl7-org:v3"},
    )

    # verify that a text element was created (minimal section)
    text_elem = section.find(".//hl7:text", {"hl7": "urn:hl7-org:v3"})
    assert text_elem is not None

    # verify table with message exists
    table = text_elem.find("table")
    assert table is not None
    assert MINIMAL_SECTION_MESSAGE in table.findtext(".//td")

    # verify section has nullFlavor="NI"
    assert section.get("nullFlavor") == "NI"


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

    # Use a valid XPath that won't match anything
    combined_xpath = './/hl7:observation[hl7:code[@code="nonexistent-code"]]'

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


def test_build_condition_eicr_pairs(sample_xml_files: XMLFiles):
    """
    Test building condition-eICR pairs with XMLFiles objects.
    """

    reportable_conditions = [
        {"code": "840539006", "displayName": "COVID-19"},
        {"code": "27836007", "displayName": "Pertussis"},
    ]

    pairs = build_condition_eicr_pairs(sample_xml_files, reportable_conditions)

    # verify we get the expected number of pairs
    assert len(pairs) == 2

    # verify each pair has the expected structure
    for i, pair in enumerate(pairs):
        assert "reportable_condition" in pair
        assert "xml_files" in pair  # Changed from "eicr_copy"
        assert pair["reportable_condition"] == reportable_conditions[i]

        # verify the xml_files is a proper XMLFiles object
        assert isinstance(pair["xml_files"], XMLFiles)
        assert pair["xml_files"].eicr == sample_xml_files.eicr
        assert pair["xml_files"].rr == sample_xml_files.rr


def test_text_constants():
    """
    Test that our text constants are properly defined and accessible.
    """

    assert (
        REFINER_OUTPUT_TITLE
        == "Output from CDC PRIME DIBBs eCR Refiner application by request of STLT"
    )
    assert MINIMAL_SECTION_MESSAGE == "Section details have been removed as requested"
    assert OBSERVATION_TABLE_HEADERS == [
        "Display Text",
        "Code",
        "Code System",
        "Matching Condition Code",
    ]
