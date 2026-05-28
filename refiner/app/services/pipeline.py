from dataclasses import dataclass
from typing import Literal

from lxml import etree

from app.services.conditions.parsing import extract_uuid_from_canonical_url

from ..core.exceptions import XMLValidationError
from ..core.models.types import XMLFiles
from .ecr.augment import (
    REMAINDER_SCOPE,
    AugmentationRun,
    AugmentedResult,
    augment_eicr,
    augment_rr,
    create_augmentation_run,
)
from .ecr.model import JurisdictionReportableConditions, RRRefinementPlan
from .ecr.refine import (
    create_eicr_refinement_plan,
    create_rr_refinement_plan,
    get_file_size_in_bytes,
    get_file_size_in_mib,
    refine_eicr,
    refine_rr,
)
from .ecr.reportability import get_reportable_conditions_by_jurisdiction
from .format import format_xml_document_for_display
from .terminology import ProcessedConfiguration

# TODO:
# * testing.py and lambda_function.py each contain a per-jurisdiction
#   loop that discovers conditions, resolves configurations, calls
#   refine_for_condition, and decides whether a remainder RR is needed
# * that loop is duplicated across the two callers
# * the if-and-only-if rule for the remainder is currently enforced
#   inside produce_remainder_rr_for_jurisdiction as a None return
#   rather than being expressed structurally
# * RefinementTrace is dual-purpose: it carries both pipeline input
#   and execution output

# NOTE:
# METRICS
# =============================================================================


def _get_size_reduction_percentage(unrefined: str, refined: str) -> int:
    """
    Compute the byte-size reduction percentage between two XML strings.

    Both inputs should represent the documents in the form they will be
    persisted/observed by consumers — that is, the formatted output the
    pipeline emits, compared against the original upload as received.
    The percentage is what a user will see if they compare the size of
    their uploaded eICR against the refined eICR written by Lambda or
    packaged by the webapp.

    Lives here, not in `refine`, because it is a measurement *of* what
    the pipeline produces rather than part of the refinement engine.
    Computing it once at the pipeline boundary and propagating the
    result keeps every consumer aligned on the same number.
    """

    unrefined_bytes = get_file_size_in_bytes(unrefined)
    if unrefined_bytes == 0:
        return 0

    refined_bytes = get_file_size_in_bytes(refined)
    return round((unrefined_bytes - refined_bytes) / unrefined_bytes * 100)


# NOTE:
# SESSION CONSTRUCTION
# =============================================================================


def create_augmentation_run_from_xml_files(
    xml_files: XMLFiles,
) -> AugmentationRun:
    """
    Build an AugmentationRun from an XMLFiles pair.

    The single XMLFiles→AugmentationRun entry point. Callers
    (lambda_function.run_refinement, testing.run_simulation,
    testing.inline_testing) build one run per input pair and thread
    it through every refine_for_condition and
    produce_remainder_rr_for_jurisdiction call, so all augmented
    outputs from that pair share a timestamp. Centralizing the parse
    and the XMLSyntaxError→XMLValidationError translation here keeps
    callers off lxml and prevents three copies of the same
    parse/translate boilerplate.

    Args:
        xml_files: The eICR/RR pair. Only the eICR is read.

    Raises:
        XMLValidationError: If the eICR XML is malformed.
        ValueError: If the input eICR is missing setId or
            versionNumber.
    """

    try:
        eicr_root = xml_files.parse_eicr()
    except etree.XMLSyntaxError as e:
        raise XMLValidationError(
            message="Failed to parse eICR document",
            details={"error": str(e)},
        )

    return create_augmentation_run(eicr_root=eicr_root)


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
    RSG code, canonical URL) and passes it into the pipeline functions,
    which fill in the execution details (outcome, size reduction,
    errors).

    Attributes:
        jurisdiction_code: The jurisdiction being processed (e.g., "SDDH").
        rsg_code: The RSG SNOMED code from the RR that triggered this
            refinement (e.g., "840539006" for COVID-19).
        canonical_url: The TES condition grouper's canonical_url
            (e.g., "https://tes.tools.aimsplatform.org/api/fhir/
            ValueSet/07221093-b8a1-4b1d-8678-259277bfba64"). Set by
            the caller after resolving the RSG → grouper mapping.
            The trailing UUID is what seeds the deterministic
            augmented-document identifiers; carrying the full URL
            keeps this field name aligned with conditions.canonical_url
            and configurations.condition_canonical_url in the database.
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
    canonical_url: str | None = None
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
    run: AugmentationRun,
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
        5. Serialize, format, and measure once at the end

    The AugmentationRun is supplied by the caller and shared across
    every refine_for_condition and produce_remainder_rr_for_jurisdiction
    call in a session. Both augment_eicr and augment_rr read from the
    same run object, so the augmented eICR and RR share an
    effectiveTime and inherit versionNumber from the source eICR. The
    shared timestamp also propagates to the per-section provenance
    footnotes (built during eICR refinement), giving downstream
    consumers a consistency check they can verify programmatically.

    The condition grouper UUID — extracted from the trace's
    canonical_url per IG v4 Vol 1 Appendix A — is what scopes the
    augmented document family within the jurisdiction. A single
    eICR/RR pair can be reportable to up to four jurisdictions
    simultaneously, each with its own configuration and its own set
    of reportable conditions; the Refiner produces one augmented
    document pair per (jurisdiction, condition) combination.

    Args:
        xml_files: The eICR/RR pair to refine.
        processed_configuration: The fully resolved configuration. Must
            have the same fidelity regardless of source — codes organized
            by system with display names, section processing rules, and
            included RSG codes.
        trace: A pre-populated trace with jurisdiction and condition
            context. This function fills in the execution details. The
            trace's canonical_url must be set before calling — its
            UUID suffix participates in the deterministic identifier
            derivation.
        run: The session-scoped AugmentationRun. Built once by the
            caller via create_augmentation_run_from_xml_files and
            threaded through every pipeline call in the session so
            all augmented outputs share a timestamp.

    Returns:
        RefinementResult containing the refined eICR and RR XML strings
        and the completed trace.

    Raises:
        XMLValidationError: If the eICR or RR XML is malformed.
        StructureValidationError: If required document structure is missing.
        ValueError: If trace.canonical_url is None or doesn't end with
            a valid UUID.
    """

    trace.configuration_resolved = True

    # * canonical_url participates in the deterministic ID derivation
    # via its trailing uuid; it must be resolved before refinement
    # begins
    # * callers (testing.py, lambda_function.py) set this when
    # they resolve the RSG -> grouper mapping before calling
    if trace.canonical_url is None:
        raise ValueError(
            "Cannot run refine_for_condition without a resolved "
            "canonical_url on the trace. Caller must set this field "
            "after resolving the RSG → grouper mapping."
        )

    try:
        # * parse both documents up front so refinement and augmentation
        # can mutate the same trees
        # * parse failures surface here rather than after wasted work
        # on the eICR side.
        eicr_root = xml_files.parse_eicr()
        rr_root = xml_files.parse_rr()

        # the AugmentationRun was built by the caller and is shared
        # across the session — see create_augmentation_run_from_xml_files
        #
        # _extract_uuid_from_canonical_url returns a validated UUID
        # (raises if the trailing segment isn't UUID-shaped), which is
        # exactly the type augment_eicr/augment_rr now require — the
        # type is the validator, no separate shape check needed
        condition_grouper_uuid = extract_uuid_from_canonical_url(trace.canonical_url)

        # plan -> refine -> augment -> output (eICR)
        eicr_plan = create_eicr_refinement_plan(
            processed_configuration=processed_configuration,
            eicr_root=eicr_root,
            augmentation_timestamp=run.augmentation_time,
            config_version=trace.configuration_version,
        )
        refine_eicr(eicr_root=eicr_root, plan=eicr_plan)
        augmented_eicr_result = augment_eicr(
            eicr_root,
            run,
            jurisdiction_id=trace.jurisdiction_code,
            condition_grouper_uuid=condition_grouper_uuid,
        )
        refined_eicr = etree.tostring(eicr_root, encoding="unicode")

        # plan -> refine -> augment -> output (RR)
        rr_plan = create_rr_refinement_plan(
            processed_configuration=processed_configuration,
        )
        refine_rr(rr_root=rr_root, plan=rr_plan)
        augmented_rr_result = augment_rr(
            rr_root,
            run,
            jurisdiction_id=trace.jurisdiction_code,
            scope=condition_grouper_uuid,
        )
        refined_rr = etree.tostring(rr_root, encoding="unicode")

        trace.refinement_outcome = "refined"

        # * pretty-print at the pipeline boundary so every consumer of
        # RefinementResult receives display-ready output
        # * lxml's pretty_print=True alone does NOT indent subtrees
        # added via SubElement after a parse without remove_blank_text
        # (the section provenance footnotes are the visible symptom);
        # the formatter does a remove_blank_text reparse + pretty_print
        # to produce uniformly indented output
        refined_eicr = format_xml_document_for_display(refined_eicr)
        refined_rr = format_xml_document_for_display(refined_rr)

        # * size metrics are computed against the formatted refined
        # output so the percentage matches what the user actually
        # observes when comparing their upload to what gets written
        # to S3 (lambda) or packaged in the demo zip (webapp)
        # * one calculation, computed here, propagated through the
        # result so testing.py and lambda_function.py do not maintain
        # parallel computations that could drift
        trace.eicr_size_reduction_percentage = _get_size_reduction_percentage(
            unrefined=xml_files.eicr, refined=refined_eicr
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


# NOTE:
# STAGE 3: REMAINDER RR PRODUCTION
# =============================================================================


@dataclass
class RemainderRRResult:
    """
    The output of producing a remainder RR for one jurisdiction.

    The remainder RR is the augmented RR-side complement to per-condition
    refined outputs. For a jurisdiction where some reportable conditions
    were refined and others were skipped (no configuration, no active
    configuration, or no mapping), the remainder carries forward the
    reportability information for the skipped conditions in a single
    RR. This prevents condition duplication in the downstream package:
    each condition's reportability appears exactly once, either in a
    per-condition refined RR or in the remainder RR.

    Contains the remainder RR XML string, the AugmentedResult capturing
    the original→augmented id transition, and the set of codes the
    remainder represents.

    Note: there is intentionally no size-reduction metric on the
    remainder. The RR-side transformation is structurally simple
    (filter to a set of condition codes in a coded information organizer);
    a size percentage would not convey useful operational information
    the way the eICR percentage does.
    """

    remainder_rr: str
    augmented_result: AugmentedResult
    skipped_codes: set[str]


def produce_remainder_rr_for_jurisdiction(
    xml_files: XMLFiles,
    jurisdiction_id: str,
    refined_condition_codes: set[str],
    skipped_condition_codes: set[str],
    run: AugmentationRun,
) -> RemainderRRResult | None:
    """
    Produce an augmented remainder RR for a jurisdiction.

    The remainder RR exists as the RR-side complement to per-condition
    refined outputs. It carries forward the reportability information
    for conditions reportable to the jurisdiction that the Refiner
    did NOT refine (no matching active configuration), so each
    condition's reportability appears exactly once across the full
    output package.

    Returns None when the if-and-only-if rule is not satisfied:
        - refined_condition_codes is empty: the remainder is a
          complement of refinement; if nothing was refined for this
          jurisdiction, the original RR moves forward untouched and
          there is no remainder to produce.
        - skipped_condition_codes is empty: every condition was
          refined, so there is nothing for the remainder to carry.

    Todo:
    * the if-and-only-if rule is enforced here as a None return
      rather than expressed structurally by the caller
    * both callers compute refined/skipped code sets independently
      to pass in

    Args:
        xml_files: The eICR/RR pair. Only the RR is mutated; the
            eICR has already been read by the caller to build the
            shared AugmentationRun.
        jurisdiction_id: The jurisdiction code this remainder is
            scoped to.
        refined_condition_codes: The set of RSG SNOMED codes for
            conditions that were refined for this jurisdiction in
            the current refinement session.
        skipped_condition_codes: The set of RSG SNOMED codes for
            conditions that were NOT refined for this jurisdiction
            in the current refinement session (no mapping, no
            configuration, no active configuration). The returned
            remainder RR will retain only these condition
            observations.
        run: The session-scoped AugmentationRun, shared with the
            per-condition refine_for_condition calls so the
            remainder's effectiveTime matches.

    Returns:
        RemainderRRResult containing the augmented remainder RR XML
        and the augmented_result describing the id transition. None
        when the if-and-only-if rule is not satisfied.

    Raises:
        XMLValidationError: If the RR XML is malformed.
    """

    if not refined_condition_codes or not skipped_condition_codes:
        return None

    rr_root = xml_files.parse_rr()

    # filter the RR down to the skipped conditions only
    plan = RRRefinementPlan(
        included_condition_child_rsg_snomed_codes_to_retain=skipped_condition_codes
    )
    refine_rr(rr_root=rr_root, plan=plan)

    # augment with REMAINDER_SCOPE in place of a condition grouper UUID
    augmented_result = augment_rr(
        rr_root,
        run,
        jurisdiction_id=jurisdiction_id,
        scope=REMAINDER_SCOPE,
    )

    # serialize and pretty-print at the pipeline boundary, same as
    # the per-condition outputs from refine_for_condition
    remainder_rr = etree.tostring(rr_root, encoding="unicode")
    remainder_rr = format_xml_document_for_display(remainder_rr)

    return RemainderRRResult(
        remainder_rr=remainder_rr,
        augmented_result=augmented_result,
        skipped_codes=skipped_condition_codes,
    )
