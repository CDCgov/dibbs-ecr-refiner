from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class DbTesVersionMetadata:
    """
    Model for TES metadata (row).
    """

    id: UUID
    version: str
    is_current_version: bool

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "DbTesVersionMetadata":
        """
        Transforms a dictionary object into a DbConfiguration.

        Args:
            row (dict[str, Any]): Dictionary containing configuration data from the database

        Returns:
            DbConfiguration: The configuration object
        """

        return cls(
            id=row["id"],
            version=row["version"],
            is_current_version=row["is_current_version"],
        )
