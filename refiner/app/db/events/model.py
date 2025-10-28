from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID


@dataclass(frozen=True)
class DbEvent:
    """
    Model to represent an event in the `events` table.
    """

    id: UUID
    jurisdiction_id: UUID
    configuration_id: UUID
    event_type: Literal["create_configuration"]
    action_text: str
    created_at: datetime
