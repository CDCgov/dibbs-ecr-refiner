from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from psycopg.rows import class_row

from app.db.configurations.model import DbConfiguration
from app.db.pool import AsyncDatabaseConnection


@dataclass
class DbCodeResult:
    """
    Result from query.
    """

    id: UUID
    condition_id: UUID
    source: str
    code: str
    description: str
    system_id: UUID
    system_name: str
    status: Literal["included", "excluded"]


async def get_configuration_codes_db(
    configuration: DbConfiguration, db: AsyncDatabaseConnection
) -> list[DbCodeResult]:
    """
    Given a configuration ID, fetch all condition codes associated with the configuration.
    """
    query = """
        SELECT
            c.id,
            cfgc.condition_id,
            con.display_name || ' CG' AS source,
            c.code,
            c.display as description,
            c.system_id,
            s.display_name AS system_name,
            CASE WHEN e.code_id IS NULL THEN 'included' ELSE 'excluded' END AS status
        FROM configurations_conditions cfgc
        JOIN conditions con ON con.id = cfgc.condition_id
        JOIN conditions_codes cc ON cc.condition_id = cfgc.condition_id
        JOIN codes c ON c.id = cc.code_id
        JOIN systems s ON s.id = c.system_id
        LEFT JOIN configurations_conditions_code_exclusions e
            ON e.configuration_id = cfgc.configuration_id
            AND e.condition_id = cfgc.condition_id
            AND e.code_id = cc.code_id
        WHERE cfgc.configuration_id = %s;
    """
    params = (configuration.id,)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeResult)) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()
            return rows
