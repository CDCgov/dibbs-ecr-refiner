from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.middleware import get_logged_in_user
from app.api.v1.configurations.models import (
    AssociateCodesetInput,
    AssociateCodesetResponse,
    ConditionEntry,
)
from app.db.conditions.db import get_condition_by_id_db
from app.db.configurations.db import (
    associate_condition_codeset_with_configuration_db,
    disassociate_condition_codeset_with_configuration_db,
    get_configuration_by_id_db,
)
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.configuration_locks import ConfigurationLock

router = APIRouter(prefix="/{configuration_id}/code-sets")


@router.put(
    "",
    response_model=AssociateCodesetResponse,
    tags=["configurations"],
    operation_id="associateConditionWithConfiguration",
)
async def associate_condition_codeset_with_configuration(
    configuration_id: UUID,
    body: AssociateCodesetInput,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> AssociateCodesetResponse:
    """
    Associate a specified code set with the given configuration.

    Args:
        configuration_id (UUID): ID of the configuration
        body (AssociateCodesetInput): payload containing a condition_id
        user (dict[str, Any], optional): User making the request
        db (AsyncDatabaseConnection, optional): Database connection

    Raises:
        HTTPException: 404 if configuration is not found in JD
        HTTPException: 404 if configuration is not found
        HTTPException: 409 if configuration is not a draft and therefore not editable
        HTTPException: 500 if configuration cannot be updated

    Returns:
        AssociateCodesetResponse: ID of updated configuration, the full list of included conditions,
              and the condition_name
    """

    # get user jurisdiction

    jd = user.jurisdiction_id

    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=jd, db=db
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found."
        )
    await ConfigurationLock.raise_if_locked_by_other(
        configuration_id,
        user.id,
        username=user.username,
        email=user.email,
        db=db,
    )

    if config.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trying to update a non-draft configuration",
        )

    condition = await get_condition_by_id_db(id=body.condition_id, db=db)

    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found."
        )

    updated_config = await associate_condition_codeset_with_configuration_db(
        config=config, condition=condition, user_id=user.id, db=db
    )

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration.",
        )

    return AssociateCodesetResponse(
        id=updated_config.id,
        included_conditions=[
            ConditionEntry(c.id) for c in updated_config.included_conditions
        ],
        condition_name=condition.display_name,
    )


@router.delete(
    "/{condition_id}",
    response_model=AssociateCodesetResponse,
    tags=["configurations"],
    operation_id="disassociateConditionWithConfiguration",
)
async def remove_condition_codeset_from_configuration(
    configuration_id: UUID,
    condition_id: UUID,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> AssociateCodesetResponse:
    """
    Remove a specified code set from the given configuration.

    Args:
        configuration_id (UUID): ID of the configuration
        condition_id (UUID): ID of the condition to remove
        user (DbUser): User making the request
        db (AsyncDatabaseConnection): Database connection

    Raises:
        HTTPException: 404 if configuration is not found in JD
        HTTPException: 404 if condition is not found
        HTTPException: 409 if trying to remove the main condition
        HTTPException: 409 if configuration is not a draft and therefore not editable
        HTTPException: 500 if configuration is cannot be updated

    Returns:
        AssociateCodesetResponse: ID of updated configuration and the full list
        of included conditions plus condition_name
    """

    jd = user.jurisdiction_id

    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=jd, db=db
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found."
        )
    await ConfigurationLock.raise_if_locked_by_other(
        configuration_id,
        user.id,
        username=user.username,
        email=user.email,
        db=db,
    )

    if config.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trying to update a non-draft configuration",
        )

    condition = await get_condition_by_id_db(id=condition_id, db=db)

    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found."
        )

    if condition.display_name == config.name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot remove initial condition.",
        )

    updated_config = await disassociate_condition_codeset_with_configuration_db(
        config=config, condition=condition, user_id=user.id, db=db
    )

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration.",
        )

    return AssociateCodesetResponse(
        id=updated_config.id,
        included_conditions=[
            ConditionEntry(c.id) for c in updated_config.included_conditions
        ],
        condition_name=condition.display_name,
    )
