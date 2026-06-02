from collections import defaultdict
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from psycopg.rows import dict_row

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

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "DbCodeSystem":
        """
        Transforms a dictionary object read from the DB into a DbCodeSystem.

        Args:
            row (dict[str, Any]): Dictionary containing system data from the database

        Returns:
            DbCodeSystem: The configuration object
        """

        return cls(
            id=row["id"],
            key=row["key"],
            display_name=row["display_name"],
            oid=row["oid"],
        )


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
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query)
            rows = await cur.fetchall()

            systems_data: dict[UUID, DbCodeSystem] = defaultdict()

            for system in rows:
                system_obj = DbCodeSystem.from_db_row(system)
                systems_data[system_obj.id] = system_obj

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
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query=query, params=params)
            row = await cur.fetchone()

            if not row:
                return None

            return DbCodeSystem.from_db_row(row)


async def _get_code_system_by_display_name_db(
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
    SELECT * FROM systems WHERE display_name = %s;
    """
    params = (name,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

            if not row:
                return None

            return DbCodeSystem.from_db_row(row)


async def get_code_system_by_key_or_display_name_db(
    name: str, db: AsyncDatabaseConnection
) -> DbCodeSystem | None:
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
    if string_to_search == "icd-10":
        string_to_search = "icd10"

    by_name = await _get_code_system_by_display_name_db(db=db, name=string_to_search)
    if by_name:
        return by_name

    # fall back to search by key
    by_key = await get_code_system_by_key_db(db=db, key=string_to_search)
    return by_key


async def get_all_code_systems_by_key(
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
