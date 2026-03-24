from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.middleware import get_logged_in_user
from app.api.v1.configurations.model import (
    CustomSectionInput,
    DeleteSectionInput,
    SectionUpdateInput,
)
from app.db.configurations.db import (
    delete_custom_section_db,
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

router = APIRouter(prefix="/{configuration_id}/sections")


@router.post(
    "", response_model=str, tags=["configurations"], operation_id="addCustomSection"
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


@router.delete(
    "", response_model=str, tags=["configurations"], operation_id="deleteCustomSection"
)
async def delete_custom_section(
    configuration_id: UUID,
    section_input: DeleteSectionInput,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> str:
    """

    Delete a custom section.

    Args:
        configuration_id (UUID): ID of the configuration with custom section to delete
        section_input (DeleteCustomSectionInput): Custom section deletion input
        user (DbUser): The logged in user
        db (AsyncDatabaseConnection): The database connection

    Raises:
        HTTPException: 404 if configuration isn't found
        HTTPException: 409 if configuration isn't a draft
        HTTPException: 404 if custom section code to delete isn't found

    Returns:
        str: Deleted custom section code
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

    updated_config = await delete_custom_section_db(
        config=config, custom_section_input=section_input, db=db
    )

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"A custom section with code {section_input.code} was not found.",
        )

    return section_input.code


@router.patch(
    "",
    response_model=str,
    tags=["configurations"],
    operation_id="updateSection",
)
async def update_section(
    configuration_id: UUID,
    section_input: SectionUpdateInput,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> str:
    """
    Update a section entry for a configuration.

    Args:
        configuration_id (UUID): ID of the configuration to update
        section_input (SectionUpdateInput): Updated section info
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
    match_code = section_input.current_code
    prev_section = None
    for s in config.section_processing:
        if s.code == match_code:
            prev_section = s
            break

    if not prev_section:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Section with code {match_code} is invalid and can't be updated.",
        )

    include = (
        section_input.include
        if section_input.include is not None
        else prev_section.include
    )
    narrative = (
        section_input.narrative
        if section_input.narrative is not None
        else prev_section.narrative
    )

    if prev_section.section_type == "custom":
        code = section_input.new_code if section_input.new_code else prev_section.code
        name = section_input.name if section_input.name else prev_section.name
        section_update = DbConfigurationSectionProcessing(
            code=code,
            name=name,
            action=section_input.action or prev_section.action,
            narrative=narrative,
            include=include,
            versions=prev_section.versions,
            section_type="custom",
        )
    else:
        section_update = DbConfigurationSectionProcessing(
            # standard section code and name cannot be changed
            code=prev_section.code,
            name=prev_section.name,
            action=section_input.action or prev_section.action,
            narrative=narrative,
            include=include,
            versions=prev_section.versions,
            section_type="standard",
        )

    try:
        updated_config = await update_configuration_section_db(
            config=config,
            current_code=prev_section.code,
            section_update=section_update,
            user_id=user.id,
            db=db,
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
