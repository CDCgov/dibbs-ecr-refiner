from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from ...api.auth.middleware import get_logged_in_user
from ...db.conditions.db import get_condition_by_id_db
from ...db.configurations.db import (
    DbTotalConditionCodeCount,
    add_custom_code_to_configuration_db,
    associate_condition_codeset_with_configuration_db,
    delete_custom_code_from_configuration_db,
    get_configuration_by_id_db,
    get_configurations_db,
    get_total_condition_code_counts_by_configuration_db,
    insert_configuration_db,
    is_config_valid_to_insert_db,
)
from ...db.configurations.model import DbConfigurationCustomCode
from ...db.pool import AsyncDatabaseConnection, get_db
from ...db.users.db import get_user_by_id_db

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
    condition = await get_condition_by_id_db(id=body.condition_id, db=db)

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
    custom_codes: list[DbConfigurationCustomCode]


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
        id=config.id,
        display_name=config.name,
        code_sets=config_condition_info,
        custom_codes=config.custom_codes,
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

    condition = await get_condition_by_id_db(id=body.condition_id, db=db)

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


class AddCustomCodeInput(BaseModel):
    """
    Input model for adding a custom code to a configuration.
    """

    code: str
    system: Literal["loinc", "snomed", "icd10", "rxnorm"]
    name: str

    @field_validator("system", mode="before")
    @classmethod
    def normalize_system(cls, v: str) -> str:
        """
        Make the system lowercase before Pydantic checks it.
        """
        if not isinstance(v, str):
            raise TypeError('"system" must be a string')
        return v.lower()


def _validate_add_custom_code_input(input: AddCustomCodeInput):
    if not input.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Required field "code" is missing.',
        )
    if not input.system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Required field "system" is missing.',
        )
    if not input.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Required field "name" is missing.',
        )


def _get_sanitized_system_name(system: str):
    lower_system = system.lower()
    if system in ["loinc", "snomed"]:
        return system.upper()
    elif lower_system == "icd10":
        return "ICD-10"
    elif lower_system == "rxnorm":
        return "RxNorm"

    raise Exception("System name provided is invalid.")


@router.put(
    "/{configuration_id}/custom-codes",
    response_model=GetConfigurationResponse,
    tags=["configurations"],
    operation_id="addCustomCodeToConfiguration",
)
async def add_custom_code(
    configuration_id: UUID,
    body: AddCustomCodeInput,
    user: dict[str, Any] = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> GetConfigurationResponse:
    """
    Add a user-defined custom code to a configuration.

    Args:
        configuration_id (UUID): The ID of the configuration to update.
        body (AddCustomCodeInput): The custom code information provided by the user.
        user (dict[str, Any]): The logged-in user.
        db (AsyncDatabaseConnection): The database connection.

    Raises:
        HTTPException: 404 if configuration isn't found
        HTTPException: 500 if custom code can't be added

    Returns:
        GetConfigurationResponse: Updated configuration
    """

    # validate input
    _validate_add_custom_code_input(body)

    sanitized_system_name = _get_sanitized_system_name(body.system)

    # get user jurisdiction
    db_user = await get_user_by_id_db(id=str(user["id"]), db=db)
    jd = db_user.jurisdiction_id

    # find config
    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=jd, db=db
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found."
        )

    # Create a custom code object
    custom_code = DbConfigurationCustomCode(
        code=body.code,
        system=sanitized_system_name,
        name=body.name,
    )

    updated_config = await add_custom_code_to_configuration_db(
        config=config, custom_code=custom_code, db=db
    )

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration.",
        )

    # Get all associated conditions and their # of codes
    config_condition_info = await get_total_condition_code_counts_by_configuration_db(
        config_id=config.id, db=db
    )

    return GetConfigurationResponse(
        id=updated_config.id,
        display_name=updated_config.name,
        code_sets=config_condition_info,
        custom_codes=updated_config.custom_codes,
    )


@router.delete(
    "/{configuration_id}/custom-codes/{system}/{code}",
    response_model=GetConfigurationResponse,
    tags=["configurations"],
    operation_id="deleteCustomCodeFromConfiguration",
)
async def delete_custom_code(
    configuration_id: UUID,
    system: str,
    code: str,
    user: dict[str, Any] = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> GetConfigurationResponse:
    """
    Delete a custom code from a configuration.

    Args:
        configuration_id (UUID): The ID of the configuration to modify.
        system (str): System of the custom code.
        code (str): Code of the custom code.
        user (dict[str, Any]): The logged-in user.
        db (AsyncDatabaseConnection): The database connection.

    Raises:
        HTTPException: 400 if system is not provided
        HTTPException: 400 if code is not provided
        HTTPException: 404 if configuration can't be found
        HTTPException: 500 if configuration can't be updated

    Returns:
        GetConfigurationResponse: The updated configuration
    """

    if not system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="System must be provided."
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Code must be provided."
        )

    # get user jurisdiction
    db_user = await get_user_by_id_db(id=str(user["id"]), db=db)
    jd = db_user.jurisdiction_id

    # find config
    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=jd, db=db
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found."
        )

    updated_config = await delete_custom_code_from_configuration_db(
        config=config, system=system, code=code, db=db
    )

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration.",
        )

    # Get all associated conditions and their # of codes
    config_condition_info = await get_total_condition_code_counts_by_configuration_db(
        config_id=config.id, db=db
    )

    return GetConfigurationResponse(
        id=updated_config.id,
        display_name=updated_config.name,
        code_sets=config_condition_info,
        custom_codes=updated_config.custom_codes,
    )
