from dataclasses import dataclass, field
from typing import TypedDict
from uuid import UUID

from ..core.models.types import XMLFiles
from ..db.conditions.db import (
    get_condition_by_id_db,
    get_conditions_by_child_rsg_snomed_codes,
)
from ..db.conditions.model import DbCondition
from ..db.configurations.db import (
    get_configuration_by_id_db,
    get_configurations_by_condition_ids_and_jurisdiction_db,
)
from ..db.configurations.model import DbConfiguration
from ..db.pool import AsyncDatabaseConnection
from ..services.terminology import ConfigurationPayload, ProcessedConfiguration
from .ecr.models import ProcessedRR, RefinedDocument, ReportableCondition
from .ecr.refine import refine_eicr
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
    refine_object: ProcessedConfiguration | None = None
    refined_document: RefinedDocument | None = None


class NoMatchEntry(TypedDict):
    """
    The structured result of a condition that doesn't have a matching configuration.

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
) -> IndependentTestingResult:
    """
    Orchestrates the full independent testing workflow for eICR refinement.

    This function performs a stepwise pipeline:
    1. Extract all reportable condition codes (RC SNOMED codes) from the RR section of the eICR XML.
    2. Filter RC codes by the specified jurisdiction.
    3. Map each RC code to a database condition (DbCondition).
    4. For each unique matched condition, collect all RR codes that mapped to it.
    5. For each condition, retrieve the jurisdiction-specific configuration (if any).
    6. For each condition with a configuration, build a ProcessedConfiguration
        and run the refinement logic to generate a per-condition refined eICR.
    7. Build a trace list containing context and outcome for each processed condition.

    Args:
        db: AsyncDatabaseConnection
        xml_files: XMLFiles object containing eICR and RR XML strings
        jurisdiction_id: The jurisdiction code to filter reportable conditions.

    Returns:
        A dictionary with a defined structure containing refined documents and a list of non-matches.
    """

    # STEP 1:
    # extract and filter reportable RC codes for jurisdiction
    reportability_data = _extract_reportable_conditions_for_jurisdiction(
        xml_files, jurisdiction_id
    )
    rc_codes_for_jurisdiction = reportability_data["rc_codes_for_jurisdiction"]
    rc_to_condition = await _map_rc_codes_to_conditions(
        db=db, rc_codes=rc_codes_for_jurisdiction
    )

    # STEP 2:
    # group RR codes by their matched DbCondition (by .id)
    condition_map: dict[UUID, IndependentTestingTrace] = {}
    for rc_code, condition in rc_to_condition.items():
        if condition is None:
            continue
        if condition.id not in condition_map:
            condition_map[condition.id] = IndependentTestingTrace(
                matching_condition=condition
            )
        trace = condition_map[condition.id]
        trace.rc_snomed_codes.append(rc_code)

    # STEP 3:
    # map conditions to configurations
    conditions = [trace.matching_condition for trace in condition_map.values()]
    condition_to_configuration = await _map_conditions_to_configurations(
        db=db, conditions=conditions, jurisdiction_id=jurisdiction_id
    )
    for trace in condition_map.values():
        trace.matching_configuration = condition_to_configuration.get(
            trace.matching_condition.id
        )

    no_matching_configurations: list[NoMatchEntry] = []

    # STEP 4:
    # for each unique condition with a configuration, process and run refinement
    # (only output if config found)
    for trace in condition_map.values():
        # if no configuration exists, this is a "no match"
        if not trace.matching_configuration:
            # add info to no_match list
            no_matching_configurations.append(
                {
                    "display_name": trace.matching_condition.display_name,
                    "rc_snomed_codes": trace.rc_snomed_codes,
                }
            )
            continue

        condition = trace.matching_condition
        configuration = trace.matching_configuration
        payload = ConfigurationPayload(
            configuration=configuration, conditions=[condition]
        )
        processed_configuration = ProcessedConfiguration.from_payload(payload)
        trace.refine_object = processed_configuration

        # TODO:
        # add in section processing when we've hooked up
        # all of the section processing instructions
        # for this to work as expected
        # for now; just give refine_eicr 'None'
        sections_to_include = None

        refined_eicr_str = refine_eicr(
            xml_files=XMLFiles(xml_files.eicr, xml_files.rr),
            processed_condition=None,
            processed_configuration=processed_configuration,
            sections_to_include=sections_to_include,
        )

        # use the first RR code that mapped to this condition for RefinedDocument
        # TODO: in the future we might want the ReportableCondition model to use
        # a list instead of a string since technically there could be more than one
        # `rc_snomed_code` that was **in** the RR that matches the condition and
        # has a configuration. picking the first entry in an index isn't correct but
        # we should wait to see how the testing service evolves with the routes
        rr_code_used = trace.rc_snomed_codes[0]
        trace.refined_document = RefinedDocument(
            reportable_condition=ReportableCondition(
                code=rr_code_used,
                display_name=condition.display_name,
            ),
            refined_eicr=refined_eicr_str,
        )

    # STEP 5:
    # build final list of successful refinements
    refined_documents = [
        trace.refined_document
        for trace in condition_map.values()
        if trace.refined_document is not None
    ]

    return {
        "refined_documents": refined_documents,
        "no_matching_configuration_for_conditions": no_matching_configurations,
    }


async def inline_testing(
    db: AsyncDatabaseConnection,
    xml_files: XMLFiles,
    configuration_id: UUID,
    jurisdiction_id: str,
) -> InlineTestingResult:
    """
    Orchestrates the full inline testing workflow for eICR refinement.

    This function performs a validation-focused pipeline:
    1. Fetch the specified configuration and its associated primary condition from the DB.
    2. Extract all reportable condition codes from the provided RR file for the given
       jurisdiction.
    3. Validate that at least one of the primary condition's `rsg_child_snomed_codes`
       is present in the reportable codes from the RR; if not, return right away.
    4. If valid, build a ProcessedConfiguration object using the configuration and its
       primary condition.
    5. Run the refinement logic (refine_eicr) using the ProcessedConfiguration.
    6. Construct and return the InlineTestingResult, containing the refined document
       or an error message if validation failed.

    Args:
        db: AsyncDatabaseConnection
        xml_files: XMLFiles object containing eICR and RR XML strings
        configuration_id: The ID of the configuration to test.
        jurisdiction_id: The jurisdiction code to filter reportable conditions.

    Returns:
        An InlineTestingResult dictionary containing either the refined
        document or a validation error.
    """

    # STEP 1:
    # gather and validate the configuration and its primary condition
    configuration, primary_condition = await _get_configuration_condition_pair(
        db, configuration_id=configuration_id, jurisdiction_id=jurisdiction_id
    )

    trace = InlineTestingTrace(
        configuration=configuration, primary_condition=primary_condition
    )

    # STEP 2:
    # perform reportability validation (fail fast)
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
        return {
            "refined_document": None,
            "configuration_does_not_match_conditions": f"The condition '{trace.primary_condition.display_name}' was not found as a reportable condition in the uploaded file for this jurisdiction.",
        }

    trace.is_reportable_in_file = True

    # use the first RR code that mapped to this condition for RefinedDocument
    # TODO: in the future we might want the ReportableCondition model to use
    # a list instead of a string since technically there could be more than one
    # `rc_snomed_code` that was **in** the RR that matches the condition and
    # has a configuration. picking the first entry in an index isn't correct but
    # we should wait to see how the testing service evolves with the routes
    trace.matched_code = list(matched_codes)[0]

    # STEP 3:
    # prepare and execute the refinement
    payload = ConfigurationPayload(
        configuration=trace.configuration,
        conditions=[trace.primary_condition],
    )
    processed_config = ProcessedConfiguration.from_payload(payload)

    # TODO:
    # add in section processing when we've hooked up
    # all of the section processing instructions
    # for this to work as expected
    # for now; just give refine_eicr 'None'
    sections_to_include = None

    refined_eicr_str = refine_eicr(
        xml_files=xml_files,
        processed_configuration=processed_config,
        processed_condition=None,
        sections_to_include=sections_to_include,
    )

    # STEP 4:
    # finalize and return the successful result
    trace.refined_document = RefinedDocument(
        reportable_condition=ReportableCondition(
            code=trace.matched_code,
            display_name=trace.primary_condition.display_name,
        ),
        refined_eicr=refined_eicr_str,
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
            # if this jurisdiction matches the one we're filtering for, add to filtered list
            if jurisdiction_group.jurisdiction == jurisdiction_id:
                rc_codes_for_jurisdiction.append(cond.code)

    return {
        "rc_codes_for_jurisdiction": rc_codes_for_jurisdiction,
        "rc_codes_all": rc_codes_all,
        "full_reportability_result": reportability_result,
    }


async def _map_rc_codes_to_conditions(
    db: AsyncDatabaseConnection,
    rc_codes: list[str],
) -> dict[str, DbCondition | None]:
    """
    Map each RC SNOMED code to a matching DbCondition, or None if not found.
    """

    if not rc_codes:
        return {}

    # STEP 1:
    # get all conditions associated with the RC SNOMED codes
    possible_conditions = await get_conditions_by_child_rsg_snomed_codes(
        db=db, codes=rc_codes
    )

    # STEP 2:
    # build a reverse index: from a RC SNOMED code to the condition it belongs to
    rc_code_to_condition_map: dict[str, DbCondition] = {
        rc_code: condition
        for condition in possible_conditions
        for rc_code in condition.child_rsg_snomed_codes
    }

    # STEP 3:
    # find the intersection between the codes from the file and all known RC SNOMED codes
    # this gives us only the codes that are both in the file AND are valid for the related condition
    rr_codes_set = set(rc_codes)
    condition_rsg_codes_set = set(rc_code_to_condition_map.keys())
    matched_codes = rr_codes_set.intersection(condition_rsg_codes_set)

    # STEP 4:
    # build the final map from the file's code to its corresponding condition object
    return {code: rc_code_to_condition_map[code] for code in matched_codes}


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


async def _get_configuration_condition_pair(
    db: AsyncDatabaseConnection, configuration_id: UUID, jurisdiction_id: str
) -> tuple[DbConfiguration, DbCondition]:
    """
    Get the DbConfiguration and DbCondition associated with the configuration_id and jurisdiciton_id.

    Before we're able to detrmine reportability we'll need to get some data from the database to check
    against the reportability_data results.

    Returns a tuple of (configuration, condition).
    """

    configuration = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=jurisdiction_id, db=db
    )
    assert configuration is not None, "Configuration not found, but was expected."

    primary_condition = await get_condition_by_id_db(
        id=configuration.condition_id, db=db
    )
    assert primary_condition is not None, "Condition not found, but was expected."

    return configuration, primary_condition
