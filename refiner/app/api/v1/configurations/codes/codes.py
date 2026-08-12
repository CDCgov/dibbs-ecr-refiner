from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from app.api.auth.middleware import get_logged_in_user
from app.db.configurations.codes.db import (
    CodeFilterOptions,
    get_all_filter_options_db,
    get_code_count_metadata_db,
    get_codes_db,
    set_codes_status_db,
)
from app.db.configurations.db import get_configuration_by_id_db
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser

router = APIRouter(prefix="/{configuration_id}")


@dataclass
class CodeResponse:
    """
    Code object to return to the client.
    """

    id: UUID
    condition_id: UUID | None
    source: str
    code: str
    description: str
    system_id: UUID
    system_name: str
    status: Literal["Included", "Excluded"]
    is_custom: bool


@dataclass
class CodeCountsResponse:
    """
    Code count information to return to the client.
    """

    total_code_count: int
    total_code_sets_count: int
    total_excluded_codes_count: int
    total_custom_codes_count: int


@dataclass
class CodesResponse:
    """
    Codes and metadata to return to the client.
    """

    next_cursor: str | None
    codes: list[CodeResponse]


@router.get(
    "/codes",
    response_model=CodesResponse,
    tags=["configurations"],
    operation_id="getCodes",
)
async def get_codes(
    configuration_id: UUID,
    cursor: str | None = None,
    db: AsyncDatabaseConnection = Depends(get_db),
    user: DbUser = Depends(get_logged_in_user),
) -> CodesResponse:
    """
    Fetches all codes associated with a configuration.

    Args:
        configuration_id (UUID): ID of the configuration to update
        cursor (str | None): The cursor for the page to start from
        user (DbUser): The logged-in user
        logger (Logger): The standard logger
        db (AsyncDatabaseConnection): Database connection
    """

    # Number of codes pulled per batch
    CODES_LIMIT = 100

    config = await get_configuration_by_id_db(
        id=configuration_id,
        jurisdiction_id=user.jurisdiction_id,
        db=db,
    )

    if not config:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Configuration cannot be found.",
        )

    codes, next_cursor = await get_codes_db(
        configuration_id=config.id, db=db, limit=CODES_LIMIT, cursor=cursor
    )

    return CodesResponse(
        next_cursor=next_cursor,
        codes=[
            CodeResponse(
                is_custom=c.condition_id is None,
                status="Included" if c.status == "included" else "Excluded",
                id=c.id,
                condition_id=c.condition_id,
                source=c.source,
                code=c.code,
                description=c.description,
                system_id=c.system_id,
                system_name=c.system_name,
            )
            for c in codes
        ],
    )


@router.get(
    "/code-counts",
    response_model=CodeCountsResponse,
    tags=["configurations"],
    operation_id="getCodeCounts",
)
async def get_code_counts(
    configuration_id: UUID,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> CodeCountsResponse:
    """
    Fetch code count information for a configuration.

    Args:
        configuration_id (UUID): ID of the configuration to update
        user (DbUser): The logged-in user
        db (AsyncDatabaseConnection): Database connection

    Raises:
        HTTPException: 404 if configuration can't be found
        HTTPException: 500 if code count metadata can't be fetched

    Returns:
        CodeCountsResponse: Object containing code count info
    """

    config = await get_configuration_by_id_db(
        id=configuration_id,
        jurisdiction_id=user.jurisdiction_id,
        db=db,
    )

    if not config:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Configuration cannot be found.",
        )

    code_counts = await get_code_count_metadata_db(configuration_id=config.id, db=db)

    if not code_counts:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to get code count metadata.",
        )

    return CodeCountsResponse(
        total_code_count=code_counts.total_code_count + code_counts.custom_code_count,
        total_code_sets_count=code_counts.code_set_count,
        total_excluded_codes_count=code_counts.excluded_code_count,
        total_custom_codes_count=code_counts.custom_code_count,
    )


@router.post(
    "/set-status",
    response_model=list[UUID],
    tags=["configurations"],
    operation_id="setCodesStatus",
)
async def set_codes_status(
    configuration_id: UUID,
    code_ids: list[UUID],
    status: Literal["included", "excluded"],
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> list[UUID]:
    """
    Sets all provided code_ids to the specified `status` for the given configuration ID.

    Args:
        configuration_id (UUID): ID of the configuration to update
        code_ids (list[UUID]): List of code IDs
        status (Literal['included', 'excluded'): Set codes as 'included' or 'excluded'
        user (DbUser): The logged-in user
        db (AsyncDatabaseConnection): Database connection

    Raises:
        HTTPException: 404 if configuration can't be found

    Returns:
        list[UUID]: Code IDs that had their status changed
    """

    config = await get_configuration_by_id_db(
        id=configuration_id,
        jurisdiction_id=user.jurisdiction_id,
        db=db,
    )

    if not config:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Configuration cannot be found.",
        )

    impacted_code_ids = await set_codes_status_db(
        configuration_id=config.id, code_ids=code_ids, status=status, db=db
    )

    return impacted_code_ids


@dataclass
class CodeFiltersResponse:
    """
    Model for code filters response.
    """

    id: UUID
    system_name: str
    code_count: int


@router.get(
    "/filters",
    response_model=CodeFilterOptions,
    tags=["configurations"],
    operation_id="getCodeFilters",
)
async def get_code_filters(
    configuration_id: UUID,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> CodeFilterOptions:
    """
    Fetches code filter information for the client to display.

    Args:
        configuration_id (UUID): The configuration ID
        user (DbUser, optional): _description_. The logged-in user
        db (AsyncDatabaseConnection, optional): The database connection

    Raises:
        HTTPException: 404 if the configuration couldn't be found

    Returns:
        CodeFiltersResponse: The code filters
    """

    config = await get_configuration_by_id_db(
        id=configuration_id,
        jurisdiction_id=user.jurisdiction_id,
        db=db,
    )

    if not config:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Configuration cannot be found.",
        )

    return await get_all_filter_options_db(configuration_id=config.id, db=db)
