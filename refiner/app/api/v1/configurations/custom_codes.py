import csv
import io
from dataclasses import dataclass
from logging import Logger
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.auth.middleware import get_logged_in_user
from app.api.v1.configurations.model import (
    AddCustomCodeInput,
    ConfigurationCustomCodeResponse,
    ConfirmUploadCustomCodesInput,
    UploadCustomCodesCsvInput,
    UploadCustomCodesPreviewItem,
)
from app.db.conditions.db import get_included_conditions_db
from app.db.configurations.db import (
    add_bulk_custom_codes_to_configuration_db,
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
from app.services.logger import get_logger
from app.services.terminology import CodeSystem

router = APIRouter(prefix="/{configuration_id}/custom-codes")


def _sanitize_system_or_raise(
    value: str, allowed: set[CodeSystem] | None = None
) -> CodeSystem:
    try:
        system = CodeSystem.sanitize(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    if allowed and system not in allowed:
        allowed_values = ", ".join(item.value for item in allowed)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"System must be one of [{allowed_values}]. Got: {system.value}",
        )

    return system


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


ALLOWED_CUSTOM_CODE_SYSTEMS: set[CodeSystem] = set(CodeSystem)
ALLOWED_CUSTOM_CODE_SYSTEM_NAMES = ", ".join(
    item.value for item in ALLOWED_CUSTOM_CODE_SYSTEMS
)


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

    sanitized_system_name = _sanitize_system_or_raise(
        body.system, allowed=ALLOWED_CUSTOM_CODE_SYSTEMS
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

    # Create a custom code object

    if sanitized_system_name not in ALLOWED_CUSTOM_CODE_SYSTEMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"System must be one of [{ALLOWED_CUSTOM_CODE_SYSTEM_NAMES}]. Got: {sanitized_system_name.value}",
        )
    custom_code = DbConfigurationCustomCode(
        code=body.code.strip(),
        system=CodeSystem(sanitized_system_name),
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


class UploadCustomCodesResponse(BaseModel):
    """CSV response model. Errors are surfaced via the `errors` array."""

    message: str | None = None
    codes_processed: int | None = None
    total_custom_codes_in_configuration: int | None = None
    errors: list[dict] | None = None


class UploadCustomCodesPreviewResponse(BaseModel):
    """Validated CSV preview for delayed confirmation; only valid if preview."""

    preview: list[UploadCustomCodesPreviewItem]
    codes_processed: int | None = None
    total_custom_codes_in_configuration: int | None = None


@router.post(
    "/upload",
    tags=["configurations"],
    operation_id="uploadCustomCodesCsv",
    response_model=UploadCustomCodesPreviewResponse,
)
async def upload_custom_codes_csv(
    configuration_id: UUID,
    body: UploadCustomCodesCsvInput,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
    logger: Logger = Depends(get_logger),
) -> UploadCustomCodesPreviewResponse:
    """
    Accepts a CSV payload in JSON body.

    Expected CSV headers:
        code_number,code_system,display_name

    Returns:
        UploadCustomCodesResponse
    """

    if body.filename and not body.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV.",
        )

    # Get user jurisdiction
    jd = user.jurisdiction_id

    # Find config
    config = await get_configuration_by_id_db(
        id=configuration_id,
        jurisdiction_id=jd,
        db=db,
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found.",
        )

    # Parse CSV from text
    decoded = body.csv_text
    csv_reader = csv.DictReader(io.StringIO(decoded))

    required_columns = {"code_number", "code_system", "display_name"}
    if not required_columns.issubset(set(csv_reader.fieldnames or [])):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV must contain headers: code_number,code_system,display_name",
        )

    preview_items: list[UploadCustomCodesPreviewItem] = []
    errors: list[dict] = []
    code_keys = [(cc.code.lower(), cc.system.lower()) for cc in config.custom_codes]
    batch_keys = set()
    allowed_systems_str = ", ".join(item.value for item in CodeSystem)
    for row_number, row in enumerate(csv_reader, start=2):
        code = (row.get("code_number") or "").strip()
        code_system_raw = (row.get("code_system") or "").strip()
        name = (row.get("display_name") or "").strip()
        row_errors = []
        if not code:
            row_errors.append("Missing code_number")
        if not code_system_raw:
            row_errors.append("Missing code_system")
        if not name:
            row_errors.append("Missing display_name")
        sanitized_system = None
        try:
            sanitized_system = CodeSystem.sanitize(code_system_raw)
        except ValueError:
            row_errors.append(
                f"Invalid system: {code_system_raw or '[blank]'}. [code_system] must be one of [{allowed_systems_str}]"
            )
        code_key = None
        if sanitized_system:
            code_key = (code.lower(), sanitized_system.value.lower())
        if code_key in code_keys:
            row_errors.append("Duplicate: matches existing custom code")
        if code_key in batch_keys:
            row_errors.append("Duplicate: matches uploaded batch code")
        if row_errors:
            errors.append({"row": row_number, "error": ", ".join(row_errors)})
            continue
        batch_keys.add(code_key)
        if sanitized_system:
            preview_items.append(
                UploadCustomCodesPreviewItem(
                    code=code,
                    system=sanitized_system,
                    name=name,
                    row=row_number,
                )
            )
    if errors:
        logger.error("CSV upload errors", extra={"errors": errors})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors},
        )
    if not preview_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": [{"row": 0, "error": "No valid rows"}]},
        )
    return UploadCustomCodesPreviewResponse(
        preview=preview_items,
        codes_processed=len(preview_items),
        total_custom_codes_in_configuration=len(config.custom_codes)
        + len(preview_items),
    )


@router.post(
    "/confirm",
    tags=["configurations"],
    operation_id="confirmUploadCustomCodesCsv",
    response_model=UploadCustomCodesResponse,
)
async def confirm_upload_custom_codes_csv(
    configuration_id: UUID,
    body: ConfirmUploadCustomCodesInput,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
    logger: Logger = Depends(get_logger),
) -> UploadCustomCodesResponse:
    """
    Confirm and save custom codes from preview list.
    """
    if not body.custom_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No custom codes to confirm.",
        )

    jd = user.jurisdiction_id
    config = await get_configuration_by_id_db(
        id=configuration_id,
        jurisdiction_id=jd,
        db=db,
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found.",
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

    try:
        result = await add_bulk_custom_codes_to_configuration_db(
            config=config,
            custom_codes=[
                DbConfigurationCustomCode(
                    code=item.code,
                    system=item.system,
                    name=item.name,
                )
                for item in body.custom_codes
            ],
            user_id=user.id,
            db=db,
        )
    except Exception as e:
        logger.error("Bulk custom code insert failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to insert custom codes.",
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration.",
        )

    return UploadCustomCodesResponse(
        message="Successfully imported custom codes.",
        codes_processed=result.added_count,
        total_custom_codes_in_configuration=len(result.config.custom_codes),
        errors=None,
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
    sanitized_system = _sanitize_system_or_raise(
        updateInput.system, allowed=ALLOWED_CUSTOM_CODE_SYSTEMS
    )
    code_to_edit = [
        cc
        for cc in custom_codes
        if cc.system == sanitized_system.value
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
    new_system_value = (
        _sanitize_system_or_raise(
            updateInput.new_system, allowed=ALLOWED_CUSTOM_CODE_SYSTEMS
        )
        if updateInput.new_system
        else CodeSystem(existing_code.system)
    )
    updated_code = DbConfigurationCustomCode(
        code=updateInput.new_code or existing_code.code,
        name=updateInput.new_name or existing_code.name,
        system=new_system_value
        if isinstance(new_system_value, CodeSystem)
        else new_system_value,
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


class ValidateCustomCodeInput(BaseModel):
    """
    Input model when validating a config's custom code.
    """

    current_code: str | None
    desired_code: str


@dataclass
class ValidateCustomCodeResponse:
    """
    Validation response model.
    """

    valid: bool


@router.post(
    "/validate",
    response_model=ValidateCustomCodeResponse,
    tags=["configurations"],
    operation_id="validateCustomCodeFromConfiguration",
)
async def validate_custom_code(
    configuration_id: UUID,
    body: ValidateCustomCodeInput,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> ValidateCustomCodeResponse:
    """
    Determines whether a custom code update is valid or not.

    If the desired code is already associated with the configuration, then the update is
    invalid.

    Args:
        configuration_id (UUID): The configuration ID
        body (ValidateCustomCodeInput): Body including the code to validate
        user (DbUser, optional): The logged in user
        db (AsyncDatabaseConnection, optional): The database connection

    Returns:
        bool: Returns True if the code name has not been used, otherwise returns False
    """

    current_code = body.current_code
    desired_code = body.desired_code

    if current_code == desired_code:
        return ValidateCustomCodeResponse(valid=True)

    # find config
    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=user.jurisdiction_id, db=db
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found."
        )

    # Fetch all included conditions
    conditions = await get_included_conditions_db(
        included_conditions=config.included_conditions, db=db
    )

    # Flatten all codes from all included conditions and custom codes
    all_codes: set[str] = set()

    for c in conditions:
        all_codes.update(c.code for c in c.get_codes_from_all_systems())

    # Include custom codes from the configuration
    for custom_code in config.custom_codes:
        all_codes.add(custom_code.code)

    all_codes.discard(current_code)

    is_valid = desired_code not in all_codes

    return ValidateCustomCodeResponse(valid=is_valid)


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
