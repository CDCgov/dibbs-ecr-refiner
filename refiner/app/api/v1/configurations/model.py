from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.db.configurations.model import (
    DbConfigurationCustomCode,
    DbConfigurationSectionProcessing,
    DbConfigurationStatus,
    DbSectionAction,
    DbTotalConditionCodeCount,
    GetConfigurationResponseVersion,
)
from app.db.demo.model import Condition
from app.db.users.model import UserInfoBase
from app.services.terminology import CodeSystem


@dataclass(frozen=True)
class GetConfigurationsResponse:
    """
    Model for a user-defined configuration.
    """

    id: UUID
    name: str
    status: DbConfigurationStatus


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
    name: str


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


@dataclass(frozen=True)
class LockedByUser(UserInfoBase):
    """
    LockedByUser response to provide user information.
    """

    pass


@dataclass(frozen=True)
class GetConfigurationResponse:
    """
    Model for a configration response.
    """

    id: UUID
    draft_id: UUID | None
    is_draft: bool
    condition_id: UUID
    condition_canonical_url: str
    display_name: str
    status: DbConfigurationStatus
    code_sets: list[DbTotalConditionCodeCount]
    included_conditions: list[IncludedCondition]
    custom_codes: list[DbConfigurationCustomCode]
    section_processing: list[DbConfigurationSectionProcessing]
    all_versions: list[GetConfigurationResponseVersion]
    version: int
    active_configuration_id: UUID | None
    active_version: int | None
    latest_version: int
    is_locked: bool
    locked_by: LockedByUser | None


@dataclass(frozen=True)
class ConfigurationCustomCodeResponse:
    """
    Configuration response for custom code operations (add/edit/delete).
    """

    id: UUID
    display_name: str
    code_sets: list[DbTotalConditionCodeCount]
    custom_codes: list[DbConfigurationCustomCode]


class AssociateCodesetInput(BaseModel):
    """
    Condition association input model.
    """

    condition_id: UUID


@dataclass(frozen=True)
class ConditionEntry:
    """
    Condition model.
    """

    id: UUID


@dataclass(frozen=True)
class AssociateCodesetResponse:
    """
    Response from adding a code set to a config.
    """

    id: UUID
    included_conditions: list[ConditionEntry]
    condition_name: str


class AddCustomCodeInput(BaseModel):
    """
    Input model for adding a custom code to a configuration.
    """

    code: str
    system: CodeSystem
    name: str

    @field_validator("system", mode="before")
    @classmethod
    def normalize_system(cls, v: str) -> str:
        """
        Make the system lowercase before Pydantic checks it.
        """

        if not isinstance(v, str):
            raise TypeError('"system" must be a string')

        lookup = {item.value.lower(): item for item in CodeSystem}
        norm_input = v.lower()
        if norm_input in lookup:
            return lookup[norm_input]

        return v


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

    pass


class SectionUpdateInput(BaseModel):
    """
    Request body for modifying a section.
    """

    include: bool | None = None
    narrative: bool | None = None
    action: DbSectionAction | None = None
    name: str | None = None
    current_code: str
    new_code: str | None = None


class AddSectionInput(SectionInputBase):
    """
    Request body for adding a section.
    """

    name: str


@dataclass(frozen=True)
class ConfigurationStatusUpdateResponse:
    """
    Response model for updating the status a configuration.
    """

    configuration_id: UUID
    status: DbConfigurationStatus


class UploadCustomCodesCsvInput(BaseModel):
    """
    Input model for Custom Code CSV.
    """

    csv_text: str = Field(..., description="Full CSV contents as UTF-8 text")
    filename: str | None = None


class UploadCustomCodesPreviewItem(BaseModel):
    """Validated CSV row ready for confirmation."""

    code: str
    system: CodeSystem
    name: str
    row: int | None = None


class ConfirmUploadCustomCodesInput(BaseModel):
    """Payload used to confirm a previously validated CSV import."""

    custom_codes: list[UploadCustomCodesPreviewItem]
