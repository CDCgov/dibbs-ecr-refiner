from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...db.pool import AsyncDatabaseConnection, get_db
from ...db.users.db import update_user_notifications_db
from ...db.users.model import DbUser
from ..auth.handlers import UserNotifications, UserResponse, build_user_response
from ..auth.middleware import get_logged_in_user

router = APIRouter(prefix="/notifications")


class UpdateUserNotificationsRequest(BaseModel):
    """
    Request to update notification acknowledgement state for the current user.
    """

    name: str
    date_acknowledged: str


@router.patch(
    "",
    response_model=UserResponse,
    tags=["app-notifications"],
    operation_id="updateUserNotifications",
)
async def update_user_notifications(
    request: UpdateUserNotificationsRequest,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> UserResponse:
    """
    Updates notification acknowledgement state for the current user.
    """
    updated_user = await update_user_notifications_db(
        user_id=user.id,
        name=request.name,
        date_acknowledged=request.date_acknowledged,
        db=db,
    )

    return build_user_response(updated_user)
