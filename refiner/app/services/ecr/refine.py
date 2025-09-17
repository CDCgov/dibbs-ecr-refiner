from ...core.exceptions import SectionValidationError
from ...core.models.types import XMLFiles
from ...db.conditions.db import get_conditions_by_child_rsg_snomed_codes
from ...db.pool import AsyncDatabaseConnection
from ..file_io import read_json_asset
from ..terminology import (
    ConditionPayload,
    ProcessedCondition,
)
from .models import RefinedDocument
from .process_eicr import build_condition_eicr_pairs, refine_eicr
from .process_rr import process_rr

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


async def refine(
    original_xml: XMLFiles,
    db: AsyncDatabaseConnection,
    jurisdiction_id: str,
    sections_to_include: list[str] | None = None,
) -> list[RefinedDocument]:
    """
    Orchestrates the eICR refinement process.

    This is the primary entry point for the eICR refinement process. It takes an eICR/RR pair,
    processes them, and produces a list of refined eICR documents—one for each reportable condition found.

    Args:
        original_xml: An eICR/RR pair.
        db: An established async DB connection to use.
        jurisdiction_id: The ID of the jurisdiction to fetch configurations for.
        sections_to_include: Optional list of section LOINC codes to preserve as-is.

    Returns:
        A list of `RefinedDocument` objects.
    """

    # STEP 1: process the RR to find all reportable conditions
    rr_results = process_rr(original_xml)
    reportable_conditions = rr_results["reportable_conditions"]

    # STEP 2: create isolated XML object pairs for each condition to ensure
    # that the refinement of one document doesn't affect another
    condition_eicr_pairs = build_condition_eicr_pairs(
        original_xml, reportable_conditions
    )

    refined_eicrs = []
    for condition, condition_specific_xml_pair in condition_eicr_pairs:
        # STEP 3: fetch all relevant DbCondition objects from the database using the code from the RR
        db_conditions = await get_conditions_by_child_rsg_snomed_codes(
            db, [condition.code]
        )

        # STEP 4: create the ProcessedCondition object using the Payload -> Processed pattern
        # this transforms the raw database models into a simple set of codes
        condition_payload = ConditionPayload(conditions=db_conditions)
        processed_condition = ProcessedCondition.from_payload(condition_payload)

        # TODO: implement configuration-based refinement next.
        # * this will involve fetching a jurisdiction-specific configuration for the condition
        #   and creating a ProcessedConfiguration object to be used in the refinement process
        processed_configuration = None

        # STEP 5: call the eICR refiner with the final processed objects
        # the refiner can now work with the clean data without needing to know how it was assembled
        refined_eicr_str = refine_eicr(
            xml_files=condition_specific_xml_pair,
            processed_condition=processed_condition,
            processed_configuration=processed_configuration,
            sections_to_include=sections_to_include,
        )

        # STEP 6: assemble the final refined document object and add it to the results
        refined_eicrs.append(
            RefinedDocument(
                reportable_condition=condition, refined_eicr=refined_eicr_str
            )
        )

    return refined_eicrs
