from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...api.auth.middleware import get_logged_in_user
from ...db.conditions.db import get_condition_by_id
from ...db.configurations.db import (
    DbTotalConditionCodeCount,
    associate_condition_codeset_with_configuration_db,
    get_configuration_by_id_db,
    get_configurations_db,
    get_total_condition_code_counts_by_configuration_db,
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

    condition_id: UUID


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

    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found."
        )

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


class GetConfigurationResponse(BaseModel):
    """
    Information about a specific condition to return to the client.
    """

    id: UUID
    display_name: str
    code_sets: list[DbTotalConditionCodeCount]


@router.get(
    "/{configuration_id}",
    response_model=GetConfigurationResponse,
    tags=["configurations"],
    operation_id="getConfiguration",
)
async def get_configuration(
    configuration_id: UUID,
    user: dict[str, Any] = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> GetConfigurationResponse:
    """
    Get a single configuration by its ID.

    Args:
        configuration_id (UUID): ID of the configuration record
        user (dict[str, Any], optional): _description_. Defaults to Depends(get_logged_in_user).
        db (AsyncDatabaseConnection, optional): _description_. Defaults to Depends(get_db).

    Returns:
        GetConfigurationResponse: Response from the API
    """

    # get user jurisdiction
    db_user = await get_user_by_id_db(id=str(user["id"]), db=db)
    jd = db_user.jurisdiction_id
    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=jd, db=db
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found."
        )

    # Get all associated conditions and their # of codes
    config_condition_info = await get_total_condition_code_counts_by_configuration_db(
        config_id=config.id, db=db
    )

    return GetConfigurationResponse(
        id=config.id, display_name=config.name, code_sets=config_condition_info
    )


class AssociateCodesetInput(BaseModel):
    """
    Condition association input model.
    """

    condition_id: UUID


class ConditionEntry(BaseModel):
    """
    Condition model.
    """

    canonical_url: str
    version: str


class AssociateCodesetResponse(BaseModel):
    """
    Response from adding a code set to a config.
    """

    id: UUID
    included_conditions: list[ConditionEntry]


@router.put("/{configuration_id}/code-set", response_model=AssociateCodesetResponse)
async def associate_condition_codeset_with_configuration(
    configuration_id: UUID,
    body: AssociateCodesetInput,
    user: dict[str, Any] = Depends(get_logged_in_user),
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
        HTTPException: 404 if condition is not found
        HTTPException: 500 if configuration is cannot be updated

    Returns:
        AssociateCodesetResponse: ID of updated configuration and the full list of included conditions
    """
    # get user jurisdiction
    db_user = await get_user_by_id_db(id=str(user["id"]), db=db)
    jd = db_user.jurisdiction_id
    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=jd, db=db
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found."
        )

    condition = await get_condition_by_id(id=body.condition_id, db=db)

    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found."
        )

    updated_config = await associate_condition_codeset_with_configuration_db(
        config=config, condition=condition, db=db
    )

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration.",
        )

    return AssociateCodesetResponse(
        id=updated_config.id,
        included_conditions=[
            ConditionEntry(canonical_url=c.canonical_url, version=c.version)
            for c in updated_config.included_conditions
        ],
    )
