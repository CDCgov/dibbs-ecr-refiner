import re
from collections import defaultdict
from dataclasses import asdict, replace
from logging import Logger
from typing import Any
from uuid import UUID

from app.api.v1.configurations.model import IncludedCondition
from app.db.code_systems.db import (
    CodeSystemKey,
    get_code_system_by_key_db,
)
from app.db.codes.db import get_rsg_codes_by_condition_id_db
from app.db.codes.model import DbCode
from app.db.conditions.db import (
    get_condition_by_id_db,
    get_included_conditions_db,
)
from app.db.conditions.model import DbConditionCoding
from app.db.configurations.db import get_configuration_by_id_db
from app.db.configurations.model import (
    ConfigurationStorageMetadata,
    ConfigurationStoragePayload,
    DbConfiguration,
    DbConfigurationSectionProcessing,
    DbSectionAction,
    GetConfigurationResponseVersion,
)
from app.db.pool import AsyncDatabaseConnection
from app.services.code_systems import (
    get_all_code_systems_by_key,
    get_allowed_code_system_keys,
)
from app.services.ecr.policy import (
    NARRATIVE_ONLY_SECTIONS,
    SECTION_PROCESSING_SKIP,
    normalize_section_narrative,
)
from app.services.ecr.specification import (
    get_section_version_map,
    load_spec,
)
from app.services.ecr.specification.constants import OID_TO_SYSTEM_KEY_MAP
from app.services.terminology import (
    CodeSystemSets,
    Coding,
    index_condition_code_list_by_system,
)


def get_default_sections() -> list[DbConfigurationSectionProcessing]:
    """
    Constructs and returns a list of default sections for the latest spec.

    Returns:
        list[DbConfigurationSectionProcessing]: List of sections with default values set.
    """

    spec = load_spec("3.1.1")
    loinc_versions_flat = get_section_version_map()

    # TODO:
    # we should try to keep `db` related models out of the
    # ecr service as much as practicable

    # Narrative-only sections (has_match_rules=False) should default to "retain"
    # since there is nothing to match against
    section_processing_defaults = [
        DbConfigurationSectionProcessing(
            name=section_spec.display_name,
            code=loinc_code,
            narrative="retain",
            include=True,
            action=(
                "retain"
                if loinc_code in SECTION_PROCESSING_SKIP
                or loinc_code in NARRATIVE_ONLY_SECTIONS
                else "refine"
            ),
            versions=loinc_versions_flat.get(loinc_code, []),
            section_type="standard",
        )
        for loinc_code, section_spec in spec.sections.items()
    ]

    return section_processing_defaults


def clone_section_processing_instructions(
    clone_from: list[DbConfigurationSectionProcessing],
    clone_to: list[DbConfigurationSectionProcessing],
    logger: Logger | None = None,
) -> list[DbConfigurationSectionProcessing]:
    """
    Clones section processing instruction info from one list of sections into another.

    Handles narrative-only sections specially: ensures they always have action="retain"
    regardless of what was cloned, since they cannot be refined (no entry match rules).

    Stale (action, narrative) combinations on the source — e.g. from
    configurations persisted before the API validators landed — are
    coerced to a safe baseline via
    `ecr.policy.normalize_section_narrative`, with each coercion
    logged. Clone is a system-initiated operation (runs during
    activation/clone of a draft), so we prefer coerce-and-log over
    raising to avoid blocking unrelated work.

    Args:
        clone_from (list[DbConfigurationSectionProcessing]): The list of sections to clone processing instruction info from.
        clone_to (list[DbConfigurationSectionProcessing]): The list of sections to clone processing instruction info into.
        logger (Logger | None): Logger used to emit a warning per
            coercion. None silences the messages but still applies
            normalization.

    Returns:
        list[DbConfigurationSectionProcessing]: The new list of sections.
    """

    # Custom sections can just be copied straight over from the original since
    # they won't change version to version
    custom_sections = [
        section for section in clone_from if section.section_type == "custom"
    ]

    # Standard sections may change and require some additional processing
    standard_sections = [
        section for section in clone_from if section.section_type == "standard"
    ]

    action_map = {section.code: section.action for section in standard_sections}
    include_map = {section.code: section.include for section in standard_sections}
    narrative_map = {section.code: section.narrative for section in standard_sections}

    standard_updates = []
    for section in clone_to:
        if section.code in NARRATIVE_ONLY_SECTIONS:
            new_action: DbSectionAction = "retain"
        else:
            new_action = action_map.get(section.code, section.action)

        new_narrative = narrative_map.get(section.code, section.narrative)

        # normalize before persisting — stale combos from older
        # configurations get coerced to a safe baseline instead of
        # propagating into a fresh draft
        coerced_action, coerced_narrative, notes = normalize_section_narrative(
            code=section.code,
            section_action=new_action,
            narrative_action=new_narrative,
        )
        if notes and logger is not None:
            for note in notes:
                logger.warning("clone_section_processing_instructions: %s", note)

        standard_updates.append(
            replace(
                section,
                action=coerced_action,
                include=include_map.get(section.code, section.include),
                narrative=coerced_narrative,
            )
        )

    return standard_updates + custom_sections


async def get_config_payload_metadata(
    configuration: DbConfiguration, logger: Logger, db: AsyncDatabaseConnection
) -> ConfigurationStorageMetadata:
    """
    Creates a minimal ConfigurationStorageMetadata object from a DbConfiguration.

    When a primary condition exists, returns its display name, canonical URL,
    TES version, and child RSG SNOMED codes. When no primary condition exists
    (zero-code-set configuration), fabricates fallback metadata with
    condition_name="No Primary Condition", canonical_url="N/A", tes_version="0",
    and an empty child RSG SNOMED codes list.

    Args:
        configuration (DbConfiguration): The configuration from the database
        logger (Logger): The standard logger
        db (AsyncDatabaseConnection): The async database connection

    Returns:
        ConfigurationStorageMetadata: A configuration metadata object that can be written to a file system.
    """
    primary_condition = None
    if configuration.primary_condition_id:
        primary_condition = await get_condition_by_id_db(
            id=configuration.primary_condition_id, db=db
        )

    if not primary_condition:
        logger.warning(
            "No primary condition found for configuration; using fallback metadata",
            extra={
                "configuration_id": configuration.id,
                "jurisdiction_id": configuration.jurisdiction_id,
                "version": configuration.version,
            },
        )
        return ConfigurationStorageMetadata(
            condition_name="No Primary Condition",
            canonical_url="N/A",
            tes_version="0",
            jurisdiction_id=configuration.jurisdiction_id,
            configuration_version=configuration.version,
            child_rsg_snomed_codes=[],
        )

    return ConfigurationStorageMetadata(
        condition_name=primary_condition.display_name,
        canonical_url=primary_condition.canonical_url,
        tes_version=primary_condition.version,
        jurisdiction_id=configuration.jurisdiction_id,
        configuration_version=configuration.version,
        child_rsg_snomed_codes=primary_condition.child_rsg_snomed_codes,
    )


async def convert_config_to_storage_payload(
    configuration: DbConfiguration, db: AsyncDatabaseConnection
) -> ConfigurationStoragePayload | None:
    """
    Takes a DbConfiguration and distills it down to the bare minimum data required for refining.

    Builds structured CodeSystemSets for refinement with proper code system
    routing and display name enrichment. The legacy flat codes array is intentionally
    not serialized into active.json because code_system_sets contains the required
    code information without duplication.

    Args:
        configuration (DbConfiguration): The configuration from the database
        db (AsyncDatabaseConnection): The async database connection

    Returns:
        ConfigurationStoragePayload | None: A configuration that can be written to a file system, or None if operation can't be completed.
    """
    sections: list[dict[str, Any]] = []
    included_condition_rsg_codes: set[str] = set()

    # build per-system code dicts for CodeSystemSets
    coding_by_code_system: dict[str, list[dict]] = defaultdict(list)
    code_systems = await get_all_code_systems_by_key(db)
    # custom codes
    for cc in configuration.custom_codes:
        cur_code_system = code_systems[cc.system_key]

        if cur_code_system is None:
            raise ValueError(
                f"System with key {cc.system_key} doesn't match supported systems"
            )

        system_to_extend = cur_code_system.key

        # route custom codes to the correct system dict
        coding_by_code_system[system_to_extend].append(
            asdict(
                Coding(
                    code=cc.code,
                    display=cc.name,
                    system_oid=cur_code_system.oid,
                )
            )
        )

    conditions = await get_included_conditions_db(
        included_conditions=configuration.included_conditions, db=db
    )
    systems_keys_to_index_by = await get_allowed_code_system_keys(db=db)
    # condition codes -> build both the flat set and per-system dicts
    for condition in conditions:
        # map each db code list to its target dict + OID
        code_system_map: dict[CodeSystemKey, list[DbConditionCoding]] = (
            index_condition_code_list_by_system(
                condition=condition, system_keys_to_index_by=systems_keys_to_index_by
            )
        )

        for key, code_list in code_system_map.items():
            system_metadata = await get_code_system_by_key_db(key=key, db=db)
            if system_metadata is None:
                raise ValueError(
                    f"System of name {key} doesn't match supported systems"
                )
            coding_by_code_system[system_metadata.key].extend(
                [
                    asdict(
                        Coding(
                            code=c.code,
                            display=c.display,
                            system_oid=system_metadata.oid,
                        )
                    )
                    for c in code_list
                ]
            )

    sections = [
        asdict(section_process) for section_process in configuration.section_processing
    ]

    for c in conditions:
        included_condition_rsg_codes.update(c.child_rsg_snomed_codes)

    # STEP 3: build the CodeSystemSets
    code_system_sets = CodeSystemSets.from_dict(
        coding_by_code_system=coding_by_code_system,
        oid_to_system_map=OID_TO_SYSTEM_KEY_MAP,
    )

    return ConfigurationStoragePayload(
        sections=sections,
        included_condition_rsg_codes=included_condition_rsg_codes,
        code_system_sets=code_system_sets.to_dict(),
    )


def format_section_naming(
    section: DbConfigurationSectionProcessing,
) -> DbConfigurationSectionProcessing:
    """
    Takes a section and modifies its name to remove `Section` at the end of it. It also converts the name to title case.

    Args:
        section (DbConfigurationSectionProcessing): Section with name to modify

    Returns:
        DbConfigurationSectionProcessing: Section with modified name
    """

    # Don't modify the name of a custom section
    if section.section_type == "custom":
        return section

    name_without_section = re.sub(
        r"\s+section\s*$", "", section.name, flags=re.IGNORECASE
    )
    return replace(section, name=name_without_section.strip().title())


async def create_configuration_service(
    condition_id: UUID | None,
    user_id: UUID,
    jurisdiction_id: str,
    db: AsyncDatabaseConnection,
    logger: Logger,
) -> DbConfiguration:
    """
    Create a new configuration with zero-code-set branching logic extracted from routes.

    Handles both condition-based configurations (with branching for latest config cloning)
    and zero-code-set configurations (no condition).

    Args:
        condition_id (UUID | None): The condition ID to base the configuration on, or None for zero-code-set
        user_id (UUID): The ID of the user creating the configuration
        jurisdiction_id (str): The jurisdiction ID
        db (AsyncDatabaseConnection): The async database connection
        logger (Logger): The standard logger

    Returns:
        DbConfiguration: The created configuration

    Raises:
        HTTPException: 404 if condition not found
        HTTPException: 409 if draft config already exists for condition + jurisdiction
        HTTPException: 500 if configuration creation fails
    """
    from app.db.conditions.db import get_condition_by_id_db
    from app.db.configurations.db import (
        get_latest_config_db,
        insert_configuration_db,
        is_config_valid_to_insert_db,
    )

    condition = None
    latest_config = None

    if condition_id is not None:
        condition = await get_condition_by_id_db(id=condition_id, db=db)

        if not condition:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Condition with ID {condition_id} could not be found or does not exist.",
            )

        # check that there isn't already a draft config for the condition + JD
        if not await is_config_valid_to_insert_db(
            condition_canonical_url=condition.canonical_url,
            jurisdiction_id=jurisdiction_id,
            db=db,
        ):
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Can't create configuration because a draft configuration for the condition already exists.",
            )

        latest_config = await get_latest_config_db(
            jurisdiction_id=jurisdiction_id,
            condition_canonical_url=condition.canonical_url,
            db=db,
        )

        if not latest_config:
            logger.info(
                "Creating fresh draft config",
                extra={
                    "condition": condition.display_name,
                    "canonical_url": condition.canonical_url,
                },
            )
        else:
            logger.info(
                "Creating cloned draft config",
                extra={
                    "condition": condition.display_name,
                    "canonical_url": condition.canonical_url,
                    "cloned_configuration_id": latest_config.id,
                },
            )
    else:
        # Zero-code-set configuration
        latest_config = None
        logger.info(
            "Creating zero-code-set configuration",
            extra={
                "jurisdiction_id": jurisdiction_id,
            },
        )

    config = await insert_configuration_db(
        condition=condition,
        user_id=user_id,
        jurisdiction_id=jurisdiction_id,
        config_to_clone=latest_config,
        db=db,
    )

    if config is None:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create configuration",
        )

    return config


async def get_configuration_service(
    configuration_id: UUID,
    jurisdiction_id: str,
    db: AsyncDatabaseConnection,
    logger: Logger,
) -> tuple[
    DbConfiguration,
    list[DbCode],
    list[IncludedCondition],
    list[GetConfigurationResponseVersion],
    int | None,
    UUID | None,
    int,
    UUID | None,
    str | None,
    bool,
    UUID | None,
]:
    """
    Get configuration with zero-code-set branching logic extracted from routes.

    Handles primary condition existence branching: when primary condition exists,
    fetches all conditions by version, builds included conditions list, retrieves
    all versions, and determines active/draft/active configuration IDs. When no
    primary condition exists, returns empty/zero values for condition-related fields.

    Args:
        configuration_id (UUID): The configuration ID
        jurisdiction_id (str): The jurisdiction ID
        db (AsyncDatabaseConnection): The async database connection
        logger (Logger): The standard logger

    Returns:
        tuple: (config, rsg_codes, included_conditions, all_versions,
                active_version, active_configuration_id, latest_version,
                condition_id, condition_canonical_url, is_draft, draft_id)
    """
    from app.db.conditions.db import (
        get_conditions_by_version_db,
        get_primary_condition_db,
    )
    from app.db.configurations.db import (
        get_configuration_versions_db,
        get_latest_config_db,
    )

    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=jurisdiction_id, db=db
    )

    if not config:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found.",
        )

    primary_condition = await get_primary_condition_db(
        configuration_id=config.id, db=db
    )

    # fetch all conditions from the db based on the primary condition's version
    # if no primary condition exists, we still return the configuration
    all_conditions = []
    latest_config = None
    included_conditions = []
    all_versions = []
    active_config = None
    draft_config = None
    draft_id = None
    is_draft = False
    active_version = None
    active_configuration_id = None
    latest_version = 0
    condition_id = None
    condition_canonical_url = None
    rsg_codes = []

    rsg_codes = (
        await get_rsg_codes_by_condition_id_db(
            condition_id=primary_condition.id,
            db=db,
        )
        if primary_condition
        else []
    )

    if primary_condition:
        all_conditions = await get_conditions_by_version_db(
            version=primary_condition.version,
            db=db,
        )

        latest_config = await get_latest_config_db(
            jurisdiction_id=jurisdiction_id,
            condition_canonical_url=primary_condition.canonical_url,
            db=db,
        )

        # Build IncludedCondition objects for ONLY associated conditions
        included_ids = set(config.included_conditions)
        included_conditions = [
            IncludedCondition(
                id=condition.id,
                display_name=condition.display_name,
                canonical_url=condition.canonical_url,
                version=condition.version,
                associated=True,
            )
            for condition in all_conditions
            if condition.id in included_ids or condition.id == primary_condition.id
        ]

        all_versions = await get_configuration_versions_db(
            jurisdiction_id=jurisdiction_id,
            condition_canonical_url=primary_condition.canonical_url,
            db=db,
        )

        active_config = next((v for v in all_versions if v.status == "active"), None)
        draft_config = next((v for v in all_versions if v.status == "draft"), None)

        draft_id = draft_config.id if draft_config is not None else None
        is_draft = draft_id == config.id
        active_version = active_config.version if active_config is not None else None
        active_configuration_id = (
            active_config.id if active_config is not None else None
        )
        latest_version = latest_config.version if latest_config is not None else 0

        condition_id = primary_condition.id
        condition_canonical_url = primary_condition.canonical_url
    else:
        # ZCS config: scope versions by original_condition_id
        from app.db.configurations.model import NO_CONDITION_SENTINEL

        all_versions = await get_configuration_versions_db(
            jurisdiction_id=jurisdiction_id,
            condition_canonical_url=NO_CONDITION_SENTINEL,
            db=db,
            original_condition_id=config.original_condition_id,
        )

        active_config = next((v for v in all_versions if v.status == "active"), None)
        draft_config = next((v for v in all_versions if v.status == "draft"), None)

        draft_id = draft_config.id if draft_config is not None else None
        is_draft = draft_id == config.id
        active_version = active_config.version if active_config is not None else None
        active_configuration_id = (
            active_config.id if active_config is not None else None
        )
        latest_version = 0

        condition_id = None
        condition_canonical_url = None

    return (
        config,
        rsg_codes,
        included_conditions,
        all_versions,
        active_version,
        active_configuration_id,
        latest_version,
        condition_id,
        condition_canonical_url,
        is_draft,
        draft_id,
    )
