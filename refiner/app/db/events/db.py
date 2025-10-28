from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg import AsyncCursor
from psycopg.rows import class_row

from ..pool import AsyncDatabaseConnection
from .model import EventInput


@dataclass
class EventResponse:
    """
    An event returned by the DB function.
    """

    id: UUID
    username: str
    configuration_name: str
    action_text: str
    created_at: datetime


async def get_events_by_jd_db(
    jurisdiction_id: str, db: AsyncDatabaseConnection
) -> list[EventResponse]:
    """
    Fetches all events for a given jurisdiction ID.
    """
    query = """
        SELECT
        e.id,
        u.username,
        c.name AS configuration_name,
        e.action_text,
        e.created_at
        FROM events e
        LEFT JOIN users u ON e.user_id = u.id
        LEFT JOIN configurations c ON e.configuration_id = c.id
        WHERE e.jurisdiction_id = %s
        ORDER BY e.created_at DESC;
    """
    params = (jurisdiction_id,)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(EventResponse)) as cur:
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
