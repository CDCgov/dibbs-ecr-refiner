from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg import AsyncCursor
from psycopg.rows import class_row, dict_row

from app.db.configurations.model import DbConfiguration, DbConfigurationCustomCode

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
    has_custom_code_upload_events: bool


@dataclass
class CustomCodeUploadEvent:
    """
    Custom code upload event.
    """

    id: UUID
    event_id: UUID
    system: str
    code: str
    name: str


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
        LEFT JOIN configurations_conditions cc ON cc.configuration_id = c.id AND cc.is_primary = true
        LEFT JOIN conditions cond ON cond.id = cc.condition_id AND (%s::TEXT IS NULL OR cond.canonical_url = %s)
        WHERE e.jurisdiction_id = %s
        AND (%s::TEXT IS NULL OR cond.id IS NOT NULL);
    """
    params = (canonical_url, canonical_url, jurisdiction_id, canonical_url)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if not row:
                return None
            return int(row["total_count"])


async def is_event_valid(
    id: UUID, jurisdiction_id: str, db: AsyncDatabaseConnection
) -> bool:
    """
    Check that the event exists within a jurisdiction.
    """

    query = """
    SELECT 1
    FROM events
    WHERE id = %s
    AND jurisdiction_id = %s
    """
    params = (id, jurisdiction_id)
    async with db.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            return row is not None


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
            c.version AS configuration_version,
            cond.id AS condition_id,
            e.action_text,
            e.created_at,
            EXISTS (
                SELECT 1 FROM events_custom_code_uploads ecu WHERE ecu.event_id = e.id
            ) AS has_custom_code_upload_events
        FROM events e
        LEFT JOIN users u ON e.user_id = u.id
        LEFT JOIN configurations c ON e.configuration_id = c.id
        LEFT JOIN configurations_conditions cc ON cc.configuration_id = c.id AND cc.is_primary = true
        LEFT JOIN conditions cond ON cond.id = cc.condition_id
                                AND (%s::TEXT IS NULL OR cond.canonical_url = %s)
        WHERE e.jurisdiction_id = %s
        AND (%s::TEXT IS NULL OR cond.id IS NOT NULL)
        ORDER BY e.created_at DESC
        LIMIT %s OFFSET %s;
    """
    params = (
        canonical_url,
        canonical_url,
        jurisdiction_id,
        canonical_url,
        page_size,
        offset,
    )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(AuditEvent)) as cur:
            await cur.execute(query, params)
            events_rows = await cur.fetchall()
            return events_rows


async def get_custom_code_upload_events_by_event_id(
    event_id: UUID, db: AsyncDatabaseConnection
) -> list[CustomCodeUploadEvent]:
    """
    Returns all custom code upload events for an event ID.
    """
    query = """
    SELECT
        id,
        event_id,
        system,
        code,
        name
    FROM events_custom_code_uploads
    WHERE event_id = %s
    """
    params = (event_id,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(CustomCodeUploadEvent)) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()
            return rows


async def insert_custom_code_upload_events_db(
    configuration: DbConfiguration,
    user_id: UUID,
    custom_codes: list[DbConfigurationCustomCode],
    cursor: AsyncCursor[Any],
) -> None:
    """
    Helper function to insert a bulk custom code upload event and its subevents.
    """

    # No events to insert
    if len(custom_codes) < 1:
        return

    # Bulk upload event info
    event = EventInput(
        jurisdiction_id=configuration.jurisdiction_id,
        user_id=user_id,
        configuration_id=configuration.id,
        event_type="bulk_add_custom_code",
        action_text=f"Added {len(custom_codes)} custom codes from CSV",
    )

    event_id = await insert_event_db(event=event, cursor=cursor)

    await cursor.executemany(
        """
        INSERT INTO events_custom_code_uploads (event_id, system, code, name)
        VALUES (%s, %s, %s, %s)
        """,
        [(event_id, cc.system_key, cc.code, cc.name) for cc in custom_codes],
    )


async def insert_event_db(
    event: EventInput,
    cursor: AsyncCursor[Any],
) -> UUID:
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
        RETURNING id;
    """
    params = (
        event.user_id,
        event.jurisdiction_id,
        event.configuration_id,
        event.event_type,
        event.action_text,
    )

    await cursor.execute(query, params)
    row = await cursor.fetchone()
    if row is None:
        raise Exception(f"Unable to insert event with type: {event.event_type}")
    return row["id"]
