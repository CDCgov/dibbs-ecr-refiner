from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.api.auth.middleware import get_logged_in_user
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.configuration_locks import ConfigurationLock

router = APIRouter(prefix="/{configuration_id}")


@router.post(
    "/acquire-lock", tags=["configurations"], operation_id="acquireConfigurationLock"
)
async def acquire_configuration_lock(
    configuration_id: UUID,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> Response:
    """
    Acquire config lock for user.

    Args:
        configuration_id (UUID): ID of the configuration to lock
        user (DbUser): The logged-in user
        db (AsyncDatabaseConnection): Database connection

    Returns:
        Response: 204 No Content on success
    """
    await ConfigurationLock.acquire_lock(
        configuration_id=configuration_id,
        user_id=user.id,
        db=db,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/release-lock",
    tags=["configurations"],
    operation_id="releaseConfigurationLock",
)
async def release_configuration_lock(
    configuration_id: UUID,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> Response:
    """
    Release config lock if held by user.

    Args:
        configuration_id (UUID): ID of the configuration to update
        user (DbUser): The logged-in user
        db (AsyncDatabaseConnection): Database connection
    """

    await ConfigurationLock.release_if_owned(
        configuration_id=configuration_id,
        user_id=user.id,
        db=db,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
