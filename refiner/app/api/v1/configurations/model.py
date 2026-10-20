from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel

from app.api.v1.configurations.custom_codes.model import CustomCodeResponse
from app.core.models.configurations import (
    ConfigurationStatus,
    NarrativeAction,
    SectionAction,
)
from app.core.models.terminology import CodeLabel, CodeSetSummary
from app.db.configurations.model import (
    ConfiguredSection,
    GetConfigurationResponseVersion,
)
from app.db.simulator.model import Condition
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
