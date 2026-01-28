from psycopg.rows import dict_row

from app.db.pool import AsyncDatabaseConnection
from app.db.tes_version.model import DbTesVersionMetadata


async def get_latest_tes_version_metadata(
    db: AsyncDatabaseConnection,
) -> DbTesVersionMetadata | None:
    """
    Fetch the latest configuration from the DB based on seeded values in the TES table.
    """
    query = """
        SELECT * FROM tes_versions WHERE is_current_version=True;
    """
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query)
            row = await cur.fetchone()
            if not row:
                return None

            return DbTesVersionMetadata.from_db_row(row)


async def get_latest_tes_version_name_db(
    db: AsyncDatabaseConnection,
) -> str:
    """
    Fetch just the name from the latest TES.
    """
    metadata = await get_latest_tes_version_metadata(db)
    if not metadata:
        raise ValueError("No information retrieved regarding latest TES information")

    return metadata.version
