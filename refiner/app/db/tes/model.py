from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.models.terminology import CodeExportRow


@dataclass(frozen=True)
class DbTes:
    """
    Model to represent a TES record in the database.
    """

    id: UUID
    version: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DbTesConditionUpdate:
    """
    Model to represent the codes within a condition packaged in a TES update.
    """

    canonical_url: str
    display_name: str
    added_code_ids: list[UUID]
    removed_code_ids: list[UUID]
    is_new: bool


@dataclass(frozen=True)
class DbConditionDiff:
    """
    The codes one condition gained and lost between two TES releases.

    The diff queries aggregate each side into JSONB; `_to_condition_diff` in `db.py`
    parses it into `CodeExportRow`s as the row lands, so nothing downstream sees a dict.
    """

    canonical_url: str
    condition_display_name: str
    added_codes: list[CodeExportRow]
    removed_codes: list[CodeExportRow]


class ExportDiffInput(BaseModel):
    """
    Body required to generate a TES update diff for a specific condition.
    """

    canonical_url: str
    cur_tes_version: str
    prev_tes_version: str


@dataclass(frozen=True)
class DbTesConfigToUpdate:
    """A configuration to update with new TES codes."""

    configuration_id: UUID
    configuration_display_name: str
    codesets_to_update: list[str]
    configuration_tes_version: str


@dataclass(frozen=True)
class DbTesConfigsToUpdate:
    """
    The response needed for rendering of the TES update configuration page.
    """

    existing_drafts: list[DbTesConfigToUpdate]
    drafts_to_create: list[DbTesConfigToUpdate]
