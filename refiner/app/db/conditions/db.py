from dataclasses import dataclass
from uuid import UUID

from psycopg.rows import class_row, dict_row

from app.services.tes import get_latest_tes_version

from ..pool import AsyncDatabaseConnection
from .model import (
    ConditionSummary,
    DbCondition,
    DbConditionBase,
    DbConditionsContextGrouper,
)


async def get_loaded_tes_versions_db(db: AsyncDatabaseConnection) -> list[str]:
    """
    Queries the database for all TES versions available for use.
    """

    query = """
        SELECT
            DISTINCT(version)
        FROM tes
        ORDER BY version
    """
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query)
            rows = await cur.fetchall()

    return [row["version"] for row in rows]


async def _get_conditions_by_canonical_urls_and_version_db(
    canonical_urls: list[str], version: str, db: AsyncDatabaseConnection
) -> list[DbCondition]:
    query = """
            SELECT
                c.id,
                c.canonical_url
            FROM conditions c
            JOIN tes t ON t.id = c.tes_id
            WHERE c.canonical_url = ANY(%s)
            AND t.version = %s
            """

    params = (
        canonical_urls,
        version,
    )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    found_urls = {row["canonical_url"] for row in rows}
    missing = set(canonical_urls) - found_urls
    if missing:
        raise ValueError(
            f"Conditions not found for canonical_urls: {missing} and version: {version}"
        )

    condition_ids = [row["id"] for row in rows]

    return await get_conditions_by_ids(ids=condition_ids, db=db)


async def _get_condition_by_canonical_url_and_version_db(
    canonical_url: str, version: str, db: AsyncDatabaseConnection
) -> DbCondition:
    conditions = await _get_conditions_by_canonical_urls_and_version_db(
        canonical_urls=[canonical_url], version=version, db=db
    )

    conditions_length = len(conditions)

    if conditions_length == 0:
        raise ValueError("Expected 1 condition but received 0.")

    if conditions_length > 1:
        raise ValueError(f"Expected 1 condition but received {conditions_length}.")

    return conditions[0]


async def get_latest_tes_condition_db(
    condition: DbCondition, db: AsyncDatabaseConnection
) -> DbCondition:
    """
    Given a condition, finds the latest TES version of that condition and returns it.

    Args:
        condition (DbCondition): ID of condition to find the latest version of
        db: The database connection

    Returns:
        DbCondition: The latest version of the condition
    """
    tes_versions = await get_loaded_tes_versions_db(db=db)
    latest_version = get_latest_tes_version(available_versions=tes_versions)
    condition = await _get_condition_by_canonical_url_and_version_db(
        canonical_url=condition.canonical_url, version=latest_version, db=db
    )
    return condition


async def get_latest_tes_condition_ids_db(
    ids: list[UUID], db: AsyncDatabaseConnection
) -> list[UUID]:
    """
    Given a list of condition IDs, finds the latest TES versions of those conditions and returns the latest IDs.

    Args:
        ids (list[UUID]): IDs of conditions
        db (AsyncDatabaseConnection): The database connection

    Returns:
        list[id]: IDs of conditions for the latest TES version
    """

    # get the latest TES version
    tes_versions = await get_loaded_tes_versions_db(db=db)
    latest_version = get_latest_tes_version(available_versions=tes_versions)

    # get the condition objects for IDs passed in
    given_conditions = await get_conditions_by_ids(ids=ids, db=db)

    # get the associated canonical URLs for each ID
    canonical_urls = [gc.canonical_url for gc in given_conditions]

    # get the latest conditions by the canonical URL and most recent TES version
    latest_conditions = await _get_conditions_by_canonical_urls_and_version_db(
        canonical_urls=canonical_urls, version=latest_version, db=db
    )

    return [lc.id for lc in latest_conditions]


async def get_conditions_by_version_db(
    db: AsyncDatabaseConnection, version: str
) -> list[DbConditionBase]:
    """
    Queries the database and retrieves a list of all conditions matching a specific version string.
    """

    query = """
        SELECT
            c.id,
            c.display_name,
            c.canonical_url,
            t.version
        FROM conditions c
        JOIN tes t ON t.id = c.tes_id
        WHERE t.version = %s
        ORDER BY c.display_name ASC;
        """

    params = (version,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbConditionBase)) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return rows


async def get_condition_by_id_db(
    id: UUID, db: AsyncDatabaseConnection
) -> DbCondition | None:
    """
    Gets a single, specific condition from the database by its primary key (UUID).
    """

    query = """
            SELECT
                c.id,
                c.canonical_url,
                c.display_name,
                t.version,
                c.child_rsg_snomed_codes,
                c.snomed_codes,
                c.loinc_codes,
                c.icd10_codes,
                c.rxnorm_codes,
                c.cvx_codes,
                c.coverage_level,
                c.coverage_level_reason,
                c.coverage_level_date
            FROM conditions c
            JOIN tes t ON t.id = c.tes_id
            WHERE c.id = %s
            """

    params = (id,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if not row:
        return None

    return DbCondition.from_db_row(row)


# TODO:
# this is a candidate for a uniform Coding model
# that represents the combination of either:
# 1. a code and a display
# 2. a code, display, and system
@dataclass(frozen=True)
class GetConditionCode:
    """
    Model for a condition code.
    """

    code: str
    system: str
    description: str


async def get_condition_codes_by_condition_id_db(
    id: UUID, db: AsyncDatabaseConnection
) -> list[GetConditionCode]:
    """
    For a condition ID, flatten all codes into a GetConditionCode shape.

    For a given condition ID, unnests and combines all terminology codes
    (LOINC, SNOMED, ICD-10, RxNorm, CVX) from their respective JSONB columns
    into a single, flat list of GetConditionCode objects.
    """

    query = """
            WITH c AS (
                SELECT *
                FROM conditions
                WHERE id = %s
            )
            SELECT DISTINCT code, system, description
            FROM (
                SELECT
                    code_elem->>'code' AS code,
                    'LOINC' AS system,
                    code_elem->>'display' AS description
                FROM c
                CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.loinc_codes, '[]'::jsonb)) AS code_elem

                UNION ALL

                SELECT
                    code_elem->>'code' AS code,
                    'SNOMED' AS system,
                    code_elem->>'display' AS description
                FROM c
                CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.snomed_codes, '[]'::jsonb)) AS code_elem

                UNION ALL

                SELECT
                    code_elem->>'code' AS code,
                    'ICD-10' AS system,
                    code_elem->>'display' AS description
                FROM c
                CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.icd10_codes, '[]'::jsonb)) AS code_elem

                UNION ALL

                SELECT
                    code_elem->>'code' AS code,
                    'RxNorm' AS system,
                    code_elem->>'display' AS description
                FROM c
                CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.rxnorm_codes, '[]'::jsonb)) AS code_elem

                UNION ALL

                SELECT
                    code_elem->>'code' AS code,
                    'CVX' AS system,
                    code_elem->>'display' AS description
                FROM c
                CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.CVX_codes, '[]'::jsonb)) AS code_elem
            ) t
            WHERE code IS NOT NULL
            ORDER BY system, code;
            """

    params = (id,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(GetConditionCode)) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return list(rows)


async def get_conditions_by_child_rsg_snomed_codes_db(
    db: AsyncDatabaseConnection, codes: list[str]
) -> list[DbCondition]:
    """
    Given a list of RC SNOMED codes, find their assocaited CG rows.

    Finds all conditions that are associated with the given list of child RSG SNOMED codes
    for any potential version of that condition data.

    This uses the GIN index on the `child_rsg_snomed_codes` array column for performance.

    Args:
        db: The database connection.
        codes: A list of RC SNOMED codes extracted from an RR.

    Returns:
        A list of matching DbCondition objects.
    """

    if not codes:
        return []

    query = """
        SELECT
            c.id,
            c.display_name,
            c.canonical_url,
            t.version,
            c.child_rsg_snomed_codes,
            c.snomed_codes,
            c.loinc_codes,
            c.icd10_codes,
            c.rxnorm_codes,
            c.cvx_codes,
            c.coverage_level,
            c.coverage_level_reason,
            c.coverage_level_date
        FROM conditions c
        JOIN tes t ON t.id = c.tes_id
        WHERE child_rsg_snomed_codes && %s::text[];
    """

    params = (codes,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return [DbCondition.from_db_row(row) for row in rows]


async def get_conditions_by_ids(
    ids: list[UUID], db: AsyncDatabaseConnection
) -> list[DbCondition]:
    """
    Given a list of condition IDs, returns a list of condition records.
    """

    if not ids:
        return []

    query = """
        SELECT c.*, t.version
        FROM conditions c
        JOIN tes t ON t.id = c.tes_id
        WHERE c.id = ANY(%s);
    """

    params = (ids,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return [DbCondition.from_db_row(row) for row in rows]


async def get_primary_conditions_for_configurations_db(
    configuration_ids: list[UUID],
    db: AsyncDatabaseConnection,
) -> dict[UUID, DbCondition]:
    """
    Given a list of configuration IDs, return a mapping of configuration ID to primary condition.
    """
    query = """
        SELECT cc.configuration_id, cond.*, t.version
        FROM conditions cond
        JOIN configurations_conditions cc ON cc.condition_id = cond.id
        JOIN tes t ON t.id = cond.tes_id
        WHERE cc.configuration_id = ANY(%s)
        AND cc.is_primary = true
    """
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, (configuration_ids,))
            rows = await cur.fetchall()

    return {row["configuration_id"]: DbCondition.from_db_row(row) for row in rows}


async def get_primary_condition_db(
    configuration_id: UUID,
    db: AsyncDatabaseConnection,
) -> DbCondition | None:
    """
    Returns the primary condition for a configuration given its ID.

    Args:
        configuration_id (UUID): The configuration ID
        db (AsyncDatabaseConnection): The database connection

    Returns:
        DbCondition | None: The primary condition, or None if it can't be found.
    """
    results = await get_primary_conditions_for_configurations_db(
        configuration_ids=[configuration_id], db=db
    )
    return results.get(configuration_id)


async def get_included_conditions_db(
    included_conditions: list[UUID], db: AsyncDatabaseConnection
) -> list[DbCondition]:
    """
    Fetches all conditions given an id.
    """

    query = """
        SELECT c.*, t.version
        FROM conditions c
        JOIN tes t ON t.id = c.tes_id
        WHERE c.id = ANY(%s)
        ORDER BY c.id;
    """

    params = (included_conditions,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return [DbCondition.from_db_row(row) for row in rows]


async def get_context_groupers_by_condition_id_db(
    condition_id: UUID, db: AsyncDatabaseConnection
) -> list[DbConditionsContextGrouper]:
    """
    Fetches all conditions context grouper rows for a given condition ID.
    """
    query = """
        SELECT
            id,
            condition_id,
            name,
            category,
            canonical_url,
            code_count,
            completeness,
            created_at,
            updated_at
        FROM conditions_context_groupers
        WHERE condition_id = %s
    """
    params = (condition_id,)
    async with db.get_connection() as conn:
        async with conn.cursor(
            row_factory=class_row(DbConditionsContextGrouper)
        ) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()
            return rows


async def get_conditions_with_rsg_codes_db(
    db: AsyncDatabaseConnection,
) -> list[ConditionSummary]:
    """
    Function to fetch all conditions with joins into codes to grab the associated condition RSGs.

    Only grabs the conditions corresponding to the latest TES version.
    """
    query = """
        SELECT
            c.id,
            c.display_name,
            JSONB_AGG(JSONB_BUILD_OBJECT('display', codes.display, 'code', codes.code)) as rsg_codes
        FROM conditions as c
        JOIN tes t ON t.id = c.tes_id
        LEFT JOIN conditions_rsg_codes as rsg ON rsg.condition_id = c.id
        LEFT JOIN codes ON codes.id = rsg.code_id
        WHERE t.version = %s
        GROUP BY
            c.id,
            c.display_name
        ORDER BY LOWER(c.display_name);
    """
    version = get_latest_tes_version(await get_loaded_tes_versions_db(db=db))
    params = (version,)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return [ConditionSummary.from_db_row(r) for r in rows]
