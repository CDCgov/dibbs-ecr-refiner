from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DbUser:
    """
    Model for a logged-in user.
    """

    id: UUID
    username: str
    email: str
    jurisdiction_id: str
