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


@dataclass
class DbTesConditionUpdate:
    """
    Model to represent the codes within a condition packaged in a TES update.
    """

    canonical_url: str
    display_name: str
    added_code_ids: list[UUID]
    removed_code_ids: list[UUID]
    is_new: bool
