from psycopg.rows import class_row

from ..pool import AsyncDatabaseConnection
from .model import DbCondition


async def get_conditions_db(db: AsyncDatabaseConnection) -> list[DbCondition]:
    """
    Queries the database and retrieves a list of conditions with version 2.0.0.

    Args:
        db (AsyncDatabaseConnection): Database connection.

    Returns:
        list[Condition]: List of conditions.
    """
    query = """
            SELECT
                id,
                REPLACE(display_name, '_', ' ') AS display_name,
                canonical_url,
                version
            FROM conditions
            WHERE version = '2.0.0'
            ORDER BY REPLACE(display_name, '_', ' ') ASC;
            """
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCondition)) as cur:
            await cur.execute(query)
            rows = await cur.fetchall()

    if not rows:
        raise Exception("No conditions found for version 2.0.0.")

    return rows


async def get_condition_by_id(
    id: str, db: AsyncDatabaseConnection
) -> DbCondition | None:
    """
    Gets a condition from the database with the provided ID.
    """

    query = """
        SELECT id,
        canonical_url,
        display_name,
        version
        FROM conditions
        WHERE version = '2.0.0'
        AND id = %s
        """
    params = (id,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCondition)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    return row
