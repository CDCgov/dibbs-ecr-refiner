from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.models.configurations import (
    ConfigurationStatus,
    NarrativeAction,
    SectionAction,
    SectionType,
)
from app.db.configurations.custom_codes.model import DbCustomCode


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


@dataclass(frozen=True)
class ConfiguredSection:
    """
    Section Processing instructions for a Configuration.

    `display_name` is the section's label.
    `code` is the LOINC code for the section.
    `versions` is a list of versions this section appears in.
    `section_type` is an indicator as to how the section was created.

    Field order is carried over from the base class this used to inherit, so
    that nothing downstream shifts: `asdict(DbConfiguration)` recurses into
    `section_processing` for the structured log payloads in
    `services/testing.py`, and that key order follows declaration order here.
    """

    include: bool
    narrative: NarrativeAction
    action: SectionAction
    display_name: str
    code: str
    versions: list[str]
    section_type: SectionType


@dataclass(frozen=True)
class DbConfigurationSection(ConfiguredSection):
    """
    A section row from the `configurations_sections` table.
    """

    id: UUID
    configuration_id: UUID
    created_at: datetime
    updated_at: datetime


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
    display_name: str
    status: ConfigurationStatus
    jurisdiction_id: str
    condition_id: UUID
    included_conditions: list[UUID]
    custom_codes: list[DbCustomCode]
    section_processing: list[ConfiguredSection]
    version: int
    last_activated_at: datetime | None
    last_activated_by: UUID | None
    created_by: UUID
    s3_url: str

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
            display_name=row["display_name"],
            status=row["status"],
            jurisdiction_id=row["jurisdiction_id"],
            condition_id=row["condition_id"],
            included_conditions=row.get("included_conditions") or [],
            custom_codes=[
                DbCustomCode(
                    id=UUID(c["id"]),
                    code=c["code"],
                    display_name=c["display_name"],
                    system_id=UUID(c["system_id"]),
                    created_at=c["created_at"],
                    updated_at=c["updated_at"],
                    configuration_id=UUID(c["configuration_id"]),
                )
                for c in row["custom_codes"]
            ],
            section_processing=[
                ConfiguredSection(**sp) for sp in (row.get("section_processing") or [])
            ],
            version=row["version"],
            last_activated_at=row["last_activated_at"],
            last_activated_by=row["last_activated_by"],
            created_by=row["created_by"],
            s3_url=row["s3_url"],
        )


@dataclass(frozen=True)
class DbConfigurationSummary:
    """
    Minimal model for a high-level configuration summary.
    """

    id: UUID
    display_name: str
    status: ConfigurationStatus
