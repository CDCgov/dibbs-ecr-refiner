from typing import Any

import pytest
from lxml import etree
from lxml.etree import _Element

from app.core.exceptions import (
    StructureValidationError,
    XMLParsingError,
)
from app.core.models.types import XMLFiles
from app.services.refiner.refine import (
    CLINICAL_DATA_TABLE_HEADERS,
    MINIMAL_SECTION_MESSAGE,
    REFINER_OUTPUT_TITLE,
    _analyze_trigger_codes_in_context,
    _create_or_update_text_element,
    _extract_clinical_data,
    _find_condition_relevant_elements,
    _find_path_to_entry,
    _get_section_by_code,
    _preserve_relevant_entries_and_generate_summary,
    _process_section,
    _prune_unwanted_siblings,
    build_condition_eicr_pairs,
    get_reportable_conditions,
    refine_eicr,
)

from .conftest import NAMESPACES

# NOTE:
# TEST FIXTURES AND SETUP


@pytest.fixture(scope="session")
def xml_test_setup(read_test_xml) -> dict[str, Any | _Element | None]:
    """
    Setup XML elements for testing section processing.
    """

    test_message: Any = read_test_xml("mon-mothma-covid-lab-positive_eicr.xml")
    structured_body: Any = test_message.find(
        ".//{urn:hl7-org:v3}structuredBody", NAMESPACES
    )

    return {
        "structured_body": structured_body,
        "results_section": _get_section_by_code(structured_body, "30954-2"),
        "encounters_section": _get_section_by_code(structured_body, "46240-8"),
        "social_history_section": _get_section_by_code(structured_body, "29762-2"),
    }


@pytest.fixture(scope="session")
def clinical_test_data(
    xml_test_setup,
) -> dict[str, str | Any | None]:
    """
    Setup clinical test data for section processing.
    """

    # use a simple XPath to find clinical elements with specific codes
    clinical_xpath = './/hl7:observation[hl7:code[@code="94310-0"]]'

    # use direct XPath instead of _get_observations
    clinical_elements: Any = xml_test_setup["results_section"].xpath(
        clinical_xpath, namespaces=NAMESPACES
    )

    return {
        "xpath": clinical_xpath,
        "clinical_elements": clinical_elements,
        "single_clinical_element": clinical_elements[0] if clinical_elements else None,
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

    entries: Any = section.xpath(".//hl7:entry", namespaces=namespaces)
    return entries if entries is not None else []


# NOTE:
# PUBLIC API FUNCTION TESTS


def test_get_reportable_conditions_no_codes() -> None:
    """
    Test get_reportable_conditions when no codes are found.
    """

    root: _Element = etree.fromstring("""
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


def test_get_reportable_conditions_uniqueness() -> None:
    """
    Test that get_reportable_conditions returns unique conditions only.
    Uses sample RR with duplicate reportable conditions to verify deduplication.
    """

    root: _Element = etree.fromstring("""
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

    result: list[dict[str, str]] | None = get_reportable_conditions(root)

    # verify we get exactly 2 unique conditions
    assert len(result) == 2

    # verify the specific conditions are present
    expected_conditions: list[dict[str, str]] = [
        {"code": "840539006", "displayName": "COVID-19"},
        {"code": "27836007", "displayName": "Pertussis"},
    ]
    assert result == expected_conditions


def test_get_reportable_conditions_empty_rr11() -> None:
    """
    Test that RR11 organizer with no qualifying observations returns None.
    """

    root: _Element = etree.fromstring("""
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

    result: list[dict[str, str]] | None = get_reportable_conditions(root)
    assert result is None


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
) -> None:
    """
    Test eICR refinement with required condition_codes.
    """

    refined_output: str = refine_eicr(
        xml_files=sample_xml_files,
        sections_to_include=sections_to_include,
        condition_codes_xpath=condition_codes,
    )

    refined_doc: _Element = etree.fromstring(refined_output)
    refined_structured_body: _Element | None = refined_doc.find(
        path=".//{urn:hl7-org:v3}structuredBody", namespaces={"hl7": "urn:hl7-org:v3"}
    )
    refined_results_section = _get_section_by_code(refined_structured_body, "30954-2")

    xpath_query = ".//hl7:code"
    result: bool = bool(
        refined_results_section.xpath(
            _path=xpath_query, namespaces={"hl7": "urn:hl7-org:v3"}
        )
    )
    assert result == expected_in_results


def test_build_condition_eicr_pairs(sample_xml_files: XMLFiles) -> None:
    """
    Test building condition-eICR pairs with XMLFiles objects.
    """

    reportable_conditions: list[dict[str, str]] = [
        {"code": "840539006", "displayName": "COVID-19"},
        {"code": "27836007", "displayName": "Pertussis"},
    ]

    pairs: list[dict[str, Any]] = build_condition_eicr_pairs(
        original_xml_files=sample_xml_files, reportable_conditions=reportable_conditions
    )

    # verify we get the expected number of pairs
    assert len(pairs) == 2

    # verify each pair has the expected structure
    for i, pair in enumerate(pairs):
        assert "reportable_condition" in pair
        assert "xml_files" in pair
        assert pair["reportable_condition"] == reportable_conditions[i]

        # verify the xml_files is a proper XMLFiles object
        assert isinstance(pair["xml_files"], XMLFiles)
        assert pair["xml_files"].eicr == sample_xml_files.eicr
        assert pair["xml_files"].rr == sample_xml_files.rr


# NOTE:
# SECTION PROCESSING TESTS


def test_process_section_no_clinical_elements() -> None:
    """
    Test _process_section when no clinical elements are found.
    """

    section: _Element = etree.fromstring("""
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
        </section>
    """)

    # pass empty XPath since no condition codes provided
    _process_section(
        section=section,
        # empty XPath means no condition codes
        combined_xpath="",
        namespaces={"hl7": "urn:hl7-org:v3"},
    )

    # verify that a text element was created (minimal section)
    text_elem: _Element | None = section.find(
        path=".//hl7:text", namespaces={"hl7": "urn:hl7-org:v3"}
    )
    assert text_elem is not None

    # verify table with message exists
    table: _Element = text_elem.find(path="table")
    assert table is not None
    assert MINIMAL_SECTION_MESSAGE in table.findtext(".//td")

    # verify section has nullFlavor="NI"
    assert section.get("nullFlavor") == "NI"


def test_process_section_with_error():
    """
    Test error handling in _process_section.
    """

    section: _Element = etree.fromstring("""
        <section xmlns="urn:hl7-org:v3">
            <code code="invalid"/>
            <entry>
                <observation>
                    <code code="nonexistent"/>
                </observation>
            </entry>
        </section>
    """)

    # use a valid XPath that won't match anything
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
    result = section.xpath(_path=xpath_query, namespaces=NAMESPACES)
    # empty list means no elements found
    assert not result


def test_find_condition_relevant_elements_with_matches(xml_test_setup) -> None:
    """
    Test _find_condition_relevant_elements with matching clinical elements.
    """

    section: Any = xml_test_setup["results_section"]
    # use XPath that should find elements in the test data
    xpath = './/hl7:observation[hl7:code[@code="94310-0"]]'

    result: list[_Element] = _find_condition_relevant_elements(
        section=section, combined_xpath=xpath, namespaces=NAMESPACES
    )

    assert isinstance(result, list)
    assert len(result) > 0

    # verify elements are actually clinical elements
    for elem in result:
        assert elem.tag.endswith("observation")


def test_process_section_complete_workflow_with_matches(xml_test_setup) -> None:
    """
    Test complete _process_section workflow when matches are found.
    """

    section: Any = xml_test_setup["results_section"]
    xpath = './/hl7:observation[hl7:code[@code="94310-0"]]'

    _process_section(
        section=section,
        combined_xpath=xpath,
        namespaces=NAMESPACES,
        section_config=None,
        version="1.1",
    )

    # verify section was processed (not minimal)
    assert section.get("nullFlavor") != "NI"

    # verify text element was updated
    final_text: Any = section.find(".//hl7:text", namespaces=NAMESPACES)
    assert final_text is not None

    # verify table structure
    table: Any = final_text.find("table")
    assert table is not None
    rows: Any = table.findall(".//tr")
    # header + data rows
    assert len(rows) > 1


def test_find_condition_relevant_elements_no_matches(xml_test_setup) -> None:
    """
    Test _find_condition_relevant_elements when no elements match.
    """

    section: Any = xml_test_setup["results_section"]
    # use XPath that won't match anything
    xpath = './/hl7:observation[hl7:code[@code="nonexistent-code"]]'

    result: list[_Element] = _find_condition_relevant_elements(
        section=section, combined_xpath=xpath, namespaces=NAMESPACES
    )

    assert isinstance(result, list)
    assert len(result) == 0


def test_find_condition_relevant_elements_empty_xpath(xml_test_setup) -> None:
    """
    Test _find_condition_relevant_elements with empty XPath.
    """

    section: Any = xml_test_setup["results_section"]

    # empty XPath should return empty list, not raise exception
    result: list[_Element] = _find_condition_relevant_elements(
        section=section, combined_xpath="", namespaces=NAMESPACES
    )

    assert isinstance(result, list)
    assert len(result) == 0

    # test whitespace-only XPath too
    result_whitespace: list[_Element] = _find_condition_relevant_elements(
        section=section, combined_xpath="   ", namespaces=NAMESPACES
    )
    assert isinstance(result_whitespace, list)
    assert len(result_whitespace) == 0


def test_find_condition_relevant_elements_invalid_xpath(xml_test_setup) -> None:
    """
    Test _find_condition_relevant_elements with invalid XPath.
    """

    section: Any = xml_test_setup["results_section"]
    # invalid XPath syntax
    invalid_xpath = ".//hl7:observation[["

    with pytest.raises(XMLParsingError) as exc_info:
        _find_condition_relevant_elements(
            section=section, combined_xpath=invalid_xpath, namespaces=NAMESPACES
        )

    assert "Failed to evaluate XPath for condition-relevant elements" in str(
        exc_info.value
    )


@pytest.mark.parametrize(
    "trigger_templates,expected_trigger_count",
    [
        # no trigger templates configured
        ([], 0),
        # trigger templates that won't match
        (["2.16.840.1.113883.10.20.15.2.3.99"], 0),
        # valid trigger template
        (["2.16.840.1.113883.10.20.15.2.3.12"], 0),
    ],
)
def test_analyze_trigger_codes_in_context(
    clinical_test_data, trigger_templates, expected_trigger_count
) -> None:
    """
    Test _analyze_trigger_codes_in_context with various trigger template configurations.
    """

    contextual_matches: Any = clinical_test_data["clinical_elements"]

    # mock section config
    section_config: None = None
    if trigger_templates:
        section_config: None = {
            "trigger_codes": {
                "test_trigger": {"template_id_root": trigger_templates[0]}
            }
        }

    result: dict[int, bool] = _analyze_trigger_codes_in_context(
        contextual_matches, section_config
    )

    assert isinstance(result, dict)
    assert len(result) == len(contextual_matches)

    # count trigger codes
    trigger_count: int = sum(1 for is_trigger in result.values() if is_trigger)
    assert trigger_count == expected_trigger_count

    # verify all elements have analysis
    for elem in contextual_matches:
        element_id: int = id(elem)
        assert element_id in result
        assert isinstance(result[element_id], bool)


def test_analyze_trigger_codes_in_context_empty_matches() -> None:
    """
    Test _analyze_trigger_codes_in_context with empty contextual matches.
    """

    result: dict[int, bool] = _analyze_trigger_codes_in_context(
        contextual_matches=[], section_config=None
    )

    assert isinstance(result, dict)
    assert len(result) == 0


def test_analyze_trigger_codes_in_context_no_config() -> None:
    """
    Test _analyze_trigger_codes_in_context with no section config.
    """

    # create mock clinical elements
    clinical_elements: list[_Element] = [
        etree.fromstring(
            '<observation xmlns="urn:hl7-org:v3"><code code="test"/></observation>'
        )
    ]

    result: dict[int, bool] = _analyze_trigger_codes_in_context(
        contextual_matches=clinical_elements, section_config=None
    )

    assert isinstance(result, dict)
    assert len(result) == 1
    # all should be False when no trigger templates
    assert all(not is_trigger for is_trigger in result.values())


def test_trigger_code_identification_principle() -> None:
    """
    Test that trigger codes are only identified within contextually relevant elements.
    """

    # create elements that would have trigger templates but aren't contextually relevant
    # this test validates the principle that trigger identification happens AFTER context filtering
    trigger_element: _Element = etree.fromstring("""
        <observation xmlns="urn:hl7-org:v3">
            <templateId root="2.16.840.1.113883.10.20.15.2.3.12"/>
            <code code="trigger-code"/>
        </observation>
    """)

    non_trigger_element: _Element = etree.fromstring("""
        <observation xmlns="urn:hl7-org:v3">
            <code code="regular-code"/>
        </observation>
    """)

    # only contextually relevant elements should be passed to trigger analysis
    # trigger element is NOT in contextual matches
    contextual_matches: list[_Element] = [non_trigger_element]

    # verify trigger_element would be identified as trigger if it were in context
    section_config: dict[str, dict[str, dict[str, str]]] = {
        "trigger_codes": {
            "test_trigger": {"template_id_root": "2.16.840.1.113883.10.20.15.2.3.12"}
        }
    }

    # verify that trigger_element WOULD be identified if it were in contextual matches
    result_with_trigger: dict[int, bool] = _analyze_trigger_codes_in_context(
        contextual_matches=[trigger_element], section_config=section_config
    )
    assert len(result_with_trigger) == 1
    assert result_with_trigger[id(trigger_element)] is True

    # test with trigger_element excluded from context
    result: dict[int, bool] = _analyze_trigger_codes_in_context(
        contextual_matches, section_config
    )
    # even though trigger template exists, no elements should be marked as triggers
    # because the trigger element wasn't in contextual matches
    assert len(result) == 1
    assert result[id(non_trigger_element)] is False


@pytest.mark.parametrize(
    "section_config,expected_template_count",
    [
        # no trigger codes configuration
        (None, 0),
        # empty trigger codes
        ({"trigger_codes": {}}, 0),
        # single trigger code
        (
            {
                "trigger_codes": {
                    "lab": {"template_id_root": "2.16.840.1.113883.10.20.15.2.3.12"}
                }
            },
            1,
        ),
        # multiple trigger codes
        (
            {
                "trigger_codes": {
                    "lab": {"template_id_root": "2.16.840.1.113883.10.20.15.2.3.12"},
                    "medication": {
                        "template_id_root": "2.16.840.1.113883.10.20.15.2.3.13"
                    },
                }
            },
            2,
        ),
        # trigger code without template_id_root (should be ignored)
        ({"trigger_codes": {"invalid": {"other_field": "value"}}}, 0),
    ],
)
def test_trigger_template_extraction(section_config, expected_template_count) -> None:
    """
    Test extraction of trigger templates from section configuration.
    """

    # create a simple clinical element
    clinical_element: _Element = etree.fromstring("""
        <observation xmlns="urn:hl7-org:v3">
            <code code="test"/>
        </observation>
    """)

    result: dict[int, bool] = _analyze_trigger_codes_in_context(
        contextual_matches=[clinical_element], section_config=section_config
    )

    # should get result for our element
    assert len(result) == 1
    assert id(clinical_element) in result


def test_preserve_relevant_entries_and_generate_summary(xml_test_setup) -> None:
    """
    Test _preserve_relevant_entries_and_generate_summary integration.
    """

    section: Any = xml_test_setup["results_section"]

    # find some clinical elements to work with
    clinical_elements = section.xpath(
        './/hl7:observation[hl7:code[@code="94310-0"]]', namespaces=NAMESPACES
    )

    if not clinical_elements:
        pytest.skip("No clinical elements found in test data")

    # mock trigger analysis (no triggers for simplicity)
    trigger_analysis: dict[int, bool] = {id(elem): False for elem in clinical_elements}

    # get initial entry count
    initial_entries: Any = section.xpath(".//hl7:entry", namespaces=NAMESPACES)
    initial_count: int = len(initial_entries)

    _preserve_relevant_entries_and_generate_summary(
        section=section,
        contextual_matches=clinical_elements,
        trigger_analysis=trigger_analysis,
        namespaces=NAMESPACES,
    )

    # verify that we started with some entries (test data validation)
    assert initial_count > 0, "Test data should contain entries"

    # verify text element was updated
    text_element: Any = section.find(".//hl7:text", namespaces=NAMESPACES)
    assert text_element is not None

    # verify table structure
    table: Any = text_element.find("table")
    assert table is not None

    # verify title
    title: Any = text_element.find("title")
    assert title is not None
    assert title.text == REFINER_OUTPUT_TITLE


def test_preserve_relevant_entries_and_generate_summary_empty_matches() -> None:
    """
    Test _preserve_relevant_entries_and_generate_summary with empty matches.
    """

    # create a simple section
    section: _Element = etree.fromstring("""
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry>
                <observation>
                    <code code="test"/>
                </observation>
            </entry>
        </section>
    """)

    _preserve_relevant_entries_and_generate_summary(
        section=section,
        contextual_matches=[],
        trigger_analysis={},
        namespaces=NAMESPACES,
    )

    # should still create/update text element even with no matches
    text_element: _Element = section.find(path=".//hl7:text", namespaces=NAMESPACES)
    assert text_element is not None


def test_three_step_process_integration(xml_test_setup) -> None:
    """
    Test the complete three-step process integration.
    """

    section: Any = xml_test_setup["results_section"]
    xpath = './/hl7:observation[hl7:code[@code="94310-0"]]'

    # STEP 1: find contextual matches
    contextual_matches: list[_Element] = _find_condition_relevant_elements(
        section=section, combined_xpath=xpath, namespaces=NAMESPACES
    )

    # STEP 2: analyze trigger codes within context
    trigger_analysis: dict[int, bool] = _analyze_trigger_codes_in_context(
        contextual_matches=contextual_matches, section_config=None
    )

    # STEP 3: preserve entries and generate summary
    _preserve_relevant_entries_and_generate_summary(
        section=section,
        contextual_matches=contextual_matches,
        trigger_analysis=trigger_analysis,
        namespaces=NAMESPACES,
    )

    # verify the complete process worked
    assert len(contextual_matches) == len(trigger_analysis)

    # verify text element was created/updated
    text_element: Any = section.find(".//hl7:text", namespaces=NAMESPACES)
    assert text_element is not None

    # verify trigger analysis structure
    for elem in contextual_matches:
        element_id: int = id(elem)
        assert element_id in trigger_analysis
        assert isinstance(trigger_analysis[element_id], bool)


# NOTE:
# ENTRY AND ELEMENT TESTS


def test_find_path_to_entry_no_match() -> None:
    """
    Test finding path when no match exists.
    """

    clinical_element: _Element = etree.fromstring("""
        <observation xmlns="urn:hl7-org:v3">
            <code code="different"/>
        </observation>
    """)

    with pytest.raises(StructureValidationError) as exc_info:
        _find_path_to_entry(element=clinical_element)
    assert "Parent <entry> element not found" in str(exc_info.value)


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
def test_prune_unwanted_siblings(xml_content, xpath, expected_entry_count) -> None:
    """
    Test removal of non-matching sibling entries.
    """

    # parse the XML string into an element
    element: _Element = etree.fromstring(xml_content)

    # find matching clinical elements using XPath
    matching_clinical_elements = element.xpath(xpath, namespaces=NAMESPACES)
    paths: list[_Element] = [
        _find_path_to_entry(elem) for elem in matching_clinical_elements
    ]

    # call with the section element (element is the section in this case)
    _prune_unwanted_siblings(entry_paths=paths, section=element)

    # verify the result
    remaining_entries: list[Any] = _get_entries_for_section(section=element)
    assert len(remaining_entries) == expected_entry_count


# NOTE:
# CLINICAL DATA EXTRACTION


@pytest.mark.parametrize(
    "clinical_index,expected_data",
    [
        (
            0,
            {
                "display_text": "SARS-like Coronavirus N gene [Presence] in Unspecified specimen by NAA with probe detection",
                "code": "94310-0",
                "code_system": "LOINC",
            },
        ),
    ],
)
def test_extract_clinical_data(
    clinical_test_data,
    clinical_index,
    expected_data,
) -> None:
    """
    Test extraction of clinical element metadata.
    """

    clinical_element: Any = clinical_test_data["clinical_elements"][clinical_index]
    data: dict[str, str | bool | None] = _extract_clinical_data(clinical_element)
    assert data == expected_data


# NOTE:
# TEXT ELEMENT GENERATION TESTS


def test_create_or_update_text_element(clinical_test_data) -> None:
    """
    Test creation of text element from clinical elements.
    """

    # updated function signature to include trigger_code_elements parameter
    # empty set for test
    trigger_code_elements: set[Any] = set()
    text_element: _Element = _create_or_update_text_element(
        clinical_elements=clinical_test_data["clinical_elements"],
        trigger_code_elements=trigger_code_elements,
    )

    # verify basic structure
    assert text_element.tag.endswith("text")
    assert text_element.find(path=".//table") is not None
    assert text_element.find(path=".//title") is not None

    # verify title contains expected text
    title: _Element | None = text_element.find(path=".//title")
    assert title.text == REFINER_OUTPUT_TITLE

    # verify content
    table: _Element | None = text_element.find(".//table")
    rows: list[_Element] = table.findall(path=".//tr")
    # header row plus at least one data row
    assert len(rows) > 1

    # verify header uses new constants
    header: list[_Element] = rows[0].findall(".//th")
    assert [h.text for h in header] == CLINICAL_DATA_TABLE_HEADERS


def test_create_or_update_text_invalid_section() -> None:
    """
    Test creating text element with invalid section.
    """

    clinical_elements: list[_Element] = [
        etree.fromstring("""
            <observation xmlns="urn:hl7-org:v3">
                <code code="test" displayName="Test Code" codeSystemName="Test System"/>
            </observation>
        """)
    ]

    # updated function signature
    trigger_code_elements: set[Any] = set()
    text_element: _Element = _create_or_update_text_element(
        clinical_elements=clinical_elements, trigger_code_elements=trigger_code_elements
    )
    assert text_element is not None
    assert text_element.tag == "{urn:hl7-org:v3}text"
    assert text_element.find(path="table") is not None


def test_text_constants() -> None:
    """
    Test that our text constants are properly defined and accessible.
    """

    assert (
        REFINER_OUTPUT_TITLE
        == "Output from CDC PRIME DIBBs eCR Refiner application by request of STLT"
    )
    assert MINIMAL_SECTION_MESSAGE == "Section details have been removed as requested"
    assert CLINICAL_DATA_TABLE_HEADERS == [
        "Display Text",
        "Code",
        "Code System",
        "Is Trigger Code",
        "Matching Condition Code",
    ]
