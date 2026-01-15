from typing import Literal, cast

from lxml import etree
from lxml.etree import _Element

from app.services.ecr.models import RefinementPlan
from app.services.terminology import ConfigurationPayload, ProcessedConfiguration

from ...core.exceptions import (
    StructureValidationError,
    XMLValidationError,
)
from ...core.models.types import XMLFiles
from ..format import remove_element
from .models import NamespaceMap
from .process_eicr import (
    create_minimal_section,
    get_section_by_code,
    get_section_loinc_codes,
    process_section,
)
from .specification import detect_eicr_version, load_spec

# NOTE:
# PUBLIC API FUNCTIONS
# =============================================================================


def get_file_size_reduction_percentage(unrefined_eicr: str, refined_eicr: str) -> int:
    """
    Given an unrefined document eICR document and a refined eICR document, calculate the percentage in which the file size was reduced post-refinement.

    Args:
        unrefined_eicr (str): An unrefined eICR XML document
        refined_eicr (str): A refined eICR XML document
    Returns:
        int: Integer representing the percentage in which the file size was reduced.
    """

    unrefined_bytes = len(unrefined_eicr.encode("utf-8"))
    refined_bytes = len(refined_eicr.encode("utf-8"))

    if unrefined_bytes == 0:
        return 0

    percent_diff = (unrefined_bytes - refined_bytes) / unrefined_bytes * 100
    return round(percent_diff)


def create_refinement_plan(
    processed_configuration: ProcessedConfiguration, xml_files: XMLFiles
) -> RefinementPlan:
    """
    Create a RefinementPlan by combining configuration rules and the sections present in the eICR document.

    This function lives in the orchestration layer (`testing.py`) because it
    requires access to both the processed configuration data and the raw XML
    file to create the final, actionable plan.

    Args:
        processed_configuration: The processed configuration containing terminology
                                 and section processing rules.
        xml_files: The XMLFiles object containing the eICR to be inspected.

    Returns:
        A RefinementPlan containing the exact instructions for `refine_eicr`.
    """

    # get eICR root and pull out the structuredBody
    eicr_root = xml_files.parse_eicr()
    structured_body = eicr_root.find(
        ".//hl7:structuredBody", namespaces={"hl7": "urn:hl7-org:v3"}
    )

    # discover which sections are present in this specific eICR
    if structured_body is None:
        present_section_codes = []
    else:
        present_section_codes = get_section_loinc_codes(structured_body)

    # create a map of the rules from the configuration for efficient lookup
    rules_map: dict[str, str] = {
        rule["code"]: rule["action"]
        for rule in processed_configuration.section_processing
    }

    # build the final instruction set: for each section in the document,
    # find its rule, defaulting to "remove" if no rule is specified
    final_instructions: dict[str, Literal["retain", "refine", "remove"]] = {
        code: cast(Literal["retain", "refine", "remove"], rules_map.get(code, "remove"))
        for code in present_section_codes
    }

    return RefinementPlan(
        xpath=processed_configuration.build_xpath(),
        section_instructions=final_instructions,
    )


def refine_eicr(
    xml_files: XMLFiles,
    plan: RefinementPlan,
) -> str:
    """
    Refine an eICR XML document by executing a provided RefinementPlan.

    This function is a "pure executor." It does not make decisions; it only
    carries out the instructions given to it in the plan.

    Processing behavior:
        - It iterates through the instructions in the plan.
        - For each section, it performs one of three actions:
          - retain: Leaves the section completely unmodified.
          - remove: Replaces the section with a minimal "stub" section.
          - refine: Processes the section using the plan's XPath to filter entries.

    Args:
        xml_files: The XMLFiles container with the eICR document to refine.
        plan: A complete, actionable plan for refining the eICR.

    Returns:
        str: The refined eICR XML document as a string.

    Raises:
        XMLValidationError: If the XML is invalid.
        StructureValidationError: If the document structure is invalid.
    """

    try:
        # parse the eicr document
        eicr_root = xml_files.parse_eicr()

        namespaces: NamespaceMap = {"hl7": "urn:hl7-org:v3"}
        structured_body = eicr_root.find(".//hl7:structuredBody", namespaces)

        # if we don't have a structuredBody this is a major problem
        if structured_body is None:
            raise StructureValidationError(
                message="No structured body found in eICR",
                details={"document_type": "eICR"},
            )

        # 1. detect version
        version = detect_eicr_version(eicr_root)

        # 2. load specification
        specification = load_spec(version)

        for section_code, action in plan.section_instructions.items():
            section = get_section_by_code(
                structured_body=structured_body,
                loinc_code=section_code,
                namespaces=namespaces,
            )
            if section is None:
                continue

            if action == "retain":
                # retain means that we're not processing this section so we continue
                continue
            if action == "remove":
                # we will just force a minimal section
                create_minimal_section(section=section, removal_reason="configured")
            elif action == "refine":
                section_specification = specification.sections.get(section_code)
                process_section(
                    section=section,
                    combined_xpath=plan.xpath,
                    namespaces=namespaces,
                    section_specification=section_specification,
                    version=version,
                )

        # format and return the result
        return etree.tostring(eicr_root, encoding="unicode")

    except etree.XMLSyntaxError as e:
        raise XMLValidationError(
            message="Failed to parse eICR document", details={"error": str(e)}
        )
    except etree.XPathEvalError as e:
        raise XMLValidationError(
            message="Failed to evaluate XPath expression in eICR document",
            details={"error": str(e)},
        )


def refine_rr(
    jurisdiction_id: str,
    xml_files: XMLFiles,
    payload: ConfigurationPayload,
) -> str:
    """
    Refine a RR XML document from anything not reportable to the specified jurisdiction.

    Processing behavior:
        - It iterates through the RR and removes information common to all RR's.
        - It removes anything not applicable to the specified jurisdiction
        - It loops through all the condition observations in the reportability RC
            - Anything that isn't RRSVS1 reportable is filtered out
            - Of the remaining reportable observations, anything that isn't specified
              in the refinement configurations are filtered out
            - For anything remaining, any codes that aren't specified within the
              in the configuration RSG or custom codes are filtered out.

    Args:
        jurisdiction_id: the ID of the jurisdiction we're currently processing information for
        xml_files: The XMLFiles container with the eICR document to refine.
        payload: The ConfigurationPayload for the corresponding eICR.

    Returns:
        str: The refined RR XML document as a string.

    Raises:
        XMLValidationError: If the XML is invalid.
        StructureValidationError: If the document structure is invalid.
    """

    # look for structured body
    rr_root = xml_files.parse_rr()
    namespaces: NamespaceMap = {
        "hl7": "urn:hl7-org:v3",
        "cda": "urn:hl7-org:v3",
    }

    # now, move on to processing the actual RR body
    structured_body = rr_root.find(".//hl7:structuredBody", namespaces)

    if structured_body is None:
        raise StructureValidationError(
            message="No structured body found in RR",
            details={"document_type": "RR"},
        )
    rr11_organizers = cast(
        list[_Element],
        structured_body.xpath(
            ".//cda:section[cda:code/@code='55112-7']//cda:entry/cda:organizer[cda:code/@code='RR11']",
            namespaces=namespaces,
        ),
    )

    if not rr11_organizers and not rr11_organizers[0]:
        raise StructureValidationError(
            message="Missing required RR11 Coded Information Organizer",
            details={
                "document_type": "RR",
                "error": "RR11 organizer not found in Summary Section",
            },
        )

    rr_organizer = rr11_organizers[0]

    # Compile the set of conditions the jurisdiction has a configuration
    # for as represented by the child_rsg_snomed codes that exist in the payload
    codes_to_keep = set()
    for condition in payload.conditions:
        codes_to_keep.update(condition.child_rsg_snomed_codes)

    components_to_check = cast(
        list[_Element],
        rr_organizer.xpath(
            ".//cda:component[cda:observation[cda:templateId/@root='2.16.840.1.113883.10.20.15.2.3.12']]",
            namespaces=namespaces,
        ),
    )

    for component in components_to_check:
        observation = component.find("cda:observation", namespaces)
        if observation is None:
            continue

        value = observation.find("cda:value", namespaces)
        if value is None:
            continue

        value_to_check = value.get("code")
        if value_to_check not in codes_to_keep:
            # if the payload in question doesn't have that condition in the config,
            # remove that observation
            remove_element(component)
            continue

        organizers = cast(
            list[_Element],
            observation.xpath(
                ".//cda:entryRelationship/cda:organizer",
                namespaces=namespaces,
            ),
        )

        if not organizers:
            continue

        organizer = organizers[0]

        rr7_roles = cast(
            list[_Element],
            organizer.xpath(
                ".//cda:participant/cda:participantRole[cda:code/@code='RR7']",
                namespaces=namespaces,
            ),
        )

        if not rr7_roles:
            continue

        for rr7_role in rr7_roles:
            id_element = rr7_role.find("cda:id", namespaces)

            if id_element is None:
                continue

            jurisdiction_code = id_element.get("extension")
            if not jurisdiction_code:
                continue

            # remove any that don't match the specified JID
            if jurisdiction_code != jurisdiction_id:
                remove_element(component)

        # Similarly, if component / observation doesn't have a tagged RRVS1 entry,
        # it's not reportable, so throw out the whole thing
        reportable_observation_tags = cast(
            list[_Element],
            organizer.xpath(
                ".//cda:component/cda:observation[cda:value/@code='RRVS1']",
                namespaces=namespaces,
            ),
        )

        if len(reportable_observation_tags) == 0:
            remove_element(component)
            continue

    return etree.tostring(rr_root, encoding="unicode")
