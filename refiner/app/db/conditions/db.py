from psycopg.rows import class_row

from ..pool import AsyncDatabaseConnection
from .model import Condition


async def get_all_conditions(db: AsyncDatabaseConnection) -> list[Condition]:
    """
    Queries the database and retrieves a list of conditions with version 2.0.0.

    Args:
        db (AsyncDatabaseConnection): Database connection.

    Returns:
        list[Condition]: List of conditions.
    """
    query = """
        SELECT id, display_name, canonical_url
        FROM conditions
        WHERE version = '2.0.0'
        ORDER BY display_name ASC
        """
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(Condition)) as cur:
            await cur.execute(query)
            rows = await cur.fetchall()

    if not rows:
        raise Exception("No conditions found for version 2.0.0.")

    return rows
