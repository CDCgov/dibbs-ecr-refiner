from dataclasses import dataclass
from typing import Literal, get_args
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status

from app.api.auth.middleware import get_logged_in_user
from app.api.v1.configurations.codes.model import FilterInput
from app.db.conditions.db import get_primary_condition_db
from app.db.configurations.codes.db import (
    CodeFilterOptions,
    get_all_filter_options_db,
    get_code_count_metadata_db,
    get_codes_db,
    set_codes_status_beyond_rendered_db,
    set_codes_status_within_rendered_set_db,
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
    source: list[str]
    code: str
    description: str
    system_id: UUID
    system_name: str
    status: Literal["Included", "Excluded"]
    is_custom: bool
    is_primary_condition_rsg: bool


@dataclass
class CodeCountsResponse:
    """
    Code count information to return to the client.
    """

    total_code_count: int
    total_code_sets_count: int
    total_excluded_codes_count: int
    total_custom_codes_count: int


CodesLimit = Literal[100]
CODES_LIMIT = get_args(CodesLimit)[0]


@dataclass
class CodesLimitResponse:
    """
    Utility class to help Orval ship these values to the frontend.
    """

    codes_limit: CodesLimit = CODES_LIMIT


@dataclass(frozen=True)
class CodesResponse:
    """
    Codes and metadata to return to the client.
    """

    next_cursor: str | None
    codes: list[CodeResponse]
    codes_limit: CodesLimitResponse


def _get_filter_input(
    search: str | None = None,
    code_systems: list[str] = Query(default=[]),
    sources: list[str] = Query(default=[]),
    statuses: list[str] = Query(default=[]),
) -> FilterInput:
    return FilterInput(
        search=search,
        code_systems=code_systems,
        sources=sources,
        statuses=statuses,
    )


@router.post(
    "/set-status",
    response_model=list[UUID],
    tags=["configurations"],
    operation_id="setCodesStatus",
)
async def set_codes_status(
    configuration_id: UUID,
    update_beyond_rendered_set: bool,
    code_ids_to_skip: list[UUID],
    code_ids: list[UUID],
    status: Literal["included", "excluded"],
    filters: FilterInput = Depends(_get_filter_input),
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> list[UUID]:
    """
    Sets selected codes to the specified `status` for the given configuration ID.

    If `update_beyond_rendered_set` is false, we update status for only the specified
    `code_ids` within the rendered page.

    If `update_beyond_rendered_set` is true, we skip any codes within `code_ids_to_skip`
    and update status for all other codes that don't get clipped away by the passed-in filters

    Args:
        configuration_id (UUID): ID of the configuration to update
        update_beyond_rendered_set (bool): Whether the action should be only within the rendered codes or include all codes.
        code_ids (list[UUID]): List of code IDs to specifically action. Used in the "within cursor" flow.
        code_ids_to_skip (list[UUID]): List of code IDs to skip since they've been manually actioned by the user.
        filters (FilterInput): Filter input coming from the client to build the "complete" set of codes to bulk select
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

    if config.status != "draft":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Trying to update a non-draft configuration",
        )

    try:
        if update_beyond_rendered_set:
            impacted_code_ids = await set_codes_status_beyond_rendered_db(
                configuration_id=config.id,
                code_ids_to_skip=code_ids_to_skip,
                status=status,
                filters=filters,
                db=db,
            )
        else:
            impacted_code_ids = await set_codes_status_within_rendered_set_db(
                configuration_id=config.id,
                configuration_primary_condition_id=config.condition_id,
                status=status,
                code_ids=code_ids,
                db=db,
            )
        return impacted_code_ids
    except ValueError:
        primary_condition = await get_primary_condition_db(
            configuration_id=config.id, db=db
        )

        if not primary_condition:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Could not find configuration's primary condition.",
            )

        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration's primary condition ({primary_condition.display_name}) RSG codes cannot be modified.",
        )


@router.get(
    "/codes",
    response_model=CodesResponse,
    tags=["configurations"],
    operation_id="getCodes",
)
async def get_codes(
    configuration_id: UUID,
    cursor: str | None = None,
    filters: FilterInput = Depends(_get_filter_input),
    db: AsyncDatabaseConnection = Depends(get_db),
    user: DbUser = Depends(get_logged_in_user),
) -> CodesResponse:
    """
    Fetches all codes associated with a configuration.

    Args:
        configuration_id (UUID): ID of the configuration to update
        filters (FilterInput): Filter input coming from the client
        cursor (str | None): The cursor for the page to start from
        user (DbUser): The logged-in user
        logger (Logger): The standard logger
        db (AsyncDatabaseConnection): Database connection
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

    codes, next_cursor = await get_codes_db(
        configuration_id=config.id,
        configuration_primary_condition_id=config.condition_id,
        limit=CODES_LIMIT,
        cursor=cursor,
        filters=filters,
        db=db,
    )

    return CodesResponse(
        next_cursor=next_cursor,
        codes_limit=CodesLimitResponse(),
        codes=[
            CodeResponse(
                is_custom=c.condition_id is None,
                is_primary_condition_rsg=c.is_child_rsg,
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
        user (DbUser): The logged-in user
        db (AsyncDatabaseConnection): The database connection

    Raises:
        HTTPException: 404 if the configuration couldn't be found

    Returns:
        CodeFilterOptions: The code filters
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
