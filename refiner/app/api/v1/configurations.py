from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, field_validator

from ...api.auth.middleware import get_logged_in_user
from ...api.validation.file_validation import validate_zip_file
from ...db.conditions.db import (
    get_condition_by_id_db,
    get_conditions_db,
)
from ...db.configurations.db import (
    DbTotalConditionCodeCount,
    add_custom_code_to_configuration_db,
    associate_condition_codeset_with_configuration_db,
    delete_custom_code_from_configuration_db,
    disassociate_condition_codeset_with_configuration_db,
    edit_custom_code_from_configuration_db,
    get_configuration_by_id_db,
    get_configurations_db,
    get_total_condition_code_counts_by_configuration_db,
    insert_configuration_db,
    is_config_valid_to_insert_db,
)
from ...db.configurations.model import DbConfiguration, DbConfigurationCustomCode
from ...db.demo.model import Condition
from ...db.pool import AsyncDatabaseConnection, get_db
from ...db.users.model import DbUser
from ...services.ecr.refine import get_file_size_reduction_percentage, refine
from ...services.file_io import read_xml_zip
from ...services.format import normalize_xml, strip_comments
from ...services.logger import get_logger
from ...services.sample_file import create_sample_zip_file, get_sample_zip_path

router = APIRouter(prefix="/configurations")


@dataclass(frozen=True)
class GetConfigurationsResponse:
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
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> list[GetConfigurationsResponse]:
    """
    Returns a list of configurations based on the logged-in user.

    Returns:
        List of configuration objects.
    """

    # get user jurisdiction
    jd = user.jurisdiction_id

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


@dataclass(frozen=True)
class CreateConfigurationResponse:
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
    user: DbUser = Depends(get_logged_in_user),
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
    jd = user.jurisdiction_id

    # check that there isn't already a config for the condition + JD
    if not await is_config_valid_to_insert_db(
        condition_id=condition.id, jurisdiction_id=jd, db=db
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


@dataclass(frozen=True)
class IncludedCondition:
    """
    Model for a condition that is associated with a configuration.
    """

    id: UUID
    display_name: str
    canonical_url: str
    version: str
    associated: bool


@dataclass(frozen=True)
class GetConfigurationResponse:
    """
    Information about a specific configuration to return to the client.
    """

    id: UUID
    display_name: str
    code_sets: list[DbTotalConditionCodeCount]
    included_conditions: list[IncludedCondition]
    custom_codes: list[DbConfigurationCustomCode]


@dataclass(frozen=True)
class ConfigurationCustomCodeResponse:
    """
    Configuration response for custom code operations (add/edit/delete).
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
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> GetConfigurationResponse:
    """
    Get a single configuration by its ID including all associated conditions.
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
    config_condition_info = await get_total_condition_code_counts_by_configuration_db(
        config_id=config.id, db=db
    )

    associated_conditions = {
        (c.canonical_url, c.version)
        for c in config.included_conditions
        if c.canonical_url and c.version
    }

    all_conditions = await get_conditions_db(db=db)

    included_conditions = [
        IncludedCondition(
            id=cond.id,
            display_name=cond.display_name,
            canonical_url=cond.canonical_url,
            version=cond.version,
            associated=(cond.canonical_url, cond.version) in associated_conditions,
        )
        for cond in all_conditions
    ]
    return GetConfigurationResponse(
        id=config.id,
        display_name=config.name,
        code_sets=config_condition_info,
        included_conditions=included_conditions,
        custom_codes=config.custom_codes,
    )


class AssociateCodesetInput(BaseModel):
    """
    Condition association input model.
    """

    condition_id: UUID


@dataclass(frozen=True)
class ConditionEntry:
    """
    Condition model.
    """

    canonical_url: str
    version: str


@dataclass(frozen=True)
class AssociateCodesetResponse:
    """
    Response from adding a code set to a config.
    """

    id: UUID
    included_conditions: list[ConditionEntry]
    condition_name: str


@router.put(
    "/{configuration_id}/code-sets",
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
        HTTPException: 404 if condition is not found
        HTTPException: 500 if configuration is cannot be updated

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
        condition_name=condition.display_name,
    )


@router.delete(
    "/{configuration_id}/code-sets/{condition_id}",
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
        condition_name=condition.display_name,
    )


class AddCustomCodeInput(BaseModel):
    """
    Input model for adding a custom code to a configuration.
    """

    code: str
    system: Literal["loinc", "snomed", "icd-10", "rxnorm"]
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

    raise Exception(f"System name provided: {system} is invalid.")


@router.post(
    "/{configuration_id}/custom-codes",
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

    return ConfigurationCustomCodeResponse(
        id=updated_config.id,
        display_name=updated_config.name,
        code_sets=config_condition_info,
        custom_codes=updated_config.custom_codes,
    )


@router.delete(
    "/{configuration_id}/custom-codes/{system}/{code}",
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
    updated_code = DbConfigurationCustomCode(
        code=updateInput.new_code or existing_code.code,
        system=_get_sanitized_system_name(updateInput.new_system)
        if updateInput.new_system
        else existing_code.system,
        name=updateInput.new_name or existing_code.name,
    )

    # check for duplicates
    if any(
        cc.code == updated_code.code and cc.system == updated_code.system
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
    "/{configuration_id}/custom-codes",
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

    custom_codes = _get_modified_custom_codes(
        config=config,
        updateInput=body,
    )

    updated_config = await edit_custom_code_from_configuration_db(
        config=config,
        updated_custom_codes=custom_codes,
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


@dataclass(frozen=True)
class ConfigurationTestResponse:
    """
    Model to represent the response provided to the client when in-line testing is run.
    """

    original_eicr: str
    refined_download_url: str
    condition: Condition


@router.post(
    "/test",
    response_model=ConfigurationTestResponse,
    tags=["configurations"],
    operation_id="runInlineConfigurationTest",
)
async def run_configuration_test(
    id: UUID = Form(...),
    uploaded_file: UploadFile | None = File(None),
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
    sample_zip_path: Path = Depends(get_sample_zip_path),
    logger: Logger = Depends(get_logger),
) -> ConfigurationTestResponse:
    """
    Runs an in-line test using the provided configuration ID and test files.

    Args:
        id (UUID): ID of Configuration to use for the test
        uploaded_file (UploadFile | None): user uploaded eICR/RR pair
        user (DbUser): Logged in user
        db (AsyncDatabaseConnection): Database connection
        sample_zip_path (Path): Path to example .zip eICR/RR pair
        logger (Logger): Standard logger
    Returns:
        ConfigurationTestResponse: response given to the client
    """

    if not sample_zip_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to find demo zip file to download.",
        )

    file = None
    if uploaded_file:
        file = await validate_zip_file(file=uploaded_file)
        logger.info(
            "Running inline test using user-provided file",
            extra={"file": file.filename},
        )
    else:
        file = create_sample_zip_file(sample_zip_path=sample_zip_path)
        logger.info(
            "Running inline test using sample file", extra={"file": file.filename}
        )

    # get user jurisdiction
    jd = user.jurisdiction_id

    # find config
    config = await get_configuration_by_id_db(id=id, jurisdiction_id=jd, db=db)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found."
        )

    logger.info(
        "Using config for inline testing",
        extra={"config_id": config.id, "jurisdiction_id": jd},
    )

    # find the primary condition associated with the config
    associated_condition = await get_condition_by_id_db(id=config.condition_id, db=db)
    if not associated_condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Condition associated with configuration (ID: {config.id}) not found.",
        )

    original_xml_files = await read_xml_zip(file)

    refined_results = await refine(
        original_xml=original_xml_files,
        db=db,
        jurisdiction_id=jd,
    )

    child_rsg_codes = set(associated_condition.child_rsg_snomed_codes)
    seen_condition_codes = set()
    matched_result = None
    for result in refined_results:
        # Add current code to seen codes
        seen_condition_codes.add(result.reportable_condition.code)

        # If a child rsg code is found in the "seen" set then we have a match
        if seen_condition_codes & child_rsg_codes:
            matched_result = result
            break

    if not matched_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{associated_condition.display_name} was not detected as a reportable condition in the eCR file you uploaded.",
        )

    original_unrefined_eicr = strip_comments(normalize_xml(original_xml_files.eicr))

    matched_condition_refined_eicr = strip_comments(
        normalize_xml(matched_result.refined_eicr)
    )

    return ConfigurationTestResponse(
        original_eicr=original_unrefined_eicr,
        refined_download_url="http://s3.com",
        condition=Condition(
            code=matched_result.reportable_condition.code,
            display_name=matched_result.reportable_condition.display_name,
            refined_eicr=matched_condition_refined_eicr,
            stats=[
                f"eICR file size reduced by {
                    get_file_size_reduction_percentage(
                        original_unrefined_eicr, matched_condition_refined_eicr
                    )
                }%",
            ],
        ),
    )
