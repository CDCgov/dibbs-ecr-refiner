from dataclasses import dataclass, field
from logging import Logger
from typing import TypedDict
from uuid import UUID

from packaging.version import parse

from ..core.models.types import XMLFiles
from ..db.conditions.db import (
    get_conditions_by_child_rsg_snomed_codes_db,
    get_included_conditions_db,
)
from ..db.conditions.model import DbCondition
from ..db.configurations.db import (
    get_configurations_by_condition_ids_and_jurisdiction_db,
    get_configurations_db,
)
from ..db.configurations.model import DbConfiguration
from ..db.pool import AsyncDatabaseConnection
from ..services.terminology import ConfigurationPayload, ProcessedConfiguration
from .ecr.models import (
    ProcessedRR,
    RefinedDocument,
    ReportableCondition,
)
from .ecr.refine import (
    create_eicr_refinement_plan,
    create_rr_refinement_plan,
    refine_eicr,
    refine_rr,
)
from .ecr.reportability import determine_reportability

# NOTE:
# DATA STRUCTURES
# =============================================================================


@dataclass
class IndependentTestingTrace:
    """
    Holds all the tracing data for a single condition through the independent testing pipeline.
    """

    matching_condition: DbCondition
    rc_snomed_codes: list[str] = field(default_factory=list)
    matching_configuration: DbConfiguration | None = None
    number_of_included_conditions: int = 0
    all_conditions_for_configuration: list[DbCondition] = field(default_factory=list)
    refine_object: ProcessedConfiguration | None = None
    refined_document: RefinedDocument | None = None


class NoMatchEntry(TypedDict):
    """
    The structured result of failure to match conditions and configurations bi-directionally.

    This structure is used in both:
    - IndependentTestingResult: no_matching_configuration_for_conditions
    - InlineTestingResult: configuration_does_not_match_conditions

    A TypedDict that contains:
        - `display_name`: The name of the condition that doesn't have an associated configuration for the jurisdiction.
        - `rc_snomed_codes`: The list of reportable condition SNOMED codes associated with this condition.
    """

    display_name: str
    rc_snomed_codes: list[str]


class IndependentTestingResult(TypedDict):
    """
    The structured result of the independent_testing function.

    A TypedDict that contains:
        - 'refined_documents': list of RefinedDocument objects for successfully refined conditions.
        - 'no_matching_configuration_for_conditions': A list of conditions that were found but had
           no matching configuration for the jurisdiction.
    """

    refined_documents: list[RefinedDocument]
    no_matching_configuration_for_conditions: list[NoMatchEntry]


@dataclass
class InlineTestingTrace:
    """
    Holds tracing data for a single configuration through the validation pipeline.
    """

    configuration: DbConfiguration
    primary_condition: DbCondition
    number_of_included_conditions: int = 0
    all_conditions_for_configuration: list[DbCondition] = field(default_factory=list)
    is_reportable_in_file: bool = False
    matched_code: str | None = None
    refined_document: RefinedDocument | None = None


class InlineTestingResult(TypedDict):
    """
    The structured result for the inline_testing "validation" workflow.

    A TypedDict that contains:
        - 'refined_documents': list of RefinedDocument objects for successfully refined conditions.
        - 'configuration_does_not_match_conditions': A list of conditions that were found but had
           no matching configuration for the jurisdiction.

    """

    refined_document: RefinedDocument | None
    configuration_does_not_match_conditions: str | None


# NOTE:
# PUBLIC FUNCTIONS
# =============================================================================


async def independent_testing(
    db: AsyncDatabaseConnection,
    xml_files: XMLFiles,
    jurisdiction_id: str,
    logger: Logger,
) -> IndependentTestingResult:
    """
    Orchestrates the full independent testing workflow for eICR refinement.

    This function performs a version-aware, stepwise pipeline:
    1. Extracts all reportable condition (RC) SNOMED codes from the RR file for the specified jurisdiction.
    2. For each RC code, finds all matching condition versions from the database.
    3. Fetches all configurations for the jurisdiction to identify which specific condition versions are configured.
    4. Reconciles the found conditions with the active configurations. For each conceptual condition (e.g., "COVID-19"),
       it checks if any of its detected versions match a configured version.
    5. For each valid match, it builds a processing plan (ProcessedConfiguration) and refines the eICR.
    6. Returns a result containing the refined documents for matching conditions and a list of conditions that were
       found in the file but had no corresponding configuration.

    Args:
        db: AsyncDatabaseConnection
        xml_files: XMLFiles object containing eICR and RR XML strings
        jurisdiction_id: The jurisdiction code to filter reportable conditions.
        logger: A logger for recording operational details.

    Returns:
        An IndependentTestingResult dictionary containing refined documents and a list of non-matches.
    """

    # STEP 1:
    # extract all reportable condition snomed codes from the RR file that are reportable for the given jurisdiction
    # then, for each code, get a list of all possible condition versions (because we can't know which version is configured a priori)
    reportability_data = _extract_reportable_conditions_for_jurisdiction(
        xml_files, jurisdiction_id
    )
    rc_codes_for_jurisdiction = reportability_data["rc_codes_for_jurisdiction"]
    rc_to_conditions_list = await _map_rc_codes_to_conditions(
        db=db, rc_codes=rc_codes_for_jurisdiction
    )

    # if no reportable conditions are found for this jurisdiction, exit early.
    if not rc_codes_for_jurisdiction:
        return {
            "refined_documents": [],
            "no_matching_configuration_for_conditions": [],
        }

    # STEP 2:
    # get all configurations for the jurisdiction to create a lookup set of exactly
    # which condition versions are configured
    all_jurisdiction_configs = await get_configurations_db(
        db=db, jurisdiction_id=jurisdiction_id
    )
    # this set contains the specific uuids of condition rows linked as primary conditions
    configured_primary_condition_ids = {
        config.condition_id for config in all_jurisdiction_configs
    }

    # STEP 3:
    # group all found condition versions by their conceptual group (canonical_url)
    # to treat all versions of a condition (e.g., all "Influenza" versions) as a single entity
    conditions_grouped_by_url: dict[str, list[DbCondition]] = defaultdict(list)
    seen_ids_by_url: dict[str, set[str]] = defaultdict(set)

    for conditions_list in rc_to_conditions_list.values():
        for condition in conditions_list:
            url = condition.canonical_url
            if condition.id not in seen_ids_by_url[url]:
                seen_ids_by_url[url].add(condition.id)
                conditions_grouped_by_url[url].append(condition)

    # STEP 4:
    # build a trace for each conceptual condition, determining if it is configured
    all_traces: list[IndependentTestingTrace] = []
    for canonical_url, all_versions in conditions_grouped_by_url.items():
        # check if any of the detected versions for this condition are configured
        configured_version = next(
            (
                cond
                for cond in all_versions
                if cond.id in configured_primary_condition_ids
            ),
            None,
        )

        # use the configured version if one was found; otherwise, pick the latest version for display
        representative_condition = configured_version or max(
            all_versions, key=lambda c: parse(c.version)
        )

        # find the full configuration object that links to the representative condition's id
        matching_config = next(
            (
                config
                for config in all_jurisdiction_configs
                if config.condition_id == representative_condition.id
            ),
            None,
        )

        # collect all snomed codes that led to detecting this conceptual condition
        snomed_codes_for_this_group = [
            code
            for code, cond_list in rc_to_conditions_list.items()
            if any(c.canonical_url == canonical_url for c in cond_list)
        ]

        trace = IndependentTestingTrace(
            matching_condition=representative_condition,
            matching_configuration=matching_config,
            rc_snomed_codes=list(set(snomed_codes_for_this_group)),
        )
        all_traces.append(trace)

    no_matching_configurations: list[NoMatchEntry] = []

    # STEP 5:
    # process each trace; if a configuration exists, refine the eICR
    # otherwise, add it to the list of non-matches
    for trace in all_traces:
        if not trace.matching_configuration:
            no_matching_configurations.append(
                {
                    "display_name": trace.matching_condition.display_name,
                    "rc_snomed_codes": trace.rc_snomed_codes,
                }
            )
            continue

        configuration = trace.matching_configuration
        trace.number_of_included_conditions = len(configuration.included_conditions)

        if trace.number_of_included_conditions > 1:
            all_conditions_for_configuration = await get_included_conditions_db(
                included_conditions=configuration.included_conditions, db=db
            )
        else:
            all_conditions_for_configuration = [trace.matching_condition]

        trace.all_conditions_for_configuration = all_conditions_for_configuration

        payload = ConfigurationPayload(
            configuration=configuration,
            conditions=trace.all_conditions_for_configuration,
        )
        processed_configuration = ProcessedConfiguration.from_payload(payload)
        trace.refine_object = processed_configuration

        eicr_refinement_plan = create_eicr_refinement_plan(
            processed_configuration=processed_configuration, xml_files=xml_files
        )
        refined_eicr_str = refine_eicr(xml_files=xml_files, plan=eicr_refinement_plan)

        rr_refinement_plan = create_rr_refinement_plan(
            processed_configuration=processed_configuration
        )
        refined_rr_str = refine_rr(
            jurisdiction_id=jurisdiction_id,
            xml_files=xml_files,
            plan=rr_refinement_plan,
        )

        # TODO: in the future we might want the ReportableCondition model to use
        # a list instead of a string since technically there could be more than one
        # `rc_snomed_code` that was **in** the RR that matches the condition and
        # has a configuration. picking the first entry in an index isn't correct but
        # we should wait to see how the testing service evolves with the routes
        rr_code_used = trace.rc_snomed_codes[0]
        trace.refined_document = RefinedDocument(
            reportable_condition=ReportableCondition(
                code=rr_code_used,
                display_name=trace.matching_condition.display_name,
            ),
            refined_eicr=refined_eicr_str,
            refined_rr=refined_rr_str,
        )

        logger.info(
            "Independent testing: Processed one condition",
            extra={
                "triggered_by_condition": trace.matching_condition.display_name,
                "triggering_codes": trace.rc_snomed_codes,
                "configuration_found": trace.matching_configuration.name,
                "total_conditions_used": trace.number_of_included_conditions,
                "outcome": "Refinement successful",
            },
        )

    # STEP 6:
    # build the final result object from the processed traces
    refined_documents = [
        trace.refined_document
        for trace in all_traces
        if trace.refined_document is not None
    ]

    return {
        "refined_documents": refined_documents,
        "no_matching_configuration_for_conditions": no_matching_configurations,
    }


async def inline_testing(
    xml_files: XMLFiles,
    configuration: DbConfiguration,
    primary_condition: DbCondition,
    all_conditions: list[DbCondition],
    jurisdiction_id: str,
    logger: Logger,
) -> InlineTestingResult:
    """
    Orchestrates the full inline testing workflow for eICR refinement using an already-fetched configuration and primary condition.

    This function performs a validation-focused pipeline:
    1. Receives the configuration and primary condition as arguments (ensured non-None by the route/controller).
    2. Extracts all reportable condition codes from the provided RR file for the given jurisdiction.
    3. Validates that at least one of the primary condition's `child_rsg_snomed_codes`
       is present in the reportable codes from the RR; if not, returns an error.
    4. If valid, builds a ProcessedConfiguration object using the configuration and its primary condition.
    5. Use the ProcessedConfiguration to create a final set of instructions for refinement
       and execute the plan via refine_eicr.
    6. Constructs and returns the InlineTestingResult, containing the refined document or an error message if validation failed.

    Args:
        xml_files: XMLFiles object containing eICR and RR XML strings.
        configuration: The configuration to test (must not be None).
        primary_condition: The primary condition associated with the configuration (must not be None).
        all_conditions: If the configuration has included additional conditions, this will be the list[DbCondition]
          of the primary and secondary conditions.
        jurisdiction_id: The jurisdiction code to filter reportable conditions.
        logger: we're passing the logger from the route to the service.

    Returns:
        An InlineTestingResult dictionary containing either the refined document or a validation error.
    """

    # STEP 1:
    # start with already-fetched configuration and primary condition
    trace = InlineTestingTrace(
        configuration=configuration,
        primary_condition=primary_condition,
        all_conditions_for_configuration=all_conditions,
        number_of_included_conditions=len(configuration.included_conditions),
    )

    # STEP 2:
    # extract and validate reportable condition codes from RR
    reportability_data = _extract_reportable_conditions_for_jurisdiction(
        xml_files, jurisdiction_id
    )

    reportable_codes_in_rr = set(reportability_data["rc_codes_for_jurisdiction"])
    rsg_codes_from_primary_condition = set(
        trace.primary_condition.child_rsg_snomed_codes
    )

    # inner join the codes
    matched_codes = rsg_codes_from_primary_condition.intersection(
        reportable_codes_in_rr
    )

    # if no matching codes, then the eICR/RR pair was not suitable for testing the configuration
    if not matched_codes:
        logger.warning(
            "Inline testing: Processed one configuration",
            extra={
                "configuration_tested": trace.configuration.name,
                "primary_condition": trace.primary_condition.display_name,
                "total_conditions_used": trace.number_of_included_conditions,
                "outcome": "Validation failed: No matching reportable condition code found in file.",
            },
        )
        return {
            "refined_document": None,
            "configuration_does_not_match_conditions": f"The condition '{trace.primary_condition.display_name}' was not found as a reportable condition in the uploaded file for this jurisdiction.",
        }

    # STEP 3:
    # use the first RR code that matched the condition for the RefinedDocument
    # TODO: in the future we might want the ReportableCondition model to use
    # a list instead of a string since technically there could be more than one
    # `rc_snomed_code` that was **in** the RR that matches the condition and
    # has a configuration. picking the first entry in an index isn't correct but
    # we should wait to see how the testing service evolves with the routes
    trace.matched_code = list(matched_codes)[0]

    # STEP 4:
    # prepare and execute the refinement from payload -> processed_configuration -> refinement plan
    payload = ConfigurationPayload(
        configuration=trace.configuration,
        conditions=trace.all_conditions_for_configuration,
    )
    processed_configuration = ProcessedConfiguration.from_payload(payload)

    eicr_refinement_plan = create_eicr_refinement_plan(
        processed_configuration=processed_configuration, xml_files=xml_files
    )
    refined_eicr_str = refine_eicr(xml_files=xml_files, plan=eicr_refinement_plan)

    rr_refinement_plan = create_rr_refinement_plan(
        processed_configuration=processed_configuration
    )
    refined_rr_str = refine_rr(
        jurisdiction_id=jurisdiction_id,
        xml_files=xml_files,
        plan=rr_refinement_plan,
    )

    # STEP 5:
    # finalize and return the successful result
    trace.refined_document = RefinedDocument(
        reportable_condition=ReportableCondition(
            code=trace.matched_code,
            display_name=trace.primary_condition.display_name,
        ),
        refined_eicr=refined_eicr_str,
        refined_rr=refined_rr_str,
    )

    # log high level details of the refinement flow for this
    # condition
    logger.info(
        "Inline testing: Processed one configuration",
        extra={
            "configuration_tested": trace.configuration.name,
            "primary_condition": trace.primary_condition.display_name,
            "matched_code_in_rr": trace.matched_code,
            "total_conditions_used": trace.number_of_included_conditions,
            "outcome": "Refinement successful",
        },
    )

    return {
        "refined_document": trace.refined_document,
        "configuration_does_not_match_conditions": None,
    }


# NOTE:
# PRIVATE FUNCTIONS
# =============================================================================


class ReportabilityData(TypedDict):
    """
    In determining reportability package necessary data into this shape.
    """

    rc_codes_for_jurisdiction: list[str]
    rc_codes_all: list[str]
    full_reportability_result: ProcessedRR


def _extract_reportable_conditions_for_jurisdiction(
    xml_files: XMLFiles, jurisdiction_id: str
) -> ReportabilityData:
    """
    Extract RC SNOMED codes from RR, filter by jurisdiction, and collect all RCs for trace.
    """

    # run reportability logic (assuming function is async, otherwise remove await)
    reportability_result = determine_reportability(xml_files)

    # example structure: reportability_result["conditions"] = list of dicts
    # each dict: {"code": "...", "is_reportable": True/False, "jurisdictions": [...]}

    rc_codes_for_jurisdiction = []
    rc_codes_all = []

    for jurisdiction_group in reportability_result["reportable_conditions"]:
        # add all codes to rc_codes_all
        for cond in jurisdiction_group.conditions:
            rc_codes_all.append(cond.code)
            jd_code_to_check = jurisdiction_group.jurisdiction.upper()

            # if this jurisdiction matches the one we're filtering for, add to filtered list
            if jd_code_to_check == jurisdiction_id:
                rc_codes_for_jurisdiction.append(cond.code)

    return {
        "rc_codes_for_jurisdiction": rc_codes_for_jurisdiction,
        "rc_codes_all": rc_codes_all,
        "full_reportability_result": reportability_result,
    }


async def _map_rc_codes_to_conditions(
    db: AsyncDatabaseConnection,
    rc_codes: list[str],
) -> dict[str, list[DbCondition]]:
    """
    Map each RC SNOMED code to a matching DbCondition, or None if not found.
    """

    if not rc_codes:
        return {}

    # STEP 1:
    # get all conditions associated with the RC SNOMED codes
    possible_conditions = await get_conditions_by_child_rsg_snomed_codes_db(
        db=db, codes=rc_codes
    )

    # STEP 2:
    # build a reverse index: from a RC SNOMED code to ALL conditions (keeping all versions)
    rc_code_to_conditions_map: dict[str, list[DbCondition]] = {}
    for condition in possible_conditions:
        for rc_code in condition.child_rsg_snomed_codes:
            if rc_code not in rc_code_to_conditions_map:
                rc_code_to_conditions_map[rc_code] = []
            rc_code_to_conditions_map[rc_code].append(condition)

    # STEP 3:
    # find the intersection between the codes from the file and all known RC SNOMED codes
    # this gives us only the codes that are both in the file AND are valid for the related condition
    rr_codes_set = set(rc_codes)
    condition_rsg_codes_set = set(rc_code_to_conditions_map.keys())
    matched_codes = rr_codes_set.intersection(condition_rsg_codes_set)

    # STEP 4:
    # build the final map from the file's code to its corresponding condition objects (all versions)
    return {code: rc_code_to_conditions_map[code] for code in matched_codes}


async def _map_conditions_to_configurations(
    db: AsyncDatabaseConnection,
    conditions: list[DbCondition],
    jurisdiction_id: str,
) -> dict[UUID, DbConfiguration | None]:
    """
    Map each condition to its configuration for a jurisdiction.
    """

    condition_ids = [cond.id for cond in conditions]
    return await get_configurations_by_condition_ids_and_jurisdiction_db(
        db, condition_ids, jurisdiction_id
    )
