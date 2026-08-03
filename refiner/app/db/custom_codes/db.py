from uuid import UUID

from psycopg.rows import class_row, dict_row

from app.db.configurations.db import get_configuration_by_id_db
from app.db.configurations.model import DbConfiguration
from app.db.custom_codes.model import DbCustomCode
from app.db.events.db import insert_event_db
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
) -> DbConfiguration | None:
    """
    Inserts a new custom code and associates it with the given configuration.
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
