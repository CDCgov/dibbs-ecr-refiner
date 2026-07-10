from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class DbTes:
    """
    Model to represent a TES record in the database.
    """

    id: UUID
    version: str
    created_at: datetime
    updated_at: datetime
