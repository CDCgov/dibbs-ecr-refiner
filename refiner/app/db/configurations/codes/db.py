import base64
import json
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from psycopg.rows import class_row, dict_row

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

    Custom codes are returned first (ordered by code), followed by all condition
    code set codes (ordered by condition_id, code). Condition codes begin only
    once all custom code pages are exhausted, indicated by `cursor.in_custom`
    being False.

    Returns a tuple of (codes, next_cursor), where `next_cursor` is `None` if
    there are no more pages.
    """
    rows: list[DbCodeResult] = []
    next_cursor: str | None = None

    decoded = _decode_cursor(cursor) if cursor else None
    in_custom = decoded.in_custom if decoded else True  # start in custom

    # Handle custom codes first
    if in_custom:
        remaining = limit + 1  # +1 to detect next page
        custom_params: dict = {
            "configuration_id": configuration_id,
            "limit": remaining,
        }
        custom_cursor_clause = ""

        if decoded:
            custom_cursor_clause = "AND c.code > %(cursor_code)s"
            custom_params["cursor_code"] = decoded.code

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
            WHERE c.configuration_id = %(configuration_id)s
            {custom_cursor_clause}
            ORDER BY c.code
            LIMIT %(limit)s;
        """

        async with db.get_connection() as conn:
            async with conn.cursor(row_factory=class_row(DbCodeResult)) as cur:
                await cur.execute(custom_query, custom_params)
                custom_rows = await cur.fetchall()

        if len(custom_rows) >= remaining:
            # More custom code pages remain, don't go to condition codes yet
            rows = custom_rows[:limit]
            last = rows[-1]
            next_cursor = _encode_cursor(
                DbCodeCursor(
                    condition_id=None,
                    code=last.code,
                    in_custom=True,
                )
            )
            return rows, next_cursor

        # Carry custom codes forward
        rows = custom_rows

    # Handle condition-linked codes
    remaining = limit - len(rows) + 1  # +1 to detect next page
    cond_params: dict = {
        "configuration_id": configuration_id,
        "limit": remaining,
    }
    cursor_clause = ""

    if not in_custom and decoded:
        cursor_clause = "AND (cfgc.condition_id, c.code) > (%(cursor_condition_id)s, %(cursor_code)s)"
        cond_params["cursor_condition_id"] = decoded.condition_id
        cond_params["cursor_code"] = decoded.code

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
        JOIN conditions_codes_temp cc ON cc.condition_id = cfgc.condition_id
        JOIN codes c ON c.id = cc.code_id
        JOIN systems s ON s.id = c.system_id
        LEFT JOIN configurations_conditions_code_exclusions e
            ON e.configuration_id = cfgc.configuration_id
            AND e.code_id = cc.code_id
        WHERE cfgc.configuration_id = %(configuration_id)s
        {cursor_clause}
        ORDER BY cfgc.condition_id, c.code
        LIMIT %(limit)s;
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCodeResult)) as cur:
            await cur.execute(cond_query, cond_params)
            cond_rows = await cur.fetchall()

    if len(cond_rows) > limit - len(rows):
        cond_rows = cond_rows[: remaining - 1]
        last = cond_rows[-1]
        next_cursor = _encode_cursor(
            DbCodeCursor(
                condition_id=str(last.condition_id),
                code=last.code,
                in_custom=False,
            )
        )
    else:
        next_cursor = None

    rows += cond_rows
    return rows, next_cursor


async def set_codes_status_db(
    configuration_id: UUID,
    code_ids: list[UUID],
    status: Literal["included", "excluded"],
    db: AsyncDatabaseConnection,
) -> list[UUID]:
    """
    Given a list of code IDs and a status, updates the `configurations_conditions_code_exclusions` table.

    If `status="included"` is provided, entries will be deleted from the table.
    If `status="excluded"` is provided, entries will be added to the table. Since multiple
    conditions can share the same code ID, one row is inserted per (condition_id, code_id) pair.

    Args:
        configuration_id (UUID): ID of the configuration
        code_ids (list[UUID]): List of code IDs
        status (Literal['included', 'excluded'): Set codes as 'included' or 'excluded'
        db (AsyncDatabaseConnection): The database connection

    Returns:
        list[UUID]: List of impacted code IDs
    """
    if status == "included":
        query = """
            DELETE FROM configurations_conditions_code_exclusions
            WHERE configuration_id = %(configuration_id)s
              AND code_id = ANY(%(code_ids)s)
            RETURNING code_id
        """
    else:
        query = """
            INSERT INTO configurations_conditions_code_exclusions (configuration_id, code_id)
            SELECT %(configuration_id)s, UNNEST(%(code_ids)s::uuid[])
            ON CONFLICT DO NOTHING
            RETURNING code_id
        """

    params = {
        "configuration_id": configuration_id,
        "code_ids": code_ids,
    }

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return [row["code_id"] for row in rows]


@dataclass
class CodeSystemFilterOption:
    """
    Model to represent a code system filter option.
    """

    system_id: UUID
    system_name: str
    code_count: int


@dataclass
class SourceFilterOption:
    """
    Model to represent a source filter option.
    """

    condition_id: UUID | None  # This will be `None` for custom codes
    source: str
    code_count: int


@dataclass
class StatusFilterOption:
    """
    Model to represent a status filter option.
    """

    label: Literal["Included", "Excluded"]
    status: Literal["included", "excluded"]
    code_count: int


@dataclass
class CodeFilterOptions:
    """
    Model to represent all filter options available to the client.
    """

    code_systems: list[CodeSystemFilterOption]
    sources: list[SourceFilterOption]
    statuses: list[StatusFilterOption]


async def get_all_filter_options_db(
    configuration_id: UUID,
    db: AsyncDatabaseConnection,
) -> CodeFilterOptions:
    """
    Fetches filter options to present to the client.
    """
    query = """
    WITH all_codes AS (
        SELECT
            s.id AS system_id,
            s.display_name AS system_name,
            NULL::uuid AS source_id,
            'Custom Code' AS source,
            'included' AS status
        FROM custom_codes c
        JOIN systems s ON s.id = c.system_id
        WHERE c.configuration_id = %(configuration_id)s

        UNION ALL

        SELECT
            s.id AS system_id,
            s.display_name AS system_name,
            con.id AS source_id,
            con.display_name || ' CG' AS source,
            CASE WHEN e.code_id IS NULL THEN 'included' ELSE 'excluded' END AS status
        FROM configurations_conditions cfgc
        JOIN conditions con ON con.id = cfgc.condition_id
        JOIN conditions_codes cc ON cc.condition_id = cfgc.condition_id
        JOIN codes c ON c.id = cc.code_id
        JOIN systems s ON s.id = c.system_id
        LEFT JOIN configurations_conditions_code_exclusions e
            ON e.configuration_id = cfgc.configuration_id
            AND e.code_id = cc.code_id
        WHERE cfgc.configuration_id = %(configuration_id)s
    )
    SELECT * FROM (
        SELECT 'code_system' AS filter_type, s.id::text AS value, s.display_name AS label, COUNT(ac.system_id) AS code_count
        FROM systems s
        LEFT JOIN all_codes ac ON ac.system_id = s.id
        GROUP BY s.id, s.display_name

        UNION ALL

        SELECT 'source' AS filter_type, source_id::text AS value, source AS label, COUNT(*) AS code_count
        FROM all_codes
        GROUP BY source_id, source

        UNION ALL

        SELECT 'status' AS filter_type, s.status AS value, s.status_label AS label, COUNT(ac.status) AS code_count
        FROM (VALUES ('included', 'Included'), ('excluded', 'Excluded')) AS s(status, status_label)
        LEFT JOIN all_codes ac ON ac.status = s.status
        GROUP BY s.status, s.status_label
    ) AS filter_results
    ORDER BY filter_type, code_count DESC;
        """

    async with db.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, {"configuration_id": configuration_id})
            rows = await cur.fetchall()

    code_systems, sources, statuses = [], [], []
    for filter_type, value, label, code_count in rows:
        if filter_type == "code_system":
            code_systems.append(
                CodeSystemFilterOption(
                    system_id=UUID(value), system_name=label, code_count=code_count
                )
            )
        elif filter_type == "source":
            sources.append(
                SourceFilterOption(
                    condition_id=UUID(value) if value is not None else None,
                    source=label,
                    code_count=code_count,
                )
            )
        elif filter_type == "status":
            statuses.append(
                StatusFilterOption(status=value, label=label, code_count=code_count)
            )

    return CodeFilterOptions(
        code_systems=code_systems,
        sources=sources,
        statuses=statuses,
    )


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
    JOIN conditions_codes_temp cc ON cc.condition_id = cfgc.condition_id
    LEFT JOIN configurations_conditions_code_exclusions e
        ON e.configuration_id = cfgc.configuration_id
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
