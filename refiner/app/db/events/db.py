from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg import AsyncCursor
from psycopg.rows import class_row

from app.db.configurations.model import ConfigurationTrace

from ..pool import AsyncDatabaseConnection
from .model import EventInput


@dataclass
class AuditEvent:
    """
    An event returned by the DB function.
    """

    id: UUID
    username: str
    configuration_name: str
    condition_id: UUID
    action_text: str
    created_at: datetime


@dataclass
class EventResponse:
    """
    Response needed for the audit log page.
    """

    audit_events: list[AuditEvent]
    configuration_options: list[ConfigurationTrace]


async def get_events_by_jd_db(
    jurisdiction_id: str,
    db: AsyncDatabaseConnection,
    condition_filter: UUID | None = None,
) -> list[AuditEvent]:
    """
    Fetches all events for a given jurisdiction ID.
    """

    query = """
        SELECT
        e.id,
        u.username,
        c.name AS configuration_name,
        c.id AS condition_id,
        e.action_text,
        e.created_at
        FROM events e
        LEFT JOIN users u ON e.user_id = u.id
        LEFT JOIN configurations c ON e.configuration_id = c.id
        WHERE e.jurisdiction_id = %s
        AND (%s::uuid is NULL or c.id = %s::uuid)
        ORDER BY e.created_at DESC;
    """
    params_lst = (
        jurisdiction_id,
        condition_filter,
        condition_filter,
    )

    params = tuple(params_lst)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(AuditEvent)) as cur:
            await cur.execute(query, params)
            events_rows = await cur.fetchall()
            return events_rows


async def get_condition_options_by_jd_db(
    jurisdiction_id: str,
    db: AsyncDatabaseConnection,
) -> list[ConfigurationTrace]:
    """
    Fetches all configuration options that have corresponding audit events for a given jurisdiction ID.
    """

    query = """
        SELECT
        c.id,
        c.name
        FROM configurations c
        WHERE c.jurisdiction_id = %s
        ORDER BY c.jurisdiction_id;
    """

    params = (jurisdiction_id,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(ConfigurationTrace)) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()
            return rows


async def insert_event_db(
    event: EventInput,
    cursor: AsyncCursor[Any],
) -> None:
    """
    Inserts an event into the `events` table.
    """
    query = """
        INSERT INTO events (
            user_id,
            jurisdiction_id,
            configuration_id,
            event_type,
            action_text
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """
    params = (
        event.user_id,
        event.jurisdiction_id,
        event.configuration_id,
        event.event_type,
        event.action_text,
    )

    await cursor.execute(query, params)
