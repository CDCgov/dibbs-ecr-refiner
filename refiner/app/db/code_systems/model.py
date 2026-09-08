from dataclasses import dataclass
from uuid import UUID


@dataclass
class DbCodeSystem:
    """
    A code system row from the `systems` table.
    """

    id: UUID
    key: str
    display_name: str
    oid: str
