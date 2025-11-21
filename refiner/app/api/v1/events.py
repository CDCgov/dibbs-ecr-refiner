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
    cannonical_url: str | None = None,
) -> EventResponse:
    """
    Returns a list of all events for a jurisdiction, ordered from newest to oldest.

    Args:
        user (DbUser): The user making the request.
        db (AsyncDatabaseConnection): Database connection.
        cannonical_url (str | None): An optional filter on the condition.

    Returns:
        EventResponse: A bundle with
            - The list of AuditEvents relevant for the (optional) filter.
            - The list of condition information with potentially filter-able data
    """

    audit_events = await get_events_by_jd_db(
        jurisdiction_id=user.jurisdiction_id, db=db, cannonical_url=cannonical_url
    )

    jd_configurations = await get_configurations_db(
        jurisdiction_id=user.jurisdiction_id, db=db
    )

    seen_urls = set()
    configuration_options = []

    for c in jd_configurations:
        if c.condition_canonical_url not in seen_urls:
            trace = ConfigurationTrace(
                name=c.name, id=c.id, cannonical_url=c.condition_canonical_url
            )
            configuration_options.append(trace)
            seen_urls.add(c.condition_canonical_url)

    return EventResponse(
        audit_events=audit_events, configuration_options=configuration_options
    )
