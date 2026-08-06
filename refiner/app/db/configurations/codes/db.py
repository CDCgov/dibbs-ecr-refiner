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
    condition_id: UUID | None
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

    code: str
    condition_id: str | None  # this will be `None` when `in_custom=True`
    in_custom: bool = False


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
    Given a configuration ID, fetch a paginated set of condition codes and custom codes associated with the configuration.

    Condition code set codes are returned first (ordered by condition_id, code), followed
    by all custom codes (ordered by code). Custom codes begin only once all
    condition code pages are exhausted, indicated by `cursor.in_custom` being True.

    Returns a tuple of (codes, next_cursor), where `next_cursor` is `None` if
    there are no more pages.
    """
    rows: list[DbCodeResult] = []
    next_cursor: str | None = None

    decoded = _decode_cursor(cursor) if cursor else None
    in_custom = decoded.in_custom if decoded else False

    # Handle condition-linked codes
    # Skip this if we've moved on to custom
    if not in_custom:
        cond_params: list = [configuration_id]
        cursor_clause = ""

        if decoded:
            cursor_clause = "AND (cfgc.condition_id, c.code) > (%s, %s)"
            cond_params += [decoded.condition_id, decoded.code]

        cond_params.append(limit + 1)

        cond_query = f"""
            SELECT
                c.id,
                cfgc.condition_id,
                con.display_name || ' CG' AS source,
                c.code,
                c.display AS description,
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
                await cur.execute(cond_query, cond_params)
                cond_rows = await cur.fetchall()

        if len(cond_rows) >= limit:
            # More condition code pages remain, don't go for custom codes yet
            rows = cond_rows[:limit]
            last = rows[-1]
            next_cursor = _encode_cursor(
                DbCodeCursor(
                    condition_id=str(last.condition_id),
                    code=last.code,
                    in_custom=False,
                )
            )
            return rows, next_cursor

        # Carry condition codes forward to next page
        rows = cond_rows

    # Handle custom codes
    remaining = limit - len(rows) + 1  # +1 for next page
    custom_params: list = [configuration_id]
    custom_cursor_clause = ""

    if in_custom and decoded:
        custom_cursor_clause = "AND c.code > %s"
        custom_params.append(decoded.code)

    custom_params.append(remaining)

    custom_query = f"""
        SELECT
            c.id,
            NULL::uuid AS condition_id,
            'Custom Code' AS source,
            c.code,
            c.display AS description,
            c.system_id,
            s.display_name AS system_name,
            'included' AS status
        FROM custom_codes c
        JOIN systems s ON s.id = c.system_id
        WHERE c.configuration_id = %s
        {custom_cursor_clause}
        ORDER BY c.code
        LIMIT %s;
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeResult)) as cur:
            await cur.execute(custom_query, custom_params)
            custom_rows = await cur.fetchall()

    if len(custom_rows) > limit - len(rows):
        custom_rows = custom_rows[: remaining - 1]
        last = custom_rows[-1]
        next_cursor = _encode_cursor(
            DbCodeCursor(
                condition_id=None,
                code=last.code,
                in_custom=True,
            )
        )
    else:
        next_cursor = None

    rows += custom_rows
    return rows, next_cursor


@dataclass
class DbCodeResultCountMetadata:
    """
    Code count metadata.
    """

    total_code_count: int
    excluded_code_count: int
    code_set_count: int
    custom_code_count: int


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
        COUNT(DISTINCT cfgc.condition_id) AS code_set_count,
        (
            SELECT COUNT(*)
            FROM custom_codes cc2
            WHERE cc2.configuration_id = %(configuration_id)s
        ) AS custom_code_count
    FROM configurations_conditions cfgc
    JOIN conditions_codes cc ON cc.condition_id = cfgc.condition_id
    LEFT JOIN configurations_conditions_code_exclusions e
        ON e.configuration_id = cfgc.configuration_id
        AND e.condition_id = cfgc.condition_id
        AND e.code_id = cc.code_id
    WHERE cfgc.configuration_id = %(configuration_id)s;
    """

    params = {"configuration_id": configuration_id}
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeResultCountMetadata)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if not row:
                return None
            return row
