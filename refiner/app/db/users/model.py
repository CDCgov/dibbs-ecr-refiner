from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class UserInfoBase:
    """
    A class for information about a user.
    """

    id: UUID
    name: str
    email: str


type NotificationName = str
type DateTimeAcknowledged = str
type Notifications = dict[NotificationName, DateTimeAcknowledged]


@dataclass(frozen=True)
class DbUser:
    """
    A `user` row from the database.
    """

    id: UUID
    username: str
    email: str
    jurisdiction_id: str
    created_at: datetime
    updated_at: datetime
    notifications: Notifications
