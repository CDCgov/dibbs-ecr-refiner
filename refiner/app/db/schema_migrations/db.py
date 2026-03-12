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
            rows = await cur.fetchall()

    return [row["version"] for row in rows]
