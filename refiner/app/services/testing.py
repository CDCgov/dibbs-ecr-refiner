from dataclasses import dataclass, field
from typing import TypedDict
from uuid import UUID

from ..core.models.types import XMLFiles
from ..db.conditions.db import get_conditions_by_child_rsg_snomed_codes
from ..db.conditions.model import DbCondition
from ..db.configurations.db import (
    get_configurations_by_condition_ids_and_jurisdiction_db,
)
from ..db.configurations.model import DbConfiguration
from ..db.pool import AsyncDatabaseConnection
from ..services.terminology import ConfigurationPayload, ProcessedConfiguration
from .ecr.models import RefinedDocument, ReportableCondition
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


class IndependentTestingResult(TypedDict):
    """
    The structured result of the independent_testing function.

    A TypedDict that contains:
        - 'refined_documents': list of RefinedDocument objects for successfully refined conditions.
        - 'no_match': A list of conditions that were found but had no matching configuration for the jurisdiction.
    """

    refined_documents: list[RefinedDocument]
    no_match: list[dict[str, str | list[str]]]


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
    rc_to_condition = await _map_rc_codes_to_conditions(db, rc_codes_for_jurisdiction)

    # STEP 2:
    # group RR codes by their matched DbCondition (by .id)
    condition_map: dict[UUID, IndependentTestingTrace] = {}
    for rc_code, cond in rc_to_condition.items():
        if cond is None:
            continue
        if cond.id not in condition_map:
            condition_map[cond.id] = IndependentTestingTrace(matching_condition=cond)
        trace = condition_map[cond.id]
        trace.rc_snomed_codes.append(rc_code)

    # STEP 3:
    # map conditions to configurations
    conditions = [trace.matching_condition for trace in condition_map.values()]
    condition_to_configuration = await _map_conditions_to_configurations(
        db, conditions, jurisdiction_id
    )
    for trace in condition_map.values():
        trace.matching_configuration = condition_to_configuration.get(
            trace.matching_condition.id
        )

    # no_match: list[dict{str: str, str: list | str}] = []
    no_match: list[dict[str, str | list[str]]] = []

    # STEP 4:
    # for each unique condition with a configuration, process and run refinement
    # (only output if config found)
    for trace in condition_map.values():
        # if no configuration exists, this is a "no match"
        if not trace.matching_configuration:
            # add info to no_match list
            no_match.append(
                {
                    "display_name": trace.matching_condition.display_name,
                    "rc_snomed_codes": trace.rc_snomed_codes,
                }
            )
            continue

        cond = trace.matching_condition
        config = trace.matching_configuration

        payload = ConfigurationPayload(configuration=config, conditions=[cond])
        processed_config = ProcessedConfiguration.from_payload(payload)
        trace.refine_object = processed_config

        # TODO:
        # add in section processing when we've hooked up
        # all of the section processing instructions
        # for this to work as expected
        # for now; just give refine_eicr 'None'
        sections_to_include = None

        refined_eicr_str = refine_eicr(
            xml_files=XMLFiles(xml_files.eicr, xml_files.rr),
            processed_condition=None,
            processed_configuration=processed_config,
            sections_to_include=sections_to_include,
        )

        # use the first RR code that mapped to this condition for output
        # TODO: in the future we might want the object to use a list since technically
        # there could be more than one `rc_snomed_code` that was **in** the RR,
        # matched to the condition, and has a configuration. picking the first entry
        # in an index doesn't feel right but we should wait to see how the trace object
        # evolves and how the response model evolves
        rr_code_used = trace.rc_snomed_codes[0]
        trace.refined_document = RefinedDocument(
            reportable_condition=ReportableCondition(
                code=rr_code_used,
                display_name=cond.display_name,
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

    return {"refined_documents": refined_documents, "no_match": no_match}


# NOTE:
# PRIVATE FUNCTIONS
# =============================================================================


def _extract_reportable_conditions_for_jurisdiction(
    xml_files: XMLFiles, jurisdiction_id: str
) -> dict:
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

    # get all conditions associated with the RC SNOMED codes
    conditions = await get_conditions_by_child_rsg_snomed_codes(db, rc_codes)

    # build mapping from RC code to condition
    rc_to_condition = {}

    # build a lookup: child_rsg_snomed_code -> DbCondition
    # one condition may support multiple RC codes
    for rc_code in rc_codes:
        # find any condition where rc_code is in condition.child_rsg_snomed_codes
        found = None
        for cond in conditions:
            if rc_code in cond.child_rsg_snomed_codes:
                found = cond
                break
        rc_to_condition[rc_code] = found

    return rc_to_condition


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
