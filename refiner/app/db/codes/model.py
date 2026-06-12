from dataclasses import dataclass
from uuid import UUID


@dataclass
class DbCode:
    """
    DB model for code stored in the codes table.
    """

    name: str
    value: str
    version: str
    system_id: UUID
