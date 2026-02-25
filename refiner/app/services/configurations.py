from collections import defaultdict
from dataclasses import replace
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
from app.services.ecr.specification import (
    EICR_SPECS_DATA,
    SECTION_PROCESSING_SKIP,
    load_spec,
)


def get_default_sections() -> list[DbConfigurationSectionProcessing]:
    """
    Constructs and returns a list of default sections for the latest spec.

    Returns:
        list[DbConfigurationSectionProcessing]: List of sections with default values set.
    """

    # use the new specification system in the ecr service
    spec = load_spec("3.1.1")

    # build loinc->versions dict once per import
    _LOINC_VERSIONS_MAP: dict[str, set[str]] = defaultdict(set)
    for version, version_data in EICR_SPECS_DATA.items():
        for loinc in version_data.keys():
            _LOINC_VERSIONS_MAP[loinc].add(version)
    _LOINC_VERSIONS_FLAT = {k: sorted(v) for k, v in _LOINC_VERSIONS_MAP.items()}

    section_processing_defaults = [
        DbConfigurationSectionProcessing(
            name=section_spec.display_name,
            code=loinc_code,
            action="refine",
            versions=_LOINC_VERSIONS_FLAT.get(loinc_code, []),
        )
        for loinc_code, section_spec in spec.sections.items()
        if loinc_code
        not in SECTION_PROCESSING_SKIP  # Skipping emergency outbreak and reportability response sections
    ]

    return section_processing_defaults


def clone_section_actions(
    clone_from: list[DbConfigurationSectionProcessing],
    clone_to: list[DbConfigurationSectionProcessing],
) -> list[DbConfigurationSectionProcessing]:
    """
    Clones section actions from one list of sections into another.

    Args:
        clone_from (list[DbConfigurationSectionProcessing]): The list of sections to clone actions from.
        clone_to (list[DbConfigurationSectionProcessing]): The list of sections to clone actions into.

    Returns:
        list[DbConfigurationSectionProcessing]: The new list of sections.
    """
    action_map = {section.code: section.action for section in clone_from}

    return [replace(ds, action=action_map.get(ds.code, ds.action)) for ds in clone_to]


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

    Args:
        configuration (DbConfiguration): The configuration from the database
        db (AsyncDatabaseConnection): The async database connection

    Returns:
        ConfigurationStoragePayload | None: A configuration that can be written to a file system, or None if operation can't be completed.
    """
    codes: set[str] = set()
    sections: list[dict[str, Any]] = []
    included_condition_rsg_codes: set[str] = set()

    # custom codes
    for cc in configuration.custom_codes:
        codes.add(cc.code)

    conditions = await get_included_conditions_db(
        included_conditions=configuration.included_conditions, db=db
    )

    # condition codes
    for condition in conditions:
        for code_list in [
            condition.snomed_codes,
            condition.loinc_codes,
            condition.icd10_codes,
            condition.rxnorm_codes,
        ]:
            codes.update(code.code for code in code_list)

    sections = [
        {
            "code": section_process.code,
            "name": section_process.name,
            "action": section_process.action,
        }
        for section_process in configuration.section_processing
    ]

    for c in conditions:
        included_condition_rsg_codes.update(c.child_rsg_snomed_codes)

    return ConfigurationStoragePayload(
        codes=codes,
        sections=sections,
        included_condition_rsg_codes=included_condition_rsg_codes,
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
