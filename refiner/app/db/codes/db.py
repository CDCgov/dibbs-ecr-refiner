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
        SELECT c.display, c.code, c.system_id, s.display_name as system_name
        FROM conditions_codes_temp as cc
        LEFT JOIN codes c on c.id = cc.code_id
        JOIN systems s ON c.system_id = s.id
        LEFT JOIN conditions cond on cond.id = %(condition_id)s
        WHERE cc.condition_id = %(condition_id)s AND cc.is_child_rsg;
    """
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCode)) as cur:
            await cur.execute(query, {"condition_id": condition_id})

            return await cur.fetchall()


async def get_pruned_configuration_codes_db(
    configuration_id: UUID, db: AsyncDatabaseConnection
) -> list[DbCode]:
    """
    Function to get the list of configuration codes, minus exclusions for final serialization.
    """

    query = """
       SELECT DISTINCT display, code, system_id, system_name
        FROM (
            -- Standard codes
            SELECT c.display, c.code, c.system_id, s.display_name as system_name
            FROM configurations_conditions as cc
            JOIN conditions_codes_temp cond_codes ON cond_codes.condition_id = cc.condition_id
            JOIN codes c ON c.id = cond_codes.code_id
            JOIN conditions cond ON cond.id = cc.condition_id
            JOIN systems s ON c.system_id = s.id
            JOIN tes t ON t.id = cond.tes_id
            WHERE cc.configuration_id = %(configuration_id)s
            AND NOT EXISTS (
                SELECT 1
                FROM configurations_conditions_code_exclusions ce
                WHERE ce.configuration_id = %(configuration_id)s AND ce.code_id = c.id
            )

            UNION

            -- Custom codes
            SELECT cc_code.display, cc_code.code, cc_code.system_id, cc_code.system_name
            FROM configurations_conditions cc
            JOIN custom_codes cc_code ON cc_code.configuration_id = cc.configuration_id
            WHERE cc.configuration_id = %(configuration_id)s
        ) combined_codes;
    """

    async with (
        db.get_connection() as conn,
        conn.cursor(row_factory=class_row(DbCode)) as cur,
    ):
        await cur.execute(query, {"configuration_id": configuration_id})

        return await cur.fetchall()
