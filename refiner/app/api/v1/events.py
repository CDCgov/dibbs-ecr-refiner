from fastapi import APIRouter, Depends

from app.api.auth.middleware import get_logged_in_user
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser

from ...db.events.db import EventResponse, get_events_by_jd_db

router = APIRouter(prefix="/events")


@router.get(
    "/",
    response_model=list[EventResponse],
    tags=["events"],
    operation_id="getEvents",
)
async def get_events(
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> list[EventResponse]:
    """
    Returns a list of all events for a jurisdiction, ordered from newest to oldest.

    Args:
        user (DbUser): The user making the request.
        db (AsyncDatabaseConnection): Database connection.

    Returns:
        list[EventResponse]: A list of all events for the jurisdiction.
    """

    return await get_events_by_jd_db(jurisdiction_id=user.jurisdiction_id, db=db)
