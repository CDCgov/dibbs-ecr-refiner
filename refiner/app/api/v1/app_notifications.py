from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...db.pool import AsyncDatabaseConnection, get_db
from ...db.users.db import update_user_notifications_db
from ...db.users.model import DbUser
from ..auth.handlers import NotificationKeys, UserResponse
from ..auth.middleware import get_logged_in_user

router = APIRouter(prefix="/notifications")


class UpdateUserNotificationsRequest(BaseModel):
    """
    Request to update notification acknowledgement state for the current user.
    """

    key: NotificationKeys


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
        name=request.key,
        date_acknowledged=datetime.now(UTC).isoformat(),
        db=db,
    )

    return await UserResponse.from_db_user(user=updated_user, db=db)
