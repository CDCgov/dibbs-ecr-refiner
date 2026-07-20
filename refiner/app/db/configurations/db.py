from typing import Any, Literal
from uuid import UUID

from psycopg import AsyncCursor
from psycopg.rows import class_row, dict_row
from psycopg.types.json import Jsonb

from app.api.v1.configurations.model import (
    AddCustomCodeInput,
    AddSectionInput,
    DeleteSectionInput,
)
from app.db.code_systems.db import DbCodeSystem
from app.db.conditions.db import (
    get_latest_tes_condition_db,
    get_latest_tes_condition_ids_db,
)
from app.db.custom_codes.model import DbCustomCode
from app.db.events.db import insert_custom_code_upload_events_db, insert_event_db
from app.db.events.model import EventInput
from app.services.configurations import (
    clone_section_processing_instructions,
    get_default_sections,
)
from app.services.logger import get_logger

from ..conditions.model import DbCondition
from ..pool import AsyncDatabaseConnection
from .model import (
    BulkAddCustomCodesResult,
    DbConfiguration,
    DbConfigurationCustomCode,
    DbConfigurationSection,
    DbConfigurationSectionProcessing,
    DbConfigurationSummary,
    DbSectionAction,
    DbTotalConditionCodeCount,
    GetConfigurationResponseVersion,
)

EMPTY_JSONB = Jsonb([])

type CursorType = dict[str, Any]


async def insert_custom_section_db(
    config: DbConfiguration,
    user_id: UUID,
    custom_section_input: AddSectionInput,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Inserts a custom section into the configurations_sections table.

    Args:
        config (DbConfiguration): Configuration associated with the section
        user_id (UUID): ID of the user creating the custom section
        custom_section_input (CustomSectionInput): Custom section properties to use for creation
        db (AsyncDatabaseConnection): The database connection

    Returns:
        DbConfiguration: Updated configuration
    """
    name, code = custom_section_input.name, custom_section_input.code

    query = """
        INSERT INTO configurations_sections (
            configuration_id,
            code,
            name,
            action,
            include,
            narrative,
            versions,
            section_type
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        RETURNING
            id;
        """

    versions: list[str] = []
    params = (
        config.id,
        code,
        name,
        "refine",
        True,
        "remove",
        versions,
        "custom",
    )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if not row:
                return None

            await insert_event_db(
                event=EventInput(
                    configuration_id=config.id,
                    jurisdiction_id=config.jurisdiction_id,
                    user_id=user_id,
                    event_type="create_custom_section",
                    action_text=f"Custom section '{name}' with code '{code}' created",
                ),
                cursor=cur,
            )

    return await get_configuration_by_id_db(
        id=config.id, jurisdiction_id=config.jurisdiction_id, db=db
    )


async def delete_custom_section_db(
    config: DbConfiguration,
    user_id: UUID,
    custom_section_input: DeleteSectionInput,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Deletes a custom section from the configurations_sections table.

    Args:
        config (DbConfiguration): Configuration associated with the section
        user_id (UUID): ID of the user deleting the custom section
        custom_section_input (DeleteCustomSectionInput): Custom section to delete
        db (AsyncDatabaseConnection): The database connection

    Returns:
        DbConfiguration: Updated configuration
    """

    query = """
        DELETE from configurations_sections
        WHERE configuration_id = %s
        AND code = %s
        AND section_type = 'custom'
        RETURNING code
    """
    params = (config.id, custom_section_input.code)

    section_name = next(
        (
            s.name
            for s in config.section_processing
            if s.code == custom_section_input.code
        ),
        None,
    )
    if not section_name:
        return None

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
                    event_type="delete_custom_section",
                    action_text=f'Deleted custom section "{section_name}" with code "{custom_section_input.code}"',
                ),
                cursor=cur,
            )

    return await get_configuration_by_id_db(
        id=config.id, jurisdiction_id=config.jurisdiction_id, db=db
    )


async def _insert_configuration_sections_db(
    configuration_id: UUID,
    sections_to_insert: list[DbConfigurationSectionProcessing],
    cursor: AsyncCursor[CursorType],
) -> None:
    """
    Inserts sections into the configurations_sections table.
    """
    query = """
        INSERT INTO configurations_sections (
            configuration_id,
            code,
            name,
            action,
            include,
            narrative,
            versions,
            section_type
        )
        VALUES (
            %s,
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
            s.section_type,
        )
        for s in sections_to_insert
    ]

    await cursor.executemany(query, params)


async def _get_next_configuration_version_db(
    canonical_url: str,
    jurisdiction_id: str,
    cursor: AsyncCursor[CursorType],
) -> int:
    """
    Given a condition canonical URL and jurisdiction ID, determines the next version a configuration should use.
    """
    await cursor.execute(
        """
        SELECT MAX(c.version) AS max_version
        FROM configurations c
        JOIN configurations_conditions cc ON cc.configuration_id = c.id AND cc.is_primary = true
        JOIN conditions cond ON cond.id = cc.condition_id
        WHERE cond.canonical_url = %s
          AND c.jurisdiction_id = %s
        """,
        (canonical_url, jurisdiction_id),
    )
    row = await cursor.fetchone()
    max_version = 0 if (not row or row["max_version"] is None) else row["max_version"]
    return max_version + 1


async def insert_configuration_db(
    condition: DbCondition,
    user_id: UUID,
    jurisdiction_id: str,
    db: AsyncDatabaseConnection,
    config_to_clone: DbConfiguration | None = None,
) -> DbConfiguration | None:
    """
    Inserts a configuration into the database. If a `config_to_clone` is passed in, it'll base the new config's values off of that config.

    - Determines the version number the new configuration should have
    - Determines default info (cloned or brand new)
    - Inserts a configuration record
    - Inserts section info
    - Inserts condition relation info
    """

    # always use the latest version of the given condition when creating a new config
    # this applies to both a "fresh" config and cloning from an old config
    latest_condition = await get_latest_tes_condition_db(condition=condition, db=db)

    query = """
    INSERT INTO configurations (
        jurisdiction_id,
        name,
        created_by,
        version
    )
    VALUES (
        %s,
        %s,
        %s,
        %s
    )
    RETURNING
        id
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            next_version = await _get_next_configuration_version_db(
                canonical_url=latest_condition.canonical_url,
                jurisdiction_id=jurisdiction_id,
                cursor=cur,
            )

            if config_to_clone:
                params = (
                    jurisdiction_id,
                    # always set name to condition display name
                    config_to_clone.name,
                    # cloned by this user
                    user_id,
                    # TODO: UPDATE CLONING FOR CUSTOM CODES
                    # custom_codes
                    # Jsonb(
                    #     [
                    #         {"name": c.name, "code": c.code, "system_key": c.system_key}
                    #         for c in config_to_clone.custom_codes
                    #     ]
                    # ),
                    next_version,
                )
            else:
                params = (
                    jurisdiction_id,
                    # always set name to condition display name
                    latest_condition.display_name,
                    # created by this user
                    user_id,
                    next_version,
                )

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
                        logger=get_logger(),
                    ),
                    cursor=cur,
                )

                # Clone custom codes
                if config_to_clone.custom_codes:
                    await cur.executemany(
                        """
                        INSERT INTO custom_codes (configuration_id, code, display, system_id)
                        VALUES (%s, %s, %s, %s)
                        """,
                        [
                            (config_id, cc.code, cc.name, cc.system_id)
                            for cc in config_to_clone.custom_codes
                        ],
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

            if config_to_clone:
                included_condition_ids = await get_latest_tes_condition_ids_db(
                    ids=config_to_clone.included_conditions, db=db
                )
                condition_ids_to_insert = included_condition_ids
                if latest_condition.id not in condition_ids_to_insert:
                    condition_ids_to_insert = [
                        latest_condition.id,
                        *condition_ids_to_insert,
                    ]
            else:
                condition_ids_to_insert = [latest_condition.id]

            await cur.executemany(
                """
                INSERT INTO configurations_conditions (configuration_id, condition_id, is_primary)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                [
                    (config_id, cond_id, cond_id == latest_condition.id)
                    for cond_id in condition_ids_to_insert
                ],
            )

    return await get_configuration_by_id_db(
        id=row["id"], jurisdiction_id=jurisdiction_id, db=db
    )


async def get_configurations_db(
    jurisdiction_id: str, db: AsyncDatabaseConnection, status: str | None = None
) -> list[DbConfiguration]:
    """
    Fetch all configurations from the DB for a given jurisdiction.
    """

    query = _get_configurations_core_query() + " WHERE c.jurisdiction_id = %s"
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

    return [DbConfiguration.from_db_row(row) for row in config_rows]


async def get_configurations_by_ids_db(
    ids: list[UUID], jurisdiction_id: str, db: AsyncDatabaseConnection
) -> list[DbConfiguration]:
    """
    Fetch configurations by the given IDs.
    """
    if not ids:
        return []

    query = (
        _get_configurations_core_query()
        + " WHERE c.id = ANY(%s) AND c.jurisdiction_id = %s"
        + " ORDER BY c.name ASC;"
    )

    params = (
        ids,
        jurisdiction_id,
    )

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

    results = await get_configurations_by_ids_db([id], jurisdiction_id, db)
    return results[0] if results else None


async def is_config_valid_to_insert_db(
    condition_canonical_url: str, jurisdiction_id: str, db: AsyncDatabaseConnection
) -> bool:
    """
    Query the database to check if a configuration can be created. If a config for a condition already exists, returns False.
    """

    query = """
        SELECT c.id
        FROM configurations c
        JOIN configurations_conditions cc ON cc.configuration_id = c.id AND cc.is_primary = true
        JOIN conditions cond ON cond.id = cc.condition_id
        WHERE cond.canonical_url = %s
        AND c.jurisdiction_id = %s
        AND c.status = 'draft'
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
        INSERT INTO configurations_conditions (configuration_id, condition_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        RETURNING configuration_id;
    """

    params = (config.id, condition.id)

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
        DELETE FROM configurations_conditions
        WHERE configuration_id = %s
        AND condition_id = %s
        RETURNING configuration_id;
    """

    params = (config.id, condition.id)

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
            SELECT condition_id AS cond_id
            FROM configurations_conditions
            WHERE configuration_id = %s
        ),
        codes AS (
            SELECT
                c.id AS condition_id,
                code_elem->>'code' AS code
            FROM conds
            JOIN conditions c
                ON c.id = cond_id
            CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.loinc_codes, '[]'::jsonb)) AS code_elem

            UNION

            SELECT
                c.id AS condition_id,
                code_elem->>'code' AS code
            FROM conds
            JOIN conditions c
                ON c.id = cond_id
            CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.snomed_codes, '[]'::jsonb)) AS code_elem

            UNION

            SELECT
                c.id AS condition_id,
                code_elem->>'code' AS code
            FROM conds
            JOIN conditions c
                ON c.id = cond_id
            CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.icd10_codes, '[]'::jsonb)) AS code_elem

            UNION

            SELECT
                c.id AS condition_id,
                code_elem->>'code' AS code
            FROM conds
            JOIN conditions c
                ON c.id = cond_id
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
    display_name: str,
    code: str,
    system_id: UUID,
    user_id: UUID,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Given a config, adds a user-defined custom code to the configuration.
    """

    query = """
            INSERT INTO custom_codes (configuration_id, display, code, system_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (configuration_id, system_id, code) DO NOTHING
            RETURNING id;
        """

    params = (config.id, display_name, code, system_id)

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
                    action_text=f"Added custom code '{code}'",
                ),
                cursor=cur,
            )

    return await get_configuration_by_id_db(
        id=config.id, jurisdiction_id=config.jurisdiction_id, db=db
    )


async def add_bulk_custom_codes_to_configuration_db(
    config: DbConfiguration,
    custom_codes: list[AddCustomCodeInput],
    code_systems: list[DbCodeSystem],
    user_id: UUID,
    db: AsyncDatabaseConnection,
) -> BulkAddCustomCodesResult | None:
    """
    Adds multiple custom codes to a configuration in a single update.

    Returns:
        BulkAddCustomCodesResult | None
    """

    placeholders = ", ".join(["(%s, %s, %s, %s)"] * len(custom_codes))
    query = f"""
        INSERT INTO custom_codes (configuration_id, display, code, system_id)
        VALUES {placeholders}
        ON CONFLICT DO NOTHING
        RETURNING *;
    """

    params = [
        val for c in custom_codes for val in (config.id, c.display, c.code, c.system_id)
    ]

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            new_codes_added = await cur.fetchall()

            # Insert a single audit event if codes were added
            await insert_custom_code_upload_events_db(
                configuration=config,
                user_id=user_id,
                custom_codes=[
                    DbConfigurationCustomCode(
                        id=str(cc["id"]),
                        code=cc["code"],
                        name=cc["display"],
                        system_id=cc["system_id"],
                    )
                    for cc in new_codes_added
                ],
                code_systems=code_systems,
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
    id: UUID,
    user_id: UUID,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Given a config and custom code ID, deletes the custom code from the configuration.
    """

    query = """
            DELETE FROM custom_codes
            WHERE id = %s
            RETURNING
                code;
            """
    params = (id,)

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
                    action_text=f"Removed custom code '{row['code']}'",
                ),
                cursor=cur,
            )

    return await get_configuration_by_id_db(
        id=config.id, jurisdiction_id=config.jurisdiction_id, db=db
    )


async def edit_custom_code_from_configuration_db(
    config: DbConfiguration,
    custom_code: DbCustomCode,
    user_id: UUID,
    display: str,
    code: str,
    system_id: UUID,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Given a config and a list of custom codes, updates the configuration's custom codes using the provided list.
    """

    query = """
            UPDATE custom_codes
            SET display = %s,
                code = %s,
                system_id = %s
            WHERE id = %s
            RETURNING *;
            """

    params = (
        display,
        code,
        system_id,
        custom_code.id,
    )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

            if row is None:  # TODO: is this right?
                return None

            # Collect all event messages
            events_to_insert = []

            # 1. Code changed
            if code != custom_code.code:
                events_to_insert.append(
                    EventInput(
                        jurisdiction_id=config.jurisdiction_id,
                        user_id=user_id,
                        configuration_id=config.id,
                        event_type="edit_code",
                        action_text=f"Updated custom code from '{custom_code.code}' to '{code}'",
                    )
                )

            # 2. Name changed
            if display != custom_code.display:
                events_to_insert.append(
                    EventInput(
                        jurisdiction_id=config.jurisdiction_id,
                        user_id=user_id,
                        configuration_id=config.id,
                        event_type="edit_code",
                        action_text=f"Updated name for custom code '{custom_code.code}' from '{custom_code.display}' to '{display}'",
                    )
                )

            # 3. System changed
            if system_id != custom_code.system_id:
                events_to_insert.append(
                    EventInput(
                        jurisdiction_id=config.jurisdiction_id,
                        user_id=user_id,
                        configuration_id=config.id,
                        event_type="edit_code",
                        action_text=f"Updated system for custom code '{custom_code.code}' from '{custom_code.system_id}' to '{system_id}'",  # TODO: Use system name instead
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
            section_type,
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


def _bool_label(value: bool) -> Literal["enabled", "disabled"]:
    """
    Small helper function to convert a boolean into "enabled" or "disabled".

    Args:
        value (bool): True or False value

    Returns:
        Literal['enabled', 'disabled']: "enabled" or "disabled"
    """
    return "enabled" if value else "disabled"


async def update_configuration_section_db(
    config: DbConfiguration,
    current_code: str,
    section_update: DbConfigurationSectionProcessing,
    user_id: UUID,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Update section processing instructions for a configuration.

    Args:
        config: The configuration to update
        current_code: The section code to update
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
        configuration_id=config.id, code=current_code, db=db
    )

    if not prev_section:
        raise ValueError(f"No existing section with code {current_code} to update")

    # Calculate what changed and generate the text for the event
    change_specs = [
        (
            prev_section.action,
            section_update.action,
            lambda old, new: (
                f"data handling approach from '{ACTION_LABELS.get(old, old)}' "
                f"to '{ACTION_LABELS.get(new, new)}'"
            ),
        ),
        (
            prev_section.include,
            section_update.include,
            lambda old, new: (
                f"include from '{_bool_label(old)}' to '{_bool_label(new)}'"
            ),
        ),
        (
            prev_section.code,
            section_update.code,
            lambda old, new: f"code from '{old}' to '{new}'",
        ),
        (
            prev_section.name,
            section_update.name,
            lambda old, new: f"name from '{old}' to '{new}'",
        ),
        (
            prev_section.narrative,
            section_update.narrative,
            lambda old, new: f"narrative from '{old}' to '{new}'",
        ),
    ]

    section_events = [
        EventInput(
            jurisdiction_id=config.jurisdiction_id,
            user_id=user_id,
            configuration_id=config.id,
            event_type="section_update",
            action_text=f"Updated section '{prev_section.name}' {formatter(old, new)}",
        )
        for old, new, formatter in change_specs
        if old != new
    ]

    query = """
            UPDATE configurations_sections
            SET
                code = %s,
                name = %s,
                action = %s,
                include = %s,
                narrative = %s,
                updated_at = NOW()
            WHERE configuration_id = %s
            AND code = %s
            RETURNING id;
            """

    params = (
        section_update.code,
        section_update.name,
        section_update.action,
        section_update.include,
        section_update.narrative,
        config.id,
        current_code,
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
        SELECT c.id
        FROM configurations c
        JOIN configurations_conditions cc ON cc.configuration_id = c.id AND cc.is_primary = true
        JOIN conditions cond ON cond.id = cc.condition_id
        WHERE c.jurisdiction_id = %s
        AND cond.canonical_url = %s
        ORDER BY c.version DESC
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
        SELECT c.id
        FROM configurations c
        JOIN configurations_conditions cc ON cc.configuration_id = c.id AND cc.is_primary = true
        JOIN conditions cond ON cond.id = cc.condition_id
        WHERE c.jurisdiction_id = %s
        AND cond.canonical_url = %s
        AND c.status = 'active';
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
            cond.canonical_url AS condition_canonical_url,
            c.last_activated_at,
            la.username AS last_activated_by,
            c.created_at,
            u.username AS created_by
        FROM configurations c
        JOIN configurations_conditions cc ON cc.configuration_id = c.id AND cc.is_primary = true
        JOIN conditions cond ON cond.id = cc.condition_id
        JOIN users u ON u.id = c.created_by
        LEFT JOIN users la ON la.id = c.last_activated_by
        WHERE c.jurisdiction_id = %s
        AND cond.canonical_url = %s
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


async def get_configurations_summary_db(
    jurisdiction_id: str, db: AsyncDatabaseConnection
) -> list[DbConfigurationSummary]:
    """
    Returns a high-level summary of all configuration info within a jurisdiction.
    """
    query = """
        WITH ranked AS (
            SELECT
                c.id,
                c.name,
                c.status,
                cond.canonical_url,
                ROW_NUMBER() OVER (
                    PARTITION BY cond.canonical_url
                    ORDER BY
                        CASE c.status
                            WHEN 'active' THEN 1
                            WHEN 'draft' THEN 2
                            WHEN 'inactive' THEN 3
                        END,
                        c.version DESC
                ) AS rn
            FROM configurations c
            JOIN configurations_conditions cc ON cc.configuration_id = c.id AND cc.is_primary = true
            JOIN conditions cond ON cond.id = cc.condition_id
            WHERE c.jurisdiction_id = %s
        )
        SELECT id, name, status
        FROM ranked
        WHERE rn = 1
        ORDER BY LOWER(name)
    """
    params = (jurisdiction_id,)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbConfigurationSummary)) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return rows


def _get_configurations_core_query() -> str:
    return """
    SELECT
        c.id,
        c.name,
        c.status,
        c.jurisdiction_id,
        cc_primary.condition_id,
        COALESCE(codes.custom_codes, '[]'::jsonb) AS custom_codes,

        COALESCE(conds.included_conditions, '{}') AS included_conditions,
        COALESCE(secs.section_processing, '[]'::jsonb) AS section_processing,

        c.version,
        c.last_activated_at,
        c.last_activated_by,
        c.created_by,
        c.s3_url
    FROM configurations c
    JOIN configurations_conditions cc_primary ON cc_primary.configuration_id = c.id AND cc_primary.is_primary = true
    LEFT JOIN LATERAL (
        SELECT jsonb_agg(
                   jsonb_build_object(
                       'id', cc.id::text,
                       'code', cc.code,
                       'name', cc.display,
                       'system_id', cc.system_id::text
                   )
               ) AS custom_codes
        FROM custom_codes cc
        WHERE cc.configuration_id = c.id
    ) codes ON TRUE
    LEFT JOIN LATERAL (
        SELECT array_agg(cc.condition_id) AS included_conditions
        FROM configurations_conditions cc
        WHERE cc.configuration_id = c.id
    ) conds ON TRUE
    LEFT JOIN LATERAL (
        SELECT jsonb_agg(
                   jsonb_build_object(
                       'code', s.code,
                       'name', s.name,
                       'action', s.action::text,
                       'include', s.include,
                       'versions', to_jsonb(s.versions),
                       'narrative', s.narrative,
                       'section_type', s.section_type
                   )
                   ORDER BY s.code
               ) AS section_processing
        FROM configurations_sections s
        WHERE s.configuration_id = c.id
    ) secs ON TRUE
"""
