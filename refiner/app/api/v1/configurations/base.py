from datetime import UTC, datetime
from logging import Logger
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.middleware import get_logged_in_user
from app.db.conditions.db import (
    get_condition_by_id_db,
    get_conditions_by_version_db,
    get_included_conditions_db,
)
from app.db.conditions.model import DbConditionCoding
from app.db.configurations.db import (
    get_configuration_by_id_db,
    get_configuration_versions_db,
    get_configurations_db,
    get_latest_config_db,
    get_total_condition_code_counts_by_configuration_db,
    insert_configuration_db,
    is_config_valid_to_insert_db,
)
from app.db.configurations.model import DbConfiguration, DbConfigurationCustomCode
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.db import get_user_by_id_db
from app.db.users.model import DbUser
from app.services.configuration_locks import ConfigurationLock
from app.services.configurations import (
    get_canonical_url_to_highest_inactive_version_map,
)
from app.services.logger import get_logger

from .models import (
    CreateConfigInput,
    CreateConfigurationResponse,
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

    # fetch all conditions from the db based on the primary condition's version
    condition_version_to_use = conditions[0].version
    all_conditions = await get_conditions_by_version_db(
        db=db, version=condition_version_to_use
    )

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
