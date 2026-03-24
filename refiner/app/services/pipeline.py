from dataclasses import dataclass
from typing import Literal

from ..core.models.types import XMLFiles
from .ecr.model import JurisdictionReportableConditions
from .ecr.refine import (
    create_eicr_refinement_plan,
    create_rr_refinement_plan,
    get_file_size_reduction_percentage,
    refine_eicr,
    refine_rr,
)
from .ecr.reportability import determine_reportability
from .terminology import ProcessedConfiguration

# NOTE:
# TRACE
# =============================================================================


@dataclass
class RefinementTrace:
    """
    Tracks a single jurisdiction/condition refinement through the pipeline.

    Populated progressively as the pipeline executes. Both the webapp
    testing service and the lambda production service use this to get
    structured visibility into what happened and why.

    The caller creates the trace with the context it knows (jurisdiction,
    RSG code, condition grouper name) and passes it into the pipeline
    functions, which fill in the execution details (outcome, size
    reduction, errors).

    Attributes:
        jurisdiction_code: The jurisdiction being processed (e.g., "SDDH").
        rsg_code: The RSG SNOMED code from the RR that triggered this
            refinement (e.g., "840539006" for COVID-19).
        condition_grouper_name: The name of the condition grouper that
            the RSG code maps to (e.g., "COVID19"). Set by the caller
            after resolving the mapping.
        configuration_version: The version number of the configuration
            used for refinement. Set by the caller after resolution.
        configuration_resolved: Whether a valid ProcessedConfiguration
            was successfully built for this jurisdiction/condition pair.
        refinement_outcome: The final status of the refinement attempt.
        skip_reason: If outcome is "skipped", why it was skipped
            (e.g., "no_mapping", "no_active_configuration").
        eicr_size_reduction_percentage: The percentage by which the
            eICR was reduced during refinement.
        error_detail: If outcome is "error", the error message.
    """

    jurisdiction_code: str
    rsg_code: str
    condition_grouper_name: str | None = None
    configuration_version: int | None = None
    configuration_resolved: bool = False
    refinement_outcome: Literal["refined", "skipped", "error"] = "skipped"
    skip_reason: str | None = None
    eicr_size_reduction_percentage: int | None = None
    error_detail: str | None = None


# NOTE:
# RESULTS
# =============================================================================


@dataclass
class RefinementResult:
    """
    The output of refining a single eICR/RR pair against one configuration.

    Contains the refined XML strings and the trace that documents how
    the refinement was executed.
    """

    refined_eicr: str
    refined_rr: str
    trace: RefinementTrace


# NOTE:
# STAGE 1: REPORTABILITY DISCOVERY
# =============================================================================


def discover_reportable_conditions(
    xml_files: XMLFiles,
) -> list[JurisdictionReportableConditions]:
    """
    Parse the RR and return all reportable conditions grouped by jurisdiction.

    This is the shared entry point for both the webapp and lambda pipelines.
    The caller decides how to filter or iterate the results:

    - testing.py filters to the logged-in user's jurisdiction
    - lambda processes all jurisdictions that have reportable conditions

    Args:
        xml_files: The eICR/RR pair.

    Returns:
        All reportable condition groups extracted from the RR.
    """

    result = determine_reportability(xml_files)
    return result["reportable_conditions"]


# NOTE:
# STAGE 2: REFINEMENT EXECUTION
# =============================================================================


def refine_for_condition(
    xml_files: XMLFiles,
    processed_configuration: ProcessedConfiguration,
    trace: RefinementTrace,
) -> RefinementResult:
    """
    Execute the full refinement pipeline for a single condition.

    Takes a ProcessedConfiguration that has already been resolved by the
    caller (from the database in the webapp, or from S3 in lambda) and
    runs plan creation and refinement for both the eICR and RR.

    This is the shared core that ensures refinement behavior is identical
    regardless of how the configuration was sourced.

    Args:
        xml_files: The eICR/RR pair to refine.
        processed_configuration: The fully resolved configuration. Must
            have the same fidelity regardless of source — codes organized
            by system with display names, section processing rules, and
            included RSG codes.
        trace: A pre-populated trace with jurisdiction and condition
            context. This function fills in the execution details.

    Returns:
        RefinementResult containing the refined eICR and RR XML strings
        and the completed trace.

    Raises:
        XMLValidationError: If the eICR or RR XML is malformed.
        StructureValidationError: If required document structure is missing.
    """

    trace.configuration_resolved = True

    try:
        # create and execute the eICR refinement plan
        eicr_plan = create_eicr_refinement_plan(
            processed_configuration=processed_configuration,
            xml_files=xml_files,
        )
        refined_eicr = refine_eicr(xml_files=xml_files, plan=eicr_plan)

        # create and execute the RR refinement plan
        rr_plan = create_rr_refinement_plan(
            processed_configuration=processed_configuration,
        )
        refined_rr = refine_rr(xml_files=xml_files, plan=rr_plan)

        # record success in the trace
        trace.refinement_outcome = "refined"
        trace.eicr_size_reduction_percentage = get_file_size_reduction_percentage(
            unrefined_eicr=xml_files.eicr, refined_eicr=refined_eicr
        )

        return RefinementResult(
            refined_eicr=refined_eicr,
            refined_rr=refined_rr,
            trace=trace,
        )

    except Exception as e:
        trace.refinement_outcome = "error"
        trace.error_detail = str(e)
        raise
