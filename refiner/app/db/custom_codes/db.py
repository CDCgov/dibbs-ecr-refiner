from uuid import UUID

from psycopg.rows import class_row, dict_row

from app.api.v1.configurations.custom_codes.model import AddCustomCodeInput
from app.db.code_systems.db import DbCodeSystem, get_code_system_by_id_db
from app.db.configurations.model import DbConfiguration
from app.db.custom_codes.model import DbCustomCode
from app.db.events.db import insert_custom_code_upload_events_db, insert_event_db
from app.db.events.model import EventInput
from app.db.pool import AsyncDatabaseConnection


async def get_custom_codes_by_configuration_id_db(
    configuration_id: UUID, db: AsyncDatabaseConnection
) -> list[DbCustomCode]:
    """
    Fetches all custom codes for a configuration by its ID.
    """
    query = """
    SELECT
        id,
        display,
        code,
        system_id,
        created_at,
        updated_at,
        configuration_id
    FROM custom_codes
    WHERE configuration_id = %s
    """
    params = (configuration_id,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCustomCode)) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()
            return rows


async def get_custom_code_by_id_db(
    id: UUID,
    db: AsyncDatabaseConnection,
) -> DbCustomCode | None:
    """
    Returns a custom code row when given a record ID. Returns None if the ID cannot be found.
    """

    query = """
    SELECT
        id,
        display,
        code,
        system_id,
        created_at,
        updated_at,
        configuration_id
    FROM custom_codes
    WHERE id = %s
    """
    params = (id,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCustomCode)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

            if not row:
                return None
            return row


async def insert_custom_code_db(
    config: DbConfiguration,
    display_name: str,
    code: str,
    system_id: UUID,
    user_id: UUID,
    db: AsyncDatabaseConnection,
) -> DbCustomCode | None:
    """
    Inserts a new custom code and associates it with the given configuration.
    """

    query = """
            INSERT INTO custom_codes (configuration_id, display, code, system_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (configuration_id, system_id, code) DO NOTHING
            RETURNING *;
        """

    params = (config.id, display_name, code, system_id)

    async with db.get_connection() as conn:
        async with conn.transaction():
            async with conn.cursor(row_factory=class_row(DbCustomCode)) as cur:
                await cur.execute(query, params)
                row = await cur.fetchone()

                if not row:
                    return None

            async with conn.cursor(row_factory=dict_row) as event_cur:
                await insert_event_db(
                    event=EventInput(
                        jurisdiction_id=config.jurisdiction_id,
                        user_id=user_id,
                        configuration_id=config.id,
                        event_type="add_code",
                        action_text=f"Added custom code '{code}'",
                    ),
                    cursor=event_cur,
                )

            return row


async def insert_custom_codes_db(
    config: DbConfiguration,
    custom_codes: list[AddCustomCodeInput],
    code_systems: list[DbCodeSystem],
    user_id: UUID,
    db: AsyncDatabaseConnection,
) -> list[DbCustomCode]:
    """
    Adds multiple custom codes to a configuration in a single update.
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
        async with conn.cursor(row_factory=class_row(DbCodeSystem)) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

            # Insert a single audit event if codes were added
            await insert_custom_code_upload_events_db(
                configuration=config,
                user_id=user_id,
                custom_codes=[
                    # TODO: add `from_db_row`?
                    DbCustomCode(
                        id=cc["id"],
                        code=cc["code"],
                        display=cc["display"],
                        system_id=cc["system_id"],
                        created_at=cc["created_at"],
                        updated_at=cc["updated_at"],
                        configuration_id=cc["configuration_id"],
                    )
                    for cc in rows
                ],
                code_systems=code_systems,
                cursor=cur,
            )
            return rows


async def delete_custom_code_db(
    config: DbConfiguration,
    id: UUID,
    user_id: UUID,
    db: AsyncDatabaseConnection,
) -> DbCustomCode | None:
    """
    Given a config and custom code ID, deletes the custom code from the configuration.
    """

    query = """
            DELETE FROM custom_codes
            WHERE id = %s
            RETURNING *;
            """
    params = (id,)

    async with db.get_connection() as conn:
        async with conn.transaction():
            async with conn.cursor(row_factory=class_row(DbCustomCode)) as cur:
                await cur.execute(query, params)
                row = await cur.fetchone()

                if not row:
                    return None

            async with conn.cursor(row_factory=dict_row) as event_cur:
                await insert_event_db(
                    event=EventInput(
                        jurisdiction_id=config.jurisdiction_id,
                        user_id=user_id,
                        configuration_id=config.id,
                        event_type="delete_code",
                        action_text=f"Removed custom code '{row.code}'",
                    ),
                    cursor=event_cur,
                )

            return row


async def edit_custom_code_db(
    config: DbConfiguration,
    custom_code: DbCustomCode,
    user_id: UUID,
    display: str,
    code: str,
    system: DbCodeSystem,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Given a config and a custom code, edits the custom code using the specified properties.
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
        system.id,
        custom_code.id,
    )

    async with db.get_connection() as conn:
        async with conn.transaction():
            async with conn.cursor(row_factory=class_row(DbCustomCode)) as cur:
                await cur.execute(query, params)
                row = await cur.fetchone()

                if not row:
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
                if system.id != custom_code.system_id:
                    prev_system = await get_code_system_by_id_db(
                        id=custom_code.system_id, db=db
                    )
                    if prev_system is None:
                        raise ValueError(
                            f"Could not find code system with ID {custom_code.system_id}"
                        )

                    events_to_insert.append(
                        EventInput(
                            jurisdiction_id=config.jurisdiction_id,
                            user_id=user_id,
                            configuration_id=config.id,
                            event_type="edit_code",
                            action_text=f"Updated system for custom code '{custom_code.code}' from '{prev_system.display_name}' to '{system.display_name}'",
                        )
                    )

            # Insert all generated events
            async with conn.cursor(row_factory=dict_row) as event_cur:
                for event in events_to_insert:
                    await insert_event_db(event=event, cursor=event_cur)

            return row
