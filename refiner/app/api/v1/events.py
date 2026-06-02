import asyncio
from dataclasses import dataclass
from logging import Logger
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.middleware import get_logged_in_user
from app.core.exceptions import DatabaseConnectionError, DatabaseQueryError
from app.db.events.db import (
    AuditEvent,
    get_custom_code_upload_events_by_event_id,
    get_event_count_by_condition_db,
    get_event_filter_options_db,
    get_events_by_jd_db,
    is_event_valid,
)
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.code_systems import get_all_code_systems_by_key
from app.services.logger import get_logger

router = APIRouter(prefix="/events")


@dataclass
class EventFilterOption:
    """
    Conditions returned to the user to be used for filtering events.
    """

    id: UUID
    name: str
    canonical_url: str


@dataclass
class EventsResponse:
    """
    Response needed for the audit log page.
    """

    audit_events: list[AuditEvent]
    configuration_options: list[EventFilterOption]
    total_pages: int


@router.get(
    "/",
    response_model=EventsResponse,
    tags=["events"],
    operation_id="getEvents",
)
async def get_events(
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
    logger: Logger = Depends(get_logger),
    page: int = 1,
    canonical_url: str | None = None,
) -> EventsResponse:
    """
    Returns a list of all events for a jurisdiction, ordered from newest to oldest.

    Args:
        user (DbUser): The user making the request.
        db (AsyncDatabaseConnection): Database connection.
        logger (Logger): Standard logger.
        page (int): page of events to return to the client.
        canonical_url (str | None): An optional filter on the condition.

    Returns:
        EventResponse: A bundle with
            - Total page count
            - The list of AuditEvents relevant for the (optional) filter
            - The list of condition information with potentially filter-able data
    """

    PAGE_SIZE = 10
    jd = user.jurisdiction_id

    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'page' must be a number greater than 0.",
        )

    try:
        total_event_count, audit_events, configuration_options = await asyncio.gather(
            get_event_count_by_condition_db(
                jurisdiction_id=jd, canonical_url=canonical_url, db=db
            ),
            get_events_by_jd_db(
                jurisdiction_id=jd,
                page=page,
                page_size=PAGE_SIZE,
                canonical_url=canonical_url,
                db=db,
            ),
            get_event_filter_options_db(jurisdiction_id=jd, db=db),
        )
    except (DatabaseConnectionError, DatabaseQueryError) as db_err:
        logger.error(
            msg="Database error occurred while retrieving audit logs.",
            extra={
                "error": str(db_err),
                "error_details": db_err.details,
                "user_id": user.id,
                "jurisdiction_id": jd,
                "canonical_url": canonical_url,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve audit logs.",
        )

    total_pages = max((total_event_count + PAGE_SIZE - 1) // PAGE_SIZE, 1)

    if page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'page' must be a number less than or equal to {total_pages}.",
        )

    return EventsResponse(
        total_pages=total_pages,
        audit_events=audit_events,
        configuration_options=[
            EventFilterOption(id=co.id, name=co.name, canonical_url=co.canonical_url)
            for co in configuration_options
        ],
    )


@dataclass
class CustomCodeUploadEventResponse:
    """
    Response model for a custom code upload event.
    """

    id: UUID
    system_display_name: str
    code: str
    name: str


@router.get(
    "/{event_id}/custom-code-uploads",
    response_model=list[CustomCodeUploadEventResponse],
    tags=["events"],
    operation_id="getCustomCodeUploadEvents",
)
async def get_custom_code_upload_events(
    event_id: UUID,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> list[CustomCodeUploadEventResponse]:
    """
    Returns a list of all custom code upload events associated with a parent event ID.

    Args:
        event_id (UUID): The parent event
        user (DbUser): The logged in user
        db (AsyncDatabaseConnection): The database connection

    Raises:
        HTTPException: 404 if event with requested ID is not found or does not belong to user's jurisdiction
    """
    jd = user.jurisdiction_id
    event_exists = await is_event_valid(id=event_id, jurisdiction_id=jd, db=db)

    if not event_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No event found for ID: {event_id}",
        )

    custom_code_events = await get_custom_code_upload_events_by_event_id(
        event_id=event_id, db=db
    )

    system_by_key = await get_all_code_systems_by_key(db=db)

    return [
        CustomCodeUploadEventResponse(
            id=cc.id,
            system_display_name=system_by_key[cc.system].display_name,
            code=cc.code,
            name=cc.name,
        )
        for cc in custom_code_events
    ]
