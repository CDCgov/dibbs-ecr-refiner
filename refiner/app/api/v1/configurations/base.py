from datetime import UTC, datetime
from logging import Logger
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.middleware import get_logged_in_user
from app.db.codes.db import get_rsg_codes_by_condition_id_db
from app.db.conditions.db import (
    get_condition_by_id_db,
    get_conditions_by_version_db,
    get_primary_condition_db,
)
from app.db.configurations.db import (
    get_configuration_by_id_db,
    get_configuration_versions_db,
    get_configurations_summary_db,
    get_latest_config_db,
    get_total_condition_code_counts_by_configuration_db,
    insert_configuration_db,
    is_config_valid_to_insert_db,
)
from app.db.configurations.model import (
    DbConfigurationCustomCode,
)
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.db import get_user_by_id_db
from app.db.users.model import DbUser
from app.services.code_systems import get_all_code_systems_by_key
from app.services.configuration_locks import ConfigurationLock
from app.services.configurations import (
    format_section_naming,
)
from app.services.logger import get_logger

from .model import (
    CreateConfigInput,
    CreateConfigurationResponse,
    CustomCodes,
    GetConfigurationResponse,
    GetConfigurationsResponse,
    IncludedCondition,
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

    return [
        GetConfigurationsResponse(id=c.id, name=c.name, status=c.status)
        for c in await get_configurations_summary_db(
            jurisdiction_id=user.jurisdiction_id, db=db
        )
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

    # get the condition by the ID we are provided with by the client
    condition = await get_condition_by_id_db(id=body.condition_id, db=db)

    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Condition with ID {body.condition_id} could not be found or does not exist.",
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

    config_condition_info = await get_total_condition_code_counts_by_configuration_db(
        config_id=config.id, db=db
    )

    # precomputed set of included_conditions ids
    included_ids = set(config.included_conditions)

    primary_condition = await get_primary_condition_db(
        configuration_id=config.id, db=db
    )

    if not primary_condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find primary condition associated with configuration.",
        )

    # fetch all conditions from the db based on the primary condition's version
    all_conditions = await get_conditions_by_version_db(
        version=primary_condition.version,
        db=db,
    )

    latest_config = await get_latest_config_db(
        jurisdiction_id=jd,
        condition_canonical_url=primary_condition.canonical_url,
        db=db,
    )

    # Build IncludedCondition objects, marking which are associated
    included_conditions = [
        IncludedCondition(
            id=condition.id,
            display_name=condition.display_name,
            canonical_url=condition.canonical_url,
            version=condition.version,
            associated=condition.id in included_ids
            or condition.id == primary_condition.id,
        )
        for condition in all_conditions
    ]

    all_versions = await get_configuration_versions_db(
        jurisdiction_id=jd,
        condition_canonical_url=primary_condition.canonical_url,
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

    rsg_codes = await get_rsg_codes_by_condition_id_db(
        condition_id=primary_condition.id,
        db=db,
    )
    return GetConfigurationResponse(
        id=config.id,
        draft_id=draft_id,
        is_draft=is_draft,
        condition_id=primary_condition.id,
        condition_canonical_url=primary_condition.canonical_url,
        display_name=config.name,
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
        is_locked=is_locked,
    )
