from collections import defaultdict
from dataclasses import asdict, dataclass, field
from logging import Logger
from uuid import UUID

from packaging.version import parse

from app.services.configurations import convert_config_to_storage_payload

from ..core.models.types import XMLFiles
from ..db.conditions.db import (
    get_condition_by_id_db,
    get_conditions_by_child_rsg_snomed_codes_db,
)
from ..db.conditions.model import DbCondition
from ..db.configurations.db import (
    get_configurations_db,
)
from ..db.configurations.model import DbConfiguration, DbConfigurationStatus
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
    shadow_rr: str | None


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


@dataclass
class DiscoveredConfigurationVersion:
    """
    Model to represent individual discovered configurations.
    """

    id: UUID
    version: int
    status: DbConfigurationStatus


@dataclass
class DiscoveredConfigurationGroup:
    """
    Model to represent a group of discovered configurations.
    """

    name: str
    condition_id: UUID
    versions: list[DiscoveredConfigurationVersion]


@dataclass
class DiscoveredConfigurationsResponse:
    """
    Model to represent the groups of discovered configurations to return to the client.
    """

    groups: list[DiscoveredConfigurationGroup]


# NOTE:
# PUBLIC FUNCTIONS
# =============================================================================


async def get_matching_configurations(
    xml_files: XMLFiles,
    jurisdiction_id: str,
    db: AsyncDatabaseConnection,
) -> DiscoveredConfigurationsResponse:
    """

    Finds all reportable conditions in an eCR file package and attempts to find their matching configurations.

    Matching configurations are grouped by condition.

    Args:
        xml_files (XMLFiles): The eCR files package
        jurisdiction_id (str): The jursidiction ID to search within
        db (AsyncDatabaseConnection): The database connection

    Returns:
        DiscoveredConfigurationsResponse: The response to return to the client
    """
    rc_codes_for_jurisdiction = _get_reportable_codes_for_jurisdiction(
        xml_files=xml_files, jurisdiction_id=jurisdiction_id
    )

    if not rc_codes_for_jurisdiction:
        return DiscoveredConfigurationsResponse(groups=[])

    rc_to_conditions_map = await _map_rc_codes_to_conditions(
        rc_codes=rc_codes_for_jurisdiction, db=db
    )

    all_jurisdiction_configs = await get_configurations_db(
        jurisdiction_id=jurisdiction_id, db=db
    )

    configured_primary_condition_ids = {
        config.condition_id for config in all_jurisdiction_configs
    }

    conditions_grouped_by_url = _group_conditions_by_url(rc_to_conditions_map)

    groups: list[DiscoveredConfigurationGroup] = []
    for all_versions in conditions_grouped_by_url.values():
        representative_condition = next(
            (c for c in all_versions if c.id in configured_primary_condition_ids),
            None,
        ) or max(all_versions, key=lambda c: parse(c.version))

        condition_configs = sorted(
            [
                c
                for c in all_jurisdiction_configs
                if c.condition_id == representative_condition.id
            ],
            key=lambda c: c.version,
            reverse=True,
        )

        groups.append(
            DiscoveredConfigurationGroup(
                name=representative_condition.display_name,
                condition_id=representative_condition.id,
                versions=[
                    DiscoveredConfigurationVersion(
                        id=c.id, version=c.version, status=c.status
                    )
                    for c in condition_configs
                ],
            )
        )

    return DiscoveredConfigurationsResponse(groups=sorted(groups, key=lambda g: g.name))


def _group_conditions_by_url(
    rc_to_conditions_map: dict,
) -> dict[str, list[DbCondition]]:
    """
    Deduplicates and groups DbConditions by their canonical url.
    """
    grouped: dict[str, list[DbCondition]] = defaultdict(list)
    seen_ids: dict[str, set[UUID]] = defaultdict(set)

    for conditions_list in rc_to_conditions_map.values():
        for condition in conditions_list:
            url = condition.canonical_url
            if condition.id not in seen_ids[url]:
                seen_ids[url].add(condition.id)
                grouped[url].append(condition)

    return grouped


async def independent_testing(
    xml_files: XMLFiles,
    jurisdiction_id: str,
    configurations: list[DbConfiguration],
    conditions_without_config: list[DbCondition],
    logger: Logger,
    db: AsyncDatabaseConnection,
) -> IndependentTestingResult:
    """
    Orchestrates the full independent testing workflow for eICR refinement.

    Args:
        xml_files: XMLFiles object containing eICR and RR XML strings
        jurisdiction_id: The jurisdiction code to filter reportable conditions.
        configurations: The configurations to use for testing
        conditions_without_config: The conditions that do not have a matching config.
            This is used for shadow RR generation.
        logger: A logger for recording operational details.
        db: AsyncDatabaseConnection

    Returns:
        An IndependentTestingResult dictionary containing refined documents and a list of non-matches.
    """

    first_original_eicr_doc_id = None
    refined_docs: list[RefinedDocument] = []
    for configuration in configurations:
        processed_configuration = await _convert_to_processed_config(
            configuration=configuration, logger=logger, db=db
        )

        condition = await get_condition_by_id_db(id=configuration.condition_id, db=db)

        rr_code_used = condition.child_rsg_snomed_codes[0]
        pipeline_trace = RefinementTrace(
            jurisdiction_code=jurisdiction_id,
            rsg_code=rr_code_used,
            canonical_url=configuration.condition_canonical_url,
            configuration_version=configuration.version,
        )

        result = refine_for_condition(
            xml_files=xml_files,
            processed_configuration=processed_configuration,
            trace=pipeline_trace,
        )

        if first_original_eicr_doc_id is None:
            first_original_eicr_doc_id = result.augmented_eicr_result.original_doc_id

        refined_docs.append(
            RefinedDocument(
                reportable_condition=ReportableCondition(
                    code=rr_code_used, display_name=configuration.name
                ),
                refined_eicr=result.refined_eicr,
                refined_rr=result.refined_rr,
            )
        )

        logger.info(
            "Independent testing: Processed one condition",
            extra={
                "triggered_by_condition": condition.display_name,
                "triggering_codes": condition.child_rsg_snomed_codes,
                "configuration_found": configuration.name,
                "total_conditions_used": len(configurations),
                "configuration_settings": asdict(configuration),
                "eicr_size_reduction_percentage": pipeline_trace.eicr_size_reduction_percentage,
                "outcome": "Refinement successful",
            },
        )

        if not first_original_eicr_doc_id:
            first_original_eicr_doc_id = str(UUID())
            logger.warning(
                "No eICR document was detected. Using a randomly generated UUID as a fallback value.",
                extra={"augmented_eicr_result": result.augmented_eicr_result},
            )

    return IndependentTestingResult(
        original_eicr_doc_id=first_original_eicr_doc_id,
        refined_documents=refined_docs,
        shadow_rr=_generate_shadow_rr(
            xml_files=xml_files, conditions_without_config=conditions_without_config
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
    xml_files: XMLFiles, conditions_without_config: list[DbCondition]
) -> str | None:
    """
    Generates a shadow RR based on conditions with no active configuration.

    Args:
        xml_files (XMLFiles): the original XML eCR files
        conditions_without_config (list[DbCondition]): List of condition objects that don't have an associated config

    Returns:
        str | None: RR content, or None if a shadow RR isn't generated
    """

    no_match_codes = {
        code for c in conditions_without_config for code in c.child_rsg_snomed_codes
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
        canonical_url=trace.primary_condition.canonical_url,
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
