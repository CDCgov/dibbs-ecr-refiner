from dataclasses import dataclass
from logging import Logger
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.middleware import get_logged_in_user
from app.db.configurations.db import get_configurations_db
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.configuration_locks import ConfigurationLock
from app.services.logger import get_logger

from ...db.events.db import (
    AuditEvent,
    get_event_count_by_condition_db,
    get_events_by_jd_db,
)

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
class EventResponse:
    """
    Response needed for the audit log page.
    """

    audit_events: list[AuditEvent]
    configuration_options: list[EventFilterOption]
    total_pages: int


@router.get(
    "/",
    response_model=EventResponse,
    tags=["events"],
    operation_id="getEvents",
)
async def get_events(
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
    logger: Logger = Depends(get_logger),
    page: int = 1,
    canonical_url: str | None = None,
) -> EventResponse:
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

    total_event_count = await get_event_count_by_condition_db(
        jurisdiction_id=jd, canonical_url=canonical_url, db=db
    )

    if total_event_count is None:
        logger.error(
            msg="Could not retrieve total event count.",
            extra={
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

    if page < 1 or page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'page' must be a number between 1 and {total_pages}.",
        )

    audit_events = await get_events_by_jd_db(
        jurisdiction_id=jd,
        page=page,
        page_size=PAGE_SIZE,
        canonical_url=canonical_url,
        db=db,
    )

    jd_configurations = await get_configurations_db(jurisdiction_id=jd, db=db)

    seen_urls = set()
    configuration_options = []

    for c in jd_configurations:
        if c.condition_canonical_url not in seen_urls:
            option = EventFilterOption(
                name=c.name, id=c.id, canonical_url=c.condition_canonical_url
            )
            configuration_options.append(option)
            seen_urls.add(c.condition_canonical_url)

    # unlock if user holds lock
    for c in jd_configurations:
        lock = await ConfigurationLock.get_lock(str(c.id), db)
        if lock and str(lock.user_id) == str(user.id):
            await ConfigurationLock.release_lock(
                configuration_id=c.id,
                user_id=user.id,
                jurisdiction_id=jd,
                db=db,
            )

    return EventResponse(
        total_pages=total_pages,
        audit_events=audit_events,
        configuration_options=configuration_options,
    )
