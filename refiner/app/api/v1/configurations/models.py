from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.db.configurations.db import (
    DbTotalConditionCodeCount,
    GetConfigurationResponseVersion,
)
from app.db.configurations.model import (
    DbConfigurationCustomCode,
    DbConfigurationSectionProcessing,
    DbConfigurationStatus,
)
from app.db.demo.model import Condition
from app.db.users.model import UserInfoBase


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
    deduplicated_codes: list[str]
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
    system: Literal["loinc", "snomed", "icd-10", "rxnorm", "other"]
    name: str

    @field_validator("system", mode="before")
    @classmethod
    def normalize_system(cls, v: str) -> str:
        """
        Make the system lowercase before Pydantic checks it.
        """
        if not isinstance(v, str):
            raise TypeError('"system" must be a string')
        return v.lower()


@dataclass(frozen=True)
class ConfigurationTestResponse:
    """
    Model to represent the response provided to the client when in-line testing is run.
    """

    original_eicr: str
    refined_download_url: str
    condition: Condition


class UpdateSectionProcessingEntry(BaseModel):
    """
    Model for a single section processing update.
    """

    code: str
    action: Literal["retain", "refine", "remove"]


class UpdateSectionProcessingPayload(BaseModel):
    """
    Payload for updating section processing entries.
    """

    sections: list[UpdateSectionProcessingEntry]


@dataclass(frozen=True)
class UpdateSectionProcessingResponse:
    """
    Response model for updating section processing entries.
    """

    message: str


@dataclass(frozen=True)
class ConfigurationStatusUpdateResponse:
    """
    Response model for updating the status a configuration.
    """

    configuration_id: UUID
    status: DbConfigurationStatus
