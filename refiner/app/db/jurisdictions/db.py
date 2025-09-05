from psycopg.rows import class_row

from ..pool import AsyncDatabaseConnection
from .model import DbJurisdiction


async def upsert_jurisdiction_db(
    jurisdiction: DbJurisdiction, db: AsyncDatabaseConnection
) -> str:
    """
    Upserts a jurisdiction sent from the IdP.

    Args:
        jurisdiction (Jurisdiction): Jurisdiction information from the IdP.
        db (AsyncDatabaseConnection): The DB connection pool.

    Returns:
        str: Jurisdiction ID of the created or modified jurisdiction.
    """
    query = """
        INSERT INTO jurisdictions (id, name, state_code)
        VALUES (%s, %s, %s)
        ON CONFLICT (id)
        DO UPDATE SET
            name = EXCLUDED.name,
            state_code = EXCLUDED.state_code
        """
    params = (jurisdiction.id, jurisdiction.name, jurisdiction.state_code)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbJurisdiction)) as cur:
            await cur.execute(query, params)

    return jurisdiction.id
