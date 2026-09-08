from dataclasses import dataclass, field
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
        "lock_acquire",
        "lock_release",
        "lock_renew",
        "bulk_add_custom_code",
        "bulk_delete_custom_code",
        "create_custom_section",
        "edit_custom_section",
        "delete_custom_section",
    ]
    action_text: str
    condition_id: UUID | None = field(default=None, kw_only=True)
    code_count: int | None = field(default=None, kw_only=True)


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


@dataclass(frozen=True)
class CodeSetEvent:
    """
    Minimal event data needed to export a code set.
    """

    id: UUID
    condition_id: UUID | None
    condition_name: str | None
    code_count: int | None
    event_type: str
    created_at: datetime
