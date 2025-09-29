from typing import Any
from uuid import UUID

from ..core.models.types import XMLFiles
from ..db.conditions.db import get_conditions_by_child_rsg_snomed_codes
from ..db.conditions.model import DbCondition
from ..db.configurations.db import get_configurations_by_condition_ids_and_jurisdiction
from ..db.configurations.model import DbConfiguration
from ..db.pool import AsyncDatabaseConnection
from ..services.terminology import ConfigurationPayload, ProcessedConfiguration
from .ecr.models import RefinedDocument
from .ecr.refine import refine_eicr
from .ecr.reportability import determine_reportability


async def independent_testing(
    db: AsyncDatabaseConnection,
    xml_files: XMLFiles,
    jurisdiction_id: str,
) -> dict[str, Any]:
    """
    Orchestrates the full independent testing workflow for eICR refinement.

    This function performs a stepwise pipeline to:
      1. Extract reportable condition codes (RC SNOMED codes) from the RR section of the eICR XML.
      2. Filter RC codes by the specified jurisdiction (from the logged in user and the who the
         condition is reportable to in the RR).
      3. Map RC codes to conditions in the database.
      4. Identify RC codes not found as conditions (this shouldn't happen but we check just in case).
      5. For conditions found, retrieve jurisdiction-specific configurations.
      6. Identify conditions lacking configurations.
      7. Pair each condition with its configuration, create a ProcessedConfiguration object, and run the refinement logic.

    Throughout the workflow, a 'trace' dictionary is built to record intermediate data, mappings, and results.
    This trace object is useful for debugging, auditing, and future extension, and includes:
      - All RC codes found and filtered
      - Mappings between codes, conditions, and configurations
      - Lists of missing or unmatched codes/conditions
      - The final list of 'RefinedDocument' objects produced by the refinement step

    **Data Exposure:**
    For privacy, efficiency, and maintainability, the full trace is kept internal to this workflow.
    Only a minimal payload (currently the list of RefinedDocument objects) is returned to the route layer.
    This ensures the API responds with just the necessary data for downstream logic and UI,
    while retaining the trace for internal logging and future needs.

    Args:
        db: AsyncDatabaseConnection
        xml_files: XMLFiles object containing eICR and RR XML strings
        jurisdiction_id: The jurisdiction code to filter reportable conditions that we pull from the user.

    Returns:
        dict: Minimal payload containing:
            - 'refined_documents': list of RefinedDocument objects for conditions with configurations and successful refinement
    """

    # internal trace object to collect necessary data for both workflow and response to route
    trace = {}

    # STEP 1:
    # extract and filter reportable RC codes for jurisdiction
    reportability_data = extract_reportable_conditions_for_jurisdiction(
        xml_files, jurisdiction_id
    )
    trace["rc_codes_for_jurisdiction"] = reportability_data["rc_codes_for_jurisdiction"]
    trace["rc_codes_all"] = reportability_data["rc_codes_all"]
    trace["full_reportability_result"] = reportability_data["full_reportability_result"]

    # STEP 2:
    # map RC codes to conditions
    rc_codes = trace["rc_codes_for_jurisdiction"]
    rc_to_condition = await map_rc_codes_to_conditions(db, rc_codes)
    trace["rc_to_condition"] = rc_to_condition

    # STEP 3:
    # identify RC codes with no matching condition
    trace["rc_codes_no_condition"] = [
        rc for rc, cond in rc_to_condition.items() if cond is None
    ]

    # STEP 4:
    # map conditions to configurations
    conditions = [cond for cond in rc_to_condition.values() if cond is not None]
    condition_to_configuration = await map_conditions_to_configurations(
        db, conditions, jurisdiction_id
    )
    trace["condition_to_configuration"] = condition_to_configuration

    # STEP 5:
    # identify conditions with no configuration
    conditions_no_configuration = [
        cond for cond in conditions if condition_to_configuration.get(cond.id) is None
    ]
    trace["conditions_no_configuration"] = conditions_no_configuration

    # STEP 6:
    # build (condition, configuration) pairs
    condition_config_pairs = [
        (cond, condition_to_configuration[cond.id])
        for cond in conditions
        if condition_to_configuration.get(cond.id) is not None
    ]

    # STEP 7:
    # for each pair, build ProcessedConfiguration and run refinement
    refined_documents = []
    for cond, config in condition_config_pairs:
        payload = ConfigurationPayload(configuration=config, conditions=[cond])
        processed_config = ProcessedConfiguration.from_payload(payload)
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
        refined_doc = RefinedDocument(
            reportable_condition=cond,
            refined_eicr=refined_eicr_str,
        )
        refined_documents.append(refined_doc)

    trace["refined_documents"] = refined_documents
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
