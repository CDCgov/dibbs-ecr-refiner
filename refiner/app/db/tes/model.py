from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.db.codes.model import CodeDisplay


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


@dataclass
class TesUpdate:
    """
    All metadata for a TES update needed for the frontend.
    """

    id: UUID
    version: str
    created_at: datetime


@dataclass
class ConditionDiffExportData:
    """
    All metadata for a TES update needed for the frontend.
    """

    canonical_url: str
    condition_name: str
    added_codes: list[CodeDisplay]
    removed_codes: list[CodeDisplay]

    def __post_init__(self):
        """Helper to transform nested JSON returned from SQL into CodeDisplay objects."""
        self.added_codes = [
            c if isinstance(c, CodeDisplay) else CodeDisplay(**c)
            for c in self.added_codes
        ]
        self.removed_codes = [
            c if isinstance(c, CodeDisplay) else CodeDisplay(**c)
            for c in self.removed_codes
        ]


class ExportDiffInput(BaseModel):
    """
    Body required to generate a TES update diff for a specific condition.
    """

    canonical_url: str
    cur_tes_version: str
    prev_tes_version: str
