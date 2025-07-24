import logging
from dataclasses import dataclass
from typing import Literal, TypedDict, cast

from lxml import etree
from lxml.etree import _Element

from ...core.exceptions import (
    SectionValidationError,
    StructureValidationError,
    XMLParsingError,
    XMLValidationError,
)
from ...core.models.types import XMLFiles
from ...db.connection import DatabaseConnection
from ..file_io import read_json_asset
from .helpers import (
    get_condition_codes_xpath,
    get_processed_groupers_from_condition_codes,
)

# NOTE:
# CONSTANTS AND CONFIGURATION
# =============================================================================

log = logging.getLogger(__name__).error

# read json that contains details for refining and is the base of what drives `refine`
REFINER_DETAILS = read_json_asset("refiner_details.json")

# extract section LOINC codes from the REFINER_DETAILS dictionary
SECTION_LOINCS = set(REFINER_DETAILS["sections"].keys())

# <text> constants for refined sections
REFINER_OUTPUT_TITLE = (
    "Output from CDC PRIME DIBBs eCR Refiner application by request of STLT"
)
MINIMAL_SECTION_MESSAGE = "Section details have been removed as requested"
CLINICAL_DATA_TABLE_HEADERS = [
    "Display Text",
    "Code",
    "Code System",
    "Is Trigger Code",
    "Matching Condition Code",
]


@dataclass
class ReportableCondition:
    """
    Object to hold the properties of a reportable condition.
    """

    code: str
    display_name: str


# NOTE:
# =============================================================================
# In lxml, use _Element for type hints and etree.Element in code.
# -> _Element (from lxml.etree) is the actual type of xml element objects, suitable for
#    type annotations and for static type checkers
# -> etree.Element is a factory function that creates and returns _Element instances; use
#    it in code to create nodes.
# * Do not use etree.Element for type hints; it's not a class, but a function.
#   See: https://lxml.de/api/lxml.etree._Element-class.html
# * this will change in lxml 6.0
#   See: on this PR: https://github.com/lxml/lxml/pull/405


# NOTE:
# PUBLIC API FUNCTIONS
# =============================================================================


def validate_sections_to_include(
    sections_to_include: str | None,
) -> list[str] | None:
    """
    Validates section codes from query parameter.

    Args:
        sections_to_include: Comma-separated section codes

    Returns:
        list[str] | None: List of validated section codes, or None if no sections provided

    Raises:
        SectionValidationError: If any section code is invalid
    """

    if sections_to_include is None:
        return None

    sections = [s.strip() for s in sections_to_include.split(",") if s.strip()]
    valid_sections = set(REFINER_DETAILS["sections"].keys())

    invalid_sections = [s for s in sections if s not in valid_sections]
    if invalid_sections:
        raise SectionValidationError(
            message=f"Invalid section codes: {', '.join(invalid_sections)}",
            details={
                "invalid_sections": invalid_sections,
                "valid_sections": list(valid_sections),
            },
        )

    return sections


def get_reportable_conditions(root: _Element) -> list[ReportableCondition] | None:
    """
    Get reportable conditions from the Report Summary section.

    Following RR spec 1.1 structure:
    - Summary Section (55112-7) contains exactly one RR11 organizer
    - RR11 Coded Information Organizer contains condition observations
    - Each observation must have:
      - Template ID 2.16.840.1.113883.10.20.15.2.3.12
      - RR1 determination code with RRVS1 value for reportable conditions
      - SNOMED CT code in value element (codeSystem 2.16.840.1.113883.6.96)

    Args:
        root: The root element of the XML document to parse.

    Returns:
        list[dict[str, str]] | None: List of reportable conditions or None if none found.
        Each condition is a dict with 'code' and 'displayName' keys.

    Raises:
        StructureValidationError: If RR11 Coded Information Organizer is missing (invalid RR)
        XMLParsingError: If XPath evaluation fails
    """

    conditions = []

    # standard CDA namespace declarations required for RR documents
    namespaces = {
        "cda": "urn:hl7-org:v3",
        "sdtc": "urn:hl7-org:sdtc",
        "voc": "http://www.lantanagroup.com/voc",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }

    try:
        # the summary section (55112-7) must contain exactly one RR11 organizer
        # this is specified in the RR IG
        coded_info_organizers = cast(
            list[_Element],
            root.xpath(
                ".//cda:section[cda:code/@code='55112-7']"
                "//cda:entry/cda:organizer[cda:code/@code='RR11']",
                namespaces=namespaces,
            ),
        )

        # if there is no coded information organizer then the RR is not valid
        # this would be a major problem
        if not coded_info_organizers:
            raise StructureValidationError(
                message="Missing required RR11 Coded Information Organizer",
                details={
                    "document_type": "RR",
                    "error": "RR11 organizer with cardinality 1..1 not found in Summary Section",
                },
            )

        # we can safely take [0] because cardinality is 1..1
        coded_info_organizer = coded_info_organizers[0]

        # find all condition observations using the specified templateId
        # This templateId is fixed in the RR spec and identifies condition observations
        observations = cast(
            list[_Element],
            coded_info_organizer.xpath(
                ".//cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12']]",
                namespaces=namespaces,
            ),
        )

        for observation in observations:
            # RR1 with value RRVS1 indicates a "reportable" condition
            # this is how the RR explicitly marks conditions that should be reported
            # other values like "not reportable" or "may be reportable" are filtered out
            determination = observation.xpath(
                ".//cda:observation[cda:code/@code='RR1']/cda:value[@code='RRVS1']",
                namespaces=namespaces,
            )
            if not determination:
                continue

            # per RR spec, each reportable condition observation MUST contain
            # a valid SNOMED CT code (CONF:3315-552) in its value element
            # codeSystem 2.16.840.1.113883.6.96 is required for SNOMED CT
            value = cast(
                list[_Element],
                observation.xpath(
                    ".//cda:value[@codeSystem='2.16.840.1.113883.6.96']",
                    namespaces=namespaces,
                ),
            )
            if not value:
                continue

            code = value[0].get("code")
            display_name = value[0].get(
                "displayName", "Condition display name not found"
            )
            if not code:
                continue

            # when a condition is reportable, we must capture its
            # required SNOMED CT code and display name and build the
            # condition object and ensure uniqueness--duplicate conditions
            # should not be reported multiple times
            condition = ReportableCondition(code=code, display_name=display_name)
            if condition not in conditions:
                conditions.append(condition)

    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message="Failed to evaluate XPath expression in RR document",
            details={"xpath_error": str(e)},
        )

    return conditions if conditions else None


class ProcessedRR(TypedDict):
    """
    The returned result of processing an RR.
    """

    reportable_conditions: list[ReportableCondition]


def process_rr(xml_files: XMLFiles) -> ProcessedRR:
    """
    Process the RR XML document to extract relevant information.

    Args:
        xml_files: Container with both eICR and RR XML content
                  (currently only using RR)

    Returns:
        dict: Extracted information from the RR document

    Raises:
        XMLParsingError
    """

    try:
        rr_root = xml_files.parse_rr()
        return {"reportable_conditions": get_reportable_conditions(rr_root)}
    except etree.XMLSyntaxError as e:
        raise XMLParsingError(
            message="Failed to parse RR document", details={"error": str(e)}
        )


def refine_eicr(
    xml_files: XMLFiles,
    condition_codes_xpath: str,
    sections_to_include: list[str] | None = None,
) -> str:
    """
    Refine an eICR XML document by processing its sections.

    Processing behavior:
        - condition_codes **must** be provided; if missing or empty, the function raises ConditionCodeError.
        - If sections_to_include is provided, those sections are preserved unmodified.
        - For all other sections, only entries matching the clinical codes related to the given condition_codes are kept.
        - If no matching entries are found in a section, it is replaced with a minimal section and marked with nullFlavor="NI".

    Args:
        xml_files: The XMLFiles container with the eICR document to refine.
        sections_to_include: Optional list of section LOINC codes to preserve.
        condition_codes_xpath: Comma-separated string of SNOMED condition codes
            to use for filtering sections in an eICR. Each code will be looked up in the
            groupers table in the terminology database to find related clinical codes.
            **This parameter is required. If not provided, a ConditionCodeError is raised.**

    Returns:
        str: The refined eICR XML document as a string.

    Raises:
        ConditionCodeError: If no condition_codes are provided.
        SectionValidationError: If any section code is invalid.
        XMLValidationError: If the XML is invalid.
        StructureValidationError: If the document structure is invalid.
    """

    try:
        # parse the eicr document
        validated_message = xml_files.parse_eicr()

        namespaces = {"hl7": "urn:hl7-org:v3"}
        structured_body = validated_message.find(".//hl7:structuredBody", namespaces)

        # if we don't have a structuredBody this is a major problem
        if structured_body is None:
            raise StructureValidationError(
                message="No structured body found in eICR",
                details={"document_type": "eICR"},
            )

        # TODO:
        # detect version from document. in future we'll have a function here to check
        # we'll then use the 'refiner_config.json' as the brain for processing in a
        # config-driven way for section processing where the version will be passed to
        # _process_section
        version: Literal["1.1"] = "1.1"

        for section_code, section_config in REFINER_DETAILS["sections"].items():
            # skip if in sections_to_include (preserve unmodified)
            if sections_to_include and section_code in sections_to_include:
                continue

            section = _get_section_by_code(structured_body, section_code, namespaces)
            if section is None:
                continue

            _process_section(
                section, condition_codes_xpath, namespaces, section_config, version
            )

        # format and return the result
        return etree.tostring(validated_message, encoding="unicode")

    except etree.XMLSyntaxError as e:
        raise XMLValidationError(
            message="Failed to parse eICR document", details={"error": str(e)}
        )
    except etree.XPathEvalError as e:
        raise XMLValidationError(
            message="Failed to evaluate XPath expression in eICR document",
            details={"error": str(e)},
        )


def build_condition_eicr_pairs(
    original_xml_files: XMLFiles,
    reportable_conditions: list[ReportableCondition],
) -> list[tuple[ReportableCondition, XMLFiles]]:
    """
    Generate pairs of reportable conditions and fresh XMLFiles copies.

    Each reportable condition gets its own copy of the XMLFiles object so that
    condition-specific refinement can be performed independently.

    Args:
        original_xml_files: The original XMLFiles object containing eICR and RR.
        reportable_conditions: List of reportable condition objects with 'code' keys.

    Returns:
        list[dict[str, Any]]: A list of dictionaries, each containing a
                             `reportable_condition` and `xml_files`.
    """

    condition_eicr_pairs = []

    for condition in reportable_conditions:
        # create fresh XMLFiles for each condition to ensure complete isolation
        condition_xml_files = XMLFiles(original_xml_files.eicr, original_xml_files.rr)
        condition_eicr_pairs.append(
            (
                condition,
                condition_xml_files,
            )
        )

    return condition_eicr_pairs


# NOTE:
# SECTION PROCESSING (Core refinement logic)
# =============================================================================


def _process_section(
    section: _Element,
    combined_xpath: str,
    namespaces: dict = {"hl7": "urn:hl7-org:v3"},
    section_config: dict | None = None,
    version: Literal["1.1"] = "1.1",
) -> None:
    """
    Process a section using a three-step filtering approach.

    STEP 1 (Context Filter): Find clinical elements matching SNOMED condition codes
    STEP 2 (Trigger Identification): Among contextual matches, identify trigger codes
    STEP 3 (Entry Processing): Preserve relevant entries and generate section summary

    This three-step process ensures we only preserve entries that are:
    1. Relevant to the reportable condition (contextual filtering)
    2. Properly marked if they triggered the original eICR (trigger identification)
    3. Properly structured and summarized in the final output (entry processing)

    The key principle: trigger code identification only happens within an already-filtered
    context, ensuring we don't keep random trigger codes unrelated to the condition.

    Args:
        section: The XML section element to process
        combined_xpath: XPath query from ProcessedGrouper codes
        namespaces: XML namespaces for XPath evaluation
        section_config: Configuration for this section from refiner_details.json
        version: eICR version being processed
    """

    if not combined_xpath:
        # no condition codes provided - create minimal section
        _create_minimal_section(section)
        return

    try:
        # STEP 1: CONTEXT FILTERING
        # find all clinical elements matching our SNOMED condition codes
        # this is our primary filter - only contextually relevant elements proceed
        contextual_matches = _find_condition_relevant_elements(
            section, combined_xpath, namespaces
        )

        if not contextual_matches:
            # no matching clinical elements found for our condition
            _create_minimal_section(section)
            return

        # STEP 2: TRIGGER IDENTIFICATION WITHIN CONTEXT
        # among our contextual matches, identify which are trigger codes
        # this ensures trigger codes are only identified within relevant clinical context
        trigger_analysis = _analyze_trigger_codes_in_context(
            contextual_matches, section_config
        )

        # STEP 3: PROCESS ENTRIES AND GENERATE OUTPUT
        # handle entry-level operations and create final section content
        _preserve_relevant_entries_and_generate_summary(
            section, contextual_matches, trigger_analysis, namespaces
        )

    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message="Invalid XPath expression",
            details={"xpath": combined_xpath, "error": str(e)},
        )


def _find_condition_relevant_elements(
    section: _Element, combined_xpath: str, namespaces: dict
) -> list[_Element]:
    """
    STEP 1: Find clinical elements matching SNOMED condition codes.

    This is the context filter - only elements relevant to our reportable
    condition should proceed to the next step.

    Args:
        section: The XML section element to search within
        combined_xpath: XPath query from ProcessedGrouper codes
        namespaces: XML namespaces for XPath evaluation

    Returns:
        list[_Element]: Deduplicated list of contextually relevant clinical elements

    Raises:
        XMLParsingError: If XPath evaluation fails
    """

    # handle empty XPath early
    if not combined_xpath or not combined_xpath.strip():
        return []

    try:
        # find all clinical elements matching our SNOMED condition codes
        xpath_result = section.xpath(combined_xpath, namespaces=namespaces)

        if not isinstance(xpath_result, list):
            return []

        clinical_elements = cast(list[_Element], xpath_result)

        # deduplicate hierarchical matches within our SNOMED-filtered set
        # this prevents duplicate content when both parent and child elements match
        return _deduplicate_clinical_elements(clinical_elements)

    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message="Failed to evaluate XPath for condition-relevant elements",
            details={"xpath": combined_xpath, "error": str(e)},
        )


def _analyze_trigger_codes_in_context(
    contextual_matches: list[_Element], section_config: dict | None
) -> dict[int, bool]:
    """
    STEP 2: Identify trigger codes among already-contextually-relevant elements.

    This function performs trigger code identification ONLY within the context
    of elements that have already been deemed relevant to our reportable condition.
    This ensures we don't preserve random trigger codes unrelated to the condition.

    Args:
        contextual_matches: List of clinical elements already filtered for context
        section_config: Configuration for this section from refiner_details.json

    Returns:
        dict[int, bool]: Mapping of element_id -> is_trigger_code for each element
    """

    trigger_analysis = {}

    # get trigger templates for this section from config
    trigger_templates = []
    if section_config and "trigger_codes" in section_config:
        # extract template_id_root values from trigger_codes
        for trigger_type, trigger_info in section_config["trigger_codes"].items():
            if "template_id_root" in trigger_info:
                trigger_templates.append(trigger_info["template_id_root"])

    if not trigger_templates:
        # no trigger templates defined for this section
        # mark all contextual matches as non-trigger codes
        return {id(elem): False for elem in contextual_matches}

    # cache template ancestor checks to avoid repeated tree traversals
    # fresh cache per section ensures clean slate for each processing cycle
    template_cache = {}

    for clinical_element in contextual_matches:
        element_id = id(clinical_element)

        # check cache first to avoid redundant tree traversals
        if element_id not in template_cache:
            template_cache[element_id] = _has_trigger_template_ancestor(
                clinical_element, trigger_templates
            )

        # store the trigger code analysis for this element
        is_trigger = template_cache[element_id]
        trigger_analysis[element_id] = is_trigger

    return trigger_analysis


def _preserve_relevant_entries_and_generate_summary(
    section: _Element,
    contextual_matches: list[_Element],
    trigger_analysis: dict[int, bool],
    namespaces: dict,
) -> None:
    """
    STEP 3: Process entry-level operations and generate final section content.

    This function handles the final processing steps:
    1. Find and preserve entries containing our contextually relevant elements
    2. Remove unwanted entries
    3. Generate summary text showing both regular matches and trigger codes

    Args:
        section: The XML section element being processed
        contextual_matches: List of contextually relevant clinical elements
        trigger_analysis: Mapping of element_id -> is_trigger_code
        namespaces: XML namespaces for XPath evaluation
    """

    # find parent entries for all matching clinical elements
    entry_paths = []
    for clinical_element in contextual_matches:
        entry_path = _find_path_to_entry(clinical_element)
        entry_paths.append(entry_path)

    # deduplicate entry paths to prevent overlapping XML branches
    deduplicated_entry_paths = _deduplicate_entry_paths(entry_paths)

    # remove entries that don't contain our contextually relevant clinical elements
    _prune_unwanted_siblings(deduplicated_entry_paths, section)

    # clean up all comments from processed sections
    _remove_all_comments(section)

    # generate summary text showing both regular matches and trigger codes
    # build trigger_code_elements set for compatibility with existing text generation
    trigger_code_elements = {
        element_id for element_id, is_trigger in trigger_analysis.items() if is_trigger
    }

    _update_text_element(section, contextual_matches, trigger_code_elements)


def _get_section_by_code(
    structured_body: _Element,
    loinc_code: str,
    namespaces: dict = {"hl7": "urn:hl7-org:v3"},
) -> _Element | None:
    """
    Get a section from structuredBody by its LOINC code.

    Args:
        structured_body: The HL7 structuredBody element to search within.
        loinc_code: The LOINC code of the section to retrieve.
        namespaces: The namespaces to use for element search. Defaults to hl7.

    Returns:
        _Element: The section element or None if not found

    Raises:
        XMLParsingError: If XPath evaluation fails
    """

    try:
        xpath_query = f'.//hl7:section[hl7:code[@code="{loinc_code}"]]'
        xpath_result = structured_body.xpath(xpath_query, namespaces=namespaces)

        if isinstance(xpath_result, list) and len(xpath_result) == 1:
            section = cast(list[_Element], xpath_result)
            return section[0]
    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message=f"Failed to evaluate XPath for section code {loinc_code}",
            details={"xpath_query": xpath_query, "error": str(e)},
        )
    return None


# NOTE:
# XML TREE MANIPULATION (Entry and element management)
# =============================================================================


def _find_path_to_entry(element: _Element) -> _Element:
    """
    Find the nearest entry ancestor of an element.

    Args:
        element: The element to find the entry for

    Returns:
        The entry element

    Raises:
        StructureValidationError: If no entry ancestor found
    """

    current_element: _Element | None = element

    # walk up the tree until we find an entry element
    while (
        current_element is not None and current_element.tag != "{urn:hl7-org:v3}entry"
    ):
        current_element = current_element.getparent()

    if current_element is None:
        raise StructureValidationError(
            message="Parent <entry> element not found.",
            details={"element_tag": element.tag},
        )

    return current_element


def _prune_unwanted_siblings(
    entry_paths: list[_Element],
    section: _Element,
) -> None:
    """
    Remove entries that don't contain relevant clinical elements.

    Args:
        entry_paths: List of entry elements to preserve
        section: The section being processed
    """

    # find all entries in the section
    namespaces = {"hl7": "urn:hl7-org:v3"}

    xpath_result = section.xpath(".//hl7:entry", namespaces=namespaces)
    if not isinstance(xpath_result, list):
        return

    all_entries = cast(list[_Element], xpath_result)

    # remove entries not in our keep list
    for entry in all_entries:
        if entry not in entry_paths:
            parent = entry.getparent()
            if parent is not None:
                parent.remove(entry)


def _deduplicate_entry_paths(entry_paths: list[_Element]) -> list[_Element]:
    """
    Remove duplicate and nested entry paths to prevent overlapping XML branches.

    When XPath matches find nested elements (e.g., both an <act> and an <observation>
    within that <act>), we could end up with duplicate entries or parent/child entries
    both being preserved, leading to duplicate content in the refined eICR.

    Args:
        entry_paths: List of entry elements that may contain duplicates or nested relationships

    Returns:
        list[_Element]: Deduplicated list with no overlapping branches
    """

    if not entry_paths:
        return entry_paths

    # remove exact duplicates first (same entry element referenced multiple times)
    unique_entries = []
    seen_entries = set()

    for entry in entry_paths:
        entry_id = id(entry)  # Use object identity for exact duplicates
        if entry_id not in seen_entries:
            unique_entries.append(entry)
            seen_entries.add(entry_id)

    # remove nested relationships (parent/child entries)
    # if entry A is an ancestor of entry B, keep only entry A (the parent)
    final_entries = []

    for current_entry in unique_entries:
        is_nested_within_another = False

        # check if this entry is a descendant of any other entry
        for potential_parent_entry in unique_entries:
            if current_entry is not potential_parent_entry and _is_ancestor(
                potential_parent_entry, current_entry
            ):
                is_nested_within_another = True
                break

        # only keep entries that are not nested within other entries
        if not is_nested_within_another:
            final_entries.append(current_entry)

    return final_entries


def _deduplicate_clinical_elements(clinical_elements: list[_Element]) -> list[_Element]:
    """
    Remove nested clinical elements that represent the same logical finding.

    When XPath matches both a parent element (like <organizer>) and its child
    elements (like <observation>), we want to keep only the highest-level
    parent that contains the complete clinical context.
    """

    if not clinical_elements:
        return clinical_elements

    # group elements by their code value to handle same-code hierarchies
    code_groups: dict[str, list[_Element]] = {}

    for elem in clinical_elements:
        data = _extract_clinical_data(elem)
        code = data.get("code")

        # only use string codes for grouping
        if isinstance(code, str):
            if code not in code_groups:
                code_groups[code] = []
            code_groups[code].append(elem)

    deduplicated = []

    for code, elements in code_groups.items():
        if len(elements) == 1:
            # only one element with this code, keep it
            deduplicated.append(elements[0])
        else:
            # multiple elements with same code--keep only the highest ancestor
            # that contains all the others
            ancestors = []

            for elem in elements:
                is_descendant = False
                for other_elem in elements:
                    if elem != other_elem and _is_ancestor(other_elem, elem):
                        is_descendant = True
                        break

                if not is_descendant:
                    ancestors.append(elem)

            # add the top-level ancestors
            deduplicated.extend(ancestors)

    return deduplicated


def _is_ancestor(potential_ancestor: _Element, potential_descendant: _Element) -> bool:
    """
    Check if one element is an ancestor of another in the XML tree.

    Args:
        potential_ancestor: Element that might be the ancestor
        potential_descendant: Element that might be the descendant

    Returns:
        bool: True if potential_ancestor contains potential_descendant
    """

    current = potential_descendant.getparent()

    while current is not None:
        if current is potential_ancestor:
            return True
        current = current.getparent()

    return False


# NOTE:
# CLINICAL DATA EXTRACTION AND ANALYSIS
# =============================================================================


def _extract_clinical_data(
    clinical_element: _Element,
) -> dict[str, str | bool | None]:
    """
    Extract basic data from a clinical element.

    Extracts display text, code, and code system from clinical elements.

    * Note: Trigger code status is handled separately through the trigger_analysis
      dictionary in the section processing pipeline.

    Args:
        clinical_element: The clinical element to extract data from.

    Returns:
        dict[str, str | None]: Dictionary containing the extracted clinical data
                               with display_text, code, and code_system.
    """

    # find the code element
    code_element: _Element | None = (
        clinical_element
        if clinical_element.tag.endswith("code")
        else clinical_element.find(".//hl7:code", namespaces={"hl7": "urn:hl7-org:v3"})
    )

    # extract basic information - handle the fact that get() can return True
    display_text: str | None = None
    code: str | None = None
    code_system: str | None = None

    if code_element is not None:
        display_text_raw = code_element.get("displayName")
        if isinstance(display_text_raw, str):
            display_text = display_text_raw

        code_raw = code_element.get("code")
        if isinstance(code_raw, str):
            code = code_raw

        code_system_raw = code_element.get("codeSystemName")
        if isinstance(code_system_raw, str):
            code_system = code_system_raw

    return {
        "display_text": display_text,
        "code": code,
        "code_system": code_system,
    }


def _has_trigger_template_ancestor(
    element: _Element, trigger_templates: list[str]
) -> bool:
    """
    Check if element is within a trigger code template.

    This function is called during STEP 2 of the processing pipeline,
    after elements have already been filtered for contextual relevance.

    Trigger code templateIds are OIDs that indicate something is a trigger code
    but have no inherent clinical context. Our approach ensures we only identify
    trigger codes among elements that are already clinically relevant to the
    reportable condition.

    Args:
        element: The XML element to check
        trigger_templates: List of template IDs that indicate trigger codes

    Returns:
        bool: True if element is within any of the trigger templates
    """

    if not trigger_templates:
        return False

    current: _Element | None = element
    namespaces: dict[str, str] = {"hl7": "urn:hl7-org:v3"}

    # Walk up the tree looking for trigger template IDs
    while current is not None:
        xpath_result = current.xpath(".//hl7:templateId/@root", namespaces=namespaces)
        if isinstance(xpath_result, list):
            template_ids = xpath_result
            if any(tid in trigger_templates for tid in template_ids):
                return True
        current = current.getparent()

    return False


# NOTE:
# TEXT ELEMENT GENERATION (HTML table creation)
# =============================================================================


def _create_or_update_text_element(
    clinical_elements: list[_Element], trigger_code_elements: set[int]
) -> _Element:
    """
    Create clean, professional text element with trigger code information.

    Simple, clean text generation that clearly shows trigger code status
    without complex formatting that might break downstream systems.

    Args:
        clinical_elements: List of clinical elements to include in the text.
        trigger_code_elements: Set of clinical element IDs that are trigger codes.

    Returns:
        _Element: The created text element with clean formatting.
    """

    text_element = etree.Element("{urn:hl7-org:v3}text")

    # main title
    title = etree.SubElement(text_element, "title")
    title.text = REFINER_OUTPUT_TITLE

    # create table
    table_element = etree.SubElement(text_element, "table", border="1")

    # table header - add back the "Is Trigger Code" column
    header_row = etree.SubElement(table_element, "tr")
    headers = CLINICAL_DATA_TABLE_HEADERS

    for header in headers:
        th = etree.SubElement(header_row, "th")
        th.text = header

    # add clinical data rows - trigger codes first
    trigger_elements = [
        elem for elem in clinical_elements if id(elem) in trigger_code_elements
    ]
    other_elements = [
        elem for elem in clinical_elements if id(elem) not in trigger_code_elements
    ]

    # add trigger codes first
    for clinical_element in trigger_elements:
        _add_clinical_data_row(table_element, clinical_element, is_trigger=True)

    # add other clinical elements
    for clinical_element in other_elements:
        _add_clinical_data_row(table_element, clinical_element, is_trigger=False)

    return text_element


def _add_clinical_data_row(
    table_element: _Element, clinical_element: _Element, is_trigger: bool
) -> None:
    """
    Add a single clinical data row to the table.

    Args:
        table_element: The table element to add the row to
        clinical_element: The clinical element
        is_trigger: Whether this is a trigger code
    """

    data = _extract_clinical_data(clinical_element)
    row = etree.SubElement(table_element, "tr")

    # display text - handle potential non-string values
    td = etree.SubElement(row, "td")
    display_text_raw = data["display_text"]
    display_text = display_text_raw if isinstance(display_text_raw, str) else None

    if is_trigger and display_text:
        # simple bold formatting for trigger codes
        b = etree.SubElement(td, "b")
        b.text = display_text
    else:
        td.text = display_text or "Not specified"

    # code - handle potential non-string values
    td = etree.SubElement(row, "td")
    code_raw = data["code"]
    code = code_raw if isinstance(code_raw, str) else None

    if is_trigger and code:
        b = etree.SubElement(td, "b")
        b.text = code
    else:
        td.text = code or "Not specified"

    # code system - handle potential non-string values
    td = etree.SubElement(row, "td")
    code_system_raw = data["code_system"]
    code_system = code_system_raw if isinstance(code_system_raw, str) else None
    td.text = code_system or "Not specified"

    # is trigger code
    td = etree.SubElement(row, "td")
    td.text = "YES" if is_trigger else "NO"

    # matching condition code (always YES since we only keep matches; if we
    # filter parts of sections we may need to update how this works)
    td = etree.SubElement(row, "td")
    td.text = "YES"


def _update_text_element(
    section: _Element,
    clinical_elements: list[_Element],
    trigger_code_elements: set[int],
) -> None:
    """
    Update a section's text element with clinical data information.

    Args:
        section: The section element containing the text element to update.
        clinical_elements: List of clinical elements to include in the text.
        trigger_code_elements: Set of clinical element IDs that are trigger codes.
    """

    new_text_element = _create_or_update_text_element(
        clinical_elements, trigger_code_elements
    )

    existing_text_element = section.find(
        ".//hl7:text", namespaces={"hl7": "urn:hl7-org:v3"}
    )

    if existing_text_element is not None:
        section.replace(existing_text_element, new_text_element)
    else:
        section.insert(0, new_text_element)


def _create_minimal_section(section: _Element) -> None:
    """
    Create a minimal section with updated text and nullFlavor.

    Updates the text element, removes all entry elements, and adds
    nullFlavor="NI" to the section element.

    Args:
        section: The section element to update.

    Raises:
        XMLParsingError: If XPath evaluation fails
    """

    namespaces = {"hl7": "urn:hl7-org:v3"}
    text_element = section.find(".//hl7:text", namespaces=namespaces)

    if text_element is None:
        text_element = etree.Element("{urn:hl7-org:v3}text")
        section.append(text_element)

    # update the <text> element with the specific message
    text_element.clear()
    title_element = etree.SubElement(text_element, "title")
    title_element.text = REFINER_OUTPUT_TITLE

    table_element = etree.SubElement(text_element, "table", border="1")
    tr_element = etree.SubElement(table_element, "tr")
    td_element = etree.SubElement(tr_element, "td")
    td_element.text = MINIMAL_SECTION_MESSAGE

    # remove all <entry> elements
    for entry in section.findall(".//hl7:entry", namespaces=namespaces):
        section.remove(entry)

    # clean up all comments from processed sections
    _remove_all_comments(section)

    # add nullFlavor="NI" to the <section> element
    section.attrib["nullFlavor"] = "NI"


# NOTE:
# XML CLEANUP UTILITIES
# =============================================================================


def _remove_all_comments(section: _Element) -> None:
    """
    Remove all XML comments from a processed section.

    After refining a section, comments may no longer be accurate or relevant.
    This ensures clean output without orphaned or misleading comments.

    Args:
        section: The section element to clean up
    """
    xpath_result = section.xpath(".//comment()")
    if isinstance(xpath_result, list):
        for comment in xpath_result:
            if isinstance(comment, etree._Element):
                parent = comment.getparent()
                if parent is not None:
                    parent.remove(comment)


# TODO:
# it might be beneficial to add a function that will add comments back to the <entry>s that we're
# persisting in our refined output (even the minimal sections too). we can discuss this at some
# point in the future


@dataclass
class RefinedDocument:
    """
    Object to hold a reportable condition and its refined eICR XML string.
    """

    reportable_condition: ReportableCondition
    refined_eicr: str


def refine_sync(
    condition_specific_xml_pair: XMLFiles,
    db: DatabaseConnection,
    additional_condition_codes: str | None = None,
    sections_to_include: list[str] | None = None,
) -> list[RefinedDocument]:
    """
    (Primarily for use in AWS Lambda) Takes an eICR/RR pair as `XMLFiles` and produces a list of refined eICR documents by condition code.

    Args:
        condition_specific_xml_pair (XMLFiles): an eICR/RR pair
        db: Established DB connection to use
        additional_condition_codes: Codes to include regardless of whether
            they're discovered in the RR or not
        sections_to_include: list of section codes to include, or None

    Returns:
        list[dict[str, str]]: condition code is the key, refined eICR document is the value
    """

    # Process RR and find conditions
    rr_results = process_rr(condition_specific_xml_pair)
    reportable_conditions = rr_results["reportable_conditions"]

    # create condition-eICR pairs with XMLFiles objects
    condition_eicr_pairs = build_condition_eicr_pairs(
        condition_specific_xml_pair, reportable_conditions
    )

    refined_eicrs = []
    for pair in condition_eicr_pairs:
        condition, condition_specific_xml_pair = pair

        # Combine codes found in the RR + additional codes
        condition_codes = (
            f"{condition.code}," + additional_condition_codes
            if additional_condition_codes is not None
            else condition.code
        )

        # Generate xpaths based on condition codes
        processed_groupers = get_processed_groupers_from_condition_codes(
            condition_codes, db
        )
        condition_codes_xpath = get_condition_codes_xpath(processed_groupers)

        # refine the eICR for this specific condition code.
        refined_eicr = refine_eicr(
            xml_files=condition_specific_xml_pair,
            condition_codes_xpath=condition_codes_xpath,
            sections_to_include=sections_to_include,
        )

        refined_eicrs.append(
            RefinedDocument(reportable_condition=condition, refined_eicr=refined_eicr)
        )

    return refined_eicrs
