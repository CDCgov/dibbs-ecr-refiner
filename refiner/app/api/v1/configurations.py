import csv
import io
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from io import StringIO
from logging import Logger
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, field_validator

from app.core.exceptions import (
    FileProcessingError,
    XMLValidationError,
    ZipValidationError,
)
from app.db.configurations.activations.db import (
    activate_configuration_db,
    deactivate_configuration_db,
)
from app.db.users.db import get_user_by_id_db
from app.db.users.model import UserInfoBase
from app.services.configuration_locks import ConfigurationLock
from app.services.configurations import (
    get_canonical_url_to_highest_inactive_version_map,
)
from app.services.ecr.refine import get_file_size_reduction_percentage
from app.services.file_io import (
    create_refined_ecr_zip_in_memory,
    create_split_condition_filename,
    read_xml_zip,
)
from app.services.format import normalize_xml, strip_comments
from app.services.testing import inline_testing

from ...api.auth.middleware import get_logged_in_user
from ...api.v1.demo import XML_FILE_ERROR, ZIP_READING_ERROR
from ...api.validation.file_validation import validate_zip_file
from ...db.conditions.db import (
    get_condition_by_id_db,
    get_condition_codes_by_condition_id_db,
    get_conditions_db,
    get_included_conditions_db,
)
from ...db.conditions.model import DbConditionCoding
from ...db.configurations.db import (
    DbTotalConditionCodeCount,
    GetConfigurationResponseVersion,
    SectionUpdate,
    add_custom_code_to_configuration_db,
    associate_condition_codeset_with_configuration_db,
    delete_custom_code_from_configuration_db,
    disassociate_condition_codeset_with_configuration_db,
    edit_custom_code_from_configuration_db,
    get_configuration_by_id_db,
    get_configuration_versions_db,
    get_configurations_db,
    get_latest_config_db,
    get_total_condition_code_counts_by_configuration_db,
    insert_configuration_db,
    is_config_valid_to_insert_db,
    update_section_processing_db,
)
from ...db.configurations.model import (
    DbConfiguration,
    DbConfigurationCustomCode,
    DbConfigurationSectionProcessing,
    DbConfigurationStatus,
)
from ...db.demo.model import Condition
from ...db.pool import AsyncDatabaseConnection, get_db
from ...db.users.model import DbUser
from ...services.aws.s3 import (
    upload_configuration_payload,
    upload_current_version_file,
    upload_refined_ecr,
)
from ...services.configurations import (
    convert_config_to_storage_payload,
    get_config_payload_metadata,
)
from ...services.logger import get_logger
from ...services.sample_file import create_sample_zip_file, get_sample_zip_path
from ...services.xslt import (
    get_path_to_xslt_stylesheet,
    transform_xml_to_html,
)

router = APIRouter(prefix="/configurations")


@dataclass(frozen=True)
class GetConfigurationsResponse:
    """
    Model for a user-defined configuration.
    """

    id: UUID
    name: str
    status: DbConfigurationStatus


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

    # get all configs in a JD
    all_configs = await get_configurations_db(jurisdiction_id=jd, db=db)

    # active config by condition
    active_configs_map = {
        c.condition_canonical_url: c for c in all_configs if c.status == "active"
    }

    # draft config by condition
    draft_configs_map = {
        c.condition_canonical_url: c for c in all_configs if c.status == "draft"
    }

    # inactive config with the highest version by condition
    highest_version_inactive_configs_map: dict[str, DbConfiguration] = (
        get_canonical_url_to_highest_inactive_version_map(all_configs)
    )

    unique_urls = {c.condition_canonical_url for c in all_configs}
    response = []
    for key in unique_urls:
        has_active = key in active_configs_map
        has_draft = key in draft_configs_map
        has_inactive = key in highest_version_inactive_configs_map

        # Active
        if has_active:
            response.append(
                GetConfigurationsResponse(
                    id=active_configs_map[key].id,
                    name=active_configs_map[key].name,
                    status=active_configs_map[key].status,
                )
            )
        # Inactive
        elif has_inactive:
            response.append(
                GetConfigurationsResponse(
                    id=highest_version_inactive_configs_map[key].id,
                    name=highest_version_inactive_configs_map[key].name,
                    status=highest_version_inactive_configs_map[key].status,
                )
            )
        # Draft
        elif has_draft:
            response.append(
                GetConfigurationsResponse(
                    id=draft_configs_map[key].id,
                    name=draft_configs_map[key].name,
                    status=draft_configs_map[key].status,
                )
            )

    # TODO: What should the order be?
    return sorted(response, key=lambda r: r.name.lower())


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
    logger: Logger = Depends(get_logger),
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

    # check that there isn't already a draft config for the condition + JD
    if not await is_config_valid_to_insert_db(
        condition_canonical_url=condition.canonical_url, jurisdiction_id=jd, db=db
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Can't create configuration because a draft configuration for the condition already exists.",
        )

    latest_config = await get_latest_config_db(
        jurisdiction_id=jd, condition_canonical_url=condition.canonical_url, db=db
    )

    if not latest_config:
        logger.info(
            "Creating fresh draft config",
            extra={
                "condition": condition.display_name,
                "canonical_url": condition.canonical_url,
            },
        )
    else:
        logger.info(
            "Creating cloned draft config",
            extra={
                "condition": condition.display_name,
                "canonical_url": condition.canonical_url,
                "cloned_configuration_id": latest_config.id,
            },
        )

    config = await insert_configuration_db(
        condition=condition,
        user_id=user.id,
        jurisdiction_id=jd,
        config_to_clone=latest_config,
        db=db,
    )

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create configuration",
        )

    # acquire lock for new configuration
    success = await ConfigurationLock.acquire_lock(
        configuration_id=config.id,
        user_id=user.id,
        db=db,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to acquire lock for new configuration",
        )

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
class LockedByUser(UserInfoBase):
    """
    LockedByUser response to provide user information.
    """

    pass


@dataclass(frozen=True)
class GetConfigurationResponse:
    """
    Model for a configration response.
    """

    id: UUID
    draft_id: UUID | None
    is_draft: bool
    condition_id: UUID
    condition_canonical_url: str
    display_name: str
    status: DbConfigurationStatus
    code_sets: list[DbTotalConditionCodeCount]
    included_conditions: list[IncludedCondition]
    custom_codes: list[DbConfigurationCustomCode]
    section_processing: list[DbConfigurationSectionProcessing]
    deduplicated_codes: list[str]
    all_versions: list[GetConfigurationResponseVersion]
    version: int
    active_configuration_id: UUID | None
    active_version: int | None
    latest_version: int
    is_locked: bool
    locked_by: LockedByUser | None


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
    logger: Logger = Depends(get_logger),
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

    # get current lock
    lock = await ConfigurationLock.get_lock(configuration_id, db)
    # Only acquire lock if none or expired. Never override valid lock
    # from other user.
    if not lock or lock.expires_at.timestamp() <= datetime.now(UTC).timestamp():
        await ConfigurationLock.acquire_lock(
            configuration_id=configuration_id,
            user_id=user.id,
            db=db,
        )
        lock = await ConfigurationLock.get_lock(configuration_id, db)
    locked_by = None
    if lock and lock.expires_at.timestamp() > datetime.now(UTC).timestamp():
        try:
            user_obj = await get_user_by_id_db(lock.user_id, db)
            if user_obj:
                locked_by = LockedByUser(
                    id=user_obj.id, name=user_obj.username, email=user_obj.email
                )
            else:
                locked_by = None
                logger.warning(f"Could not find user with ID: {lock.user_id}")
        except Exception as e:
            locked_by = None
            logger.error(f"Error fetching user for lock: {e}")

    # Fetch all included conditions
    conditions = await get_included_conditions_db(
        included_conditions=config.included_conditions, db=db
    )

    # Flatten all codes from all included conditions and custom codes
    all_codes = set()

    for c in conditions:
        for code_list in [
            getattr(c, "snomed_codes", []),
            getattr(c, "loinc_codes", []),
            getattr(c, "icd10_codes", []),
            getattr(c, "rxnorm_codes", []),
        ]:
            for coding in code_list:
                if isinstance(coding, DbConditionCoding) and hasattr(coding, "code"):
                    all_codes.add(coding.code)

    # Include custom codes from the configuration
    for custom_code in getattr(config, "custom_codes", []):
        if isinstance(custom_code, DbConfigurationCustomCode) and hasattr(
            custom_code, "code"
        ):
            all_codes.add(custom_code.code)

    # Final flattened, deduplicated list of codes
    deduplicated_codes = sorted(all_codes)

    config_condition_info = await get_total_condition_code_counts_by_configuration_db(
        config_id=config.id, db=db
    )

    # precomputed set of included_conditions ids
    included_ids = {c.id for c in config.included_conditions}

    # Fetch all conditions from the database
    all_conditions = await get_conditions_db(db=db)

    latest_config = await get_latest_config_db(
        jurisdiction_id=jd,
        condition_canonical_url=config.condition_canonical_url,
        db=db,
    )

    # Build IncludedCondition objects, marking which are associated
    included_conditions = []
    for condition in all_conditions:
        is_associated = condition.id in included_ids
        included_conditions.append(
            IncludedCondition(
                id=condition.id,
                display_name=condition.display_name,
                canonical_url=condition.canonical_url,
                version=condition.version,
                associated=is_associated,
            )
        )

    all_versions = await get_configuration_versions_db(
        jurisdiction_id=jd,
        condition_canonical_url=config.condition_canonical_url,
        db=db,
    )

    active_config = next((v for v in all_versions if v.status == "active"), None)
    draft_config = next((v for v in all_versions if v.status == "draft"), None)

    draft_id = draft_config.id if draft_config is not None else None
    is_draft = draft_id == config.id
    active_version = active_config.version if active_config is not None else None
    active_configuration_id = active_config.id if active_config is not None else None
    latest_version = latest_config.version if latest_config is not None else 0

    is_locked = locked_by is not None and locked_by.id != user.id

    return GetConfigurationResponse(
        id=config.id,
        draft_id=draft_id,
        is_draft=is_draft,
        condition_id=config.condition_id,
        condition_canonical_url=config.condition_canonical_url,
        display_name=config.name,
        status=config.status,
        code_sets=config_condition_info,
        included_conditions=included_conditions,
        custom_codes=config.custom_codes,
        section_processing=config.section_processing,
        deduplicated_codes=deduplicated_codes,
        all_versions=all_versions,
        version=config.version,
        active_version=active_version,
        active_configuration_id=active_configuration_id,
        latest_version=latest_version,
        locked_by=locked_by,
        is_locked=is_locked,
    )


@router.get(
    "/{configuration_id}/export",
    tags=["configurations"],
    operation_id="getConfigurationExport",
    response_class=Response,
)
async def get_configuration_export(
    configuration_id: UUID,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> Response:
    """
    Create a CSV export of a configuration and all associated codes.
    """

    # --- Validate configuration ---
    jd = user.jurisdiction_id
    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=jd, db=db
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found.",
        )

    lock = await ConfigurationLock.get_lock(configuration_id, db)
    if (
        lock
        and str(lock.user_id) != str(user.id)
        and lock.expires_at.timestamp() > datetime.now(UTC).timestamp()
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{user.username}/{user.email} currently has this configuration open.",
        )
    # Determine included conditions
    included_conditions = await get_included_conditions_db(
        included_conditions=config.included_conditions, db=db
    )

    # Write CSV to StringIO (text)
    with StringIO() as csv_text:
        writer = csv.writer(csv_text)
        writer.writerow(
            [
                "Code Type",
                "Code System",
                "Code",
                "Display Name",
            ]
        )
        for cond in included_conditions:
            codes = await get_condition_codes_by_condition_id_db(id=cond.id, db=db)
            for code_obj in codes:
                writer.writerow(
                    [
                        "TES condition grouper code",
                        code_obj.system or "",
                        code_obj.code or "",
                        code_obj.description or "",
                    ]
                )
        for custom in config.custom_codes or []:
            writer.writerow(
                [
                    "Custom code",
                    custom.system or "",
                    custom.code or "",
                    custom.name or "",
                ]
            )

        csv_bytes = csv_text.getvalue().encode("utf-8")

    # Replace spaces with underscores in the config name
    safe_name = config.name.replace(" ", "_")

    # Format current date/time as YYMMDD HH:MM:SS
    timestamp = datetime.now().strftime("%m%d%y_%H:%M:%S")

    # Build final filename
    filename = f"{safe_name}_Code Export_{timestamp}.csv"

    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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

    id: UUID


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


class AddCustomCodeInput(BaseModel):
    """
    Input model for adding a custom code to a configuration.
    """

    code: str
    system: Literal["loinc", "snomed", "icd-10", "rxnorm", "other"]
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
    elif lower_system == "other":
        return "Other"

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


def _upload_to_s3():
    """
    Returns a function to upload an eICR/RR pair .zip to S3.
    """
    return upload_refined_ecr


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
    create_output_zip: Callable[..., tuple[str, io.BytesIO]] = Depends(
        lambda: create_refined_ecr_zip_in_memory
    ),
    upload_refined_files_to_s3: Callable[
        [UUID, io.BytesIO, str, Logger], str
    ] = Depends(_upload_to_s3),
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
    sample_zip_path: Path = Depends(get_sample_zip_path),
    logger: Logger = Depends(get_logger),
) -> ConfigurationTestResponse:
    """
    Runs an inline test of a given configuration against an eICR/RR pair.

    This endpoint orchestrates the validation and refinement process by:
    1. Handling file input, either from a user upload or a default sample file.
    2. Calling the `inline_testing` service, which validates that the specified
       configuration's condition is reportable in the provided file.
    3. Handling the service response:
        - If validation fails, raises a 400 Bad Request with a specific error.
        - If successful, proceeds with the returned refined document.
    4. Packaging the original eICR, RR, and the single refined eICR into a
       new in-memory zip archive.
    5. Uploading the archive to S3 and generating a pre-signed download URL.
    6. Returning a `ConfigurationTestResponse` with the download URL and details
       of the successful refinement.

    Args:
        id: The ID of the configuration to test.
        uploaded_file: An optional user-provided zip file with an eICR and RR.
        create_output_zip: Dependency to create a zip archive in memory.
        upload_refined_files_to_s3: Dependency to upload the archive to S3.
        user: The authenticated user making the request.
        db: The database connection.
        sample_zip_path: Path to the default sample zip file.
        logger: The application logger.

    Returns:
        A response object containing the original eICR, a URL to download the
        zipped results, and details about the refined condition.
    """

    # STEP 1:
    # handle file upload
    if not sample_zip_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to find sample zip file to download.",
        )

    if uploaded_file:
        try:
            file = await validate_zip_file(file=uploaded_file)
        except ZipValidationError as e:
            logger.error(
                msg="ZipValidationError in validate_zip_file", extra={"error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ZIP archive cannot be read. CDA_eICR.xml and CDA_RR.xml files must be present.",
            )
        logger.info(
            msg="Running inline test using user-provided file",
            extra={"file": file.filename},
        )
    else:
        file = create_sample_zip_file(sample_zip_path=sample_zip_path)
        logger.info(
            msg="Running inline test using sample file", extra={"file": file.filename}
        )

    try:
        # STEP 2:
        # read xml and call the service layer
        original_xml_files = await read_xml_zip(file)
    except ZipValidationError as e:
        logger.error(msg="ZipValidationError in read_xml_zip", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ZIP archive cannot be read. CDA_eICR.xml and CDA_RR.xml files must be present.",
        )
    except FileProcessingError as e:
        logger.error(msg="FileProcessingError in read_xml_zip", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ZIP_READING_ERROR,
        )

    # get the user's jurisdiction_id to pass to inline_testing
    jd = user.jurisdiction_id

    # get the DbConfiguration row for the jurisdiction
    configuration = await get_configuration_by_id_db(id=id, jurisdiction_id=jd, db=db)
    if not configuration:
        raise HTTPException(
            status_code=404, detail="Configuration not found for jurisdiction."
        )

    # get the primary DbCondition row that is linked to the DbConfiguration for the jurisdiction
    primary_condition = await get_condition_by_id_db(
        id=configuration.condition_id, db=db
    )
    if not primary_condition:
        raise HTTPException(
            status_code=404, detail="Primary condition not found for configuration."
        )

    # if included_conditions is a list greater than 1, then fetch all conditions
    # in the list (which includes the primary condition) for the payload and
    # store the corresponding trace info
    if len(configuration.included_conditions) > 1:
        all_conditions_for_configuration = await get_included_conditions_db(
            included_conditions=configuration.included_conditions, db=db
        )
    else:
        all_conditions_for_configuration = [primary_condition]

    # call the testing service
    # business logic around **how** inline testing works is in services/testing.py
    try:
        result = await inline_testing(
            xml_files=original_xml_files,
            configuration=configuration,
            primary_condition=primary_condition,
            all_conditions=all_conditions_for_configuration,
            jurisdiction_id=jd,
            logger=logger,
        )
    except XMLValidationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=XML_FILE_ERROR
        )

    # STEP 3:
    # handle the service layer response
    if result["configuration_does_not_match_conditions"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["configuration_does_not_match_conditions"],
        )

    refined_document = result["refined_document"]
    if refined_document is None:
        logger.error(
            msg="Internal logic error: inline_testing returned no error but also no refined eICR."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during the refinement process.",
        )

    condition_obj = refined_document.reportable_condition

    # STEP 4:
    # prepare files for zip and s3 upload
    s3_file_package = []
    s3_file_package.append(("CDA_eICR.xml", original_xml_files.eicr))
    s3_file_package.append(("CDA_RR.xml", original_xml_files.rr))

    eicr_filename, rr_filename = create_split_condition_filename(
        condition_name=condition_obj.display_name,
        condition_code=condition_obj.code,
    )

    s3_file_package.append((rr_filename, refined_document.refined_rr))
    # Generate HTML from refined XML
    try:
        xslt_stylesheet_path = get_path_to_xslt_stylesheet()
        html_bytes = transform_xml_to_html(
            refined_document.refined_eicr.encode("utf-8"), xslt_stylesheet_path, logger
        )
        filename_html = eicr_filename.replace(".xml", ".html")
        s3_file_package.append((filename_html, html_bytes.decode("utf-8")))
        logger.info(
            f"Successfully transformed XML to HTML for: {eicr_filename}",
            extra={
                "condition_code": condition_obj.code,
                "condition_name": condition_obj.display_name,
            },
        )
    except Exception as e:
        if "XSLTTransformationError" in str(type(e)):
            logger.error(
                f"Failed to transform XML to HTML for: {eicr_filename}",
                extra={
                    "condition_code": condition_obj.code,
                    "condition_name": condition_obj.display_name,
                    "error": str(e),
                },
            )
        else:
            logger.error(
                f"Unexpected error during XML to HTML transformation for: {eicr_filename}",
                extra={
                    "condition_code": condition_obj.code,
                    "condition_name": condition_obj.display_name,
                    "error": str(e),
                },
            )
        # Continue with XML only; do not include HTML file for this condition

    try:
        output_file_name, output_zip_buffer = create_output_zip(
            files=s3_file_package,
        )
    except Exception as e:
        logger.error(msg="Error in create_output_zip", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error creating the results ZIP file during S3 packaging process.",
        )
    try:
        presigned_s3_url = await run_in_threadpool(
            upload_refined_files_to_s3,
            user.id,
            output_zip_buffer,
            output_file_name,
            logger,
        )
    except Exception as e:
        logger.error(msg="Error uploading to S3.", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error uploading ZIP file to S3.",
        )

    # STEP 5:
    # construct and return the final response
    formatted_unrefined_eicr = strip_comments(normalize_xml(original_xml_files.eicr))
    formatted_refined_eicr = strip_comments(
        normalize_xml(refined_document.refined_eicr)
    )
    formatted_refined_rr = strip_comments(normalize_xml(refined_document.refined_rr))

    return ConfigurationTestResponse(
        original_eicr=formatted_unrefined_eicr,
        refined_download_url=presigned_s3_url,
        condition=Condition(
            code=condition_obj.code,
            display_name=condition_obj.display_name,
            refined_eicr=formatted_refined_eicr,
            refined_rr=formatted_refined_rr,
            stats=[
                f"eICR file size reduced by {
                    get_file_size_reduction_percentage(
                        unrefined_eicr=formatted_unrefined_eicr,
                        refined_eicr=formatted_refined_eicr,
                    )
                }%",
            ],
        ),
    )


class UpdateSectionProcessingEntry(BaseModel):
    """
    Model for a single section processing update.
    """

    code: str
    action: Literal["retain", "refine", "remove"]


class UpdateSectionProcessingPayload(BaseModel):
    """
    Payload for updating section processing entries.
    """

    sections: list[UpdateSectionProcessingEntry]


@dataclass(frozen=True)
class UpdateSectionProcessingResponse:
    """
    Response model for updating section processing entries.
    """

    message: str


@router.patch(
    "/{configuration_id}/section-processing",
    response_model=UpdateSectionProcessingResponse,
    tags=["configurations"],
    operation_id="updateConfigurationSectionProcessing",
)
async def update_section_processing(
    configuration_id: UUID,
    payload: UpdateSectionProcessingPayload,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> UpdateSectionProcessingResponse:
    """
    Update one or more section_processing entries for a configuration.

    Args:
        configuration_id (UUID): ID of the configuration to update
        payload (UpdateSectionProcessingPayload): List of section updates with code and action
        user (DbUser): The logged-in user
        db (AsyncDatabaseConnection): Database connection

    Raises:
        HTTPException: 404 if configuration isn't found
        HTTPException: 409 if configuration is not a draft and therefore not editable
        HTTPException: 500 if section processing can't be updated

    Returns:
        UpdateSectionProcessingResponse: The message to show the user
    """

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

    if config.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trying to update a non-draft configuration",
        )
    await ConfigurationLock.raise_if_locked_by_other(
        configuration_id,
        user.id,
        username=user.username,
        email=user.email,
        db=db,
    )

    # convert payload to DB-friendly format (SectionUpdate dataclasses)
    section_updates = [
        SectionUpdate(code=s.code, action=s.action) for s in payload.sections
    ]

    try:
        updated_config = await update_section_processing_db(
            config=config, section_updates=section_updates, user_id=user.id, db=db
        )
    except ValueError as e:
        # DB layer validation error -> bad request
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration.",
        )

    return UpdateSectionProcessingResponse(message="Section processed successfully.")


@dataclass(frozen=True)
class ConfigurationStatusUpdateResponse:
    """
    Response model for updating the status a configuration.
    """

    configuration_id: UUID
    status: DbConfigurationStatus


@router.patch(
    "/{configuration_id}/activate",
    response_model=ConfigurationStatusUpdateResponse,
    tags=["configurations"],
    operation_id="activateConfiguration",
)
async def activate_configuration(
    configuration_id: UUID,
    db: AsyncDatabaseConnection = Depends(get_db),
    logger: Logger = Depends(get_logger),
    user: DbUser = Depends(get_logged_in_user),
) -> ConfigurationStatusUpdateResponse:
    """
    Activate the specified configuration.

    Args:
        configuration_id (UUID): ID of the configuration to update
        user (DbUser): The logged-in user
        logger (Logger): The standard logger
        db (AsyncDatabaseConnection): Database connection

    Raises:
        HTTPException: 400 if configuration can't be activated because of its current state
        HTTPException: 404 if configuration can't be found
        HTTPException: 500 if configuration can't be activated by the server

    Returns:
        ActivateConfigurationResponse: Metadata about the activated condition for confirmation
    """

    config_to_activate = await get_configuration_by_id_db(
        id=configuration_id,
        jurisdiction_id=user.jurisdiction_id,
        db=db,
    )

    if not config_to_activate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration to activate can't be found.",
        )

    if config_to_activate.status == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configuration is already active.",
        )

    # Convert the config to a form that can be put into object storage
    config_payload = await convert_config_to_storage_payload(
        configuration=config_to_activate,
        db=db,
    )

    if not config_payload:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration payload object could not be created.",
        )

    # Get the config's metadata
    config_metadata = await get_config_payload_metadata(
        configuration=config_to_activate, logger=logger, db=db
    )

    if not config_metadata:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration metadata object could not be created.",
        )

    # Write the config data to S3 and get the URLs back
    s3_urls = await run_in_threadpool(
        upload_configuration_payload, config_payload, config_metadata
    )

    # Activate config in the database
    active_config = await activate_configuration_db(
        configuration_id=config_to_activate.id,
        activated_by_user_id=user.id,
        canonical_url=config_to_activate.condition_canonical_url,
        jurisdiction_id=user.jurisdiction_id,
        s3_urls=s3_urls,
        db=db,
    )

    if not active_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration could not be activated.",
        )

    # Activation files have been written to S3 and the database record has been updated.
    # We can now make a new current.json file for the newly activated version.
    await run_in_threadpool(upload_current_version_file, s3_urls, active_config.version)

    return ConfigurationStatusUpdateResponse(
        configuration_id=active_config.id, status=active_config.status
    )


@router.patch(
    "/{configuration_id}/deactivate",
    response_model=ConfigurationStatusUpdateResponse,
    tags=["configurations"],
    operation_id="deactivateConfiguration",
)
async def deactivate_configuration(
    configuration_id: UUID,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> ConfigurationStatusUpdateResponse:
    """
    Deactivate the specified configuration.

    Args:
        configuration_id (UUID): ID of the configuration to update
        user (DbUser): The logged-in user
        db (AsyncDatabaseConnection): Database connection

    Raises:
        HTTPException: 400 if configuration can't be deactivated because of its current state
        HTTPException: 404 if configuration can't be found
        HTTPException: 500 if configuration can't be deactivated by the server

    Returns:
        ConfigurationStatusUpdateResponse: Metadata about the activated condition for confirmation
    """
    config_to_deactivate = await get_configuration_by_id_db(
        id=configuration_id,
        jurisdiction_id=user.jurisdiction_id,
        db=db,
    )

    if not config_to_deactivate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration to deactivate can't be found.",
        )

    if config_to_deactivate.status == "inactive":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configuration is already inactive.",
        )

    if config_to_deactivate.status == "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate a draft configuration.",
        )

    # Try updating `current.json` first
    s3_urls = config_to_deactivate.s3_urls
    await run_in_threadpool(upload_current_version_file, s3_urls, None)

    deactivated_config = await deactivate_configuration_db(
        configuration_id=config_to_deactivate.id,
        user_id=user.id,
        jurisdiction_id=user.jurisdiction_id,
        db=db,
    )

    if not deactivated_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration can't be deactivated.",
        )

    return ConfigurationStatusUpdateResponse(
        configuration_id=deactivated_config.id, status=deactivated_config.status
    )


@router.post(
    "/{configuration_id}/release-lock",
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
