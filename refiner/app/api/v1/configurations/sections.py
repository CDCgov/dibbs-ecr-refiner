from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.middleware import get_logged_in_user
from app.api.v1.configurations.model import (
    CustomSectionInput,
    StandardSectionInput,
)
from app.db.configurations.db import (
    get_configuration_by_id_db,
    insert_custom_section_db,
    update_configuration_section_db,
)
from app.db.configurations.model import (
    DbConfigurationSectionProcessing,
)
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.configuration_locks import ConfigurationLock

router = APIRouter(prefix="/{configuration_id}/section-processing")


@router.post(
    "", response_model=str, tags=["configurations"], operation_id="insertCustomSection"
)
async def insert_custom_section(
    configuration_id: UUID,
    section_input: CustomSectionInput,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> str:
    """
    Create a new custom section for a given configuration ID.

    Args:
        configuration_id (UUID): The ID of the configuration
        section_input (CustomSectionInput): Desired properties of the section
        user (DbUser): The logged-in user
        db (AsyncDatabaseConnection): The database connection
    """
    jd = user.jurisdiction_id

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

    # Check if valid
    for s in config.section_processing:
        name, code = section_input.name, section_input.code
        if s.name == name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom section name is already in use.",
            )
        if s.code == code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom section code is already in use.",
            )

    updated_config = await insert_custom_section_db(
        config=config, user_id=user.id, custom_section_input=section_input, db=db
    )

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Custom section creation failed.",
        )

    return section_input.code


@router.patch(
    "",
    response_model=str,
    tags=["configurations"],
    operation_id="updateConfigurationSectionProcessing",
)
async def update_section_processing(
    configuration_id: UUID,
    section: StandardSectionInput,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> str:
    """
    Update a section entry for a configuration.

    Args:
        configuration_id (UUID): ID of the configuration to update
        section (UpdateSectionInput): Updated section info
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

    # Can't update a section unless it exists
    updated_code = section.code
    prev_section = None
    for s in config.section_processing:
        if s.code == updated_code:
            prev_section = s
            break

    if not prev_section:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Section with code {updated_code} is invalid and can't be updated.",
        )

    section_update = DbConfigurationSectionProcessing(
        code=section.code,
        action=section.action,
        narrative=section.narrative,
        include=section.include,
        name=prev_section.name,
        versions=prev_section.versions,
        section_type="standard",
    )

    try:
        updated_config = await update_configuration_section_db(
            config=config, section_update=section_update, user_id=user.id, db=db
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided section is not valid.",
        )

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration.",
        )

    return section_update.code
