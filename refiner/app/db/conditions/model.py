from uuid import UUID

from pydantic import BaseModel


class Condition(BaseModel):
    """
    Model to represent a condition in the database.
    """

    id: UUID
    display_name: str
    canonical_url: str
