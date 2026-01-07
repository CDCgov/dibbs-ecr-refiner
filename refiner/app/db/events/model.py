from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID


@dataclass(frozen=True)
class _EventBase:
    jurisdiction_id: str
    user_id: UUID
    configuration_id: UUID
    event_type: Literal[
        "create_configuration",
        "activate_configuration",
        "deactivate_configuration",
        "add_code",
        "delete_code",
        "edit_code",
        "section_update",
    ]
    action_text: str


@dataclass(frozen=True)
class EventInput(_EventBase):
    """
    Data required to insert a new event.
    """


@dataclass(frozen=True)
class DbEvent(_EventBase):
    """
    Model to represent an event in the `events` table.
    """

    id: UUID
    created_at: datetime
