from uuid import UUID

from pydantic import BaseModel


class DbUser(BaseModel):
    """
    Model for a logged-in user.
    """

    id: UUID
    username: str
    email: str
    jurisdiction_id: str
