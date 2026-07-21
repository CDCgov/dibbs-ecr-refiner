from uuid import UUID

from fastapi import HTTPException, status

from app.db.code_systems.db import (
    DbCodeSystem,
    IndexedCodeSystem,
    get_all_code_systems_db,
)
from app.db.pool import AsyncDatabaseConnection


def get_code_system_by_id_or_raise(
    id: UUID, systems: list[DbCodeSystem]
) -> DbCodeSystem:
    """
    Attempts to find a code by the provided ID.

    Args:
        id (UUID): The desired system ID
        systems (list[DbCodeSystem]): A list of systems to search for the matching ID

    Raises:
        HTTPException: 404 is raised if the system ID is not found in the list of systems

    Returns:
        DbCodeSystem: The matching code system
    """
    system = next((s for s in systems if s.id == id), None)
    if system is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find code system with ID: {id}",
        )
    return system


async def get_all_code_systems_by_key(
    db: AsyncDatabaseConnection,
) -> IndexedCodeSystem:
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
