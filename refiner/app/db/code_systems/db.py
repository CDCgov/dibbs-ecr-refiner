from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from uuid import UUID

from psycopg.rows import class_row

from app.db.pool import AsyncDatabaseConnection


@dataclass
class DbCodeSystem:
    """
    A code system row from the `systems` table.
    """

    id: UUID
    name: str
    display_name: str
    oid: str


type CodeSystemName = str


@lru_cache(maxsize=1)
async def get_all_code_systems_db(
    db: AsyncDatabaseConnection,
) -> dict[CodeSystemName, DbCodeSystem]:
    """
    Function that grabs all information from the code systems table to be used for enum construction.

    Returns:
        Values from the systems table to be consumed by the system enum.
    """

    query = """
    SELECT * FROM systems;
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeSystem)) as cur:
            await cur.execute(query)
            rows = await cur.fetchall()

            systems_data = defaultdict()

            for system in rows:
                systems_data[system.name] = system

            return systems_data
