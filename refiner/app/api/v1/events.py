from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.auth.middleware import get_logged_in_user
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser

from ...db.events.db import (
    EventResponse,
    get_condition_options_by_jd_db,
    get_events_by_jd_db,
)

router = APIRouter(prefix="/events")


@router.get(
    "/",
    response_model=EventResponse,
    tags=["events"],
    operation_id="getEvents",
)
async def get_events(
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
    condition_filter: UUID | None = None,
) -> EventResponse:
    """
    Returns a list of all events for a jurisdiction, ordered from newest to oldest.

    Args:
        user (DbUser): The user making the request.
        db (AsyncDatabaseConnection): Database connection.
        condition_filter (UUID | None): An optional filter on the condition.

    Returns:
        EventResponse: A bundle with
            - The list of AuditEvents relevant for the (optional) filter.
            - The list of condition information with potentially filter-able data
    """

    audit_events = await get_events_by_jd_db(
        jurisdiction_id=user.jurisdiction_id, db=db, condition_filter=condition_filter
    )

    configuration_options = await get_condition_options_by_jd_db(
        jurisdiction_id=user.jurisdiction_id, db=db
    )

    return EventResponse(
        audit_events=audit_events, configuration_options=configuration_options
    )
