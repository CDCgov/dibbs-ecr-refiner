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
    DbSectionType,
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

    _raise_if_invalid_section_addition(config=config, section_input=section_input)

    updated_config = await insert_custom_section_db(
        config=config, user_id=user.id, custom_section_input=section_input, db=db
    )

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Section creation failed.",
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
        configuration_id=configuration_id,
        user=user,
        db=db,
    )

    prev_section = _validate_section_exists_or_raise(
        code=section_input.current_code,
        sections=config.section_processing,
    )

    _raise_if_invalid_section_update(
        existing_section=prev_section,
        all_sections=config.section_processing,
        desired_name=section_input.name,
        desired_code=section_input.new_code,
    )

    section_update = _build_section_update(
        prev_section=prev_section,
        section_input=section_input,
    )

    try:
        updated_config = await update_configuration_section_db(
            config=config,
            current_code=prev_section.code,
            section_update=section_update,
            user_id=user.id,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided section is not valid.",
        ) from exc

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration.",
        )

    return section_update.code


def _raise_if_invalid_section_fields(
    sections: list[DbConfigurationSectionProcessing],
    desired_name: str | None,
    desired_code: str | None,
):
    """
    Raises an exception if the desired name or desired code are invalid.

    Args:
        sections (list[DbConfigurationSectionProcessing]): The list of sections to check against
        desired_name (str | None): The desired name to use
        desired_code (str | None): The desired code to use

    Raises:
        HTTPException: 400 if name is in use
        HTTPException: 400 if code is in use
    """
    if desired_name is not None and not _is_valid_name(
        desired_name=desired_name,
        sections=sections,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Section name is already in use.",
        )

    if desired_code is not None and not _is_valid_code(
        desired_code=desired_code,
        sections=sections,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Section code is already in use.",
        )


def _raise_if_invalid_section_addition(
    config: DbConfiguration, section_input: CustomSectionInput
) -> None:
    """
    Raises an exception if any properties of a section addition are not valid.

    Args:
        config (DbConfiguration): The configuration
        section_input (CustomSectionInput): The section addition input
    """
    _raise_if_invalid_section_fields(
        sections=config.section_processing,
        desired_name=section_input.name,
        desired_code=section_input.code,
    )


def _raise_if_invalid_section_update(
    existing_section: DbConfigurationSectionProcessing,
    all_sections: list[DbConfigurationSectionProcessing],
    desired_name: str | None,
    desired_code: str | None,
) -> None:
    """
    Raises an exception if any properties of an update are not valid.

    Args:
        existing_section (DbConfigurationSectionProcessing): The existing section to update
        all_sections (list[DbConfigurationSectionProcessing]): All sections associated with a config
        desired_name (str | None): The desired name to update to
        desired_code (str | None): the desired code to update to
    """
    other_sections = [s for s in all_sections if s.code != existing_section.code]

    _raise_if_invalid_section_fields(
        sections=other_sections,
        desired_name=desired_name,
        desired_code=desired_code,
    )


def _value_or_default[T](new_value: T | None, old_value: T) -> T:
    """
    Helper function to use the new value if available, otherwise fall back to the old value.
    """
    return new_value if new_value is not None else old_value


def _build_section_update(
    prev_section: DbConfigurationSectionProcessing,
    section_input: SectionUpdateInput,
) -> DbConfigurationSectionProcessing:
    """
    Builds a section update object when given the existing section and the properties to modify.

    Args:
        prev_section (DbConfigurationSectionProcessing): The existing section to modify
        section_input (SectionUpdateInput): The object containing section properties to update

    Returns:
        DbConfigurationSectionProcessing: The modified section
    """
    include = _value_or_default(section_input.include, prev_section.include)
    narrative = _value_or_default(section_input.narrative, prev_section.narrative)
    action = _value_or_default(section_input.action, prev_section.action)
    section_type: DbSectionType

    if prev_section.section_type == "custom":
        code = _value_or_default(section_input.new_code, prev_section.code)
        name = _value_or_default(section_input.name, prev_section.name)
        section_type = "custom"
    else:
        # standard section code and name cannot be changed
        code = prev_section.code
        name = prev_section.name
        section_type = "standard"

    return DbConfigurationSectionProcessing(
        code=code,
        name=name,
        action=action,
        narrative=narrative,
        include=include,
        versions=prev_section.versions,
        section_type=section_type,
    )


def _validate_section_exists_or_raise(
    code: str, sections: list[DbConfigurationSectionProcessing]
) -> DbConfigurationSectionProcessing:
    """
    Raises an exception if a section in the list doesn't match the code. Otherwise returns the matched section.

    Args:
        code (str): The section's code to match on
        sections (list[DbConfigurationSectionProcessing]): The list of sections

    Raises:
        HTTPException: 400 if no matching section was found

    Returns:
        DbConfigurationSectionProcessing: The section with the matching code
    """
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
