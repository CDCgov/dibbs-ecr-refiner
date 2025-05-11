import logging

from lxml import etree

from ..core.exceptions import SectionValidationError
from ..core.models.types import XMLFiles
from .file_io import read_json_asset

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


def get_reportable_conditions(root: etree.Element) -> str | None:
    """
    Get SNOMED CT codes from the Report Summary section.

    Scan the Report Summary section for SNOMED CT codes and return
    them as a comma-separated string, or None if none found.

    Args:
        root: The root element of the XML document to parse.

    Returns:
        str | None: Comma-separated SNOMED CT codes or None if none found.
    """

    codes = []

    namespaces = {
        "cda": "urn:hl7-org:v3",
        "sdtc": "urn:hl7-org:sdtc",
        "voc": "http://www.lantanagroup.com/voc",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }
    # find sections with loinc code 55112-7
    for section in root.xpath(
        ".//cda:section[cda:code/@code='55112-7']", namespaces=namespaces
    ):
        # find all values with the specified codeSystem
        values = section.xpath(
            ".//cda:value[@codeSystem='2.16.840.1.113883.6.96']/@code",
            namespaces=namespaces,
        )
        codes.extend(values)

    return ",".join(codes) if codes else None


def process_rr(xml_files: XMLFiles) -> dict:
    """
    Process the RR XML document to extract relevant information.

    Args:
        xml_files: Container with both eICR and RR XML content
                  (currently only using RR)

    Returns:
        dict: Extracted information from the RR document
    """

    rr_root = xml_files.parse_rr()

    return {
        "reportable_conditions": get_reportable_conditions(rr_root),
    }


def refine_eicr(
    xml_files: XMLFiles,
    sections_to_include: list[str] | None = None,
    clinical_services: dict[str, list[str]] | None = None,
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

    3. With clinical_services:
        - Check both template IDs and codes
        - Process matching observations or create minimal section

    4. With both parameters:
        - For included sections: Check template IDs and codes
        - For other sections: Process normally

    Args:
        xml_files: The NamedTuple XMLFiles that contains the eICR XML document to refine.
        sections_to_include: Optional list of section LOINC codes. When provided
            alone, preserves these sections. When provided with clinical_services,
            focuses the search to these sections.
        clinical_services: Optional dictionary of clinical service codes from the
            Trigger Code Reference Service to check within sections.

    Returns:
        str: The refined eICR XML document as a string.
    """

    # parse the eicr document
    validated_message = xml_files.parse_eicr()

    # dictionary that will hold the section processing instructions
    # this is based on the combination of parameters passed to `refine`
    # as well as deails from REFINER_DETAILS
    section_processing = dict(REFINER_DETAILS["sections"].items())

    namespaces = {"hl7": "urn:hl7-org:v3"}
    structured_body = validated_message.find(".//hl7:structuredBody", namespaces)

    # case 2: if only sections_to_include is provided, remove these sections from section_processing
    if sections_to_include is not None and clinical_services is None:
        section_processing = {
            key: value
            for key, value in section_processing.items()
            if key not in sections_to_include
        }

    # process sections
    for code, details in section_processing.items():
        section = _get_section_by_code(structured_body, code)
        if section is None:
            continue  # go to the next section if not found

        # case 4: search in sections_to_include for clinical_services; for sections
        # not in sections_to_include, search for templateIds
        if sections_to_include is not None and clinical_services is not None:
            if code in sections_to_include:
                combined_xpaths = _generate_combined_xpath(
                    template_ids=TRIGGER_CODE_TEMPLATE_IDS,
                    clinical_services_dict=clinical_services,
                )
                clinical_services_codes = [
                    code for codes in clinical_services.values() for code in codes
                ]
                _process_section(
                    section,
                    combined_xpaths,
                    namespaces,
                    TRIGGER_CODE_TEMPLATE_IDS,
                    clinical_services_codes,
                )
            else:
                combined_xpaths = _generate_combined_xpath(
                    template_ids=TRIGGER_CODE_TEMPLATE_IDS,
                    clinical_services_dict={},
                )
                _process_section(
                    section, combined_xpaths, namespaces, TRIGGER_CODE_TEMPLATE_IDS
                )

        # case 3: process all sections with clinical_services (no sections_to_include)
        elif clinical_services is not None and sections_to_include is None:
            combined_xpaths = _generate_combined_xpath(
                template_ids=TRIGGER_CODE_TEMPLATE_IDS,
                clinical_services_dict=clinical_services,
            )
            clinical_services_codes = [
                code for codes in clinical_services.values() for code in codes
            ]
            _process_section(
                section,
                combined_xpaths,
                namespaces,
                TRIGGER_CODE_TEMPLATE_IDS,
                clinical_services_codes,
            )

        # case 1: no parameters, process all sections normally
        # case 2: process sections not in sections_to_include
        else:
            combined_xpaths = _generate_combined_xpath(
                template_ids=TRIGGER_CODE_TEMPLATE_IDS, clinical_services_dict={}
            )
            _process_section(
                section, combined_xpaths, namespaces, TRIGGER_CODE_TEMPLATE_IDS
            )

    # TODO: there may be sections that are not standard but appear in an eICR that
    # we could either decide to add to the refiner_details.json or use this code
    # before returning the refined output that removes sections that are not required
    for section in structured_body.findall(".//hl7:section", namespaces):
        section_code = section.find(".//hl7:code", namespaces).get("code")
        if section_code not in SECTION_LOINCS:
            parent = section.getparent()
            parent.remove(section)

    return etree.tostring(validated_message, encoding="unicode")


def _process_section(
    section: etree.Element,
    combined_xpaths: str,
    namespaces: dict,
    template_ids: list[str],
    clinical_services_codes: list[str] | None = None,
) -> None:
    """
    Process a section by checking elements and updating observations.

    Args:
        section: The section element to process.
        combined_xpaths: The combined XPath expression for finding elements.
        namespaces: The namespaces to use in XPath queries.
        template_ids: The list of template IDs to check.
        clinical_services_codes: Optional list of clinical service codes to check.
    """

    check_elements = _are_elements_present(
        section, "templateId", template_ids, namespaces
    )
    if clinical_services_codes:
        check_elements |= _are_elements_present(
            section, "code", clinical_services_codes, namespaces
        )

    if check_elements:
        observations = _get_observations(section, combined_xpaths, namespaces)
        if observations:
            paths = [_find_path_to_entry(obs) for obs in observations]
            _prune_unwanted_siblings(paths, observations)
            _update_text_element(section, observations)
        else:
            _create_minimal_section(section)
    else:
        _create_minimal_section(section)


def _generate_combined_xpath(
    template_ids: list[str], clinical_services_dict: dict[str, list[str]]
) -> str:
    """
    Generate a combined XPath expression for templateIds and all codes across all systems, ensuring they are within 'observation' elements.
    """

    xpath_conditions = []

    # add templateId conditions within <observation> elements if needed
    if template_ids:
        template_id_conditions = [
            f'.//hl7:observation[hl7:templateId[@root="{tid}"]]' for tid in template_ids
        ]
        xpath_conditions.extend(template_id_conditions)

    # add code conditions within <observation> elements
    for codes in clinical_services_dict.values():
        for code in codes:
            code_conditions = f'.//hl7:observation[hl7:code[@code="{code}"]]'
            xpath_conditions.append(code_conditions)

    # combine all conditions into a single XPath query using the union operator
    combined_xpath = " | ".join(xpath_conditions)
    return combined_xpath


def _get_section_by_code(
    structured_body: etree.Element,
    code: str,
    namespaces: dict = {"hl7": "urn:hl7-org:v3"},
) -> etree.Element:
    """
    Get a section from structuredBody by its LOINC code.

    Args:
        structured_body: The structuredBody element to search within.
        code: LOINC code of the section to retrieve.
        namespaces: The namespaces to use for element search. Defaults to hl7.

    Returns:
        etree.Element: The section element with the given LOINC code.
    """

    xpath_query = f'.//hl7:section[hl7:code[@code="{code}"]]'
    section = structured_body.xpath(xpath_query, namespaces=namespaces)
    if section is not None and len(section) == 1:
        return section[0]


def _get_observations(
    section: etree.Element,
    combined_xpath: str,
    namespaces: dict = {"hl7": "urn:hl7-org:v3"},
) -> list[etree.Element]:
    """
    Get matching observations using combined XPath query.

    Args:
        section: The section element to retrieve observations from.
        combined_xpath: Combined XPath using TCR codes or templateId root values.
        namespaces: The namespaces for element search. Defaults to hl7.

    Returns:
        list[etree.Element]: List of matching observation elements.
    """

    # use a list to store the final list of matching observation elements
    observations = []
    # use a set to store elements for uniqueness; trigger code data _may_ match clinical services
    seen = set()

    # search once for matching elements using the combined XPath expression
    matching_elements = section.xpath(combined_xpath, namespaces=namespaces)
    for element in matching_elements:
        if element not in seen:
            seen.add(element)
            observations.append(element)

    # TODO: we are not currently checking the codeSystemName at this time. this is because
    # there is variation even within a single eICR in connection to the codeSystemName.
    # you may see both "LOINC" and "loinc.org" as well as "SNOMED" and "SNOMED CT" in the
    # same message. dynamically altering the XPath with variant names adds complexity and computation;
    # we _can_ post filter, which i would suggest as a function that uses this one as its input.
    # this is why there are two main transformations of the response from the TCR; one that is a dictionary
    # of code systems and codes and another that is a combined XPath for all codes. this way we
    # loop less, search less, and aim for simplicity

    return observations


def _are_elements_present(
    section: etree.Element,
    search_type: str,
    search_values: list[str],
    namespaces: dict = {"hl7": "urn:hl7-org:v3"},
) -> bool:
    """
    Check if specified elements exist in a section.

    Args:
        section: The section element to search within.
        search_type: Type of search ('templateId' or 'code').
        search_values: List of values to search for (template IDs or codes).
        namespaces: The namespaces for element search. Defaults to hl7.

    Returns:
        bool: True if any specified elements are present, False otherwise.
    """

    if search_type == "templateId":
        xpath_queries = [
            f'.//hl7:templateId[@root="{value}"]' for value in search_values
        ]
    elif search_type == "code":
        xpath_queries = [f'.//hl7:code[@code="{value}"]' for value in search_values]

    combined_xpath = " | ".join(xpath_queries)
    return bool(section.xpath(combined_xpath, namespaces=namespaces))


def _find_path_to_entry(element: etree.Element) -> list[etree.Element]:
    """
    Helper function to find the path from a given element to the parent <entry> element.
    """

    path = []
    current_element = element
    while current_element.tag != "{urn:hl7-org:v3}entry":
        path.append(current_element)
        current_element = current_element.getparent()
        if current_element is None:
            raise ValueError("Parent <entry> element not found.")
    path.append(current_element)  # Add the <entry> element
    path.reverse()  # Reverse to get the path from <entry> to the given element
    return path


def _prune_unwanted_siblings(
    paths: list[list[etree.Element]], desired_elements: list[etree.Element]
):
    """
    Prune unwanted sibling elements.

    Args:
        paths: List of paths, each containing elements from entry to observation.
        desired_elements: List of observation elements to keep.
    """

    # flatten the list of paths and remove duplicates
    all_elements_to_keep = {elem for path in paths for elem in path}

    # iterate through all collected paths to prune siblings
    for path in paths:
        for element in path:
            parent = element.getparent()
            if parent is not None:
                siblings = parent.findall(element.tag)
                for sibling in siblings:
                    # only remove siblings that are not in the collected elements
                    if sibling not in all_elements_to_keep:
                        parent.remove(sibling)


def _extract_observation_data(
    observation: etree.Element,
) -> dict[str, str | bool]:
    """
    Extract data from an observation element.

    Includes checking for trigger code template ID.

    Args:
        observation: The observation element to extract data from.

    Returns:
        dict[str, str | bool]: Dictionary containing the extracted observation data.
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

    data = {
        "display_text": observation.find(
            ".//hl7:code", namespaces={"hl7": "urn:hl7-org:v3"}
        ).get("displayName"),
        "code": observation.find(
            ".//hl7:code", namespaces={"hl7": "urn:hl7-org:v3"}
        ).get("code"),
        "code_system": observation.find(
            ".//hl7:code", namespaces={"hl7": "urn:hl7-org:v3"}
        ).get("codeSystemName"),
        "is_trigger_code": is_trigger_code,
    }
    return data


def _create_or_update_text_element(observations: list[etree.Element]) -> etree.Element:
    """
    Create or update a text element with observation data.

    Args:
        observations: List of observation elements to include in the text.

    Returns:
        etree.Element: The created or updated text element.
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


def _update_text_element(
    section: etree.Element, observations: list[etree.Element]
) -> None:
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


def _create_minimal_section(section: etree.Element) -> None:
    """
    Create a minimal section with updated text and nullFlavor.

    Updates the text element, removes all entry elements, and adds
    nullFlavor="NI" to the section element.

    Args:
        section: The section element to update.
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
