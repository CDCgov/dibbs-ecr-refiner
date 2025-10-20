from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID


@dataclass(frozen=True)
class DbConfigurationCondition:
    """
    Condition associated with a Configuration.
    """

    included_conditions_ids: list[UUID]


# TODO: Revisit this to see if we can figure out how to reduce overlap with other types.
# This is a "custom_code" column on the configuration row in the configurations table.
# This is one object in the `custom_codes` list and we have many objects that are Similar
# shaped. A flexible FHIR R4 Coding model with standard metadata could simplify a lot of
# redundancy.
@dataclass(frozen=True)
class DbConfigurationCustomCode:
    """
    Custom code associated with a Configuration.
    """

    code: str
    system: Literal["LOINC", "SNOMED", "ICD-10", "RxNorm"]
    name: str


@dataclass(frozen=True)
class DbConfigurationLocalCode:
    """
    Local code associated with a Configuration.

    Similar to CustomCode but allows for nonstandard code systems and local codes.
    """

    code: str
    system: str
    name: str


@dataclass(frozen=True)
class DbConfigurationSectionProcessing:
    """
    Section Processing instructions for a Configuration.

    Name is the section's name.
    Code is the LOINC code for the section.
    Action is either: retain, refine, or remove
    """

    name: str
    code: str
    action: str


@dataclass(frozen=True)
class DbConfiguration:
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
    section_processing: list[DbConfigurationSectionProcessing]
    version: int

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "DbConfiguration":
        """
        Transforms a dictionary object into a DbConfiguration.

        Args:
            row (dict[str, Any]): Dictionary containing configuration data from the database

        Returns:
            DbConfiguration: The configuration object
        """

        return cls(
            id=row["id"],
            name=row["name"],
            jurisdiction_id=row["jurisdiction_id"],
            condition_id=row["condition_id"],
            included_conditions = row.get("included_conditions", []) or [],
            custom_codes=[DbConfigurationCustomCode(**c) for c in row["custom_codes"]],
            local_codes=[DbConfigurationLocalCode(**lc) for lc in row["local_codes"]],
            section_processing=[
                DbConfigurationSectionProcessing(**sp)
                for sp in row["section_processing"]
            ],
            version=row["version"],
        )
