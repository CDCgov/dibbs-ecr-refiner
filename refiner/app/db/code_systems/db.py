from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from psycopg.rows import class_row

from app.db.pool import AsyncDatabaseConnection

type CodeSystemKey = str


@dataclass
class DbCodeSystem:
    """
    A code system row from the `systems` table.
    """

    id: UUID
    key: CodeSystemKey
    display_name: str
    oid: str


async def get_all_code_systems_db(
    db: AsyncDatabaseConnection,
) -> dict[UUID, DbCodeSystem]:
    """
    Get all code systems.

    Args:
        db: AsyncDatabaseConnection: A database connection.

    Returns:
        dict[UUID, DbCodeSystem]: Dictionary of found code systems, indexed by their db ID's.
    """

    query = """
    SELECT * FROM systems;
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeSystem)) as cur:
            await cur.execute(query)
            rows = await cur.fetchall()

            systems_data: dict[UUID, DbCodeSystem] = defaultdict()

            for system in rows:
                systems_data[system.id] = system

            return systems_data
