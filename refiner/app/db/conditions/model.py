from uuid import UUID

from pydantic import BaseModel


class DbCondition(BaseModel):
    """
    Model to represent a condition in the database.
    """

    id: UUID
    display_name: str
    canonical_url: str
    version: str
