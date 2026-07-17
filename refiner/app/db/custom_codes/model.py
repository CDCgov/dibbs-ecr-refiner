from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class DbCustomCode:
    """
    Model to represent a custom code row in the database.
    """

    id: UUID
    display: str
    code: str
    system_id: UUID
    created_at: datetime
    updated_at: datetime
    configuration_id: UUID
