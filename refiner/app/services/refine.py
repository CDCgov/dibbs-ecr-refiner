import logging
from copy import deepcopy
from typing import Any

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
)
from ..core.models.types import XMLFiles
from ..db.operations import GrouperOperations
from .file_io import read_json_asset
from .terminology import ProcessedGrouper

log = logging.getLogger(__name__).error


# read json that contains details for refining and is the base of what drives `refine`
REFINER_DETAILS = read_json_asset("refiner_details.json")

# extract section LOINC codes from the REFINER_DETAILS dictionary
SECTION_LOINCS = list(REFINER_DETAILS["sections"].keys())

# ready to use list of all trigger code templateIds for simpler XPath query construction
TRIGGER_CODE_TEMPLATE_IDS = [
    "2.16.840.1.113883.10.20.15.2.3.5",
    "2.16.840.1.113883.10.20.15.2.3.3",
    "2.16.840.1.113883.10.20.15.2.3.4",
    "2.16.840.1.113883.10.20.15.2.3.2",
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
        coded_info_organizers = root.xpath(
            ".//cda:section[cda:code/@code='55112-7']"
            "//cda:entry/cda:organizer[cda:code/@code='RR11']",
            namespaces=namespaces,
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
        observations = coded_info_organizer.xpath(
            ".//cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12']]",
            namespaces=namespaces,
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
            value = observation.xpath(
                ".//cda:value[@codeSystem='2.16.840.1.113883.6.96']",
                namespaces=namespaces,
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

    Processing behavior varies based on provided parameters:

    1. Base Case (validated_message only):
        - Check template IDs
        - Process matching observations or create minimal section

    2. With sections_to_include:
        - Skip processing for included sections
        - Process all other sections normally

    3. With condition_codes:
        - Look up condition code(s) in the groupers table in the terminology database
        - Process sections based on matching codes or templateIds

    4. With both parameters:
        - For included sections: Skip processing
        - For other sections: Look up codes and process normally

    Args:
        xml_files: The XMLFiles container with the eICR document to refine.
        sections_to_include: Optional list of section LOINC codes to preserve.
        condition_codes: Optional comma-separated string of SNOMED condition codes
            to use for filtering sections in an eICR. Each code will be looked up in the
            groupers table in the terminology database to find related clinical codes.

    Returns:
        str: The refined eICR XML document as a string.
    """

    try:
        # parse the eicr document
        validated_message = xml_files.parse_eicr()

        # dictionary that will hold the section processing instructions
        # this is based on the combination of parameters passed to `refine`
        # as well as details from REFINER_DETAILS
        section_processing = dict(REFINER_DETAILS["sections"].items())

        namespaces = {"hl7": "urn:hl7-org:v3"}
        structured_body = validated_message.find(".//hl7:structuredBody", namespaces)

        # if we don't have a structuredBody this is a major problem
        if structured_body is None:
            raise StructureValidationError(
                message="No structured body found in eICR",
                details={"document_type": "eICR"},
            )

        # case 1 and 3:
        # -> prepare xpath expressions for templateIds and/or conditions codes

        # generate templateId xpath (used in all cases as fallback)
        template_xpath = _get_template_id_xpath(TRIGGER_CODE_TEMPLATE_IDS) or ""
        # case 3:
        # -> if condition_codes provided, generate code-based xpath
        #    in the future this should **always** be the case since we
        #    will no longer process **only** an eICR without an RR
        if condition_codes:
            code_xpath = _get_xpath_from_condition_codes(condition_codes) or ""
            combined_xpath = f"{code_xpath} | {template_xpath}"
        else:
            # case 1:
            # -> base case--only templateId xpath
            #    this will be phased out soon
            combined_xpath = template_xpath

        # case 2 and 4:
        # -> handle sections_to_include parameter
        if sections_to_include is not None:
            # case 2 or 4:
            # -> skip processing for included sections
            section_processing = {
                code: details
                for code, details in section_processing.items()
                if code not in sections_to_include
            }

        # process each section based on the applicable case
        for code, details in section_processing.items():
            section = _get_section_by_code(structured_body, code, namespaces)
            if section is None:
                continue

            _process_section(section, combined_xpath, namespaces)

        # Format and return the result
        return etree.tostring(validated_message, encoding="unicode")

    except etree.XMLSyntaxError as e:
        raise XMLParsingError(
            message="Failed to parse eICR document", details={"error": str(e)}
        )
    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message="Failed to evaluate XPath expression in eICR document",
            details={"error": str(e)},
        )


def _process_section(
    section: _Element,
    combined_xpath: str,
    namespaces: dict = {"hl7": "urn:hl7-org:v3"},
) -> None:
    """
    Process a section using the combined XPath query.

    Args:
        section: The XML section element to process
        combined_xpath: XPath query that combines template ID and code conditions
        namespaces: XML namespaces for XPath evaluation
    """

    if not isinstance(section, _Element):
        raise SectionValidationError(
            message="Invalid section element provided",
            details={"section_type": type(section).__name__},
        )

    if not combined_xpath:
        log("Warning: Empty XPath query provided to _process_section")
        _create_minimal_section(section)
        return

    try:
        # Find all matching observations using the combined XPath
        observations = section.xpath(combined_xpath, namespaces=namespaces)

        if observations:
            # if we found matches, preserve those elements
            # find paths to all matching entries to avoid pruning their parents
            entry_paths = []
            for observation in observations:
                entry_path = _find_path_to_entry(observation)
                if entry_path is not None:
                    entry_paths.append(entry_path)

            # remove entries that don't contain relevant observations
            _prune_unwanted_siblings(entry_paths, observations, section)

            # use the original function with whatever parameters it expects
            _update_text_element(section, observations)
        else:
            # if no matches, create a minimal section
            _create_minimal_section(section)
    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message="Invalid XPath expression",
            details={"xpath": combined_xpath, "error": str(e)},
        )


def _get_xpath_from_condition_codes(condition_codes: str | None) -> str:
    """
    Generate XPath from condition codes using the ProcessedGrouper.

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

    # TODO: we are not currently checking the codeSystemName at this time. this is because
    # there is variation even within a single eICR in connection to the codeSystemName.
    # you may see both "LOINC" and "loinc.org" as well as "SNOMED" and "SNOMED CT" in the
    # same message. dynamically altering the XPath with variant names adds complexity and computation;
    # we _can_ post filter, which i would suggest as a function that uses this one as its input.
    # this is why there are two main transformations of the response from the TCR; one that is a dictionary
    # of code systems and codes and another that is a combined XPath for all codes. this way we
    # loop less, search less, and aim for simplicity

    try:
        # process each condition code
        for code in condition_codes.split(","):
            try:
                grouper_row = grouper_ops.get_grouper_by_condition(code)
                if grouper_row:
                    processed = ProcessedGrouper.from_grouper_row(grouper_row)
                    xpath = processed.build_xpath(search_in="observation")
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


def _get_template_id_xpath(template_ids: list[str]) -> str:
    """
    Generate XPath to find elements with specific template IDs.

    Args:
        template_ids: List of template ID root values to search for

    Returns:
        str: XPath expression to find elements with matching template IDs
    """

    template_conditions = [
        f'.//hl7:observation[hl7:templateId[@root="{tid}"]]' for tid in template_ids
    ]

    return " | ".join(template_conditions)


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
        section = structured_body.xpath(xpath_query, namespaces=namespaces)
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

    current_element = element

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

    all_entries = section.xpath(".//hl7:entry", namespaces=namespaces)

    # remove entries not in our keep list
    for entry in all_entries:
        if entry not in entry_paths:
            parent = entry.getparent()
            if parent is not None:
                parent.remove(entry)


def _extract_observation_data(
    observation: _Element,
) -> dict[str, str | bool]:
    """
    Extract data from an observation element.

    Includes checking for trigger code templateId.

    Args:
        observation: The observation element to extract data from.

    Returns:
        dict[str, str | bool]: Dictionary containing the extracted observation data
                               with display_text, code, code_system and is_trigger_code.
    """

    template_id_elements = observation.findall(
        ".//hl7:templateId", namespaces={"hl7": "urn:hl7-org:v3"}
    )
    is_trigger_code = False

    for elem in template_id_elements:
        root = elem.get("root")
        if root in TRIGGER_CODE_TEMPLATE_IDS:
            is_trigger_code = True
            break

    # check of observation is already a code element
    if observation.tag.endswith("code"):
        code_element = observation
    else:
        # otherwise find the other code element
        code_element = observation.find(
            ".//hl7:code", namespaces={"hl7": "urn:hl7-org:v3"}
        )

    # handle the case where the code element might be None
    display_text = code_element.get("displayName") if code_element is not None else None
    code = code_element.get("code") if code_element is not None else None
    code_system = (
        code_element.get("codeSystemName") if code_element is not None else None
    )

    data = {
        "display_text": display_text,
        "code": code,
        "code_system": code_system,
        "is_trigger_code": is_trigger_code,
    }
    return data


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
    title.text = "Output from CDC PRIME DIBBs `message-refiner` API by request of STLT"

    table_element = etree.SubElement(text_element, "table", border="1")
    header_row = etree.SubElement(table_element, "tr")
    headers = ["Display Text", "Code", "Code System", "Trigger Code Observation"]

    for header in headers:
        th = etree.SubElement(header_row, "th")
        th.text = header

    # add observation data to table
    for observation in observations:
        data = _extract_observation_data(observation)
        row = etree.SubElement(table_element, "tr")
        for key in headers[:-1]:  # Exclude the last header as it's for the boolean flag
            td = etree.SubElement(row, "td")
            td.text = data[key.lower().replace(" ", "_")]

        # add boolean flag for trigger code observation
        td = etree.SubElement(row, "td")
        td.text = "TRUE" if data["is_trigger_code"] else "FALSE"

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
    title_element.text = (
        "Output from CDC PRIME DIBBs `message-refiner` API by request of STLT"
    )

    table_element = etree.SubElement(text_element, "table", border="1")
    tr_element = etree.SubElement(table_element, "tr")
    td_element = etree.SubElement(tr_element, "td")
    td_element.text = "Section details have been removed as requested"

    # remove all <entry> elements
    for entry in section.findall(".//hl7:entry", namespaces=namespaces):
        section.remove(entry)

    # add nullFlavor="NI" to the <section> element
    section.attrib["nullFlavor"] = "NI"


def build_condition_eicr_pairs(
    parsed_eicr: etree._Element,
    reportable_conditions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Generate pairs of reportable conditions and a deepcopy of the original eICR XML.

    Each reportable condition gets its own copy of the eICR document so that
    condition-specific refinement can be performed independently.

    Args:
        parsed_eicr (etree._Element): The original parsed eICR XML document.
        reportable_conditions (list[dict]): List of reportable condition objects with 'code' keys.

    Returns:
        list[dict[str, Any]]: A list of dictionaries, each containing a `reportable_condition` and `eicr_copy`.
    """
    condition_eicr_pairs = []

    for condition in reportable_conditions:
        condition_eicr_pairs.append(
            {
                "reportable_condition": condition,
                "eicr_copy": deepcopy(parsed_eicr),
            }
        )

    return condition_eicr_pairs
