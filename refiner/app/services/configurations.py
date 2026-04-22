import re
from collections import defaultdict
from dataclasses import asdict, replace
from logging import Logger
from typing import Any

from app.db.conditions.db import get_condition_by_id_db, get_included_conditions_db
from app.db.configurations.model import (
    ConfigurationStorageMetadata,
    ConfigurationStoragePayload,
    DbConfiguration,
    DbConfigurationSectionProcessing,
)
from app.db.pool import AsyncDatabaseConnection
from app.services.ecr.policy import SECTION_PROCESSING_SKIP
from app.services.ecr.specification import (
    get_section_version_map,
    load_spec,
)
from app.services.terminology import (
    CodeSystem,
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
    section_processing_defaults = [
        DbConfigurationSectionProcessing(
            name=section_spec.display_name,
            code=loinc_code,
            narrative=True,
            include=True,
            action="retain" if loinc_code in SECTION_PROCESSING_SKIP else "refine",
            versions=loinc_versions_flat.get(loinc_code, []),
            section_type="standard",
        )
        for loinc_code, section_spec in spec.sections.items()
    ]

    return section_processing_defaults


def clone_section_processing_instructions(
    clone_from: list[DbConfigurationSectionProcessing],
    clone_to: list[DbConfigurationSectionProcessing],
) -> list[DbConfigurationSectionProcessing]:
    """
    Clones section processing instruction info from one list of sections into another.

    Args:
        clone_from (list[DbConfigurationSectionProcessing]): The list of sections to clone processing instruction info from.
        clone_to (list[DbConfigurationSectionProcessing]): The list of sections to clone processing instruction info into.

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

    standard_updates = [
        replace(
            section,
            action=action_map.get(section.code, section.action),
            include=include_map.get(section.code, section.include),
            narrative=narrative_map.get(section.code, section.narrative),
        )
        for section in clone_to
    ]

    return standard_updates + custom_sections


async def get_config_payload_metadata(
    configuration: DbConfiguration, logger: Logger, db: AsyncDatabaseConnection
) -> ConfigurationStorageMetadata | None:
    """
    Creates a minimal ConfigurationStorageMetadata object from a DbConfiguration.

    Args:
        configuration (DbConfiguration): The configuration from the database
        logger (Logger): The standard logger
        db (AsyncDatabaseConnection): The async database connection

    Returns:
        ConfigurationStorageMetadata | None: A configuration metadata object that can be written to a file system, or None if operation can't be completed.
    """
    primary_condition = await get_condition_by_id_db(
        id=configuration.condition_id, db=db
    )

    if not primary_condition:
        logger.error(
            "Configuration metadata could not be created due to missing primary condition ID.",
            extra={
                "configuration_id": configuration.id,
                "jurisdiction_id": configuration.jurisdiction_id,
            },
        )
        return None

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

    Produces both a flat code set (for the generic fallback matching path) and a
    structured CodeSystemSets (for section-aware matching with proper code system
    routing and displayName enrichment). Both are serialized into the active.json
    file so that lambda has full parity with the webapp's refinement pipeline.

    Args:
        configuration (DbConfiguration): The configuration from the database
        db (AsyncDatabaseConnection): The async database connection

    Returns:
        ConfigurationStoragePayload | None: A configuration that can be written to a file system, or None if operation can't be completed.
    """
    codes: set[str] = set()
    sections: list[dict[str, Any]] = []
    included_condition_rsg_codes: set[str] = set()

    # build per-system code dicts for CodeSystemSets
    coding_by_code_system: dict[str, list[dict]] = defaultdict(list)

    # custom codes
    for cc in configuration.custom_codes:
        codes.add(cc.code)
        cur_code_system = CodeSystem(cc.system)
        system_to_extend = cur_code_system.format_system_string()

        # route custom codes to the correct system dict
        coding_by_code_system[system_to_extend].append(
            asdict(
                Coding(
                    code=cc.code,
                    display=cc.name,
                    system=cur_code_system.oid,
                )
            )
        )

    conditions = await get_included_conditions_db(
        included_conditions=configuration.included_conditions, db=db
    )

    # condition codes -> build both the flat set and per-system dicts
    for condition in conditions:
        # map each db code list to its target dict + OID
        code_system_map: dict[CodeSystem, list] = index_condition_code_list_by_system(
            condition
        )

        for code_system, code_list in code_system_map.items():
            codes = codes | {c.code for c in code_list}
            system_to_extend = CodeSystem(code_system).format_system_string()
            coding_by_code_system[system_to_extend] += [
                asdict(Coding(code=c.code, display=c.display, system=code_system.oid))
                for c in code_list
            ]

    sections = [
        asdict(section_process) for section_process in configuration.section_processing
    ]

    for c in conditions:
        included_condition_rsg_codes.update(c.child_rsg_snomed_codes)

    # STEP 3: build the CodeSystemSets
    code_system_sets = CodeSystemSets.from_dict(data=coding_by_code_system)

    return ConfigurationStoragePayload(
        codes=codes,
        sections=sections,
        included_condition_rsg_codes=included_condition_rsg_codes,
        code_system_sets=code_system_sets.to_dict(),
    )


def get_canonical_url_to_highest_inactive_version_map(
    configs: list[DbConfiguration],
) -> dict[str, DbConfiguration]:
    """
    Creates a dictionary that maps a condition URL to the highest inactive version configuration.

    Args:
        configs (list[DbConfiguration]): List of DbConfigurations

    Returns:
    a dictionary with the structure:
        key = Condition canonical URL
        value = Inactive configuration with highest version number
    """
    highest_version_inactive_configs_map: dict[str, DbConfiguration] = {}
    for c in configs:
        if c.status == "inactive":
            key = c.condition_canonical_url
            if (
                key not in highest_version_inactive_configs_map
                or c.version > highest_version_inactive_configs_map[key].version
            ):
                highest_version_inactive_configs_map[key] = c
    return highest_version_inactive_configs_map


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
