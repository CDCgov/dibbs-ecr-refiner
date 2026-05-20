from collections import defaultdict
from dataclasses import dataclass
from logging import Logger
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
    SELECT * FROM systems WHERE key = %s;
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
    Get code system by the internal key. If not found, raise an error.

    Args:
        key: str: the key to query for.
        db: AsyncDatabaseConnection: A database connection.

    Returns:
        DbCodeSystem: Matched code system if found.

    Raises:
        ValueError: if no code system is found
    """

    by_key = await get_code_system_by_key_db(key=key, db=db)

    if by_key is None:
        raise ValueError(f"System with key {key} not found")

    return by_key


async def _get_code_system_by_display_name_db(
    name: str, db: AsyncDatabaseConnection, logger: Logger
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
    SELECT * FROM systems WHERE display_name = %s;
    """
    params = (name,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeSystem)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchall()
            if len(row) == 0:
                return None

            if len(row) > 1:
                logger.warning(
                    f"Found multiple matches for code system when querying by display_name {name}. Returning first match"
                )

            return row[0]


async def _get_code_system_by_display_name_or_raise_db(
    name: str, db: AsyncDatabaseConnection, logger: Logger
) -> DbCodeSystem:
    """
    Get code system by its display name.

    Args:
        name: the name to query for
        db: AsyncDatabaseConnection: A database connection.
        logger: Logger: The system logger.

    Returns:
        DbCodeSystem: Values from the systems table with matching display name.

    Raises:
        ValueError: if no code system is found
    """

    system_by_name = await _get_code_system_by_display_name_db(
        name=name, db=db, logger=logger
    )
    if system_by_name is None:
        raise ValueError("No system with display name {}")

    return system_by_name


async def get_code_system_by_key_or_display_name_or_raise_db(
    name: str, db: AsyncDatabaseConnection, logger: Logger
) -> DbCodeSystem:
    """
    Get code system by its display name and fall back to key if not cound.

    Args:
        name: the name to query for
        db: AsyncDatabaseConnection: A database connection.
        logger: Logger: The system logger.

    Returns:
        DbCodeSystem: Values from the systems table with matching display name.

    Raises:
        ValueError: if no code system is found
    """
    string_to_search = name.lower()
    try:
        by_name = await _get_code_system_by_display_name_or_raise_db(
            db=db, logger=logger, name=string_to_search
        )
        return by_name
    except ValueError:
        # fall back to search by key
        by_key = await get_code_system_by_key_or_raise_db(db=db, key=string_to_search)
        return by_key


async def get_allowed_code_system_display_names(
    db: AsyncDatabaseConnection,
) -> list[str]:
    """
    Get all allowed display names for supported systems.

    Args:
        db: AsyncDatabaseConnection: A database connection.

    Returns:
        list[str]: A list of stored DB code systems
    """
    allowed_code_systems = await get_all_code_systems_db(db)

    return [s.display_name for s in allowed_code_systems.values()]


async def get_code_systems_indexed_by_key(
    db: AsyncDatabaseConnection,
) -> dict[CodeSystemKey, DbCodeSystem]:
    """
    Helper method that returns a map of key to code system.

    Args:
        db: AsyncDatabaseConnection: A database connection.

    Returns:
        list[str]: A list of stored DB code systems
    """
    allowed_code_systems = await get_all_code_systems_db(db)

    return {s.key: s for s in allowed_code_systems.values()}


async def get_allowed_code_system_keys(db: AsyncDatabaseConnection) -> list[str]:
    """
    Get all keys for supported systems as an internal index for code systems.

    Args:
        db: AsyncDatabaseConnection: A database connection.

    Returns:
        list[str]: A list of keys for supported systems
    """
    allowed_code_systems = await get_all_code_systems_db(db)

    return [s.key for s in allowed_code_systems.values()]
