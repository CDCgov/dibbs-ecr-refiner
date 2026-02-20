from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.middleware import get_logged_in_user
from app.api.v1.configurations.models import (
    UpdateSectionProcessingPayload,
    UpdateSectionProcessingResponse,
)
from app.db.configurations.db import (
    SectionUpdate,
    get_configuration_by_id_db,
    update_section_processing_db,
)
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.configuration_locks import ConfigurationLock

router = APIRouter(prefix="/{configuration_id}/section-processing")


@router.patch(
    "",
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
