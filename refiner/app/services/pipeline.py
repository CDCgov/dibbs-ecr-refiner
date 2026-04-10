from dataclasses import dataclass
from typing import Literal

from lxml import etree

from ..core.exceptions import XMLValidationError
from ..core.models.types import XMLFiles
from .ecr.augment import (
    AugmentedResult,
    augment_eicr,
    augment_rr,
    create_augmentation_context,
)
from .ecr.model import JurisdictionReportableConditions
from .ecr.refine import (
    create_eicr_refinement_plan,
    create_rr_refinement_plan,
    get_file_size_in_mib,
    get_file_size_reduction_percentage,
    refine_eicr,
    refine_rr,
)
from .ecr.reportability import get_reportable_conditions_by_jurisdiction
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
    eicr_size_mib: float | None = None
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

    augmented_eicr_result: AugmentedResult
    augmented_rr_result: AugmentedResult
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

    try:
        rr_root = xml_files.parse_rr()
        return get_reportable_conditions_by_jurisdiction(rr_root)
    except etree.XMLSyntaxError as e:
        raise XMLValidationError(
            message="Failed to parse RR document",
            details={"error": str(e)},
        )


# NOTE:
# STAGE 2: REFINEMENT EXECUTION
# =============================================================================


def refine_for_condition(
    xml_files: XMLFiles,
    processed_configuration: ProcessedConfiguration,
    trace: RefinementTrace,
) -> RefinementResult:
    """
    Execute the full refinement + augmentation pipeline for a single condition.

    Takes a ProcessedConfiguration that has already been resolved by the
    caller (from the database in the webapp, or from S3 in lambda) and
    runs plan creation, refinement, and augmentation for both the eICR
    and RR.

    The pipeline owns the parse/serialize boundary:
        1. Parse both documents once
        2. Build refinement plans
        3. Refine (mutate trees in place)
        4. Augment (mutate same trees in place)
        5. Serialize once at the end

    The augmentation context is created up front so the eICR plan, the
    eICR augmentation, and the RR augmentation all share the same
    timestamp. The shared timestamp ties the per-section provenance
    footnotes (built during eICR refinement) to the augmentation author's
    <time> value (written during eICR/RR augmentation), giving downstream
    consumers a consistency check they can verify programmatically.

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
        # augmentation contexts (created up front so both documents
        # share the same augmentation_time since we don't have a way to
        # point at the eicr by document id; may need to talk with aphl
        # about how they want this handled
        shared_context = create_augmentation_context()
        augmentation_time = shared_context.augmentation_time
        eicr_context = shared_context
        rr_context = create_augmentation_context(augmentation_time=augmentation_time)

        # plan -> refine -> augment -> output
        eicr_root = xml_files.parse_eicr()
        eicr_plan = create_eicr_refinement_plan(
            processed_configuration=processed_configuration,
            eicr_root=eicr_root,
            augmentation_timestamp=augmentation_time,
            config_version=trace.configuration_version,
        )
        refine_eicr(eicr_root=eicr_root, plan=eicr_plan)
        augmented_eicr_result = augment_eicr(eicr_root, eicr_context)
        refined_eicr = etree.tostring(eicr_root, encoding="unicode")

        # plan -> refine -> augment -> output
        rr_root = xml_files.parse_rr()
        rr_plan = create_rr_refinement_plan(
            processed_configuration=processed_configuration,
        )
        refine_rr(rr_root=rr_root, plan=rr_plan)
        augmented_rr_result = augment_rr(rr_root, rr_context)
        refined_rr = etree.tostring(rr_root, encoding="unicode")

        trace.refinement_outcome = "refined"
        trace.eicr_size_reduction_percentage = get_file_size_reduction_percentage(
            unrefined_eicr=xml_files.eicr, refined_eicr=refined_eicr
        )
        trace.eicr_size_mib = get_file_size_in_mib(file_content=refined_eicr)

        return RefinementResult(
            augmented_eicr_result=augmented_eicr_result,
            augmented_rr_result=augmented_rr_result,
            refined_eicr=refined_eicr,
            refined_rr=refined_rr,
            trace=trace,
        )

    except Exception as e:
        trace.refinement_outcome = "error"
        trace.error_detail = str(e)
        raise
