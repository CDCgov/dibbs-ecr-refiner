from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from psycopg.rows import class_row, dict_row
from psycopg.types.json import Jsonb

from app.db.events.db import insert_event_db
from app.db.events.model import EventInput

from ...services.file_io import read_json_asset
from ..conditions.model import DbCondition
from ..pool import AsyncDatabaseConnection
from .model import (
    DbConfiguration,
    DbConfigurationCustomCode,
)

EMPTY_JSONB = Jsonb([])
REFINER_DETAILS = read_json_asset("refiner_details.json")


async def insert_configuration_db(
    condition: DbCondition,
    user_id: UUID,
    jurisdiction_id: str,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Inserts a configuration into the database.

    The `name` field is always set to the display_name of the associated condition at creation time,
    for easier display and searching. The authoritative clinical context is still given by `condition_id`.
    """

    query = """
    INSERT INTO configurations (
        jurisdiction_id,
        condition_id,
        name,
        included_conditions,
        custom_codes,
        local_codes,
        section_processing
    )
    VALUES (
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
        condition_canonical_url
    """

    section_details = REFINER_DETAILS["sections"]

    section_processing_defaults = [
        {
            "name": details["display_name"],
            "code": code,
            "action": "refine",
        }
        for code, details in section_details.items()
    ]

    params: tuple[str, UUID, str, Jsonb, Jsonb, Jsonb, Jsonb] = (
        jurisdiction_id,
        # always link a configuration to a primary condition
        condition.id,
        # always set name to condition display name
        condition.display_name,
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
            condition_canonical_url
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
            condition_canonical_url
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
    condition_id: UUID, jurisdiction_id: str, db: AsyncDatabaseConnection
) -> bool:
    """
    Query the database to check if a configuration can be created. If a config for a condition already exists, returns False.
    """

    query = """
        SELECT id
        from configurations
        WHERE condition_id = %s
        AND jurisdiction_id = %s
        """

    params = (
        condition_id,
        jurisdiction_id,
    )

    async with db.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchall()

    if not row:
        return True

    return False


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
                condition_canonical_url;
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
            condition_canonical_url;
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
                condition_canonical_url;
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
                condition_canonical_url;
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
                condition_canonical_url;
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


async def update_section_processing_db(
    config: DbConfiguration,
    section_updates: list[SectionUpdate],
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Update section processing instructions for a configuration.

    Args:
        config: The configuration to update
        section_updates: List of section updates with code and action
        db: Database connection

    Returns:
        Updated DbConfiguration or None if the update fails
    """

    # Validate input actions
    valid_actions = {"retain", "refine", "remove"}
    for su in section_updates:
        if su.action not in valid_actions:
            raise ValueError(f"Invalid action '{su.action}' for section update.")

    # Build a mapping from code -> action for quick lookup
    update_map = {su.code: su.action for su in section_updates}

    # Start from the existing section_processing entries on the config
    existing_sections = [
        {"name": sp.name, "code": sp.code, "action": sp.action}
        for sp in config.section_processing
    ]

    # Apply updates in memory
    updated_sections = []
    for sec in existing_sections:
        if sec["code"] in update_map:
            updated_sections.append(
                {
                    "name": sec["name"],
                    "code": sec["code"],
                    "action": update_map[sec["code"]],
                }
            )
        else:
            updated_sections.append(sec)

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
                condition_canonical_url;
            """

    params = (Jsonb(updated_sections), config.id)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if not row:
        return None

    return DbConfiguration.from_db_row(row)


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
            condition_canonical_url
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
class DbConfigurationLock:
    """Active lock for config. Holds config id, user id, username, expiry."""

    configuration_id: UUID
    user_id: UUID
    username: str
    expires_at: datetime


async def get_configuration_lock_db(
    config_id: UUID, db: AsyncDatabaseConnection
) -> DbConfigurationLock | None:
    """Return active lock for a configuration or None. Expired lock rows are cleaned."""
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            # delete expired lock for this configuration
            await cur.execute(
                "DELETE FROM configuration_locks WHERE configuration_id = %s AND expires_at < NOW()",
                (config_id,),
            )
            # select active lock if exists
            await cur.execute(
                """
                SELECT cl.configuration_id, cl.user_id, u.username, cl.expires_at
                FROM configuration_locks cl
                JOIN users u ON cl.user_id = u.id
                WHERE cl.configuration_id = %s
                """,
                (config_id,),
            )
            row = await cur.fetchone()
            if not row:
                return None
            return DbConfigurationLock(
                configuration_id=row["configuration_id"],
                user_id=row["user_id"],
                username=row["username"],
                expires_at=row["expires_at"],
            )


async def acquire_or_refresh_lock_db(
    config_id: UUID,
    user_id: UUID,
    ttl_minutes: int,
    db: AsyncDatabaseConnection,
) -> tuple[DbConfigurationLock | None, bool]:
    """Attempt to acquire or refresh the configuration lock.

    Returns (lock, acquired_new). If lock is None, another user holds it.
    acquired_new True means the lock was newly acquired. False means it was refreshed.
    """
    expiry = datetime.now(UTC) + timedelta(minutes=ttl_minutes)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            # pre-check existing lock holder
            await cur.execute(
                "SELECT user_id FROM configuration_locks WHERE configuration_id = %s AND expires_at > NOW()",
                (config_id,),
            )
            existing = await cur.fetchone()
            # attempt insert or conditional update
            await cur.execute(
                """
                INSERT INTO configuration_locks (configuration_id, user_id, expires_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (configuration_id) DO UPDATE
                SET expires_at = EXCLUDED.expires_at, updated_at = NOW()
                WHERE configuration_locks.user_id = EXCLUDED.user_id
                RETURNING configuration_id, user_id, expires_at
                """,
                (config_id, user_id, expiry),
            )
            row = await cur.fetchone()
            if not row:
                # conflict held by different user; fetch holder for response
                await cur.execute(
                    """
                    SELECT cl.configuration_id, cl.user_id, u.username, cl.expires_at
                    FROM configuration_locks cl
                    JOIN users u ON cl.user_id = u.id
                    WHERE cl.configuration_id = %s AND cl.expires_at > NOW()
                    """,
                    (config_id,),
                )
                holder = await cur.fetchone()
                if not holder:
                    return None, False
                return None, False
            # build lock object
            await cur.execute(
                "SELECT username FROM users WHERE id = %s",
                (row["user_id"],),
            )
            user_row = await cur.fetchone()
            lock = DbConfigurationLock(
                configuration_id=row["configuration_id"],
                user_id=row["user_id"],
                username=user_row["username"],
                expires_at=row["expires_at"],
            )
            acquired_new = existing is None or existing["user_id"] != user_id
            # Event emission for new lock acquisition is handled in the API layer where jurisdiction_id context exists.
            return lock, acquired_new


async def release_lock_db(
    config_id: UUID, user_id: UUID, db: AsyncDatabaseConnection
) -> bool:
    """Release lock if held by user. Returns True if released."""
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "DELETE FROM configuration_locks WHERE configuration_id = %s AND user_id = %s RETURNING configuration_id",
                (config_id, user_id),
            )
            row = await cur.fetchone()
            if not row:
                return False
            # event requires jurisdiction; fetch configuration for audit context
            await cur.execute(
                "SELECT jurisdiction_id FROM configurations WHERE id = %s",
                (config_id,),
            )
            cfg = await cur.fetchone()
            if cfg:
                await insert_event_db(
                    event=EventInput(
                        jurisdiction_id=cfg["jurisdiction_id"],
                        user_id=user_id,
                        configuration_id=config_id,
                        event_type="release_lock",
                        action_text="Released edit lock",
                    ),
                    cursor=cur,
                )
            return True
