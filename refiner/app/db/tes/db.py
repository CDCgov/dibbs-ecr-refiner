from psycopg.rows import class_row

from app.db.pool import AsyncDatabaseConnection
from app.db.tes.model import DbTes


async def get_loaded_tes_versions_db(db: AsyncDatabaseConnection) -> list[DbTes]:
    """
    Returns an array off all loaded TES version records.
    """
    query = """
    SELECT
        id,
        version,
        created_at,
        updated_at
    FROM tes
    ORDER BY version
    """
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbTes)) as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            return rows
