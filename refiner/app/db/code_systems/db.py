from dataclasses import dataclass
from uuid import UUID

from psycopg.rows import class_row

from app.db.pool import AsyncDatabaseConnection
from app.services.terminology import CodeSystemKey


@dataclass
class DbCodeSystem:
    """
    A code system row from the `systems` table.
    """

    id: UUID
    key: CodeSystemKey
    display_name: str
    oid: str


type IndexedCodeSystem = dict[CodeSystemKey, DbCodeSystem]


async def get_code_systems_db(db: AsyncDatabaseConnection) -> list[DbCodeSystem]:
    """
    Fetches all available code systems.
    """
    query = """
    SELECT id, display_name, oid, key FROM systems;
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeSystem)) as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            return rows


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
    SELECT id, display_name, oid, key FROM systems;
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeSystem)) as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            return {system.id: system for system in rows}


async def get_code_system_by_key_db(
    key: str,
    db: AsyncDatabaseConnection,
) -> DbCodeSystem | None:
    """
    Get code system by the internal key.

    Args:
        key: str: the key to query for.
        db: AsyncDatabaseConnection: A database connection.

    Returns:
        DbCodeSystem | None: Matched code system if found, none otherwise.
    """

    query = """
    SELECT id, display_name, oid, key FROM systems WHERE key = %s;
    """
    params = (key,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeSystem)) as cur:
            await cur.execute(query=query, params=params)
            row = await cur.fetchone()

            if not row:
                return None

            return row


async def get_code_system_by_id_db(
    id: UUID,
    db: AsyncDatabaseConnection,
) -> DbCodeSystem | None:
    """
    Get code system by its ID.

    Args:
        id (str): The code system's UUID
        db (AsyncDatabaseConnection): A database connection

    Returns:
        DbCodeSystem | None: Matched code system if found, none otherwise.
    """

    query = """
    SELECT
        id,
        display_name,
        oid,
        key
    FROM systems
    WHERE id = %s;
    """
    params = (id,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeSystem)) as cur:
            await cur.execute(query=query, params=params)
            row = await cur.fetchone()

            if not row:
                return None

            return row


async def get_code_system_by_display_name_db(
    name: str, db: AsyncDatabaseConnection
) -> DbCodeSystem | None:
    """
    Get code system by its display name.

    Args:
        name: the name to query for
        db: AsyncDatabaseConnection: A database connection.
        logger: Logger: The system logger.

    Returns:
        DbCodeSystem | None: Values from the systems table to be consumed by the system enum.
    """

    query = """
    SELECT id, display_name, oid, key FROM systems WHERE display_name = %s;
    """
    params = (name,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeSystem)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

            if not row:
                return None

            return row
