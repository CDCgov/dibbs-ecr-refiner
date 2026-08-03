from uuid import UUID

from psycopg.rows import class_row

from app.db.pool import AsyncDatabaseConnection
from app.db.tes.model import DbTes, DbTesConditionUpdate


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


async def get_tes_by_version_number_db(
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
        SELECT
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


async def get_tes_update_diff_db(
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
    WITH curr AS (
        SELECT
            c.id as condition_id,
            c.canonical_url,
            cc.code_id,
            c.display_name
        FROM conditions_codes cc
        JOIN conditions c ON cc.condition_id = c.id
        WHERE c.tes_id = %(cur_tes_id)s
    ),
    prev AS (
        SELECT
            c.id as condition_id,
            c.canonical_url,
            c.display_name,
            cc.code_id
        FROM conditions_codes cc
        JOIN conditions c ON cc.condition_id = c.id
        WHERE c.tes_id = %(prev_tes_id)s
    )

    SELECT
        COALESCE(curr.canonical_url, prev.canonical_url) as canonical_url,
        MAX(COALESCE(curr.display_name, prev.display_name)) AS display_name,
        COALESCE(array_agg(curr.code_id) FILTER (where prev.code_id IS NULL), '{}'::uuid[]) as added_code_ids,
        COALESCE(array_agg(prev.code_id) FILTER (where curr.code_id IS NULL), '{}'::uuid[]) as removed_code_ids,
        FALSE as is_new

    FROM curr
    FULL OUTER JOIN prev
        ON curr.canonical_url = prev.canonical_url
        AND curr.code_id = prev.code_id
    GROUP BY
        COALESCE(curr.canonical_url, prev.canonical_url)
    HAVING
        COUNT(curr.code_id) FILTER (WHERE prev.code_id IS NULL) > 0
        OR COUNT(prev.code_id) FILTER (WHERE curr.code_id IS NULL) > 0;
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbTesConditionUpdate)) as cur:
            await cur.execute(
                query, {"cur_tes_id": cur_tes_id, "prev_tes_id": prev_tes_id}
            )
            rows = await cur.fetchall()
            return rows
