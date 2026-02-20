from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.auth.middleware import get_logged_in_user
from app.api.v1.configurations.models import (
    AddCustomCodeInput,
    ConfigurationCustomCodeResponse,
)
from app.db.configurations.db import (
    add_custom_code_to_configuration_db,
    delete_custom_code_from_configuration_db,
    edit_custom_code_from_configuration_db,
    get_configuration_by_id_db,
    get_total_condition_code_counts_by_configuration_db,
)
from app.db.configurations.model import (
    DbConfiguration,
    DbConfigurationCustomCode,
)
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.configuration_locks import ConfigurationLock

router = APIRouter(prefix="/{configuration_id}/custom-codes")


def _get_literal_system(system: str) -> Literal["LOINC", "SNOMED", "ICD-10", "RxNorm"]:
    """
    Helper to ensure Literal type for custom code system.
    """
    if system == "LOINC":
        return "LOINC"
    if system == "SNOMED":
        return "SNOMED"
    if system == "ICD-10":
        return "ICD-10"
    if system == "RxNorm":
        return "RxNorm"
    raise ValueError(f"Invalid system: {system}")


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
    if not input.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Required field "name" is missing.',
        )


def _get_sanitized_system_name(system: str):
    lower_system = system.lower()
    if system in ["loinc", "snomed"]:
        return system.upper()
    elif lower_system == "icd-10":
        return "ICD-10"
    elif lower_system == "rxnorm":
        return "RxNorm"
    elif lower_system == "other":
        return "Other"

    raise Exception(f"System name provided: {system} is invalid.")


@router.post(
    "",
    response_model=ConfigurationCustomCodeResponse,
    tags=["configurations"],
    operation_id="addCustomCodeToConfiguration",
)
async def add_custom_code(
    configuration_id: UUID,
    body: AddCustomCodeInput,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> ConfigurationCustomCodeResponse:
    """
    Add a user-defined custom code to a configuration.

    Args:
        configuration_id (UUID): The ID of the configuration to update.
        body (AddCustomCodeInput): The custom code information provided by the user.
        user (dict[str, Any]): The logged-in user.
        db (AsyncDatabaseConnection): The database connection.

    Raises:
        HTTPException: 404 if configuration isn't found
        HTTPException: 409 if configuration is not a draft and therefore not editable
        HTTPException: 500 if custom code can't be added

    Returns:
        ConfigurationCustomCodeResponse: Updated configuration
    """

    # validate input
    _validate_add_custom_code_input(body)

    sanitized_system_name = _get_sanitized_system_name(body.system)

    # get user jurisdiction
    jd = user.jurisdiction_id

    # find config
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

    # Create a custom code object
    allowed_systems = ["LOINC", "SNOMED", "ICD-10", "RxNorm"]
    if sanitized_system_name not in allowed_systems:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"System must be one of {allowed_systems}. Got: {sanitized_system_name}",
        )
    custom_code = DbConfigurationCustomCode(
        code=body.code.strip(),
        system=_get_literal_system(sanitized_system_name),
        name=body.name,
    )

    updated_config = await add_custom_code_to_configuration_db(
        config=config, custom_code=custom_code, user_id=user.id, db=db
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

    return ConfigurationCustomCodeResponse(
        id=updated_config.id,
        display_name=updated_config.name,
        code_sets=config_condition_info,
        custom_codes=updated_config.custom_codes,
    )


@router.delete(
    "/{system}/{code}",
    response_model=ConfigurationCustomCodeResponse,
    tags=["configurations"],
    operation_id="deleteCustomCodeFromConfiguration",
)
async def delete_custom_code(
    configuration_id: UUID,
    system: str,
    code: str,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> ConfigurationCustomCodeResponse:
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
        HTTPException: 409 if configuration is not a draft and therefore not editable
        HTTPException: 500 if configuration can't be updated

    Returns:
        ConfigurationCustomCodeResponse: The updated configuration
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
    jd = user.jurisdiction_id

    # find config
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

    updated_config = await delete_custom_code_from_configuration_db(
        config=config, system=system, code=code, user_id=user.id, db=db
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

    return ConfigurationCustomCodeResponse(
        id=updated_config.id,
        display_name=updated_config.name,
        code_sets=config_condition_info,
        custom_codes=updated_config.custom_codes,
    )


class UpdateCustomCodeInput(BaseModel):
    """
    Input model when updating a config's custom code.
    """

    system: str
    code: str
    name: str
    new_code: str | None
    new_system: str | None
    new_name: str | None


def _get_modified_custom_codes(
    config: DbConfiguration,
    updateInput: UpdateCustomCodeInput,
) -> list[DbConfigurationCustomCode]:
    # Get list of current codes
    custom_codes = config.custom_codes

    # find the code to modify
    code_to_edit = [
        cc
        for cc in custom_codes
        if cc.system == _get_sanitized_system_name(updateInput.system)
        and cc.code == updateInput.code
        and cc.name == updateInput.name
    ]

    # We expect exactly 1 code
    if len(code_to_edit) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not find custom code with specified system/code pair.",
        )
    if len(code_to_edit) > 1:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Multiple custom codes with system/code pair found.",
        )

    # get the code
    existing_code = code_to_edit[0]

    # remove the code from the list
    custom_codes.remove(existing_code)

    # create a new code using the changes provided by the user.
    # use the old values as fallbacks.
    allowed_systems = ["LOINC", "SNOMED", "ICD-10", "RxNorm"]
    new_system_value = (
        _get_sanitized_system_name(updateInput.new_system)
        if updateInput.new_system
        else existing_code.system
    )
    if new_system_value not in allowed_systems:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"System must be one of {allowed_systems}. Got: {new_system_value}",
        )
    updated_code = DbConfigurationCustomCode(
        code=updateInput.new_code or existing_code.code,
        name=updateInput.new_name or existing_code.name,
        system=_get_literal_system(new_system_value),
    )

    # check for duplicates
    if any(
        cc.code == updated_code.code
        and cc.system == updated_code.system
        and cc.name == updated_code.name
        for cc in custom_codes
    ):
        # put the original code back so the list is unchanged
        custom_codes.append(existing_code)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A custom code with the same system/code already exists for this configuration.",
        )

    # add the updated code
    custom_codes.append(updated_code)

    # return the full set of custom codes
    return custom_codes


def _validate_edit_custom_code_input(input: UpdateCustomCodeInput):
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


@router.put(
    "",
    response_model=ConfigurationCustomCodeResponse,
    tags=["configurations"],
    operation_id="editCustomCodeFromConfiguration",
)
async def edit_custom_code(
    configuration_id: UUID,
    body: UpdateCustomCodeInput,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> ConfigurationCustomCodeResponse:
    """
    Modify a configuration's custom code based on system/code pair.

    Args:
        configuration_id (UUID): The ID of the configuration to modify.
        body (UpdateCustomCodeInput): User-provided object containing custom code info.
        user (dict[str, Any]): The logged-in user.
        db (AsyncDatabaseConnection): The database connection.

    Raises:
        HTTPException: 400 if a system is not provided
        HTTPException: 400 if a code is not provided
        HTTPException: 404 if the configuration can't be found
        HTTPException: 409 if configuration is not a draft and therefore not editable
        HTTPException: 500 if the configuration can't be updated

    Returns:
        ConfigurationCustomCodeResponse: The updated configuration.
    """

    _validate_edit_custom_code_input(body)

    # get user jurisdiction
    jd = user.jurisdiction_id

    # find config
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

    custom_codes = _get_modified_custom_codes(
        config=config,
        updateInput=body,
    )

    updated_config = await edit_custom_code_from_configuration_db(
        config=config,
        updated_custom_codes=custom_codes,
        user_id=user.id,
        prev_code=body.code,
        prev_system=body.system,
        prev_name=body.name,
        new_code=body.new_code,
        new_system=body.new_system,
        new_name=body.new_name,
        db=db,
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

    return ConfigurationCustomCodeResponse(
        id=updated_config.id,
        display_name=updated_config.name,
        code_sets=config_condition_info,
        custom_codes=updated_config.custom_codes,
    )
