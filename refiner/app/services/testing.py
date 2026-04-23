from collections import defaultdict
from dataclasses import asdict, dataclass, field
from logging import Logger
from typing import TypedDict
from uuid import UUID

from packaging.version import parse

from app.services.configurations import convert_config_to_storage_payload

from ..core.models.types import XMLFiles
from ..db.conditions.db import (
    get_conditions_by_child_rsg_snomed_codes_db,
    get_included_conditions_db,
)
from ..db.conditions.model import DbCondition
from ..db.configurations.db import (
    get_configurations_db,
)
from ..db.configurations.model import DbConfiguration
from ..db.pool import AsyncDatabaseConnection
from ..services.terminology import ProcessedConfiguration
from .ecr.model import (
    RefinedDocument,
    ReportableCondition,
)
from .ecr.refine import refine_rr_for_unconfigured_conditions
from .pipeline import (
    RefinementTrace,
    discover_reportable_conditions,
    refine_for_condition,
)

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


@dataclass
class IndependentTestingResult:
    """
    The structured result of the independent_testing function.

    A TypedDict that contains:
        - 'refined_documents': list of RefinedDocument objects for successfully refined conditions.
        - 'no_matching_configuration_for_conditions': A list of conditions that were found but had
           no matching configuration for the jurisdiction.
        - 'no_active_configuration_for_conditions': A list of conditions that were found but had
           no active configuration for the jurisdiction.
        - 'shadow_rr': Optional RR containing only reportable conditions without active configs.
    """

    original_eicr_doc_id: str
    refined_documents: list[RefinedDocument]
    no_matching_configuration_for_conditions: list[NoMatchEntry]
    no_active_configuration_for_conditions: list[NoMatchEntry]
    shadow_rr: str | None

    def get_condition_names_with_no_matching_config(self) -> list[str]:
        """
        Returns a list of condition names that have no matching configuration.
        """
        return [
            missing_condition["display_name"]
            for missing_condition in self.no_matching_configuration_for_conditions
        ]

    def get_condition_names_with_no_active_config(self) -> list[str]:
        """
        Returns a list of condition names that have no active configuration.
        """
        return [
            missing_condition["display_name"]
            for missing_condition in self.no_active_configuration_for_conditions
        ]


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


@dataclass
class InlineTestingResult:
    """
    The structured result for the inline_testing "validation" workflow.

    A TypedDict that contains:
        - 'refined_documents': list of RefinedDocument objects for successfully refined conditions.
        - 'configuration_does_not_match_conditions': A list of conditions that were found but had
           no matching configuration for the jurisdiction.

    """

    original_eicr_doc_id: str
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
    # * use the shared pipeline to discover all reportable conditions, then
    # filter to the logged-in user's jurisdiction.
    # * for each code, get a list of all possible condition versions (because
    # we can't know which version is configured a priori)
    rc_codes_for_jurisdiction = _get_reportable_codes_for_jurisdiction(
        xml_files, jurisdiction_id
    )
    rc_to_conditions_map = await _map_rc_codes_to_conditions(
        db=db, rc_codes=rc_codes_for_jurisdiction
    )

    # if no reportable conditions are found for this jurisdiction, exit early.
    if not rc_codes_for_jurisdiction:
        return IndependentTestingResult(
            original_eicr_doc_id="",
            refined_documents=[],
            no_matching_configuration_for_conditions=[],
            no_active_configuration_for_conditions=[],
            shadow_rr=None,
        )

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
    seen_ids_by_url: dict[str, set[UUID]] = defaultdict(set)

    for conditions_list in rc_to_conditions_map.values():
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

        # find the all the relevant configs and check to see if any one is active
        condition_configs = sorted(
            [
                c
                for c in all_jurisdiction_configs
                if c.condition_id == representative_condition.id
            ],
            key=lambda c: c.version,
        )

        matching_config = next(
            (c for c in condition_configs if c.status == "active"),
            condition_configs[-1] if condition_configs else None,
        )

        # collect all snomed codes that led to detecting this conceptual condition
        snomed_codes_for_this_group = [
            code
            for code, cond_list in rc_to_conditions_map.items()
            if any(c.canonical_url == canonical_url for c in cond_list)
        ]
        trace = IndependentTestingTrace(
            matching_condition=representative_condition,
            matching_configuration=matching_config,
            rc_snomed_codes=list(set(snomed_codes_for_this_group)),
        )
        all_traces.append(trace)

    no_matching_configurations: list[NoMatchEntry] = []
    no_active_configurations: list[NoMatchEntry] = []

    # STEP 5:
    # process each trace; if a configuration exists, refine the eICR
    # if it exists but isn't active, add it to the list of non-active configurations
    # otherwise, add it to the list of non-matches
    first_original_eicr_doc_id = None
    for trace in all_traces:
        if not trace.matching_configuration:
            no_matching_configurations.append(
                {
                    "display_name": trace.matching_condition.display_name,
                    "rc_snomed_codes": trace.rc_snomed_codes,
                }
            )
            continue

        if trace.matching_configuration.status != "active":
            no_active_configurations.append(
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

        processed_configuration = await _convert_to_processed_config(
            configuration=configuration, logger=logger, db=db
        )

        trace.refine_object = processed_configuration

        # Use the shared pipeline to execute refinement
        rr_code_used = trace.rc_snomed_codes[0]
        pipeline_trace = RefinementTrace(
            jurisdiction_code=jurisdiction_id,
            rsg_code=rr_code_used,
            condition_grouper_name=trace.matching_condition.display_name,
            configuration_version=configuration.version,
        )

        result = refine_for_condition(
            xml_files=xml_files,
            processed_configuration=processed_configuration,
            trace=pipeline_trace,
        )

        if first_original_eicr_doc_id is None:
            first_original_eicr_doc_id = result.augmented_eicr_result.original_doc_id

        # TODO: in the future we might want the ReportableCondition model to use
        # a list instead of a string since technically there could be more than one
        # `rc_snomed_code` that was **in** the RR that matches the condition and
        # has a configuration. picking the first entry in an index isn't correct but
        # we should wait to see how the testing service evolves with the routes
        trace.refined_document = RefinedDocument(
            reportable_condition=ReportableCondition(
                code=rr_code_used,
                display_name=trace.matching_condition.display_name,
            ),
            refined_eicr=result.refined_eicr,
            refined_rr=result.refined_rr,
        )

        logger.info(
            "Independent testing: Processed one condition",
            extra={
                "triggered_by_condition": trace.matching_condition.display_name,
                "triggering_codes": trace.rc_snomed_codes,
                "configuration_found": trace.matching_configuration.name,
                "total_conditions_used": trace.number_of_included_conditions,
                "configuration_settings": asdict(configuration),
                "eicr_size_reduction_percentage": pipeline_trace.eicr_size_reduction_percentage,
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

    return IndependentTestingResult(
        original_eicr_doc_id=first_original_eicr_doc_id
        if first_original_eicr_doc_id
        else "",
        refined_documents=refined_documents,
        no_matching_configuration_for_conditions=no_matching_configurations,
        no_active_configuration_for_conditions=no_active_configurations,
        shadow_rr=_generate_shadow_rr(
            no_matching_configuration_for_conditions=no_matching_configurations,
            no_active_configuration_for_conditions=no_active_configurations,
            xml_files=xml_files,
        ),
    )


async def _convert_to_processed_config(
    configuration: DbConfiguration, logger: Logger, db: AsyncDatabaseConnection
):
    """
    Helper function to simulate the serialization/deserialization process Lambda uses.

    Args:
        configuration (DbConfiguration): The configuration
        logger (Logger): The logger
        db (AsyncDatabaseConnection): The database connection

    Raises:
        ValueError: Unable to convert the config to a storage payload

    Returns:
        ProcessedConfiguration: A ProcessedConfiguration created from a storage payload object
    """
    # Convert the config to a storage payload
    serialized_configuration = await convert_config_to_storage_payload(
        configuration=configuration, db=db
    )

    if not serialized_configuration:
        logger.error(
            "Converting configuration to storage payload failed.",
            extra={"configuration": asdict(configuration)},
        )
        raise ValueError(
            f"Configuration could not be converted to a storage payload: {configuration.id}"
        )

    # Convert to a ProcessedConfiguration from the serialized configuration
    return ProcessedConfiguration.from_dict(serialized_configuration.to_dict())


def _generate_shadow_rr(
    no_matching_configuration_for_conditions: list[NoMatchEntry],
    no_active_configuration_for_conditions: list[NoMatchEntry],
    xml_files: XMLFiles,
) -> str | None:
    """
    Generates a shadow RR based on conditions with no active configuration.

    Args:
        no_matching_configuration_for_conditions (list[NoMatchEntry]): list of conditions without a configuration
        no_active_configuration_for_conditions (list[NoMatchEntry]): list of conditions without an active configuration
        xml_files (XMLFiles): the original XML eCR files

    Returns:
        str | None: RR content, or None if a shadow RR isn't generated
    """
    no_match_found_conditions = (
        no_matching_configuration_for_conditions
        + no_active_configuration_for_conditions
    )
    if not no_match_found_conditions:
        return None

    no_match_codes = {
        code for entry in no_match_found_conditions for code in entry["rc_snomed_codes"]
    }

    return refine_rr_for_unconfigured_conditions(
        xml_files=xml_files, condition_codes=no_match_codes
    )


async def inline_testing(
    xml_files: XMLFiles,
    configuration: DbConfiguration,
    primary_condition: DbCondition,
    all_conditions: list[DbCondition],
    jurisdiction_id: str,
    logger: Logger,
    db: AsyncDatabaseConnection,
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
       and execute the plan via the shared refinement pipeline.
    6. Constructs and returns the InlineTestingResult, containing the refined document or an error message if validation failed.

    Args:
        xml_files: XMLFiles object containing eICR and RR XML strings.
        configuration: The configuration to test (must not be None).
        primary_condition: The primary condition associated with the configuration (must not be None).
        all_conditions: If the configuration has included additional conditions, this will be the list[DbCondition]
          of the primary and secondary conditions.
        jurisdiction_id: The jurisdiction code to filter reportable conditions.
        logger: we're passing the logger from the route to the service.
        db: The database connection

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
    # use the shared pipeline to discover reportable conditions, then
    # filter to this jurisdiction and validate against the primary condition
    rc_codes_for_jurisdiction = _get_reportable_codes_for_jurisdiction(
        xml_files, jurisdiction_id
    )

    reportable_codes_in_rr = set(rc_codes_for_jurisdiction)
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
                "configuration_settings": asdict(configuration),
                "outcome": "Validation failed: No matching reportable condition code found in file.",
            },
        )
        return InlineTestingResult(
            original_eicr_doc_id="",
            refined_document=None,
            configuration_does_not_match_conditions=f"The condition '{trace.primary_condition.display_name}' was not found as a reportable condition in the uploaded file for this jurisdiction.",
        )

    # STEP 3:
    # use the first RR code that matched the condition for the RefinedDocument
    # TODO: in the future we might want the ReportableCondition model to use
    # a list instead of a string since technically there could be more than one
    # `rc_snomed_code` that was **in** the RR that matches the condition and
    # has a configuration. picking the first entry in an index isn't correct but
    # we should wait to see how the testing service evolves with the routes
    trace.matched_code = list(matched_codes)[0]

    # STEP 4:
    # prepare and execute the refinement from payload -> processed_configuration -> shared pipeline
    processed_configuration = await _convert_to_processed_config(
        configuration=configuration, logger=logger, db=db
    )

    pipeline_trace = RefinementTrace(
        jurisdiction_code=jurisdiction_id,
        rsg_code=trace.matched_code,
        condition_grouper_name=trace.primary_condition.display_name,
        configuration_version=trace.configuration.version,
    )

    result = refine_for_condition(
        xml_files=xml_files,
        processed_configuration=processed_configuration,
        trace=pipeline_trace,
    )

    # STEP 5:
    # finalize and return the successful result
    trace.refined_document = RefinedDocument(
        reportable_condition=ReportableCondition(
            code=trace.matched_code,
            display_name=trace.primary_condition.display_name,
        ),
        refined_eicr=result.refined_eicr,
        refined_rr=result.refined_rr,
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
            "configuration_settings": asdict(configuration),
            "eicr_size_reduction_percentage": pipeline_trace.eicr_size_reduction_percentage,
            "outcome": "Refinement successful",
        },
    )

    return InlineTestingResult(
        original_eicr_doc_id=result.augmented_eicr_result.original_doc_id,
        refined_document=trace.refined_document,
        configuration_does_not_match_conditions=None,
    )


# NOTE:
# PRIVATE FUNCTIONS
# =============================================================================


def _get_reportable_codes_for_jurisdiction(
    xml_files: XMLFiles, jurisdiction_id: str
) -> list[str]:
    """
    Get reportable conditions for jurisdictions.

    Use the shared pipeline to discover reportable conditions from the RR,
    then extract just the SNOMED codes for the specified jurisdiction.

    Args:
        xml_files: The eICR/RR pair.
        jurisdiction_id: The jurisdiction to filter for (e.g., "SDDH").

    Returns:
        list[str]: The RC SNOMED codes reportable to this jurisdiction.
    """

    reportable_groups = discover_reportable_conditions(xml_files)

    rc_codes: list[str] = []
    for group in reportable_groups:
        if group.jurisdiction.upper() == jurisdiction_id:
            for condition in group.conditions:
                rc_codes.append(condition.code)

    return rc_codes


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
    rc_code_to_conditions_map: dict[str, list[DbCondition]] = defaultdict(list)

    for condition in possible_conditions:
        for rc_code in condition.child_rsg_snomed_codes:
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
