from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.models.terminology import CodeExportRow


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
    condition_display_name: str
    added_codes: list[CodeExportRow]
    removed_codes: list[CodeExportRow]

    def __post_init__(self):
        """Rebuilds the nested JSONB the diff queries aggregate into export rows."""
        self.added_codes = [
            c if isinstance(c, CodeExportRow) else CodeExportRow(**c)
            for c in self.added_codes
        ]
        self.removed_codes = [
            c if isinstance(c, CodeExportRow) else CodeExportRow(**c)
            for c in self.removed_codes
        ]


class ExportDiffInput(BaseModel):
    """
    Body required to generate a TES update diff for a specific condition.
    """

    canonical_url: str
    cur_tes_version: str
    prev_tes_version: str


@dataclass(frozen=True)
class TesConfigToUpdate:
    """A configuration to update with new TES codes."""

    configuration_id: UUID
    configuration_display_name: str
    codesets_to_update: list[str]
    configuration_tes_version: str


@dataclass
class DbTesConfigsToUpdateResponse:
    """
    The response needed for rendering of the TES update configuration page.
    """

    existing_drafts: list[TesConfigToUpdate]
    drafts_to_create: list[TesConfigToUpdate]
