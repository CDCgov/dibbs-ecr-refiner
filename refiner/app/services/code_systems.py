from app.db.code_systems.db import (
    CodeSystemKey,
    DbCodeSystem,
    get_all_code_systems_db,
)
from app.db.pool import AsyncDatabaseConnection


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
