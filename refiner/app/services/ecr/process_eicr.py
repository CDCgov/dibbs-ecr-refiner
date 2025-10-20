import uuid
from typing import Literal, cast

from lxml import etree
from lxml.etree import _Element

from ...core.exceptions import (
    StructureValidationError,
    XMLParsingError,
)

# NOTE:
# CONSTANTS AND CONFIGURATION
# =============================================================================


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
    Process a section by filtering its entries based on provided condition codes.

    This function first neutralizes the section's direct `<text>` and `<code>`
    children in-place. This prevents the search from matching the section's
    defining code or its narrative block, ensuring that filtering is limited
    to structured clinical data within `<entry>` elements.

    The filtering logic then proceeds in three steps:
    STEP 1 (Context Filter): Find clinical elements matching SNOMED condition codes.
    STEP 2 (Trigger Identification): Among contextual matches, identify trigger codes.
    STEP 3 (Entry Processing): Preserve relevant entries and generate section summary.

    The key principle: trigger code identification only happens within an already-filtered
    context, ensuring we don't keep random trigger codes unrelated to the condition.
    The section's original `code` attribute is reliably restored after processing.

    Args:
        section: The XML section element to process.
        combined_xpath: XPath query from ProcessedCondition codes.
        namespaces: XML namespaces for XPath evaluation.
        section_config: Configuration for this section from refiner_details.json.
        version: eICR version being processed.
    """

    # NOTE: neutralize section's direct <code> and <text> children to exclude from search
    # * this prevents matching the section's defining code or narrative text, ensuring
    #   the search is limited to structured clinical entries
    section_code_element = section.find("./hl7:code", namespaces=namespaces)
    original_code_value = None
    if section_code_element is not None:
        original_code_value = section_code_element.get("code")
        if original_code_value and "code" in section_code_element.attrib:
            # swap the code value with a temporary non-matching one to prevent
            # it from being found, while preserving attribute order
            section_code_element.set("code", f"TEMP_SWAP_{uuid.uuid4()}")

    text_element = section.find("./hl7:text", namespaces=namespaces)
    if text_element is not None:
        # clears all children and text content
        text_element.clear()

    try:
        if not combined_xpath:
            # no condition codes provided -> create a minimal section and exit
            _create_minimal_section(section)
            return

        # this block contains the core filtering logic. It's wrapped in a try/except
        # to handle XPath errors specifically, while the outer try/finally ensures
        # the section's code attribute is always restored
        try:
            # STEP 1: CONTEXT FILTERING
            # * find all clinical elements matching our condition codes
            # * this is our primary filter; only contextually relevant elements proceed
            contextual_matches = _find_condition_relevant_elements(
                section, combined_xpath, namespaces
            )

            if not contextual_matches:
                # no matching clinical elements found for our condition
                _create_minimal_section(section)
                return

            # STEP 2: TRIGGER IDENTIFICATION WITHIN CONTEXT
            # * among our contextual matches, identify which are trigger codes
            # * this ensures trigger codes are only identified within relevant clinical context
            #   so that the updated <text> element can call out trigger code matches from coded matches
            trigger_analysis = _analyze_trigger_codes_in_context(
                contextual_matches, section_config
            )

            # STEP 3: PROCESS ENTRIES AND GENERATE OUTPUT
            # * handle entry-level operations and create final section content
            _preserve_relevant_entries_and_generate_summary(
                section, contextual_matches, trigger_analysis, namespaces
            )

        except etree.XPathEvalError as e:
            raise XMLParsingError(
                message="Invalid XPath expression",
                details={"xpath": combined_xpath, "error": str(e)},
            )
    finally:
        # always restore the original code attribute to maintain spec compliance
        if section_code_element is not None and original_code_value:
            section_code_element.set("code", original_code_value)


def _find_condition_relevant_elements(
    section: _Element, combined_xpath: str, namespaces: dict
) -> list[_Element]:
    """
    STEP 1: Find clinical elements matching SNOMED condition codes.

    This is the context filter - only elements relevant to our reportable
    condition should proceed to the next step.

    Args:
        section: The XML section element to search within
        combined_xpath: XPath query from ProcessedCondition codes
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
    thead_row = etree.SubElement(table_element, "thead")
    header_row = etree.SubElement(thead_row, "tr")
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
    tbody = etree.SubElement(table_element, "tbody")
    row = etree.SubElement(tbody, "tr")

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
    thead_element = etree.SubElement(table_element, "thead")
    tr_element = etree.SubElement(thead_element, "tr")
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

# TODO:
# it might be beneficial to add a function that will add comments back to the <entry>s that we're
# persisting in our refined output (even the minimal sections too). we can discuss this at some
# point in the future


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
