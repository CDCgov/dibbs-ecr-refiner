from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.auth.middleware import get_logged_in_user
from app.db.configurations.db import get_configurations_db
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser

from ...db.events.db import (
    ConfigurationTrace,
    EventResponse,
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

    configurations = await get_configurations_db(
        jurisdiction_id=user.jurisdiction_id, db=db
    )
    configuration_options = [
        ConfigurationTrace(name=c.name, id=c.id) for c in configurations
    ]

    return EventResponse(
        audit_events=audit_events, configuration_options=configuration_options
    )
