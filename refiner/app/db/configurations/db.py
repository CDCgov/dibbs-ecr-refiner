from collections import defaultdict
from typing import Any
from uuid import UUID

from psycopg import AsyncCursor
from psycopg.rows import DictRow, class_row, dict_row
from psycopg.types.json import Jsonb

from app.db.events.db import insert_event_db
from app.db.events.model import EventInput
from app.services.configurations import (
    clone_section_processing_instructions,
    get_default_sections,
)

from ..conditions.model import DbCondition
from ..pool import AsyncDatabaseConnection
from .model import (
    BulkAddCustomCodesResult,
    DbConfiguration,
    DbConfigurationCustomCode,
    DbConfigurationSection,
    DbConfigurationSectionProcessing,
    DbSectionAction,
    DbTotalConditionCodeCount,
    GetConfigurationResponseVersion,
)

EMPTY_JSONB = Jsonb([])

type CursorType = dict[str, Any]


async def _insert_configuration_sections_db(
    configuration_id: UUID,
    sections_to_insert: list[DbConfigurationSectionProcessing],
    cursor: AsyncCursor[CursorType],
) -> None:
    """
    Inserts sections into configurations_sections table.
    """
    query = """
        INSERT INTO configurations_sections (
            configuration_id,
            code,
            name,
            action,
            include,
            narrative,
            versions
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )

    """

    params = [
        (
            configuration_id,
            s.code,
            s.name,
            s.action,
            s.include,
            s.narrative,
            s.versions,
        )
        for s in sections_to_insert
    ]

    await cursor.executemany(query, params)


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
        custom_codes
    )
    VALUES (
        %s,
        %s,
        %s,
        %s,
        %s::jsonb,
        %s::jsonb
    )
    RETURNING
        id
    """

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
        )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if not row:
                return None

            config_id = row["id"]

            # Insert either cloned sections or brand new sections as part of the same transaction
            if config_to_clone:
                await _insert_configuration_sections_db(
                    configuration_id=config_id,
                    sections_to_insert=clone_section_processing_instructions(
                        clone_from=config_to_clone.section_processing,
                        clone_to=get_default_sections(),
                    ),
                    cursor=cur,
                )
            else:
                await _insert_configuration_sections_db(
                    configuration_id=config_id,
                    sections_to_insert=get_default_sections(),
                    cursor=cur,
                )

            await insert_event_db(
                event=EventInput(
                    jurisdiction_id=jurisdiction_id,
                    user_id=user_id,
                    configuration_id=config_id,
                    event_type="create_configuration",
                    action_text="Created configuration",
                ),
                cursor=cur,
            )
    return await get_configuration_by_id_db(
        id=row["id"], jurisdiction_id=jurisdiction_id, db=db
    )


async def _get_configuration_sections_db(
    configuration_ids: list[UUID], db: AsyncDatabaseConnection
) -> list[DbConfigurationSection]:
    """
    Fetch all sections for the given configurations.

    Args:
        configuration_ids (UUID): List of configuration IDs
        db (AsyncDatabaseConnection): The database connection

    Returns:
        list(DbConfigurationSection): List of sections
    """

    query = """
    SELECT
        id,
        configuration_id,
        name,
        code,
        action,
        include,
        narrative,
        versions,
        created_at,
        updated_at
    FROM configurations_sections
    WHERE configuration_id = ANY(%s)
    ORDER BY name;
    """
    params = (configuration_ids,)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbConfigurationSection)) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return rows


async def _map_sections_to_config_db(
    raw_configurations: list[DictRow], db: AsyncDatabaseConnection
) -> list[DictRow]:
    """
    Given a list of unprocessed configurations, adds a `section_processing` key with a list of section data.

    Args:
        raw_configurations (list[DictRow]): List of unprocessed configuration data coming from the database
        db (AsyncDatabaseConnection): The database connection.

    Returns:
        list[DictRow]: List of unprocessed configuration data that includes `section_processing`
    """
    updated_configs_list = raw_configurations.copy()
    configuration_ids: list[UUID] = [row["id"] for row in updated_configs_list]
    sections = await _get_configuration_sections_db(
        configuration_ids=configuration_ids, db=db
    )
    sections_by_config: dict[str, list[dict]] = defaultdict(list)

    for section in sections:
        sections_by_config[str(section.configuration_id)].append(
            section.to_processing_dict()
        )
    for config in updated_configs_list:
        config["section_processing"] = sections_by_config.get(str(config["id"]), [])
    return updated_configs_list


async def get_configurations_db(
    jurisdiction_id: str, db: AsyncDatabaseConnection, status: str | None = None
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
            version,
            last_activated_at,
            last_activated_by,
            created_by,
            condition_canonical_url,
            s3_urls
        FROM configurations
        WHERE jurisdiction_id = %s
    """

    params: tuple[str, ...] = (jurisdiction_id,)

    if status is not None:
        query += " AND status = %s"
        params += (status,)

    query += " ORDER BY name ASC;"

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            config_rows = await cur.fetchall()

    if not config_rows:
        return []

    updated_config_rows = await _map_sections_to_config_db(
        raw_configurations=config_rows, db=db
    )

    return [DbConfiguration.from_db_row(row) for row in updated_config_rows]


async def get_configuration_by_id_db(
    id: UUID, jurisdiction_id: str, db: AsyncDatabaseConnection
) -> DbConfiguration | None:
    """
    Fetch a configuration by the given ID.
    """
    # TODO: Leaving `section_processing` as JSONB on read for compatability.
    # We may want to revisit this at some point.
    query = """
    SELECT
        c.id,
        c.name,
        c.status,
        c.jurisdiction_id,
        c.condition_id,
        c.included_conditions,
        c.custom_codes,

        -- build section_processing from configurations_sections
        COALESCE(secs.section_processing, '[]'::jsonb) AS section_processing,

        c.version,
        c.last_activated_at,
        c.last_activated_by,
        c.created_by,
        c.condition_canonical_url,
        c.s3_urls
    FROM configurations c
    LEFT JOIN LATERAL (
        SELECT jsonb_agg(
                   jsonb_build_object(
                       'code', s.code,
                       'name', s.name,
                       'action', s.action::text,
                       'include', s.include,
                       'versions', to_jsonb(s.versions),
                       'narrative', s.narrative
                   )
                   ORDER BY s.code
               ) AS section_processing
        FROM configurations_sections s
        WHERE s.configuration_id = c.id
    ) secs ON TRUE
    WHERE c.id = %s
    AND c.jurisdiction_id = %s;
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
                id;
            """

    new_condition = Jsonb([str(condition.id)])
    params = (new_condition, config.id)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

            if not row:
                return None

            await insert_event_db(
                event=EventInput(
                    jurisdiction_id=config.jurisdiction_id,
                    user_id=user_id,
                    configuration_id=config.id,
                    event_type="add_code",
                    action_text=f"Associated '{condition.display_name}' code set",
                ),
                cursor=cur,
            )

    return await get_configuration_by_id_db(
        id=config.id, jurisdiction_id=config.jurisdiction_id, db=db
    )


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
            id;
    """

    params = (str(condition.id), config.id)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

            if not row:
                return None

            await insert_event_db(
                event=EventInput(
                    jurisdiction_id=config.jurisdiction_id,
                    user_id=user_id,
                    configuration_id=config.id,
                    event_type="delete_code",
                    action_text=f"Removed '{condition.display_name}' code set",
                ),
                cursor=cur,
            )

    return await get_configuration_by_id_db(
        id=config.id, jurisdiction_id=config.jurisdiction_id, db=db
    )


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
                id;
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

            await insert_event_db(
                event=EventInput(
                    jurisdiction_id=config.jurisdiction_id,
                    user_id=user_id,
                    configuration_id=config.id,
                    event_type="add_code",
                    action_text=f"Added custom code '{custom_code.code}'",
                ),
                cursor=cur,
            )

    return await get_configuration_by_id_db(
        id=config.id, jurisdiction_id=config.jurisdiction_id, db=db
    )


async def add_bulk_custom_codes_to_configuration_db(
    config: DbConfiguration,
    custom_codes: list[DbConfigurationCustomCode],
    user_id: UUID,
    db: AsyncDatabaseConnection,
) -> BulkAddCustomCodesResult | None:
    """
    Adds multiple custom codes to a configuration in a single update.

    Returns:
        BulkAddCustomCodesResult | None
    """

    query = """
        UPDATE configurations
        SET custom_codes = %s::jsonb
        WHERE id = %s
        RETURNING
            id;
    """

    existing_codes = config.custom_codes or []

    # Build a set of (code, system) for fast lookup
    existing_keys = {(c.code, c.system) for c in existing_codes}

    new_codes_added: list[DbConfigurationCustomCode] = []

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

            # Insert a single audit event if codes were added
            if new_codes_added:
                await insert_event_db(
                    event=EventInput(
                        jurisdiction_id=config.jurisdiction_id,
                        user_id=user_id,
                        configuration_id=config.id,
                        event_type="bulk_add_custom_code",
                        action_text=f"Added {len(new_codes_added)} custom codes",
                    ),
                    cursor=cur,
                )

    updated_config = await get_configuration_by_id_db(
        id=config.id, jurisdiction_id=config.jurisdiction_id, db=db
    )

    if not updated_config:
        return None

    return BulkAddCustomCodesResult(
        config=updated_config,
        added_count=len(new_codes_added),
    )


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
                id;
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

            await insert_event_db(
                event=EventInput(
                    jurisdiction_id=config.jurisdiction_id,
                    user_id=user_id,
                    configuration_id=config.id,
                    event_type="delete_code",
                    action_text=f"Removed custom code '{code}'",
                ),
                cursor=cur,
            )

    return await get_configuration_by_id_db(
        id=config.id, jurisdiction_id=config.jurisdiction_id, db=db
    )


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
                id;
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

            # Collect all event messages
            events_to_insert = []

            # 1. Code changed
            if new_code is not None and new_code != prev_code:
                events_to_insert.append(
                    EventInput(
                        jurisdiction_id=config.jurisdiction_id,
                        user_id=user_id,
                        configuration_id=config.id,
                        event_type="edit_code",
                        action_text=f"Updated custom code from '{prev_code}' to '{new_code}'",
                    )
                )

            # 2. Name changed
            if new_name is not None and new_name != prev_name:
                events_to_insert.append(
                    EventInput(
                        jurisdiction_id=config.jurisdiction_id,
                        user_id=user_id,
                        configuration_id=config.id,
                        event_type="edit_code",
                        action_text=f"Updated name for custom code '{prev_code}' from '{prev_name}' to '{new_name}'",
                    )
                )

            # 3. System changed
            if new_system is not None and new_system != prev_system:
                events_to_insert.append(
                    EventInput(
                        jurisdiction_id=config.jurisdiction_id,
                        user_id=user_id,
                        configuration_id=config.id,
                        event_type="edit_code",
                        action_text=f"Updated system for custom code '{prev_code}' from '{prev_system}' to '{new_system}'",
                    )
                )

            # Insert all generated events
            for event in events_to_insert:
                await insert_event_db(event=event, cursor=cur)

    return await get_configuration_by_id_db(
        id=config.id, jurisdiction_id=config.jurisdiction_id, db=db
    )


async def _get_configuration_section_by_code(
    configuration_id: UUID, code: str, db: AsyncDatabaseConnection
) -> DbConfigurationSection | None:
    """
    Get a configuration's section by its unique code.
    """
    query = """
        SELECT
            id,
            configuration_id,
            name,
            code,
            action,
            include,
            narrative,
            versions,
            created_at,
            updated_at
        FROM configurations_sections
        WHERE configuration_id = %s
        AND code = %s
    """
    params = (configuration_id, code)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbConfigurationSection)) as cur:
            await cur.execute(query, params)
            return await cur.fetchone()


async def update_configuration_section_db(
    config: DbConfiguration,
    section_update: DbConfigurationSectionProcessing,
    user_id: UUID,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Update section processing instructions for a configuration.

    Args:
        config: The configuration to update
        section_update: Section to update
        user_id: ID of the user
        db: Database connection

    Returns:
        Updated DbConfiguration or None if the update fails
    """
    # Map internal action → display label
    ACTION_LABELS = {
        "refine": "Refine & optimize",
        "retain": "Preserve & retain all data",
    }

    # Validate input actions
    valid_actions: set[DbSectionAction] = {"retain", "refine"}
    if section_update.action not in valid_actions:
        raise ValueError(
            f"Invalid action '{section_update.action}' for section update."
        )

    prev_section = await _get_configuration_section_by_code(
        configuration_id=config.id, code=section_update.code, db=db
    )

    if not prev_section:
        raise ValueError(
            f"No existing section with code {section_update.code} to update"
        )

    action_changed = prev_section.action != section_update.action

    section_events: list[EventInput] = []
    if action_changed:
        section_events.append(
            EventInput(
                jurisdiction_id=config.jurisdiction_id,
                user_id=user_id,
                configuration_id=config.id,
                event_type="section_update",
                action_text=(
                    f"Updated section '{prev_section.name}' from '{ACTION_LABELS.get(prev_section.action, prev_section.action)}' to '{ACTION_LABELS.get(section_update.action, section_update.action)}'"
                ),
            )
        )

    query = """
            UPDATE configurations_sections
            SET
                action = %s,
                include = %s,
                narrative = %s,
                updated_at = NOW()
            WHERE configuration_id = %s
            AND code = %s
            RETURNING id;
            """

    params = (
        section_update.action,
        section_update.include,
        section_update.narrative,
        config.id,
        section_update.code,
    )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

            if not row:
                return None

            # Insert all generated section events
            for event in section_events:
                await insert_event_db(event=event, cursor=cur)

    return await get_configuration_by_id_db(
        id=config.id, jurisdiction_id=config.jurisdiction_id, db=db
    )


async def get_latest_config_db(
    jurisdiction_id: str, condition_canonical_url: str, db: AsyncDatabaseConnection
) -> DbConfiguration | None:
    """
    Given a jurisdiction ID and condition canonical URL, find the latest configuration version.
    """
    query = """
        SELECT
            id
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

    if len(rows) < 1:
        return None

    config_id = rows[0]["id"]

    return await get_configuration_by_id_db(
        id=config_id, jurisdiction_id=jurisdiction_id, db=db
    )


async def get_active_config_db(
    jurisdiction_id: str, condition_canonical_url: str, db: AsyncDatabaseConnection
) -> DbConfiguration | None:
    """
    Given a jurisdiction ID and condition canonical URL, find the active configuration version, if any.
    """
    query = """
        SELECT
            id
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

    return await get_configuration_by_id_db(
        id=row["id"], jurisdiction_id=jurisdiction_id, db=db
    )


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
