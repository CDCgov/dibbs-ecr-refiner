from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.api.v1.configurations.custom_codes.model import CustomCodeResponse
from app.api.v1.simulator.model import Condition
from app.core.models.configurations import (
    ConfigurationStatus,
    ConfiguredSection,
    NarrativeAction,
    SectionAction,
)
from app.core.models.terminology import CodeLabel
from app.db.configurations.model import (
    DbCodeSetSummary,
    DbConfigurationVersion,
)
from app.db.users.model import UserInfoBase
from app.services.conditions.grouper_statuses import CodeSetStatus


@dataclass(frozen=True)
class GetConfigurationsResponse:
    """
    Model for a user-defined configuration.
    """

    id: UUID
    display_name: str
    status: ConfigurationStatus


class CreateConfigInput(BaseModel):
    """
    Body required to create a new configuration.
    """

    condition_id: UUID


@dataclass(frozen=True)
class CreateConfigurationResponse:
    """
    Configuration creation response model.
    """

    id: UUID
    display_name: str


@dataclass(frozen=True)
class IncludedCondition:
    """
    Model for a condition that is associated with a configuration.
    """

    id: UUID
    display_name: str
    canonical_url: str
    version: str
    associated: bool
    code_set_status: CodeSetStatus


@dataclass(frozen=True)
class LockedByUser(UserInfoBase):
    """
    LockedByUser response to provide user information.
    """


@dataclass(frozen=True)
class CodeSetSummary:
    """
    One code set a configuration includes, with how many codes it contributes.
    """

    condition_id: UUID
    display_name: str
    code_count: int


def to_code_set_summary(row: DbCodeSetSummary) -> CodeSetSummary:
    """
    Maps a code set row onto its wire shape.

    Args:
        row (DbCodeSetSummary): The row from the database

    Returns:
        CodeSetSummary: The code set as the client sees it
    """
    return CodeSetSummary(
        condition_id=row.condition_id,
        display_name=row.display_name,
        code_count=row.code_count,
    )


@dataclass(frozen=True)
class GetConfigurationResponseVersion:
    """
    Model representing a version of a configuration.
    """

    id: UUID
    version: int
    condition_canonical_url: str
    status: ConfigurationStatus
    created_at: datetime
    created_by: str
    last_activated_at: datetime | None
    last_activated_by: str | None


def to_configuration_version(
    row: DbConfigurationVersion,
) -> GetConfigurationResponseVersion:
    """
    Maps a configuration version row onto its wire shape.

    Args:
        row (DbConfigurationVersion): The row from the database

    Returns:
        GetConfigurationResponseVersion: The version as the client sees it
    """
    return GetConfigurationResponseVersion(
        id=row.id,
        version=row.version,
        condition_canonical_url=row.condition_canonical_url,
        status=row.status,
        created_at=row.created_at,
        created_by=row.created_by,
        last_activated_at=row.last_activated_at,
        last_activated_by=row.last_activated_by,
    )


@dataclass(frozen=True)
class GetConfigurationResponse:
    """
    Model for a configuration response.
    """

    id: UUID
    draft_id: UUID | None
    is_draft: bool
    condition_id: UUID
    condition_canonical_url: str
    display_name: str
    status: ConfigurationStatus
    code_sets: list[CodeSetSummary]
    included_conditions: list[IncludedCondition]
    custom_codes: list[CustomCodeResponse]
    section_processing: list[ConfiguredSection]
    all_versions: list[GetConfigurationResponseVersion]
    rsg_codes: list[CodeLabel]
    version: int
    active_configuration_id: UUID | None
    active_version: int | None
    latest_version: int
    is_locked: bool
    locked_by: LockedByUser | None


class AssociateCodesetInput(BaseModel):
    """
    Condition association input model.
    """

    condition_id: UUID


@dataclass(frozen=True)
class AssociateCodesetResponse:
    """
    Response from adding a code set to a config.
    """

    id: UUID
    included_conditions: list[UUID]
    condition_display_name: str


@dataclass(frozen=True)
class ConfigurationTestResponse:
    """
    Model to represent the response provided to the client when in-line testing is run.
    """

    original_eicr: str
    refined_download_key: str
    condition: Condition


class SectionInputBase(BaseModel):
    """
    Shared request body properties for sections.
    """

    code: str


class DeleteSectionInput(SectionInputBase):
    """
    Request body to delete a section.
    """


class SectionUpdateInput(BaseModel):
    """
    Input model for updating a section's processing instructions.
    """

    include: bool | None = None
    narrative: NarrativeAction | None = None
    action: SectionAction | None = None
    display_name: str | None = None
    current_code: str
    new_code: str | None = None


class AddSectionInput(SectionInputBase):
    """
    Request body for adding a section.
    """

    display_name: str


@dataclass(frozen=True)
class ConfigurationStatusUpdateResponse:
    """
    Response model for updating the status a configuration.
    """

    configuration_id: UUID
    status: ConfigurationStatus
