from uuid import UUID

from psycopg.rows import class_row

from app.db.custom_codes.model import DbCustomCode
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
