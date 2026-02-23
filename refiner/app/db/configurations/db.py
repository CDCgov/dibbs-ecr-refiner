from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from uuid import UUID

from psycopg.rows import class_row, dict_row
from psycopg.types.json import Jsonb

import app.services.ecr.specification as spec_mod
from app.db.events.db import insert_event_db
from app.db.events.model import EventInput

from ...services.ecr.specification import load_spec
from ..conditions.model import DbCondition
from ..pool import AsyncDatabaseConnection
from .model import DbConfiguration, DbConfigurationCustomCode, DbConfigurationStatus

EMPTY_JSONB = Jsonb([])


async def insert_configuration_db(
    condition: DbCondition,
    user_id: UUID,
    jurisdiction_id: str,
    db: AsyncDatabaseConnection,
    config_to_clone: DbConfiguration | None = None,
) -> DbConfiguration | None:
    """
    Inserts a configuration into the database. If a `config_to_clone` is passed in, it'll base the new config's values off of that config.

    The `name` field is always set to the display_name of the associated condition at creation time,
    for easier display and searching. The authoritative clinical context is still given by `condition_id`.
    """

    query = """
    INSERT INTO configurations (
        jurisdiction_id,
        condition_id,
        name,
        created_by,
        included_conditions,
        custom_codes,
        local_codes,
        section_processing
    )
    VALUES (
        %s,
        %s,
        %s,
        %s,
        %s::jsonb,
        %s::jsonb,
        %s::jsonb,
        %s::jsonb
    )
    RETURNING
        id,
        name,
        status,
        jurisdiction_id,
        condition_id,
        included_conditions,
        custom_codes,
        local_codes,
        section_processing,
        version,
        last_activated_at,
        last_activated_by,
        created_by,
        condition_canonical_url,
        s3_urls
    """

    # use the new specification system in the ecr service
    # * default to version 1.1 for backward compatibility
    spec = load_spec("1.1")

    # build loinc->versions dict once per import

    _LOINC_VERSIONS_MAP: dict[str, set[str]] = {}
    for v, vdata in spec_mod.EICR_SPECS_DATA.items():
        for loinc in vdata.keys():
            _LOINC_VERSIONS_MAP.setdefault(loinc, set()).add(v)
    _LOINC_VERSIONS_FLAT = {k: sorted(v) for k, v in _LOINC_VERSIONS_MAP.items()}

    section_processing_defaults = [
        {
            "name": section_spec.display_name,
            "code": loinc_code,
            "action": "refine",
            "versions": _LOINC_VERSIONS_FLAT.get(loinc_code, []),
        }
        for loinc_code, section_spec in spec.sections.items()
    ]

    params: tuple[str, UUID, str, UUID, Jsonb, Jsonb, Jsonb, Jsonb]
    if config_to_clone:
        params = (
            jurisdiction_id,
            # always link a configuration to a primary condition
            condition.id,
            # always set name to condition display name
            config_to_clone.name,
            # cloned by this user
            user_id,
            # included_conditions: always start with primary
            Jsonb(
                [str(c.id) for c in config_to_clone.included_conditions]
            ),  # <- changed to flat list of strings (UUIDs)
            # custom_codes
            Jsonb(
                [
                    {"name": c.name, "code": c.code, "system": c.system}
                    for c in config_to_clone.custom_codes
                ]
            ),
            # local_codes
            Jsonb(
                [
                    {"name": c.name, "code": c.code, "system": c.system}
                    for c in config_to_clone.local_codes
                ]
            ),
            # section_processing
            Jsonb(
                [
                    {
                        "name": c.name,
                        "code": c.code,
                        "action": c.action,
                        "versions": c.versions,
                    }
                    for c in config_to_clone.section_processing
                ]
            ),
        )
    else:
        params = (
            jurisdiction_id,
            # always link a configuration to a primary condition
            condition.id,
            # always set name to condition display name
            condition.display_name,
            # created by this user
            user_id,
            # included_conditions: always start with primary
            Jsonb([str(condition.id)]),  # <- changed to flat list of strings (UUIDs)
            # custom_codes
            EMPTY_JSONB,
            # local_codes
            EMPTY_JSONB,
            # section_processing
            Jsonb(section_processing_defaults),
        )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if not row:
                return None

            config = DbConfiguration.from_db_row(row)
            await insert_event_db(
                event=EventInput(
                    jurisdiction_id=config.jurisdiction_id,
                    user_id=user_id,
                    configuration_id=config.id,
                    event_type="create_configuration",
                    action_text="Created configuration",
                ),
                cursor=cur,
            )
            return config


async def get_configurations_db(
    jurisdiction_id: str, db: AsyncDatabaseConnection
) -> list[DbConfiguration]:
    """
    Fetch all configurations from the DB for a given jurisdiction.
    """

    query = """
        SELECT
            id,
            name,
			status,
            jurisdiction_id,
            condition_id,
            included_conditions,
            custom_codes,
            local_codes,
            section_processing,
            version,
			last_activated_at,
			last_activated_by,
            created_by,
            condition_canonical_url,
            s3_urls
        FROM configurations
        WHERE jurisdiction_id = %s
        ORDER BY name asc;
        """

    params = (jurisdiction_id,)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return [DbConfiguration.from_db_row(row) for row in rows]


async def get_configuration_by_id_db(
    id: UUID, jurisdiction_id: str, db: AsyncDatabaseConnection
) -> DbConfiguration | None:
    """
    Fetch a configuration by the given ID.
    """

    query = """
        SELECT
            id,
            name,
			status,
            jurisdiction_id,
            condition_id,
            included_conditions,
            custom_codes,
            local_codes,
            section_processing,
            version,
			last_activated_at,
			last_activated_by,
            created_by,
            condition_canonical_url,
            s3_urls
        FROM configurations
        WHERE id = %s
        AND jurisdiction_id = %s
        """

    params = (
        id,
        jurisdiction_id,
    )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if not row:
        return None

    return DbConfiguration.from_db_row(row)


async def is_config_valid_to_insert_db(
    condition_canonical_url: str, jurisdiction_id: str, db: AsyncDatabaseConnection
) -> bool:
    """
    Query the database to check if a configuration can be created. If a config for a condition already exists, returns False.
    """

    query = """
    SELECT id
    from configurations
    WHERE condition_canonical_url = %s
    AND jurisdiction_id = %s
    and status = 'draft'
        """

    params = (
        condition_canonical_url,
        jurisdiction_id,
    )

    async with db.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return len(rows) == 0


async def associate_condition_codeset_with_configuration_db(
    config: DbConfiguration,
    condition: DbCondition,
    user_id: UUID,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Given a condition, associate its set of codes with the specified configuration. Prevents the addition of duplicate conditions.

    NOTE: If the primary condition ever changes, you should also update the `name` field to match the new condition's display_name.

    Args:
        config (DbConfiguration): The configuration
        condition (DbCondition): The condition
        user_id (UUID): The user performing the action
        db (AsyncDatabaseConnection): Database connection

    Returns:
        DbConfiguration: The updated configuration
    """

    query = """
            WITH new_condition AS (
                SELECT %s::jsonb AS val
            )
            UPDATE configurations
            SET included_conditions = (
            SELECT jsonb_agg(elem)
            FROM (
                SELECT elem
                FROM jsonb_array_elements(included_conditions) elem
                UNION ALL
                SELECT elem
                FROM new_condition,
                     jsonb_array_elements(new_condition.val) elem
                WHERE NOT EXISTS (
                SELECT 1
                FROM jsonb_array_elements(included_conditions) existing
                WHERE existing::text = elem::text
                )
            ) s
            )
            WHERE id = %s
            RETURNING
                id,
                name,
                status,
                jurisdiction_id,
                condition_id,
                included_conditions,
                custom_codes,
                local_codes,
                section_processing,
                version,
                last_activated_at,
                last_activated_by,
                created_by,
                condition_canonical_url,
                s3_urls;
            """

    new_condition = Jsonb([str(condition.id)])
    params = (new_condition, config.id)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

            if not row:
                return None

            updated_config = DbConfiguration.from_db_row(row)

            await insert_event_db(
                event=EventInput(
                    jurisdiction_id=updated_config.jurisdiction_id,
                    user_id=user_id,
                    configuration_id=updated_config.id,
                    event_type="add_code",
                    action_text=f"Associated '{condition.display_name}' code set",
                ),
                cursor=cur,
            )

            return updated_config


async def disassociate_condition_codeset_with_configuration_db(
    config: DbConfiguration,
    condition: DbCondition,
    user_id: UUID,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Given a condition, remove its codeset from the specified configuration.

    This is the opposite of associate_condition_codeset_with_configuration_db.

    Args:
        config (DbConfiguration): The configuration
        condition (DbCondition): The condition to remove
        user_id (UUID): The user performing the action
        db (AsyncDatabaseConnection): Database connection

    Returns:
        DbConfiguration: The updated configuration
    """

    query = """
        UPDATE configurations
        SET included_conditions = (
            SELECT COALESCE(jsonb_agg(elem_text), '[]'::jsonb)
            FROM (
                SELECT elem_text
                FROM (
                    SELECT jsonb_array_elements_text(COALESCE(included_conditions, '[]'::jsonb)) AS elem_text
                ) t
                WHERE elem_text <> %s
            ) filtered
        )
        WHERE id = %s
        RETURNING
            id,
            name,
            status,
            jurisdiction_id,
            condition_id,
            included_conditions,
            custom_codes,
            local_codes,
            section_processing,
            version,
			last_activated_at,
			last_activated_by,
            created_by,
            condition_canonical_url,
            s3_urls;
    """

    params = (str(condition.id), config.id)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

            if not row:
                return None

            updated_config = DbConfiguration.from_db_row(row)

            await insert_event_db(
                event=EventInput(
                    jurisdiction_id=updated_config.jurisdiction_id,
                    user_id=user_id,
                    configuration_id=updated_config.id,
                    event_type="delete_code",
                    action_text=f"Removed '{condition.display_name}' code set",
                ),
                cursor=cur,
            )

            return updated_config


@dataclass(frozen=True)
class DbTotalConditionCodeCount:
    """
    Total code count model.
    """

    condition_id: UUID
    display_name: str
    total_codes: int


async def get_total_condition_code_counts_by_configuration_db(
    config_id: UUID, db: AsyncDatabaseConnection
) -> list[DbTotalConditionCodeCount]:
    """
    Given a config ID, returns the total associated code count by condition.
    """

    query = """
        WITH conds AS (
            SELECT jsonb_array_elements_text(included_conditions) AS cond_id
            FROM configurations
            WHERE id = %s
        ),
        codes AS (
            SELECT
                c.id AS condition_id,
                code_elem->>'code' AS code
            FROM conds
            JOIN conditions c
                ON c.id::text = cond_id
            CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.loinc_codes, '[]'::jsonb)) AS code_elem

            UNION

            SELECT
                c.id AS condition_id,
                code_elem->>'code' AS code
            FROM conds
            JOIN conditions c
                ON c.id::text = cond_id
            CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.snomed_codes, '[]'::jsonb)) AS code_elem

            UNION

            SELECT
                c.id AS condition_id,
                code_elem->>'code' AS code
            FROM conds
            JOIN conditions c
                ON c.id::text = cond_id
            CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.icd10_codes, '[]'::jsonb)) AS code_elem

            UNION

            SELECT
                c.id AS condition_id,
                code_elem->>'code' AS code
            FROM conds
            JOIN conditions c
                ON c.id::text = cond_id
            CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.rxnorm_codes, '[]'::jsonb)) AS code_elem
        )
        SELECT
            c.id AS condition_id,
            c.display_name,
            COUNT(DISTINCT code) AS total_codes
        FROM conditions c
        JOIN codes cd ON c.id = cd.condition_id
        GROUP BY c.id, c.display_name
        ORDER BY c.display_name;
    """

    params = (config_id,)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbTotalConditionCodeCount)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchall()

    return row


async def add_custom_code_to_configuration_db(
    config: DbConfiguration,
    custom_code: DbConfigurationCustomCode,
    user_id: UUID,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Given a config, adds a user-defined custom code to the configuration.
    """

    query = """
            UPDATE configurations
            SET custom_codes = %s::jsonb
            WHERE id = %s
            RETURNING
                id,
                name,
                status,
                jurisdiction_id,
                condition_id,
                included_conditions,
                custom_codes,
                local_codes,
                section_processing,
                version,
                last_activated_at,
                last_activated_by,
                created_by,
                condition_canonical_url,
                s3_urls;
            """

    custom_codes = config.custom_codes

    exists = any(
        (c.code == custom_code.code and c.system == custom_code.system)
        for c in custom_codes
    )

    if not exists:
        custom_codes.append(custom_code)

    json = [
        {"code": cc.code, "system": cc.system, "name": cc.name} for cc in custom_codes
    ]

    params = (Jsonb(json), config.id)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

            if not row:
                return None

            updated_config = DbConfiguration.from_db_row(row)

            await insert_event_db(
                event=EventInput(
                    jurisdiction_id=updated_config.jurisdiction_id,
                    user_id=user_id,
                    configuration_id=updated_config.id,
                    event_type="add_code",
                    action_text=f"Added custom code '{custom_code.code}'",
                ),
                cursor=cur,
            )

            return updated_config

async def add_bulk_custom_codes_to_configuration_db(
    config: DbConfiguration,
    custom_codes: list[DbConfigurationCustomCode],
    user_id: UUID,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Adds multiple custom codes to a configuration in a single update.
    """

    query = """
        UPDATE configurations
        SET custom_codes = %s::jsonb
        WHERE id = %s
        RETURNING
            id,
            name,
            status,
            jurisdiction_id,
            condition_id,
            included_conditions,
            custom_codes,
            local_codes,
            section_processing,
            version,
            last_activated_at,
            last_activated_by,
            created_by,
            condition_canonical_url,
            s3_urls;
    """

    existing_codes = config.custom_codes or []

    # Build a set of (code, system) for fast lookup
    existing_keys = {(c.code, c.system) for c in existing_codes}

    new_codes_added = []

    for code in custom_codes:
        key = (code.code, code.system)
        if key not in existing_keys:
            existing_codes.append(code)
            existing_keys.add(key)
            new_codes_added.append(code)

    json_payload = [
        {"code": cc.code, "system": cc.system, "name": cc.name} for cc in existing_codes
    ]

    params = (Jsonb(json_payload), config.id)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

            if not row:
                return None

            updated_config = DbConfiguration.from_db_row(row)

            # Optional: single event instead of per-row
            if new_codes_added:
                await insert_event_db(
                    event=EventInput(
                        jurisdiction_id=updated_config.jurisdiction_id,
                        user_id=user_id,
                        configuration_id=updated_config.id,
                        event_type="bulk_add_custom_code",
                        action_text=f"Added {len(new_codes_added)} custom codes",
                    ),
                    cursor=cur,
                )

            return updated_config

async def delete_custom_code_from_configuration_db(
    config: DbConfiguration,
    system: str,
    code: str,
    user_id: UUID,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Given a config, system, and custom code, deletes the custom code from the configuration.
    """

    query = """
            UPDATE configurations
            SET custom_codes = %s::jsonb
            WHERE id = %s
            RETURNING
                id,
                name,
                status,
                jurisdiction_id,
                condition_id,
                included_conditions,
                custom_codes,
                local_codes,
                section_processing,
                version,
                last_activated_at,
                last_activated_by,
                created_by,
                condition_canonical_url,
                s3_urls;
            """

    updated_custom_codes = [
        {"code": cc.code, "system": cc.system, "name": cc.name}
        for cc in config.custom_codes
        if not (cc.system == system and cc.code == code)
    ]

    params = (Jsonb(updated_custom_codes), config.id)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

            if not row:
                return None

            updated_config = DbConfiguration.from_db_row(row)

            await insert_event_db(
                event=EventInput(
                    jurisdiction_id=updated_config.jurisdiction_id,
                    user_id=user_id,
                    configuration_id=updated_config.id,
                    event_type="delete_code",
                    action_text=f"Removed custom code '{code}'",
                ),
                cursor=cur,
            )

            return updated_config


async def edit_custom_code_from_configuration_db(
    config: DbConfiguration,
    updated_custom_codes: list[DbConfigurationCustomCode],
    user_id: UUID,
    prev_code: str,
    prev_system: str,
    prev_name: str,
    new_code: str | None,
    new_system: str | None,
    new_name: str | None,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Given a config and a list of custom codes, updates the configuration's custom codes using the provided list.
    """

    query = """
            UPDATE configurations
            SET custom_codes = %s::jsonb
            WHERE id = %s
            RETURNING
                id,
                name,
                status,
                jurisdiction_id,
                condition_id,
                included_conditions,
                custom_codes,
                local_codes,
                section_processing,
                version,
                last_activated_at,
                last_activated_by,
                created_by,
                condition_canonical_url,
                s3_urls;
            """

    json_codes = [
        {"code": cc.code, "system": cc.system, "name": cc.name}
        for cc in updated_custom_codes
    ]

    params = (Jsonb(json_codes), config.id)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

            if not row:
                return None

            updated_config = DbConfiguration.from_db_row(row)

            # Collect all event messages
            events_to_insert = []

            # 1. Code changed
            if new_code is not None and new_code != prev_code:
                events_to_insert.append(
                    EventInput(
                        jurisdiction_id=updated_config.jurisdiction_id,
                        user_id=user_id,
                        configuration_id=updated_config.id,
                        event_type="edit_code",
                        action_text=f"Updated custom code from '{prev_code}' to '{new_code}'",
                    )
                )

            # 2. Name changed
            if new_name is not None and new_name != prev_name:
                events_to_insert.append(
                    EventInput(
                        jurisdiction_id=updated_config.jurisdiction_id,
                        user_id=user_id,
                        configuration_id=updated_config.id,
                        event_type="edit_code",
                        action_text=f"Updated name for custom code '{prev_code}' from '{prev_name}' to '{new_name}'",
                    )
                )

            # 3. System changed
            if new_system is not None and new_system != prev_system:
                events_to_insert.append(
                    EventInput(
                        jurisdiction_id=updated_config.jurisdiction_id,
                        user_id=user_id,
                        configuration_id=updated_config.id,
                        event_type="edit_code",
                        action_text=f"Updated system for custom code '{prev_code}' from '{prev_system}' to '{new_system}'",
                    )
                )

            # Insert all generated events
            for event in events_to_insert:
                await insert_event_db(event=event, cursor=cur)

            return updated_config


@dataclass(frozen=True)
class SectionUpdate:
    """
    Represents a section processing update for a configuration.
    """

    code: str
    action: str


class SectionProcessingDict(TypedDict):
    """Typed dict for section processing entries stored in configurations.

    Fields:
        name: human-readable section name
        code: LOINC code for the section
        action: processing action ('retain'|'refine'|'remove')
        versions: list of spec version strings this section appears in
    """

    name: str
    code: str
    action: str
    versions: list[str]


async def update_section_processing_db(
    config: DbConfiguration,
    section_updates: list[SectionUpdate],
    user_id: UUID,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Update section processing instructions for a configuration.

    Args:
        config: The configuration to update
        section_updates: List of section updates with code and action
        user_id: ID of the user
        db: Database connection

    Returns:
        Updated DbConfiguration or None if the update fails
    """
    # Map internal action → display label
    ACTION_LABELS = {
        "refine": "Include & refine",
        "retain": "Include entire",
        "remove": "Remove",
    }

    # Validate input actions
    valid_actions = {"retain", "refine", "remove"}
    for su in section_updates:
        if su.action not in valid_actions:
            raise ValueError(f"Invalid action '{su.action}' for section update.")

    # Build a mapping from code -> action for quick lookup
    update_map = {su.code: su.action for su in section_updates}

    # Start from the existing section_processing entries on the config
    existing_sections: list[SectionProcessingDict] = [
        {
            "name": sp.name,
            "code": sp.code,
            "action": sp.action,
            "versions": sp.versions,
        }
        for sp in config.section_processing
    ]

    updated_sections: list[SectionProcessingDict] = []
    section_events = []

    for sec in existing_sections:
        code = sec["code"]
        old_action = sec["action"]

        if code in update_map:
            new_action = update_map[code]

            # If action changed, record event
            if new_action != old_action:
                old_label = ACTION_LABELS.get(old_action, old_action)
                new_label = ACTION_LABELS.get(new_action, new_action)

                section_events.append(
                    EventInput(
                        jurisdiction_id=config.jurisdiction_id,
                        user_id=user_id,
                        configuration_id=config.id,
                        event_type="section_update",
                        action_text=(
                            f"Updated section '{sec['name']}' from '{old_label}' to '{new_label}'"
                        ),
                    )
                )

            # Append updated section
            updated_sections.append(
                {
                    "name": sec["name"],
                    "code": sec["code"],
                    "action": new_action,
                    "versions": sec["versions"] if "versions" in sec else [],
                }
            )
        else:
            updated_sections.append(
                {
                    "name": sec["name"],
                    "code": sec["code"],
                    "action": sec["action"],
                    "versions": sec["versions"] if "versions" in sec else [],
                }
            )

    # If any update codes were not present in the existing sections, ignore them.
    # Persist the updated list back to the database
    query = """
            UPDATE configurations
            SET section_processing = %s::jsonb
            WHERE id = %s
            RETURNING
                id,
                name,
                status,
                jurisdiction_id,
                condition_id,
                included_conditions,
                custom_codes,
                local_codes,
                section_processing,
                version,
                last_activated_at,
                last_activated_by,
                created_by,
                condition_canonical_url,
                s3_urls;
            """

    params = (Jsonb(updated_sections), config.id)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

            if not row:
                return None

            updated_config = DbConfiguration.from_db_row(row)

            # Insert all generated section events
            for event in section_events:
                await insert_event_db(event=event, cursor=cur)

            return updated_config


async def get_configurations_by_condition_ids_and_jurisdiction_db(
    db: AsyncDatabaseConnection,
    condition_ids: list[UUID],
    jurisdiction_id: str,
) -> dict[UUID, DbConfiguration | None]:
    """
    For each condition_id, fetch the configuration for the given jurisdiction.

    Returns a dict: {condition_id: DbConfiguration or None}
    """

    if not condition_ids:
        return {}

    query = """
        SELECT
            id,
            name,
            status,
            jurisdiction_id,
            condition_id,
            included_conditions,
            custom_codes,
            local_codes,
            section_processing,
            version,
			last_activated_at,
			last_activated_by,
            created_by,
            condition_canonical_url,
            s3_urls
        FROM configurations
        WHERE jurisdiction_id = %s
          AND condition_id = ANY(%s::uuid[])
    """

    params = (jurisdiction_id, condition_ids)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    # build mapping from condition_id to config
    configs_by_condition_id = {
        row["condition_id"]: DbConfiguration.from_db_row(row) for row in rows
    }

    # ensure every input condition_id is present (with None if absent)
    result: dict[UUID, DbConfiguration | None] = {}
    for cond_id in condition_ids:
        result[cond_id] = configs_by_condition_id.get(cond_id)

    return result


@dataclass(frozen=True)
class GetConfigurationResponseVersion:
    """
    Model representing a version of a configuration.
    """

    id: UUID
    version: int
    condition_canonical_url: str
    status: DbConfigurationStatus
    created_at: datetime
    created_by: str
    last_activated_at: datetime | None
    last_activated_by: str | None


async def get_latest_config_db(
    jurisdiction_id: str, condition_canonical_url: str, db: AsyncDatabaseConnection
) -> DbConfiguration | None:
    """
    Given a jurisdiction ID and condition canonical URL, find the latest configuration version.
    """
    query = """
        SELECT
            id,
            name,
			status,
            jurisdiction_id,
            condition_id,
            included_conditions,
            custom_codes,
            local_codes,
            section_processing,
            version,
			last_activated_at,
			last_activated_by,
            created_by,
            condition_canonical_url,
            s3_urls
        FROM configurations
        WHERE jurisdiction_id = %s
        AND condition_canonical_url = %s
		ORDER BY version DESC
		LIMIT 1
    """
    params = (jurisdiction_id, condition_canonical_url)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    configs = [DbConfiguration.from_db_row(row) for row in rows]

    if len(configs) < 1:
        return None

    return configs[0]


async def get_active_config_db(
    jurisdiction_id: str, condition_canonical_url: str, db: AsyncDatabaseConnection
) -> DbConfiguration | None:
    """
    Given a jurisdiction ID and condition canonical URL, find the active configuration version, if any.
    """
    query = """
        SELECT
            id,
            name,
			status,
            jurisdiction_id,
            condition_id,
            included_conditions,
            custom_codes,
            local_codes,
            section_processing,
            version,
			last_activated_at,
			last_activated_by,
            created_by,
            condition_canonical_url,
            s3_urls
        FROM configurations
        WHERE jurisdiction_id = %s
        AND condition_canonical_url = %s
        AND status = 'active';
    """
    params = (jurisdiction_id, condition_canonical_url)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if not row:
        return None

    return DbConfiguration.from_db_row(row)


async def get_configuration_versions_db(
    jurisdiction_id: str, condition_canonical_url: str, db: AsyncDatabaseConnection
) -> list[GetConfigurationResponseVersion]:
    """
    Given a jurisdiction ID and condition canonical URL, finds all related configuration versions.
    """
    query = """
        SELECT
            c.id,
            c.version,
            c.status,
            c.condition_canonical_url,
            c.last_activated_at,
            la.username AS last_activated_by,
            c.created_at,
            u.username AS created_by
        FROM configurations c
        JOIN users u
            ON u.id = c.created_by
        LEFT JOIN users la
            ON la.id = c.last_activated_by
        WHERE c.jurisdiction_id = %s
        AND c.condition_canonical_url = %s
        ORDER BY c.version DESC;
    """

    params = (jurisdiction_id, condition_canonical_url)
    async with db.get_connection() as conn:
        async with conn.cursor(
            row_factory=class_row(GetConfigurationResponseVersion)
        ) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return rows
