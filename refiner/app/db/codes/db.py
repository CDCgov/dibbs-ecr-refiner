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
        SELECT c.display, c.code, tes.version, c.system_id
        FROM conditions_codes as cc
        LEFT JOIN codes c on c.id = cc.code_id
        LEFT JOIN conditions cond on cond.id = %(condition_id)s
        LEFT JOIN tes on cond.tes_id = tes.id
        WHERE cc.condition_id = %(condition_id)s AND cc.is_child_rsg;
    """
    async with (
        db.get_connection() as conn,
        conn.cursor(row_factory=class_row(DbCode)) as cur,
    ):
        await cur.execute(query, {"condition_id": condition_id})

        return await cur.fetchall()
