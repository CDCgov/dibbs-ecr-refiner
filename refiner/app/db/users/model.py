from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DbUser(BaseModel):
    """
    A `user` row from the database.
    """

    id: UUID
    username: str
    email: str
    jurisdiction_id: str
    created_at: datetime
    updated_at: datetime
