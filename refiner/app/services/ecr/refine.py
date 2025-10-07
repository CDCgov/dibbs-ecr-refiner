from typing import Literal

from lxml import etree

from ...core.exceptions import (
    SectionValidationError,
    StructureValidationError,
    XMLValidationError,
)
from ...core.models.types import XMLFiles
from ..file_io import read_json_asset
from ..terminology import ProcessedCondition, ProcessedConfiguration
from .process_eicr import _get_section_by_code, _process_section

# NOTE:
# CONSTANTS AND CONFIGURATION
# =============================================================================

# read json that contains details for refining and is the base of what drives `refine`
REFINER_DETAILS = read_json_asset("refiner_details.json")

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
    processed_configuration: ProcessedConfiguration,
    processed_condition: ProcessedCondition | None = None,
    sections_to_include: list[str] | None = None,
) -> str:
    """
    Refine an eICR XML document by processing its sections.

    Processing behavior:
        - If sections_to_include is provided, those sections are preserved unmodified.
        - For all other sections, only entries matching the clinical codes related to the given condition_codes are kept.
        - If no matching entries are found in a section, it is replaced with a minimal section and marked with nullFlavor="NI".

    Args:
        xml_files: The XMLFiles container with the eICR document to refine.
        processed_configuration: A more comprehensive object containing data from DbCondition and DbConfiguration.
        processed_condition: Optional object containing processed data from DbCondition.
        sections_to_include: Optional list of LOINC codes for eICR sections with instructions to either:
          - retain: do not process/refine. (TODO)
          - refine: refine this section. (working)
          - remove: force section to be a "minimal section". (TODO)

    Returns:
        str: The refined eICR XML document as a string.

    Raises:
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

        # per the function's design, `processed_configuration` is the required,
        # primary input. we will **always** use it
        xpath_to_use = processed_configuration.build_xpath()

        # TODO:
        # eventually phase this completely out of the codebase
        # it's now the optional object
        if processed_condition is not None:
            pass

        for section_code, section_config in REFINER_DETAILS["sections"].items():
            # skip if in sections_to_include (preserve unmodified)
            if sections_to_include and section_code in sections_to_include:
                continue

            section = _get_section_by_code(structured_body, section_code, namespaces)
            if section is None:
                continue

            _process_section(section, xpath_to_use, namespaces, section_config, version)

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
