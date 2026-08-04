import base64
import json
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from psycopg.rows import class_row

from app.db.pool import AsyncDatabaseConnection


@dataclass
class DbCodeResult:
    """
    Result from query.
    """

    id: UUID
    condition_id: UUID
    source: str
    code: str
    description: str
    system_id: UUID
    system_name: str
    status: Literal["included", "excluded"]


@dataclass
class DbCodeCursor:
    """
    Cursor object for pagination.
    """

    condition_id: str
    code: str


def _encode_cursor(cursor: DbCodeCursor) -> str:
    return base64.b64encode(
        json.dumps({"condition_id": cursor.condition_id, "code": cursor.code}).encode()
    ).decode()


def _decode_cursor(cursor: str) -> DbCodeCursor:
    data = json.loads(base64.b64decode(cursor).decode())
    return DbCodeCursor(**data)


async def get_codes_db(
    configuration_id: UUID,
    db: AsyncDatabaseConnection,
    limit: int,
    cursor: str | None = None,
) -> tuple[list[DbCodeResult], str | None]:
    """
    Given a configuration ID, fetch a paginated set of condition codes associated with the configuration using keyset pagination.

    Returns a tuple of (codes, next_cursor), where `next_cursor` is `None` if there are no more pages.
    """
    params = [configuration_id]
    cursor_clause = ""

    if cursor:
        decoded = _decode_cursor(cursor)
        cursor_clause = "AND (cfgc.condition_id, c.code) > (%s, %s)"
        params += [decoded.condition_id, decoded.code]

    params.append(limit + 1)

    query = f"""
        SELECT
            c.id,
            cfgc.condition_id,
            con.display_name || ' CG' AS source,
            c.code,
            c.display as description,
            c.system_id,
            s.display_name AS system_name,
            CASE WHEN e.code_id IS NULL THEN 'included' ELSE 'excluded' END AS status
        FROM configurations_conditions cfgc
        JOIN conditions con ON con.id = cfgc.condition_id
        JOIN conditions_codes cc ON cc.condition_id = cfgc.condition_id
        JOIN codes c ON c.id = cc.code_id
        JOIN systems s ON s.id = c.system_id
        LEFT JOIN configurations_conditions_code_exclusions e
            ON e.configuration_id = cfgc.configuration_id
            AND e.condition_id = cfgc.condition_id
            AND e.code_id = cc.code_id
        WHERE cfgc.configuration_id = %s
        {cursor_clause}
        ORDER BY cfgc.condition_id, c.code
        LIMIT %s;
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeResult)) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    if len(rows) > limit:
        rows = rows[:limit]
        next_cursor = _encode_cursor(
            DbCodeCursor(condition_id=str(rows[-1].condition_id), code=rows[-1].code)
        )
    else:
        next_cursor = None

    return rows, next_cursor


@dataclass
class DbCodeResultCountMetadata:
    """
    Code count metadata.
    """

    total_code_count: int
    excluded_code_count: int
    code_set_count: int


async def get_code_count_metadata_db(
    configuration_id: UUID, db: AsyncDatabaseConnection
) -> DbCodeResultCountMetadata | None:
    """
    Given a configuration ID, returns code count related metadata.
    """

    query = """
    SELECT
        COUNT(*) AS total_code_count,
        COUNT(*) FILTER (WHERE e.code_id IS NOT NULL) AS excluded_code_count,
        COUNT(DISTINCT cfgc.condition_id) AS code_set_count
    FROM configurations_conditions cfgc
    JOIN conditions_codes cc ON cc.condition_id = cfgc.condition_id
    LEFT JOIN configurations_conditions_code_exclusions e
        ON e.configuration_id = cfgc.configuration_id
        AND e.condition_id = cfgc.condition_id
        AND e.code_id = cc.code_id
    WHERE cfgc.configuration_id = %s;
    """
    params = (configuration_id,)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeResultCountMetadata)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if not row:
                return None
            return row
