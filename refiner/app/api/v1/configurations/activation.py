from logging import Logger
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.api.auth.middleware import get_logged_in_user
from app.db.configurations.activations.db import (
    activate_configuration_db,
    deactivate_configuration_db,
)
from app.db.configurations.db import get_configuration_by_id_db
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.aws.s3 import (
    upload_configuration_payload,
    upload_current_version_file,
)
from app.services.configurations import (
    convert_config_to_storage_payload,
    get_config_payload_metadata,
)
from app.services.logger import get_logger

from .models import ConfigurationStatusUpdateResponse

router = APIRouter(prefix="/{configuration_id}")


@router.patch(
    "/activate",
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
        upload_configuration_payload, config_payload, config_metadata, logger
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
    await run_in_threadpool(
        upload_current_version_file, s3_urls, active_config.version, logger
    )

    return ConfigurationStatusUpdateResponse(
        configuration_id=active_config.id, status=active_config.status
    )


@router.patch(
    "/deactivate",
    response_model=ConfigurationStatusUpdateResponse,
    tags=["configurations"],
    operation_id="deactivateConfiguration",
)
async def deactivate_configuration(
    configuration_id: UUID,
    user: DbUser = Depends(get_logged_in_user),
    logger: Logger = Depends(get_logger),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> ConfigurationStatusUpdateResponse:
    """
    Deactivate the specified configuration.

    Args:
        configuration_id (UUID): ID of the configuration to update
        user (DbUser): The logged-in user
        logger (Logger): The standard application logger
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
    await run_in_threadpool(upload_current_version_file, s3_urls, None, logger)

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
