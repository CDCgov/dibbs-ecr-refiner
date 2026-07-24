from datetime import UTC, datetime
from logging import Logger
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.api.auth.middleware import get_logged_in_user
from app.core.config import ENVIRONMENT
from app.db.conditions.db import (
    get_condition_by_id_db,
    get_condition_display_name_by_id_db,
)
from app.db.configurations.db import (
    get_configuration_by_id_db,
    get_configurations_summary_db,
    get_total_condition_code_counts_by_configuration_db,
)
from app.db.configurations.model import (
    DbConfigurationCustomCode,
)
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.db import get_user_by_id_db
from app.db.users.model import DbUser
from app.services.aws.s3 import SerializedFiles, get_serialized_files
from app.services.code_systems import get_all_code_systems_by_key
from app.services.configuration_locks import ConfigurationLock
from app.services.configurations import (
    create_configuration_service,
    format_section_naming,
    get_configuration_service,
)
from app.services.logger import get_logger

from .model import (
    CreateConfigInput,
    CreateConfigurationResponse,
    CustomCodes,
    GetConfigurationResponse,
    GetConfigurationsResponse,
    LockedByUser,
)

router = APIRouter()


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
    summary_response = await get_configurations_summary_db(
        jurisdiction_id=user.jurisdiction_id, db=db
    )

    return [
        GetConfigurationsResponse(
            id=c.id,
            name=c.name,
            status=c.status,
        )
        for c in summary_response
    ]


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
    config = await create_configuration_service(
        condition_id=body.condition_id,
        user_id=user.id,
        jurisdiction_id=user.jurisdiction_id,
        db=db,
        logger=logger,
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


@router.get(
    "/{configuration_id}/serialized",
    response_model=SerializedFiles,
    tags=["configurations"],
    operation_id="getSerializedConfiguration",
)
async def get_serialized_configuration(
    configuration_id: UUID,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
    logger: Logger = Depends(get_logger),
) -> SerializedFiles:
    """
    Given an active configuration ID, fetches and returns the serialized configuration file content from S3.

    Args:
        configuration_id (UUID): The active configuration ID
        user (DbUser): The logged-in user
        db (AsyncDatabaseConnection): The database connection
        logger (Logger): The standard app logger

    Raises:
        HTTPException: 403 if not running locally
        HTTPException: 404 if configuration cannot be found in the user's jurisdiction
        HTTPException: 400 if the configuration's status is not `active`
        HTTPException: 404 if the configuration's primary condition is not found

    Returns:
        Response: The serialized configuration file content
    """

    if ENVIRONMENT["ENV"] != "local":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available locally.",
        )

    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=user.jurisdiction_id, db=db
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found."
        )

    if config.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configuration must be active.",
        )

    primary_condition = None
    if config.primary_condition_id:
        primary_condition = await get_condition_by_id_db(
            id=config.primary_condition_id, db=db
        )

    if not primary_condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Condition with ID {config.primary_condition_id} could not be found or does not exist.",
        )

    try:
        return await run_in_threadpool(
            get_serialized_files,
            user.jurisdiction_id,
            primary_condition.canonical_url,
            config.version,
            logger,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch one or more files from S3. See logs for details.",
        )


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
    jd = user.jurisdiction_id

    (
        config,
        rsg_codes,
        included_conditions,
        all_versions,
        active_version,
        active_configuration_id,
        latest_version,
        condition_id,
        condition_canonical_url,
        is_draft,
        draft_id,
    ) = await get_configuration_service(
        configuration_id=configuration_id,
        jurisdiction_id=jd,
        db=db,
        logger=logger,
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

    config_condition_info = await get_total_condition_code_counts_by_configuration_db(
        config_id=config.id, db=db
    )

    # Determine the display name for the configuration
    # Priority: primary_condition.display_name > original_condition.display_name > config.name
    display_name = config.name
    if not config.primary_condition_id and config.original_condition_id:
        original_condition_name = await get_condition_display_name_by_id_db(
            id=config.original_condition_id, db=db
        )
        if original_condition_name:
            display_name = original_condition_name

    code_systems = await get_all_code_systems_by_key(db=db)
    custom_codes = CustomCodes(
        codes=[
            DbConfigurationCustomCode(
                code=c.code,
                name=c.name,
                system_key=c.system_key,
            )
            for c in config.custom_codes
        ],
        code_systems=code_systems,
    )

    return GetConfigurationResponse(
        id=config.id,
        draft_id=draft_id,
        is_draft=is_draft,
        condition_id=condition_id,
        condition_canonical_url=condition_canonical_url,
        display_name=display_name,
        status=config.status,
        code_sets=config_condition_info,
        included_conditions=included_conditions,
        custom_codes=custom_codes,
        section_processing=sorted(
            [format_section_naming(section) for section in config.section_processing],
            key=lambda r: r.name.lower(),
        ),
        rsg_codes=rsg_codes,
        all_versions=all_versions,
        version=config.version,
        active_version=active_version,
        active_configuration_id=active_configuration_id,
        latest_version=latest_version,
        locked_by=locked_by,
        is_locked=locked_by is not None and locked_by.id != user.id,
    )
