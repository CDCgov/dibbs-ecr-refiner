from typing import Any
from uuid import UUID

from pydantic import BaseModel


class Configuration(BaseModel):
    """
    Model for a user-defined configuration.
    """

    id: str
    name: str
    is_active: bool


class DbConfigurationCondition(BaseModel):
    """
    Condition associated with a Configuration.
    """

    canonical_url: str
    version: str


class DbConfiguration(BaseModel):
    """
    Model for a database Configuration object.
    """

    id: UUID
    family_id: int
    jurisdiction_id: str
    name: str
    description: str
    included_conditions: list[DbConfigurationCondition]
    loinc_codes_additions: list[Any]
    snomed_codes_additions: list[Any]
    icd10_codes_additions: list[Any]
    rxnorm_codes_additions: list[Any]
    custom_codes: list[Any]
    sections_to_include: list[str]
    cloned_from_configuration_id: UUID | None
