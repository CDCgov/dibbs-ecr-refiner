import csv
import io
from dataclasses import dataclass
from logging import Logger
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.auth.middleware import get_logged_in_user
from app.api.v1.configurations.custom_codes.model import (
    AddCustomCodeInput,
    ConfirmUploadCustomCodesInput,
    CustomCodeResponse,
    UploadCustomCodesCsvInput,
    UploadCustomCodesPreviewItem,
)
from app.db.code_systems.db import (
    get_code_system_by_id_db,
    get_code_systems_db,
)
from app.db.code_systems.model import DbCodeSystem
from app.db.conditions.db import get_included_conditions_db
from app.db.configurations.custom_codes.db import (
    delete_custom_codes_db,
    edit_custom_code_db,
    get_custom_code_by_id_db,
    get_custom_codes_by_configuration_id_db,
    insert_custom_code_db,
    insert_custom_codes_db,
)
from app.db.configurations.custom_codes.model import DbCustomCode
from app.db.configurations.db import (
    get_configuration_by_id_db,
)
from app.db.configurations.model import DbTotalConditionCodeCount
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.code_systems import (
    find_code_system_by_display_name,
    find_code_system_by_id_or_raise,
    get_allowed_code_system_keys,
)
from app.services.configuration_locks import ConfigurationLock
from app.services.logger import get_logger
from app.services.terminology import CodeSystemKey

router = APIRouter(prefix="/{configuration_id}/custom-codes")


@router.get(
    "/{id}",
    response_model=CustomCodeResponse,
    tags=["configurations"],
    operation_id="getCustomCode",
)
async def get_custom_code(
    configuration_id: UUID,
    id: UUID,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> CustomCodeResponse:
    """
    Fetch a custom code by its ID.

    Args:
        configuration_id (UUID): The associated configuration ID
        id (UUID): The custom code ID
        user (DbUser): The logged-in user
        db (AsyncDatabaseConnection): The database connection

    Raises:
        HTTPException: 404 if configuration can't be found

    Returns:
        CustomCodeResponse: The custom code response object
    """

    # find config
    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=user.jurisdiction_id, db=db
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found."
        )

    code = await get_custom_code_by_id_db(id=id, db=db)

    if not code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find custom code with ID: {id}.",
        )

    systems = await get_code_systems_db(db=db)

    return CustomCodeResponse(
        id=code.id,
        display=code.display,
        code=code.code,
        system_id=code.system_id,
        system_name=find_code_system_by_id_or_raise(
            id=code.system_id, systems=systems
        ).display_name,
    )


@dataclass(frozen=True)
class ConfigurationCustomCodeResponse:
    """
    Configuration response for custom code operations (add/edit/delete).
    """

    id: UUID
    display_name: str
    code_sets: list[DbTotalConditionCodeCount]
    custom_codes: list[CustomCodeResponse]


@router.post(
    "",
    response_model=CustomCodeResponse,
    tags=["configurations"],
    operation_id="addCustomCodeToConfiguration",
)
async def add_custom_code(
    configuration_id: UUID,
    body: AddCustomCodeInput,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> CustomCodeResponse:
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

    # find config
    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=user.jurisdiction_id, db=db
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
    system = await get_code_system_by_id_db(id=body.system_id, db=db)
    if not system:
        allowed_keys = await get_allowed_code_system_keys(db=db)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"System must be one of [{allowed_keys}]",
        )

    added_code = await insert_custom_code_db(
        config=config,
        code=body.code.strip(),
        display_name=body.display,
        system_id=body.system_id,
        user_id=user.id,
        db=db,
    )

    if not added_code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add custom code.",
        )

    systems = await get_code_systems_db(db=db)

    return CustomCodeResponse(
        id=added_code.id,
        display=added_code.display,
        code=added_code.code,
        system_id=added_code.system_id,
        system_name=find_code_system_by_id_or_raise(
            id=added_code.system_id, systems=systems
        ).display_name,
    )


class UploadCustomCodesPreviewResponse(BaseModel):
    """Validated CSV preview for delayed confirmation; only valid if preview."""

    preview_items: list[UploadCustomCodesPreviewItem]
    codes_processed: int | None = None
    total_custom_codes_in_configuration: int | None = None
    code_systems: list[DbCodeSystem]


def _create_csv_reader(
    body: UploadCustomCodesCsvInput,
):
    decoded = body.csv_text
    return csv.DictReader(io.StringIO(decoded))


def _validate_required_columns_or_raise(csv_reader: csv.DictReader[str]):
    headers = set(csv_reader.fieldnames or [])
    required_headers = {"code_system", "code", "display_name"}

    if not headers.issubset(required_headers):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV must contain headers: code, code_system, display_name",
        )


async def _get_requested_config_or_raise(
    configuration_id: UUID,
    user: DbUser,
    db: AsyncDatabaseConnection,
):
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
    return config


def _validate_csv_upload_row(
    row: dict, supported_systems: list[DbCodeSystem]
) -> tuple[str, DbCodeSystem, str] | list[str]:
    code = (row.get("code") or "").strip()
    code_system_raw = (row.get("code_system") or "").strip()
    name = (row.get("display_name") or "").strip()

    system_names = [s.display_name for s in supported_systems]

    # get the DbCodeSystem that matches CSV system
    matching_system = find_code_system_by_display_name(
        systems=supported_systems, display_name=code_system_raw
    )

    row_errors: list[str] = []

    if not code:
        row_errors.append("Missing code")
    if not name:
        row_errors.append("Missing display_name")
    if not code_system_raw:
        row_errors.append("Missing code_system")
    elif not matching_system:
        allowed_systems_str = ", ".join(system_names)
        row_errors.append(
            f"Invalid system: {code_system_raw}. "
            f"[code_system] must be one of [{allowed_systems_str}]"
        )

    if row_errors or not matching_system:
        return row_errors

    return (code, matching_system, name)


def _check_row_response_for_duplicates(
    code: str,
    system: DbCodeSystem,
    custom_codes: list[DbCustomCode],
    codes_seen_so_far: set,
) -> tuple[str, CodeSystemKey] | list[str]:
    row_errors = []
    custom_code_keys = [(cc.code, str(cc.system_id)) for cc in custom_codes]
    code_key = (code, str(system.id))

    if code_key in custom_code_keys:
        row_errors.append("Duplicate: matches existing custom code")
    if code_key in codes_seen_so_far:
        row_errors.append("Duplicate: matches uploaded batch code")
    if row_errors:
        return row_errors

    return code_key


@router.post(
    "/upload",
    tags=["configurations"],
    operation_id="uploadCustomCodesCsv",
    response_model=UploadCustomCodesPreviewResponse,
)
async def upload_custom_codes_csv(
    configuration_id: UUID,
    body: UploadCustomCodesCsvInput,
    db: AsyncDatabaseConnection = Depends(get_db),
    user: DbUser = Depends(get_logged_in_user),
    logger: Logger = Depends(get_logger),
) -> UploadCustomCodesPreviewResponse:
    """
    Accepts a CSV payload in JSON body.

    Expected CSV headers:
        code,code_system,display_name

    Returns:
        UploadCustomCodesResponse
    """

    if body.filename and not body.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV.",
        )

    csv_reader = _create_csv_reader(body)
    _validate_required_columns_or_raise(csv_reader)

    config = await _get_requested_config_or_raise(
        configuration_id=configuration_id, db=db, user=user
    )

    supported_systems = await get_code_systems_db(db=db)

    preview_items: list[UploadCustomCodesPreviewItem] = []
    errors: list[dict] = []

    custom_codes = await get_custom_codes_by_configuration_id_db(
        configuration_id=config.id, db=db
    )
    codes_seen_so_far: set[tuple[str, CodeSystemKey]] = set()

    for row_number, row in enumerate(csv_reader, start=2):
        row_errors = []
        row_response = _validate_csv_upload_row(
            row, supported_systems=supported_systems
        )
        if isinstance(row_response, list):
            row_errors.extend(row_response)
            errors.append({"row": row_number, "error": ", ".join(row_errors)})
            continue

        (code, row_system, name) = row_response

        duplicate_check_response = _check_row_response_for_duplicates(
            code=code,
            system=row_system,
            custom_codes=custom_codes,
            codes_seen_so_far=codes_seen_so_far,
        )
        if isinstance(duplicate_check_response, list):
            row_errors.extend(duplicate_check_response)
            errors.append({"row": row_number, "error": ", ".join(row_errors)})
            continue

        codes_seen_so_far.add(duplicate_check_response)
        preview_items.append(
            UploadCustomCodesPreviewItem(
                id=uuid4(),
                code=code,
                system_id=row_system.id,
                system_name=row_system.display_name,
                display=name,
                row=row_number,
            )
        )

    code_systems = await get_code_systems_db(db=db)
    if errors:
        logger.error("CSV upload errors", extra={"errors": errors})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors},
        )
    if not preview_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "errors": [{"row": 0, "error": "No valid rows"}],
            },
        )
    return UploadCustomCodesPreviewResponse(
        preview_items=preview_items,
        codes_processed=len(preview_items),
        total_custom_codes_in_configuration=len(config.custom_codes)
        + len(preview_items),
        code_systems=code_systems,
    )


@router.post(
    "/confirm",
    tags=["configurations"],
    operation_id="confirmUploadCustomCodesCsv",
    response_model=list[CustomCodeResponse],
)
async def confirm_upload_custom_codes_csv(
    configuration_id: UUID,
    body: ConfirmUploadCustomCodesInput,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
    logger: Logger = Depends(get_logger),
) -> list[CustomCodeResponse]:
    """
    Confirm and save custom codes from preview list.
    """

    config = await get_configuration_by_id_db(
        id=configuration_id,
        jurisdiction_id=user.jurisdiction_id,
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

    code_systems = await get_code_systems_db(db=db)

    try:
        inserted_codes = await insert_custom_codes_db(
            config=config,
            code_systems=code_systems,
            custom_codes=body.custom_codes,
            user_id=user.id,
            db=db,
        )
    except Exception as e:
        logger.error("Bulk custom code insert failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to insert custom codes.",
        )

    if not inserted_codes:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration.",
        )

    return [
        CustomCodeResponse(
            id=c.id,
            display=c.display,
            code=c.code,
            system_id=c.system_id,
            system_name=find_code_system_by_id_or_raise(
                id=c.system_id, systems=code_systems
            ).display_name,
        )
        for c in inserted_codes
    ]


@router.delete(
    "/{id}",
    response_model=CustomCodeResponse,
    tags=["configurations"],
    operation_id="deleteCustomCodeFromConfiguration",
)
async def delete_custom_code(
    id: UUID,
    configuration_id: UUID,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> CustomCodeResponse:
    """
    Delete a custom code from a configuration.

    Args:
        configuration_id (UUID): The ID of the configuration to modify.
        id (str): The ID of the custom code.
        user (dict[str, Any]): The logged-in user.
        db (AsyncDatabaseConnection): The database connection.

    Raises:
        HTTPException: 400 if id is not provided
        HTTPException: 404 if configuration can't be found
        HTTPException: 409 if configuration is not a draft and therefore not editable
        HTTPException: 500 if configuration can't be updated

    Returns:
        ConfigurationCustomCodeResponse: The updated configuration
    """

    # find config
    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=user.jurisdiction_id, db=db
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

    custom_code = await get_custom_code_by_id_db(id=id, db=db)

    if not custom_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to find custom code to delete with ID: {id}",
        )

    deleted_codes = await delete_custom_codes_db(
        config=config, ids=[custom_code.id], user_id=user.id, db=db
    )

    if len(deleted_codes) < 1:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete custom code.",
        )

    deleted_code = deleted_codes[0]

    systems = await get_code_systems_db(db=db)

    return CustomCodeResponse(
        id=deleted_code.id,
        display=deleted_code.display,
        code=deleted_code.code,
        system_id=deleted_code.system_id,
        system_name=find_code_system_by_id_or_raise(
            id=deleted_code.system_id, systems=systems
        ).display_name,
    )


class BulkDeleteCustomCodesInput(BaseModel):
    """
    Input model for a bulk custom codes deletion request.
    """

    ids: list[UUID]
    ids_to_skip: list[UUID]
    delete_all: bool


@router.post(
    "/bulk-delete",
    response_model=list[CustomCodeResponse],
    tags=["configurations"],
    operation_id="deleteCustomCodes",
)
async def bulk_delete_custom_codes(
    configuration_id: UUID,
    body: BulkDeleteCustomCodesInput,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> list[CustomCodeResponse]:
    """
    Deletes custom codes in bulk for a given configuration.

    Args:
        configuration_id (UUID): The ID of the configuration to modify.
        body (BulkDeleteCustomCodesInput): The input body containing IDs of the custom codes.
        user (DbUser): The logged-in user.
        db (AsyncDatabaseConnection): The database connection.

    Raises:
        HTTPException: 404 if configuration can't be found
        HTTPException: 409 if configuration is not a draft and therefore not editable
        HTTPException: 500 if configuration can't be updated

    Returns:
        ConfigurationCustomCodeResponse: The updated configuration
    """

    # find config
    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=user.jurisdiction_id, db=db
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

    deleted_codes = await delete_custom_codes_db(
        config=config,
        ids=body.ids,
        user_id=user.id,
        db=db,
        ids_to_skip=body.ids_to_skip,
        delete_all=body.delete_all,
    )

    if len(deleted_codes) < 1:
        return []

    systems = await get_code_systems_db(db=db)

    return [
        CustomCodeResponse(
            id=deleted_code.id,
            display=deleted_code.display,
            code=deleted_code.code,
            system_id=deleted_code.system_id,
            system_name=find_code_system_by_id_or_raise(
                id=deleted_code.system_id, systems=systems
            ).display_name,
        )
        for deleted_code in deleted_codes
    ]


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
        bool: Returns True if the code has not been used, otherwise returns False
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

    # Using the same code is valid
    if current_code:
        all_codes.discard(current_code)

    is_valid = desired_code not in all_codes

    return ValidateCustomCodeResponse(valid=is_valid)


class UpdateCustomCodeInput(BaseModel):
    """
    Input model when updating a config's custom code.
    """

    id: UUID
    system_id: UUID
    code: str
    display: str


@router.put(
    "",
    response_model=CustomCodeResponse,
    tags=["configurations"],
    operation_id="editCustomCodeFromConfiguration",
)
async def edit_custom_code(
    configuration_id: UUID,
    body: UpdateCustomCodeInput,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> CustomCodeResponse:
    """
    Modify a configuration's custom code based on system_key/code pair.

    Args:
        configuration_id (UUID): The ID of the configuration to modify.
        body (UpdateCustomCodeInput): User-provided object containing custom code info.
        user (dict[str, Any]): The logged-in user.
        db (AsyncDatabaseConnection): The database connection.
        logger (Logger): The system logger.

    Raises:
        HTTPException: 409 if configuration is not a draft and therefore not editable
        HTTPException: 500 if the configuration can't be updated

    Returns:
        ConfigurationCustomCodeResponse: The updated configuration.
    """

    # find config
    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=user.jurisdiction_id, db=db
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

    custom_code = await get_custom_code_by_id_db(id=body.id, db=db)

    if not custom_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find custom code with ID {body.id}",
        )

    systems = await get_code_systems_db(db=db)
    custom_code_system = find_code_system_by_id_or_raise(
        id=body.system_id, systems=systems
    )

    edited_code = await edit_custom_code_db(
        config=config,
        custom_code=custom_code,
        user_id=user.id,
        code=body.code,
        system=custom_code_system,
        display=body.display,
        db=db,
    )

    if not edited_code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update custom code.",
        )

    return CustomCodeResponse(
        id=edited_code.id,
        display=edited_code.display,
        code=edited_code.code,
        system_id=edited_code.system_id,
        system_name=find_code_system_by_id_or_raise(
            id=edited_code.system_id, systems=systems
        ).display_name,
    )
