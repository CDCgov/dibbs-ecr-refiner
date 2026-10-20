import re
from collections import defaultdict
from dataclasses import replace
from logging import Logger
from typing import Any
from uuid import UUID

from app.core.models.configurations import SectionAction
from app.core.models.payloads import (
    CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION,
    ConfigurationStorageMetadata,
    ConfigurationStoragePayload,
)
from app.core.models.terminology import Coding
from app.db.code_systems.db import (
    get_id_to_code_system_dict_db,
)
from app.db.code_systems.model import DbCodeSystem
from app.db.codes.db import get_pruned_configuration_codes_db
from app.db.conditions.db import get_condition_by_id_db, get_included_conditions_db
from app.db.configurations.custom_codes.model import DbCustomCode
from app.db.configurations.model import (
    ConfiguredSection,
    DbConfiguration,
)
from app.db.pool import AsyncDatabaseConnection
from app.services.ecr.policy import (
    NARRATIVE_ONLY_SECTIONS,
    SECTION_PROCESSING_SKIP,
    normalize_section_processing,
)
from app.services.ecr.specification import (
    get_section_version_map,
    load_spec,
)
from app.services.ecr.specification.constants import OID_TO_SYSTEM_KEY_MAP, OTHER_OID
from app.services.terminology import (
    CodeSystemKey,
    CodeSystemSets,
)


def get_default_sections() -> list[ConfiguredSection]:
    """
    Constructs and returns a list of default sections for the latest spec.

    Returns:
        list[ConfiguredSection]: List of sections with default values set.
    """

    spec = load_spec("3.1.1")
    loinc_versions_flat = get_section_version_map()

    # TODO:
    # we should try to keep `db` related models out of the
    # ecr service as much as practicable

    # Narrative-only sections (has_match_rules=False) should default to "retain"
    # since there is nothing to match against
    section_processing_defaults = [
        ConfiguredSection(
            display_name=section_spec.display_name,
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
    clone_from: list[ConfiguredSection],
    clone_to: list[ConfiguredSection],
    logger: Logger | None = None,
) -> list[ConfiguredSection]:
    """
    Clones section processing instruction info from one list of sections into another.

    Handles narrative-only sections specially: ensures they always have action="retain"
    regardless of what was cloned, since they cannot be refined (no entry match rules).
    Trigger code sections are likewise forced back to include=True, so a draft cloned
    from a configuration authored before that policy landed can't carry a removal
    forward.

    Stale (action, narrative) combinations on the source — e.g. from
    configurations persisted before the API validators landed — are
    coerced to a safe baseline via
    `ecr.policy.normalize_section_processing`, with each coercion
    logged. Clone is a system-initiated operation (runs during
    activation/clone of a draft), so we prefer coerce-and-log over
    raising to avoid blocking unrelated work.

    Args:
        clone_from (list[ConfiguredSection]): The list of sections to clone processing instruction info from.
        clone_to (list[ConfiguredSection]): The list of sections to clone processing instruction info into.
        logger (Logger | None): Logger used to emit a warning per
            coercion. None silences the messages but still applies
            normalization.

    Returns:
        list[ConfiguredSection]: The new list of sections.
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
            new_action: SectionAction = "retain"
        else:
            new_action = action_map.get(section.code, section.action)

        new_narrative = narrative_map.get(section.code, section.narrative)
        new_include = include_map.get(section.code, section.include)

        # normalize before persisting — stale combos from older
        # configurations get coerced to a safe baseline instead of
        # propagating into a fresh draft
        coerced_include, coerced_action, coerced_narrative, notes = (
            normalize_section_processing(
                code=section.code,
                include=new_include,
                section_action=new_action,
                narrative_action=new_narrative,
            )
        )
        if notes and logger is not None:
            for note in notes:
                logger.warning("clone_section_processing_instructions: %s", note)

        standard_updates.append(
            replace(
                section,
                action=coerced_action,
                include=coerced_include,
                narrative=coerced_narrative,
            )
        )

    return standard_updates + custom_sections


def as_coding(code: DbCustomCode, code_systems: dict[UUID, DbCodeSystem]) -> Coding:
    """
    Resolves a custom code's `systems.id` into the OID the refiner matches on.

    Only custom codes need this: `get_pruned_configuration_codes_db` resolves the OID
    in SQL, but `convert_config_to_storage_payload` also passes
    `configuration.custom_codes` directly, and those rows carry a `system_id`.

    Args:
        code (DbCustomCode): The custom code row.
        code_systems (dict[UUID, DbCodeSystem]): Every code system, keyed by id.

    Returns:
        Coding: The code with its system resolved to an OID.
    """

    system = code_systems.get(code.system_id)
    return Coding(
        code=code.code,
        display_name=code.display_name,
        system_oid=system.oid if system and system.oid else OTHER_OID,
    )


def index_code_list_by_system_key(
    codes: list[Coding],
    logger: Logger,
) -> dict[CodeSystemKey, list[dict]]:
    """
    Groups resolved codings into the per-system buckets `active.json` is keyed by.

    Args:
        codes (list[Coding]): Codes with their systems already resolved to OIDs.
        logger (Logger): Used to warn about an OID with no bucket.

    Returns:
        dict[CodeSystemKey, list[dict]]: Codings per system key, in payload shape.
    """

    result: dict[CodeSystemKey, list[dict]] = defaultdict(list)
    for c in codes:
        # NOTE:
        # this guard used to key off `system_id not in code_systems`, which could never
        # fire -- `codes.system_id` and `custom_codes.system_id` are NOT NULL foreign
        # keys into `systems` and the dict held every row, so the warning was dead. the
        # reachable version of the same worry is an OID with no bucket, which a seventh
        # seeded code system would produce
        system_key = OID_TO_SYSTEM_KEY_MAP.get(c.system_oid)
        if system_key is None:
            logger.warning(
                f"Code system OID {c.system_oid!r} has no bucket in "
                f"OID_TO_SYSTEM_KEY_MAP; routing to {OTHER_OID}"
            )
            system_key = OID_TO_SYSTEM_KEY_MAP[OTHER_OID]

        # NOTE:
        # the payload keys are spelled here rather than taken from `asdict(Coding(...))`.
        # that `asdict` worked only because the field names happened to equal the
        # `active.json` keys, so renaming `Coding.display` -> `display_name` silently
        # emptied every display on the way to `CodeSystemSets.from_dict` -- the same
        # writer/reader mismatch as #967, which is what ADR 0016 was written about.
        # `from_dict` reads `display`, so `display` is what gets written, until the
        # schema bump renames the key on both sides
        result[system_key].append(
            {
                "code": c.code,
                "display": c.display_name,
                "system_oid": c.system_oid,
            }
        )

    return result


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
    configuration: DbConfiguration, db: AsyncDatabaseConnection, logger: Logger
) -> ConfigurationStoragePayload | None:
    """
    Takes a DbConfiguration and distills it down to the bare minimum data required for refining.

    Builds structured CodeSystemSets for refinement with proper code system
    routing and display name enrichment. The legacy flat codes array is intentionally
    not serialized into active.json because code_system_sets contains the required
    code information without duplication.

    Section processing instructions are normalized via
    `ecr.policy.normalize_section_processing` before serialization, so an
    invalid combination can never reach the refiner even if one is sitting
    in the database. Each coercion is logged.

    Args:
        configuration (DbConfiguration): The configuration from the database
        db (AsyncDatabaseConnection): The async database connection
        logger (Logger): The logger

    Returns:
        ConfigurationStoragePayload | None: A configuration that can be written to a file system, or None if operation can't be completed.
    """

    included_condition_rsg_codes: set[str] = set()

    # build per-system code dicts for CodeSystemSets
    conditions = await get_included_conditions_db(
        included_conditions=configuration.included_conditions, db=db
    )
    code_systems = await get_id_to_code_system_dict_db(db=db)

    configuration_codes = await get_pruned_configuration_codes_db(
        configuration_id=configuration.id, db=db
    )
    # the query covers custom codes only for configurations that have at least one
    # `configurations_conditions` row, so they are added again here. duplicates
    # collapse downstream -- `CodeSystemSets.from_dict` keys each system by code
    codes_to_index = configuration_codes + [
        as_coding(code, code_systems) for code in configuration.custom_codes
    ]

    coding_by_code_system: dict[str, list[dict]] = index_code_list_by_system_key(
        codes=codes_to_index, logger=logger
    )

    # activation is the last system-initiated path before a configuration
    # reaches the refiner, and it serializes straight from the database rows.
    # the API validators guard user edits and the clone path guards new
    # versions, but an inactive configuration can be re-activated directly
    # from stale rows without passing through either — so normalize here too.
    sections: list[dict[str, Any]] = []
    for section_process in configuration.section_processing:
        coerced_include, coerced_action, coerced_narrative, notes = (
            normalize_section_processing(
                code=section_process.code,
                include=section_process.include,
                section_action=section_process.action,
                narrative_action=section_process.narrative,
            )
        )
        for note in notes:
            logger.warning("convert_config_to_storage_payload: %s", note)

        # NOTE:
        # only the fields the refiner actually reads are serialized. `versions`
        # and `section_type` are UI context derived from `_VERSION_SECTIONS`,
        # which the refinement core imports directly -- reading a stale copy
        # back from S3 would be strictly worse than calling `load_spec`
        sections.append(
            {
                "code": section_process.code,
                "name": section_process.display_name,
                "action": coerced_action,
                "narrative": coerced_narrative,
                "include": coerced_include,
            }
        )

    for c in conditions:
        included_condition_rsg_codes.update(c.child_rsg_snomed_codes)

    # STEP 3: build the CodeSystemSets
    code_system_sets = CodeSystemSets.from_dict(
        coding_by_code_system=coding_by_code_system,
        oid_to_system_map=OID_TO_SYSTEM_KEY_MAP,
    )

    return ConfigurationStoragePayload(
        schema_version=CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION,
        sections=sections,
        included_condition_rsg_codes=included_condition_rsg_codes,
        code_system_sets=code_system_sets.to_dict(),
    )


def format_section_naming(
    section: ConfiguredSection,
) -> ConfiguredSection:
    """
    Takes a section and modifies its name to remove `Section` at the end of it. It also converts the name to title case.

    Args:
        section (ConfiguredSection): Section with name to modify

    Returns:
        ConfiguredSection: Section with modified name
    """

    # Don't modify the name of a custom section
    if section.section_type == "custom":
        return section

    name_without_section = re.sub(
        r"\s+section\s*$", "", section.display_name, flags=re.IGNORECASE
    )
    return replace(section, display_name=name_without_section.strip().title())
