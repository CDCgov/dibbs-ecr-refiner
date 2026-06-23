from uuid import UUID

from psycopg.rows import class_row

from app.db.codes.model import DbCode
from app.db.pool import AsyncDatabaseConnection


async def get_rsg_codes_by_condition_id_db(
    condition_id: UUID, db: AsyncDatabaseConnection
) -> list[DbCode]:
    """
    Function to get all RSG code objects for an identified condition.
    """

    query = """
        SELECT c.display, c.code, c.version, c.system_id
        FROM conditions_rsg_codes as rsg
        LEFT JOIN codes c on c.id = rsg.code_id
        WHERE rsg.condition_id = %s;
    """
    params = (condition_id,)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCode)) as cur:
            await cur.execute(query, params)

            return await cur.fetchall()
