from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...api.auth.middleware import get_logged_in_user
from ...db.conditions.db import get_condition_by_id
from ...db.configurations.db import (
    get_configuration_by_id_db,
    get_configurations_db,
    insert_configuration_db,
    is_config_valid_to_insert_db,
)
from ...db.pool import AsyncDatabaseConnection, get_db
from ...db.user.db import get_user_by_id_db

router = APIRouter(prefix="/configurations")


class GetConfigurationsResponse(BaseModel):
    """
    Model for a user-defined configuration.
    """

    id: UUID
    name: str
    is_active: bool


@router.get(
    "/",
    response_model=list[GetConfigurationsResponse],
    tags=["configurations"],
    operation_id="getConfigurations",
)
async def get_configurations(
    user: dict[str, Any] = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> list[GetConfigurationsResponse]:
    """
    Returns a list of configurations based on the logged-in user.

    Returns:
        List of configuration objects.
    """

    # get user jurisdiction
    db_user = await get_user_by_id_db(id=str(user["id"]), db=db)
    jd = db_user.jurisdiction_id

    configs = await get_configurations_db(jurisdiction_id=jd, db=db)

    return [
        GetConfigurationsResponse(
            id=cfg.id,
            name=cfg.name,
            is_active=False,
        )
        for cfg in configs
    ]


class CreateConfigInput(BaseModel):
    """
    Body required to create a new configuration.
    """

    condition_id: str


class CreateConfigurationResponse(BaseModel):
    """
    Configuration creation response model.
    """

    id: UUID
    name: str


@router.post(
    "/",
    response_model=CreateConfigurationResponse,
    tags=["configurations"],
    operation_id="createConfiguration",
)
async def create_configuration(
    body: CreateConfigInput,
    user: dict[str, Any] = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> CreateConfigurationResponse:
    """
    Create a new configuration for a jurisdiction.
    """

    # get condition by ID
    condition = await get_condition_by_id(id=body.condition_id, db=db)

    # get user jurisdiction
    db_user = await get_user_by_id_db(id=str(user["id"]), db=db)
    jd = db_user.jurisdiction_id

    # check that there isn't already a config for the condition + JD
    if not await is_config_valid_to_insert_db(
        condition_name=condition.display_name, jurisidiction_id=jd, db=db
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Can't create configuration because configuration for condition already exists.",
        )

    config = await insert_configuration_db(
        condition=condition, jurisdiction_id=jd, db=db
    )

    if config is None:
        raise HTTPException(status_code=500, detail="Unable to create configuration")

    return CreateConfigurationResponse(id=config.id, name=config.name)


@router.get(
    "/{configuration_id}",
    response_model=GetConfigurationsResponse,
    tags=["configurations"],
    operation_id="getConfiguration",
)
async def get_configuration(
    configuration_id: str,
    user: dict[str, Any] = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> GetConfigurationsResponse:
    """
    Get a single configuration by its ID.

    Args:
        configuration_id (str): ID of the configuration record
        user (dict[str, Any], optional): _description_. Defaults to Depends(get_logged_in_user).
        db (AsyncDatabaseConnection, optional): _description_. Defaults to Depends(get_db).

    Returns:
        GetConfigurationsResponse: Response from the API
    """

    # get user jurisdiction
    db_user = await get_user_by_id_db(id=str(user["id"]), db=db)
    jd = db_user.jurisdiction_id
    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=jd, db=db
    )

    if not config:
        HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found."
        )

    return GetConfigurationsResponse(id=config.id, name=config.name, is_active=False)
