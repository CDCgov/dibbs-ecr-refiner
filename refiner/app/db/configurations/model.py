from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class DbConfigurationCondition(BaseModel):
    """
    Condition associated with a Configuration.
    """

    canonical_url: str
    version: str


# TODO: Revisit this to see if we can figure out how to reduce overlap with other types.
# This is a "custom_code" column on the configuration row in the configurations table.
# This is one object in the `custom_codes` list and we have many objects that are Similar
# shaped. A flexible FHIR R4 Coding model with standard metadata could simplify a lot of
# redundancy.
class DbConfigurationCustomCode(BaseModel):
    """
    Custom code associated with a Configuration.
    """

    code: str
    system: Literal["LOINC", "SNOMED", "ICD-10", "RxNorm"]
    name: str


class DbConfigurationLocalCode(BaseModel):
    """
    Local code associated with a Configuration.

    Similar to CustomCode but allows for nonstandard code systems and local codes.
    """

    code: str
    system: str
    name: str


class DbConfiguration(BaseModel):
    """
    Model for a database Configuration object (row).

    A Configuration is explicitly tied to a primary condition through condition_id,
    while included_conditions tracks both the primary and any secondary conditions
    using their canonical URLs and versions. At the time of creation, condition.name
    will also be added to configuration.name for a more human readable way to see the
    condition -> configuration connection.

    NOTE: family_id is present in the database, but intentionally omitted here.
    It may be used in the future to support configuration "families" or advanced versioning.
    For now, each condition has at most one configuration, and versioning is handled per-configuration.
    """

    id: UUID
    name: str
    jurisdiction_id: str
    condition_id: UUID
    included_conditions: list[DbConfigurationCondition]
    custom_codes: list[DbConfigurationCustomCode]
    local_codes: list[DbConfigurationLocalCode]
    sections_to_include: list[str]
    cloned_from_configuration_id: UUID | None
