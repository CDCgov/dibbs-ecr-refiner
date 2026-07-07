from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from psycopg.rows import class_row

from app.db.pool import AsyncDatabaseConnection


@dataclass(frozen=True)
class DbTesUpdate:
    """
    TES update metadata from the DB.
    """

    id: UUID
    version: str
    created_at: datetime


async def get_tes_updates_db(db: AsyncDatabaseConnection) -> list[DbTesUpdate]:
    """
    Returns all TES updates from the DB.

    Args:
        db (AsyncDatabaseConnection): Database connection.

    Returns:
        list[DbTesUpdate]: a list of the TES information
    """
    query = """
    SELECT
        id,
        created_at,
        version
    FROM tes
    ORDER BY version DESC;
    """
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbTesUpdate)) as cur:
            await cur.execute(query)

            return await cur.fetchall()
