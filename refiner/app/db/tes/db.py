from uuid import UUID

from psycopg.rows import class_row

from app.db.pool import AsyncDatabaseConnection
from app.db.tes.model import ConditionDiffExportData, DbTes, DbTesConditionUpdate


async def get_loaded_tes_versions_db(db: AsyncDatabaseConnection) -> list[DbTes]:
    """
    Returns an array off all loaded TES version records.

    Args:
        db (AsyncDatabaseConnection): The DB connection pool.

    Returns:
        list[DbTes]: A list of all the relevant TES details needed for the diff page
    """
    query = """
    SELECT
        id,
        version,
        created_at,
        updated_at
    FROM tes
    ORDER BY version
    """
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbTes)) as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            return rows


async def _get_tes_by_version_number_db(
    db: AsyncDatabaseConnection, version: str
) -> DbTes:
    """
    Returns a TES record by its version number.

    Args:
        db (AsyncDatabaseConnection): The DB connection pool.
        version (str): The TES version number.

    Returns:
        DbTes: the TES record.
    """
    query = """
    SELECT
        id,
        version,
        created_at,
        updated_at
    FROM tes
    WHERE version = %s
    ORDER BY version
    """

    params = (version,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbTes)) as cur:
            await cur.execute(query=query, params=params)
            row = await cur.fetchone()

            if not row:
                raise ValueError(f"No record found for TES version {version}")
            return row


async def _get_baseline_tes_diff_db(
    db: AsyncDatabaseConnection, tes_id: UUID
) -> list[DbTesConditionUpdate]:
    """
    Returns the TES update details for the first TES update, treating all conditions in that condition as "new.

    Args:
        db (AsyncDatabaseConnection): The DB connection pool.
        tes_id (UUID): The TES version ID to grab data for.

    Returns:
        DbTesCondition: The condition that changed codes between versions.
    """

    query = """
        SELECT DISTINCT
            c.canonical_url,
            c.display_name,
            COALESCE(array_agg(cc.code_id)) as added_code_ids,
            '{}'::text[] as removed_code_ids,
            TRUE as is_new
        FROM conditions_codes cc
        JOIN conditions c ON cc.condition_id = c.id
        WHERE c.tes_id = %(tes_id)s
        GROUP BY c.canonical_url, c.display_name
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbTesConditionUpdate)) as cur:
            await cur.execute(query, {"tes_id": tes_id})
            result = await cur.fetchall()
            return result


async def _get_baseline_tes_update_condition_diff_db(
    db: AsyncDatabaseConnection,
    tes_record: DbTes,
    cond_url: str,
) -> ConditionDiffExportData:
    query = """
        SELECT
            cond.canonical_url,
            cond.display_name AS condition_name,
            COALESCE(
                jsonb_agg(
                    jsonb_build_object(
                        'code', c.code,
                        'system_name', s.display_name,
                        'display', c.display
                    )
                ) FILTER (WHERE c.id IS NOT NULL),
                '[]'::jsonb
            ) AS added_codes,
            '{}'::text[] as removed_codes
        FROM conditions_codes cc
        LEFT JOIN conditions cond ON cc.condition_id = cond.id
        LEFT JOIN codes c ON c.id = cc.code_id
        LEFT JOIN tes t ON cond.tes_id = t.id
        LEFT JOIN systems s ON c.system_id = s.id
        WHERE cond.tes_id = %(tes_id)s AND cond.canonical_url = %(cond_url)s
        GROUP BY
            cond.canonical_url,
            cond.display_name;
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(ConditionDiffExportData)) as cur:
            await cur.execute(
                query,
                {
                    "tes_id": tes_record.id,
                    "cond_url": cond_url,
                },
            )
            result = await cur.fetchone()
            if not result:
                raise ValueError(
                    f"Condition with URL {cond_url} not found for TES versions {tes_record.version} "
                )
            return result


async def get_tes_update_condition_diff_db(
    db: AsyncDatabaseConnection,
    cur_version: str,
    prev_version: str,
    cond_url: str,
) -> ConditionDiffExportData:
    """
    Returns an array of codes for a specified condition within the specified TES diff.

    Args:
        db (AsyncDatabaseConnection): The DB connection pool.
        cur_version(str): The ceiling TES version to diff against
        prev_version(str): The floor TES version to diff against
        cond_url(str): The condition URL to retrieve the diff from

    Returns:
        list[DbTes]: A list of all the relevant TES details needed for the diff page
    """
    (cur_tes_record, prev_tes_record) = await _get_cur_and_prev_tes_records_db(
        db=db, cur_version=cur_version, prev_version=prev_version
    )

    if cur_tes_record.id == prev_tes_record.id:
        return await _get_baseline_tes_update_condition_diff_db(
            db=db, tes_record=cur_tes_record, cond_url=cond_url
        )

    query = """
    WITH combined AS (
        SELECT
            cond.canonical_url,
            cond.display_name AS condition_name,
            cond.tes_id,
            c.id AS code_id,
            c.code,
            c.display AS code_name,
            s.display_name AS system_name
        FROM conditions cond
        JOIN (
            SELECT DISTINCT condition_id, code_id
            FROM conditions_codes
        ) cc ON cc.condition_id = cond.id
        JOIN codes c ON c.id = cc.code_id
        LEFT JOIN systems s ON s.id = c.system_id
        WHERE cond.canonical_url = %(cond_url)s
            AND cond.tes_id IN (%(cur_tes_id)s, %(prev_tes_id)s)
    ),
    cur AS (
        SELECT * FROM combined WHERE tes_id = %(cur_tes_id)s
    ),
    prev AS (
        SELECT * FROM combined WHERE tes_id = %(prev_tes_id)s
    )
    SELECT
        COALESCE(cur.canonical_url, prev.canonical_url) AS canonical_url,
        MAX(COALESCE(cur.condition_name, prev.condition_name)) AS condition_name,
        COALESCE(
            jsonb_agg(
                jsonb_build_object(
                    'code', cur.code,
                    'system_name', cur.system_name,
                    'display', cur.code_name
                )
            ) FILTER (WHERE prev.code_id IS NULL AND cur.code_id IS NOT NULL),
            '[]'::jsonb
        ) AS added_codes,
        COALESCE(
            jsonb_agg(
                jsonb_build_object(
                    'code', prev.code,
                    'system_name', prev.system_name,
                    'display', prev.code_name
                )
            ) FILTER (WHERE cur.code_id IS NULL AND prev.code_id IS NOT NULL),
            '[]'::jsonb
        ) AS removed_codes
    FROM cur
    FULL OUTER JOIN prev
    ON cur.canonical_url = prev.canonical_url
        AND cur.code_id = prev.code_id
    GROUP BY
        COALESCE(cur.canonical_url, prev.canonical_url)
    HAVING
        COUNT(cur.code_id) FILTER (WHERE prev.code_id IS NULL) > 0
        OR COUNT(prev.code_id) FILTER (WHERE cur.code_id IS NULL) > 0;
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(ConditionDiffExportData)) as cur:
            await cur.execute(
                query,
                {
                    "cur_tes_id": cur_tes_record.id,
                    "prev_tes_id": prev_tes_record.id,
                    "cond_url": cond_url,
                },
            )
            result = await cur.fetchone()
            if not result:
                raise ValueError(
                    f"Condition with URL {cond_url} not found for TES versions {cur_version} or {prev_version} "
                )
            return result


async def _get_tes_update_diff_db(
    db: AsyncDatabaseConnection, cur_tes_id: UUID, prev_tes_id: UUID
) -> list[DbTesConditionUpdate]:
    """
    Returns all TES update details between the current and previous ID.

    Args:
        db (AsyncDatabaseConnection): The DB connection pool.
        cur_tes_id (UUID): The current TES version ID.
        prev_tes_id (UUID): The PREVIOUS TES version ID.

    Returns:
        list[DbTesCondition]: All conditions that have changed codes between versions.
    """
    if cur_tes_id == prev_tes_id:
        return await _get_baseline_tes_diff_db(db=db, tes_id=cur_tes_id)

    query = """
    WITH combined AS (
        SELECT DISTINCT
            c.id AS condition_id,
            c.canonical_url,
            c.display_name,
            c.tes_id,
            cc.code_id
        FROM conditions c
        JOIN conditions_codes cc ON cc.condition_id = c.id
        WHERE c.tes_id IN (%(cur_tes_id)s, %(prev_tes_id)s)
    ),
    cur AS (
        SELECT * FROM combined WHERE tes_id = %(cur_tes_id)s
    ),
    prev AS (
        SELECT * FROM combined WHERE tes_id = %(prev_tes_id)s
    )
    SELECT
        COALESCE(cur.canonical_url, prev.canonical_url) AS canonical_url,
        MAX(COALESCE(cur.display_name, prev.display_name)) AS display_name,
        COALESCE(
            array_agg(cur.code_id) FILTER (WHERE prev.code_id IS NULL AND cur.code_id IS NOT NULL),
            '{}'::uuid[]
        ) AS added_code_ids,
        COALESCE(
            array_agg(prev.code_id) FILTER (WHERE cur.code_id IS NULL AND prev.code_id IS NOT NULL),
            '{}'::uuid[]
        ) AS removed_code_ids,
        (COUNT(prev.condition_id) = 0) AS is_new
    FROM cur
    FULL OUTER JOIN prev
        ON cur.canonical_url = prev.canonical_url
    AND cur.code_id = prev.code_id
    GROUP BY
        COALESCE(cur.canonical_url, prev.canonical_url)
    HAVING
        COUNT(cur.code_id) FILTER (WHERE prev.code_id IS NULL) > 0
        OR COUNT(prev.code_id) FILTER (WHERE cur.code_id IS NULL) > 0;
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbTesConditionUpdate)) as cur:
            await cur.execute(
                query, {"cur_tes_id": cur_tes_id, "prev_tes_id": prev_tes_id}
            )
            rows = await cur.fetchall()
            return rows


async def get_tes_version_diff_db(
    db: AsyncDatabaseConnection, cur_version: str, prev_version: str
) -> list[DbTesConditionUpdate]:
    """
    Returns an array off all loaded TES version records.
    """
    (cur_tes_record, prev_tes_record) = await _get_cur_and_prev_tes_records_db(
        db=db, cur_version=cur_version, prev_version=prev_version
    )
    return await _get_tes_update_diff_db(
        db=db, cur_tes_id=cur_tes_record.id, prev_tes_id=prev_tes_record.id
    )


async def _get_cur_and_prev_tes_records_db(
    db: AsyncDatabaseConnection, cur_version: str, prev_version: str
) -> tuple[DbTes, DbTes]:
    """Get current and previous TES records, setting prev to the current if it's the baseline."""
    cur_tes_record = await _get_tes_by_version_number_db(db=db, version=cur_version)
    prev_tes_record = (
        await _get_tes_by_version_number_db(db=db, version=prev_version)
        if prev_version
        else cur_tes_record
    )

    return (cur_tes_record, prev_tes_record)
