from psycopg.rows import dict_row

from app.db.pool import AsyncDatabaseConnection


async def get_latest_migration_db(db: AsyncDatabaseConnection) -> str:
    """
    Queries the database for all TES versions available for use.
    """

    query = """
    SELECT
        version
    FROM schema_migrations
    ORDER BY version DESC
    LIMIT 1;
    """
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query)
            row = await cur.fetchone()

    return row["version"] if row and row["version"] else "unknown"
