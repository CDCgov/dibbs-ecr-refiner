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
    DbConfiguration,
    DbConfigurationSectionProcessing,
)
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.configuration_locks import ConfigurationLock
from app.services.configurations import format_section_naming

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
    config = await _validate_configuration_or_raise(
        configuration_id=configuration_id, user=user, db=db
    )

    if not _is_valid_name(
        desired_name=section_input.name,
        sections=config.section_processing,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Section name is already in use.",
        )

    if not _is_valid_code(
        desired_code=section_input.code, sections=config.section_processing
    ):
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

    config = await _validate_configuration_or_raise(
        configuration_id=configuration_id, user=user, db=db
    )

    updated_config = await delete_custom_section_db(
        config=config, user_id=user.id, custom_section_input=section_input, db=db
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
        HTTPException: 400 if the code is not valid, code is in use, or name is in use
        HTTPException: 404 if configuration isn't found
        HTTPException: 409 if configuration is not a draft and therefore not editable
        HTTPException: 500 if section processing can't be updated

    Returns:
        UpdateSectionProcessingResponse: The message to show the user
    """

    config = await _validate_configuration_or_raise(
        configuration_id=configuration_id, user=user, db=db
    )

    prev_section = _validate_section_exists_or_raise(
        code=section_input.current_code, sections=config.section_processing
    )

    # Can't update if desired name or code is already in user
    desired_name = section_input.name
    desired_code = section_input.new_code

    # No need to check the section we're trying to edit
    other_sections = [
        s for s in config.section_processing if s.code != prev_section.code
    ]

    if desired_name is not None and not _is_valid_name(
        desired_name=desired_name,
        sections=other_sections,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Section name is already in use.",
        )

    if desired_code is not None and not _is_valid_code(
        desired_code=desired_code, sections=other_sections
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Section code is already in use.",
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
        code = (
            section_input.new_code
            if section_input.new_code is not None
            else prev_section.code
        )
        name = (
            section_input.name if section_input.name is not None else prev_section.name
        )

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


def _validate_section_exists_or_raise(
    code: str, sections: list[DbConfigurationSectionProcessing]
) -> DbConfigurationSectionProcessing:
    section = next((s for s in sections if s.code == code), None)

    if not section:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Section with code {code} is invalid and can't be updated.",
        )
    return section


async def _validate_configuration_or_raise(
    configuration_id: UUID, user: DbUser, db: AsyncDatabaseConnection
) -> DbConfiguration:
    """
    Checks that a configuration is able to be modified. Either returns the configuration or raises an exception.

    Args:
        configuration_id (UUID): The ID of the configuration to validate
        user (DbUser): The logged in user
        db (AsyncDatabaseConnection): The database connection

    Raises:
        HTTPException: 404 if configuration can't be found
        HTTPException: 409 if the configuration is not a draft

    Returns:
        DbConfiguration: The validated configuration
    """
    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=user.jurisdiction_id, db=db
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

    return config


def _is_valid_code(
    desired_code: str, sections: list[DbConfigurationSectionProcessing]
) -> bool:
    """
    Returns True if the desired name has not already been used by another section in the list.

    Args:
        desired_code (str): The desired code of the custom section
        sections (list[DbConfigurationSectionProcessing]): A list of sections to check the codes of

    Returns:
        bool: True if the desired code is allowed, else False
    """
    existing_codes = [s.code for s in sections]
    return desired_code not in existing_codes


def _is_valid_name(
    desired_name: str, sections: list[DbConfigurationSectionProcessing]
) -> bool:
    """
    Returns True if the desired name has not already been used by another section in the list.

    Args:
        desired_name (str): The desired name of the custom section
        sections (list[DbConfigurationSectionProcessing]): A list of sections to check the names of

    Returns:
        bool: True if the desired name is allowed, else False
    """
    # the name the user is attempting to use (lowercase)
    desired_name = desired_name.lower()

    # all standard section names as they are (lowercase)
    standard_section_names = [
        s.name.lower() for s in sections if s.section_type == "standard"
    ]

    # all standard section names with "section" removed at the end (lowecase)
    standard_section_names_formatted = [
        format_section_naming(s).name.lower()
        for s in sections
        if s.section_type == "standard"
    ]

    # all custom names in use
    custom_names_in_use = [
        s.name.lower() for s in sections if s.section_type == "custom"
    ]

    # all of the above make up a list of names that cannot be used
    invalid_names = (
        standard_section_names + standard_section_names_formatted + custom_names_in_use
    )

    return desired_name not in invalid_names
