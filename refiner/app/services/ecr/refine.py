from typing import Literal

from lxml import etree

from app.services.ecr.models import RefinementPlan

from ...core.exceptions import (
    StructureValidationError,
    XMLValidationError,
)
from ...core.models.types import XMLFiles
from ..file_io import read_json_asset
from .process_eicr import (
    create_minimal_section,
    get_section_by_code,
    process_section,
)

# NOTE:
# CONSTANTS AND CONFIGURATION
# =============================================================================

# read json that contains details for refining and is the base of what drives `refine`
REFINER_DETAILS = read_json_asset("refiner_details.json")

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

        namespaces = {"hl7": "urn:hl7-org:v3"}
        structured_body = eicr_root.find(".//hl7:structuredBody", namespaces)

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
                section_config = REFINER_DETAILS["sections"].get(section_code)
                process_section(
                    section=section,
                    combined_xpath=plan.xpath,
                    namespaces=namespaces,
                    section_config=section_config,
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


def refine_rr(jurisdiction_id: str, xml_files: XMLFiles, plan: RefinementPlan):
    """
    Refine a RR XML document from anything not reportable to the specified jurisdiction.

    Processing behavior:
        - It iterates through the RR and removes information common to all RR's.
        - It removes anything not applicable to the specified jurisdiction
        - It loops through all the condition observations in the reportability RC
            - Anything that isn't RRSVS1 reportable is filtered out
            - Of the remaining reportable observations, anything that isn't specified
            in the refinement configurations are filtered out

    Args:
        jurisdiction_id: the ID of the jurisdiction we're currently processing information for
        xml_files: The XMLFiles container with the eICR document to refine.
        plan: The refinement plan for the corresponding eICR.

    Returns:
        str: The refined RR XML document as a string.

    Raises:
        XMLValidationError: If the XML is invalid.
        StructureValidationError: If the document structure is invalid.
    """

    # look for structured body
    eicr_root = xml_files.parse_rr()
    namespaces = {"hl7": "urn:hl7-org:v3"}

    structured_body = eicr_root.find(".//hl7:structuredBody", namespaces)

    if structured_body is None:
        raise StructureValidationError(
            message="No structured body found in RR",
            details={"document_type": "RR"},
        )

    # author / custodian are the same always, so we can throw those out
    # Remove anything that isn't for sure reportable

    # look for coded information organizater via RR7 / find the ID extension above it for jurisdiction.
    # Use this to filter any trigger code output sections that aren't tied to the jurisdiction in question

    # only preserve RRVS1 / reportable parts of the coded info organizer matching the jurisdiction
    # Second pass from refinement plan to get the child RSG to get codes that we want to filter
    # transform the list list[DbCondition] --> child codes that we want to keep, use that to filter anything here that remains

    # Verify RR is valid

    return ""
