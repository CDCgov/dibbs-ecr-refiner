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

            systems_data: dict[UUID, DbCodeSystem] = defaultdict()

            for system in rows:
                systems_data[system.id] = system

            return systems_data


async def get_code_system_by_key_db(
    key: str,
    db: AsyncDatabaseConnection,
) -> DbCodeSystem | None:
    """
    Function that grabs all information from the code systems table to be used for enum construction.

    Returns:
        Values from the systems table to be consumed by the system enum.
    """

    query = """
    SELECT * FROM systems WHERE key = '%s';
    """
    params = (key,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeSystem)) as cur:
            await cur.execute(query=query, params=params)
            row = await cur.fetchone()

            return row


async def get_code_system_by_key_or_raise_db(
    key: str, db: AsyncDatabaseConnection
) -> DbCodeSystem:
    """
    Function that grabs all information from the code systems table to be used for enum construction.

    Returns:
        Values from the systems table to be consumed by the system enum.
    """

    by_key = await get_code_system_by_key_db(key=key, db=db)

    if by_key is None:
        raise ValueError(f"System with key {key} not found")

    return by_key


async def get_code_system_by_oid_db(
    oid: str,
    db: AsyncDatabaseConnection,
) -> DbCodeSystem | None:
    """
    Function that grabs all information from the code systems table to be used for enum construction.

    Returns:
        Values from the systems table to be consumed by the system enum.
    """

    query = """
    SELECT * FROM systems WHERE oid = '%s';
    """
    params = (oid,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeSystem)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchall()
            if len(row) == 0:
                return None

            return row[0]
