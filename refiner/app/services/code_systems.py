from app.db.code_systems.db import (
    DbCodeSystem,
    get_all_code_systems_db,
    get_code_system_by_display_name_db,
    get_code_system_by_key_db,
)
from app.db.pool import AsyncDatabaseConnection
from app.services.terminology import CodeSystemKey


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


async def get_code_system_by_key_or_display_name(
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

    by_name = await get_code_system_by_display_name_db(db=db, name=string_to_search)
    if by_name:
        return by_name

    # fall back to search by key
    by_key = await get_code_system_by_key_db(db=db, key=string_to_search)
    return by_key
