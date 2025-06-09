import logging
from typing import Any, cast

from lxml import etree
from lxml.etree import _Element

from ..core.exceptions import (
    ConditionCodeError,
    DatabaseConnectionError,
    DatabaseQueryError,
    ResourceNotFoundError,
    SectionValidationError,
    StructureValidationError,
    XMLParsingError,
    XMLValidationError,
)
from ..core.models.types import XMLFiles
from ..db.operations import GrouperOperations
from .file_io import read_json_asset
from .terminology import ProcessedGrouper

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
OBSERVATION_TABLE_HEADERS = [
    "Display Text",
    "Code",
    "Code System",
    "Matching Condition Code",
]


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


# In lxml, use _Element for type hints and etree.Element in code.
# -> _Element (from lxml.etree) is the actual type of xml element objects, suitable for
#    type annotations and for static type checkers
# -> etree.Element is a factory function that creates and returns _Element instances; use
#    it in code to create nodes.
# NOTE: Do not use etree.Element for type hints; it's not a class, but a function.
# See: https://lxml.de/api/lxml.etree._Element-class.html
# NOTE: this will change in lxml 6.0
# See: on this PR: https://github.com/lxml/lxml/pull/405


def get_reportable_conditions(root: _Element) -> list[dict[str, str]] | None:
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
        coded_info_organizers = (
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
            condition = {"code": code, "displayName": display_name}
            if condition not in conditions:
                conditions.append(condition)

    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message="Failed to evaluate XPath expression in RR document",
            details={"xpath_error": str(e)},
        )

    return conditions if conditions else None


def process_rr(xml_files: XMLFiles) -> dict:
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
    sections_to_include: list[str] | None = None,
    condition_codes: str | None = None,
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
        condition_codes: Comma-separated string of SNOMED condition codes
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

    if not condition_codes:
        raise ConditionCodeError(
            "No condition codes provided to refine_eicr; at least one is required."
        )

    try:
        # parse the eicr document
        validated_message = xml_files.parse_eicr()

        # use the constant defined at the top of refine.py
        # TODO: this only supports eICR 1.1 so we'll need to eventually move to
        # to the refiner_config.json files with the updated structure for supporting
        # both eICR 1.1 and eICR 3.1
        section_loincs = SECTION_LOINCS

        namespaces = {"hl7": "urn:hl7-org:v3"}
        structured_body = validated_message.find(".//hl7:structuredBody", namespaces)

        # if we don't have a structuredBody this is a major problem
        if structured_body is None:
            raise StructureValidationError(
                message="No structured body found in eICR",
                details={"document_type": "eICR"},
            )

        # always require condition_codes
        # generate code-based xpath for relevant clinical codes
        code_xpath = _get_xpath_from_condition_codes(condition_codes) or ""

        # If sections_to_include is given, skip processing for those sections
        if sections_to_include is not None:
            section_loincs = {
                code for code in section_loincs if code not in sections_to_include
            }

        # Process each section based on the applicable rules
        for code in section_loincs:
            section = _get_section_by_code(structured_body, code, namespaces)
            if section is None:
                continue

            _process_section(section, code_xpath, namespaces)

        # Format and return the result
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


def _process_section(
    section: _Element,
    combined_xpath: str,
    namespaces: dict = {"hl7": "urn:hl7-org:v3"},
) -> None:
    """
    Process a section using only ProcessedGrouper-generated XPaths.

    Args:
        section: The XML section element to process
        combined_xpath: XPath query from ProcessedGrouper codes
        namespaces: XML namespaces for XPath evaluation
    """

    if not isinstance(section, _Element):
        raise SectionValidationError(
            message="Invalid section element provided",
            details={"section_type": type(section).__name__},
        )

    if not combined_xpath:
        # no condition codes provided - create minimal section
        _create_minimal_section(section)
        return

    try:
        # find all matching observations using ProcessedGrouper XPath
        observations = cast(
            list[_Element], section.xpath(combined_xpath, namespaces=namespaces)
        )

        if observations:
            # process matching observations
            entry_paths = []
            for observation in observations:
                entry_path = _find_path_to_entry(observation)
                if entry_path is not None:
                    entry_paths.append(entry_path)

            # remove entries that don't contain relevant observations
            _prune_unwanted_siblings(entry_paths, observations, section)

            # update section text with observation data
            _update_text_element(section, observations)
        else:
            # no matching observations found - create minimal section
            _create_minimal_section(section)

    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message="Invalid XPath expression",
            details={"xpath": combined_xpath, "error": str(e)},
        )


def _get_xpath_from_condition_codes(condition_codes: str | None) -> str:
    """
    Generate XPath from condition codes using ProcessedGrouper only.

    Takes a comma-separated string of condition codes, queries each one
    in the groupers database, and builds XPath expressions to find any
    matching codes in HL7 XML documents.

    Args:
        condition_codes: Comma-separated SNOMED condition codes, or None

    Returns:
        str: Combined XPath expression to find relevant elements, or empty string

    Raises:
        DatabaseConnectionError
        DatabaseQueryError
        ResourceNotFoundError
        ConditionCodeError
    """

    if not condition_codes:
        return ""

    grouper_ops = GrouperOperations()
    xpath_conditions = []

    try:
        # process each condition code
        for code in condition_codes.split(","):
            code = code.strip()
            try:
                grouper_row = grouper_ops.get_grouper_by_condition(code)
                if grouper_row:
                    processed = ProcessedGrouper.from_grouper_row(grouper_row)
                    # defaults to "observation"
                    xpath = processed.build_xpath()
                    if xpath:
                        xpath_conditions.append(xpath)
            except (DatabaseConnectionError, DatabaseQueryError) as e:
                # log but continue with other codes
                log(f"Database error processing condition code {code}: {str(e)}")
            except ResourceNotFoundError:
                # log that the code wasn't found but continue
                log(f"Condition code not found: {code}")

    except Exception as e:
        raise ConditionCodeError(
            message="Error processing condition codes",
            details={"error": str(e), "condition_codes": condition_codes},
        )

    # combine XPath conditions with union operator
    if not xpath_conditions:
        return ""

    return " | ".join(xpath_conditions)


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
        section = cast(
            list[_Element], structured_body.xpath(xpath_query, namespaces=namespaces)
        )
        if section is not None and len(section) == 1:
            return section[0]
    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message=f"Failed to evaluate XPath for section code {loinc_code}",
            details={"xpath_query": xpath_query, "error": str(e)},
        )
    return None


def _find_path_to_entry(element: _Element) -> _Element | None:
    """
    Find the nearest entry ancestor of an element.

    Args:
        element: The element to find the entry for

    Returns:
        The entry element, or None if no entry ancestor found
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
    observations: list[_Element],
    section: _Element,
) -> None:
    """
    Remove entries that don't contain relevant observations.

    Args:
        entry_paths: List of entry elements to preserve
        observations: List of observation elements that matched our search
        section: The section being processed
    """

    # find all entries in the section
    namespaces = {"hl7": "urn:hl7-org:v3"}

    all_entries = cast(
        list[_Element], section.xpath(".//hl7:entry", namespaces=namespaces)
    )

    # remove entries not in our keep list
    for entry in all_entries:
        if entry not in entry_paths:
            parent = entry.getparent()
            if parent is not None:
                parent.remove(entry)


def _extract_observation_data(
    observation: _Element,
) -> dict[str, str | bool | None]:
    """
    Extract data from an observation element.

    No longer checks for trigger code templateIds since we're using ProcessedGrouper only.

    Args:
        observation: The observation element to extract data from.

    Returns:
        dict[str, str | bool]: Dictionary containing the extracted observation data
                               with display_text, code, code_system and is_trigger_code.
    """

    # find the code element
    code_element: _Element | None = (
        observation
        if observation.tag.endswith("code")
        else observation.find(".//hl7:code", namespaces={"hl7": "urn:hl7-org:v3"})
    )

    # extract basic information
    display_text = code_element.get("displayName") if code_element is not None else None
    code = code_element.get("code") if code_element is not None else None
    code_system = (
        code_element.get("codeSystemName") if code_element is not None else None
    )

    return {
        "display_text": display_text,
        "code": code,
        "code_system": code_system,
        "is_trigger_code": False,  # Always False since we're not using templateIds
    }


def _create_or_update_text_element(observations: list[_Element]) -> _Element:
    """
    Create or update a text element with observation data.

    Args:
        observations: List of observation elements to include in the text.

    Returns:
        _Element: The created or updated text element.
    """

    text_element = etree.Element("{urn:hl7-org:v3}text")
    title = etree.SubElement(text_element, "title")
    title.text = REFINER_OUTPUT_TITLE

    table_element = etree.SubElement(text_element, "table", border="1")
    header_row = etree.SubElement(table_element, "tr")
    headers = OBSERVATION_TABLE_HEADERS

    for header in headers:
        th = etree.SubElement(header_row, "th")
        th.text = header

    # add observation data to table
    for observation in observations:
        data = _extract_observation_data(observation)
        row = etree.SubElement(table_element, "tr")
        for key in headers[:-1]:  # Exclude the last header as it's for the boolean flag
            td = etree.SubElement(row, "td")
            td.text = cast(str | None, data[key.lower().replace(" ", "_")])

        # add boolean flag for matching condition code (always TRUE since we only keep matches)
        td = etree.SubElement(row, "td")
        td.text = "TRUE"  # Always TRUE since we filtered to only matching observations

    return text_element


def _update_text_element(section: _Element, observations: list[_Element]) -> None:
    """
    Update a section's text element with observation information.

    Args:
        section: The section element containing the text element to update.
        observations: List of observation elements to include in the text.
    """

    new_text_element = _create_or_update_text_element(observations)

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

    # add nullFlavor="NI" to the <section> element
    section.attrib["nullFlavor"] = "NI"


def build_condition_eicr_pairs(
    original_xml_files: XMLFiles,
    reportable_conditions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
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
            {
                "reportable_condition": condition,
                "xml_files": condition_xml_files,
            }
        )

    return condition_eicr_pairs
