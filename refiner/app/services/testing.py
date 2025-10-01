from collections import defaultdict
from typing import Any
from uuid import UUID

from ..core.models.types import XMLFiles
from ..db.conditions.db import get_conditions_by_child_rsg_snomed_codes
from ..db.conditions.model import DbCondition
from ..db.configurations.db import get_configurations_by_condition_ids_and_jurisdiction
from ..db.configurations.model import DbConfiguration
from ..db.pool import AsyncDatabaseConnection
from ..services.terminology import ConfigurationPayload, ProcessedConfiguration
from .ecr.models import RefinedDocument, ReportableCondition
from .ecr.refine import refine_eicr
from .ecr.reportability import determine_reportability


async def independent_testing(
    db: AsyncDatabaseConnection,
    xml_files: XMLFiles,
    jurisdiction_id: str,
) -> dict[str, Any]:
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

    Throughout the workflow, a 'trace' list is built to record:
    - All RC codes found and filtered
    - Mappings between codes, conditions, and configurations
    - The RR codes that mapped to each condition
    - The final list of 'RefinedDocument' objects produced by the refinement step,
        where each RefinedDocument uses the *first* RR code (from the RR) that mapped to the condition.

    Args:
        db: AsyncDatabaseConnection
        xml_files: XMLFiles object containing eICR and RR XML strings
        jurisdiction_id: The jurisdiction code to filter reportable conditions.

    Returns:
        dict: Minimal payload containing:
            - 'refined_documents': list of RefinedDocument objects for conditions that have a configuration and successful refinement.
            Each RefinedDocument's reportable_condition.code is the first RR code from the RR that mapped to that condition.
    """

    trace = []

    # STEP 1:
    # extract and filter reportable RC codes for jurisdiction
    reportability_data = extract_reportable_conditions_for_jurisdiction(
        xml_files, jurisdiction_id
    )
    rc_codes_for_jurisdiction = reportability_data["rc_codes_for_jurisdiction"]
    rc_to_condition = await map_rc_codes_to_conditions(db, rc_codes_for_jurisdiction)

    # STEP 2:
    # group RR codes by their matched DbCondition (by .id)
    condition_map = defaultdict(
        lambda: {
            "rc_snomed_codes": [],
            "matching_condition": None,
            "matching_configuration": None,
            "refine_object": None,
            "refined_document": None,
        }
    )
    for rc_code, cond in rc_to_condition.items():
        if cond is None:
            continue
        entry = condition_map[cond.id]
        entry["rc_snomed_codes"].append(rc_code)
        entry["matching_condition"] = cond

    # STEP 3:
    # map conditions to configurations
    conditions = [entry["matching_condition"] for entry in condition_map.values()]
    condition_to_configuration = await map_conditions_to_configurations(
        db, conditions, jurisdiction_id
    )
    for entry in condition_map.values():
        cond = entry["matching_condition"]
        entry["matching_configuration"] = condition_to_configuration.get(cond.id)

    # STEP 4:
    # for each unique condition with a configuration, process and run refinement
    # (only output if config found)
    for entry in condition_map.values():
        cond = entry["matching_condition"]
        config = entry["matching_configuration"]
        if not config:
            # no config==cannot proceed
            continue

        payload = ConfigurationPayload(configuration=config, conditions=[cond])
        processed_config = ProcessedConfiguration.from_payload(payload)
        entry["refine_object"] = processed_config

        sections_to_include = (
            [sp.code for sp in config.section_processing if sp.action == "retain"]
            if config.section_processing
            else None
        )
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
        rr_code_used = entry["rc_snomed_codes"][0]
        entry["refined_document"] = RefinedDocument(
            reportable_condition=ReportableCondition(
                code=rr_code_used,
                display_name=cond.display_name,
            ),
            refined_eicr=refined_eicr_str,
        )

    # STEP 5:
    # build final trace list and output only successful refinements
    trace = list(condition_map.values())

    # output only successful refinements
    refined_documents = [
        entry["refined_document"] for entry in trace if entry["refined_document"]
    ]

    return {"refined_documents": refined_documents}


def extract_reportable_conditions_for_jurisdiction(
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


async def map_rc_codes_to_conditions(
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


async def map_conditions_to_configurations(
    db: AsyncDatabaseConnection,
    conditions: list[DbCondition],
    jurisdiction_id: str,
) -> dict[UUID, DbConfiguration | None]:
    """
    Map each condition to its configuration for a jurisdiction.
    """

    condition_ids = [cond.id for cond in conditions]
    return await get_configurations_by_condition_ids_and_jurisdiction(
        db, condition_ids, jurisdiction_id
    )
