from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg import AsyncCursor
from psycopg.rows import class_row, dict_row

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
    configuration_version: int
    condition_id: UUID
    action_text: str
    created_at: datetime


async def get_event_count_by_condition_db(
    jurisdiction_id: str,
    db: AsyncDatabaseConnection,
    canonical_url: str | None = None,
) -> int | None:
    """
    Gets a count of all events within a jurisdiction by condition.
    """

    query = """
        SELECT COUNT(*) AS total_count
        FROM events e
        LEFT JOIN configurations c ON e.configuration_id = c.id
        WHERE e.jurisdiction_id = %s
        AND (%s::TEXT is NULL or c.condition_canonical_url = %s);
    """
    params = (jurisdiction_id, canonical_url, canonical_url)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if not row:
                return None
            return int(row["total_count"])


async def get_events_by_jd_db(
    jurisdiction_id: str,
    page: int,
    page_size: int,
    db: AsyncDatabaseConnection,
    canonical_url: str | None = None,
) -> list[AuditEvent]:
    """
    Fetches all events for a given jurisdiction and condition.
    """
    offset = (page - 1) * page_size

    query = """
        SELECT
        e.id,
        u.username,
        c.name AS configuration_name,
        c.version as configuration_version,
        c.id AS condition_id,
        e.action_text,
        e.created_at
        FROM events e
        LEFT JOIN users u ON e.user_id = u.id
        LEFT JOIN configurations c ON e.configuration_id = c.id
        WHERE e.jurisdiction_id = %s
        AND (%s::TEXT is NULL or c.condition_canonical_url = %s)
        ORDER BY e.created_at DESC
        LIMIT %s OFFSET %s;
    """
    params = (jurisdiction_id, canonical_url, canonical_url, page_size, offset)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(AuditEvent)) as cur:
            await cur.execute(query, params)
            events_rows = await cur.fetchall()
            return events_rows


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
