from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from packaging.version import parse
from psycopg.rows import class_row, dict_row

from app.db.configurations.model import DbConfigurationCondition

from ..pool import AsyncDatabaseConnection
from .model import DbCondition, DbConditionBase


async def get_conditions_by_version_db(
    db: AsyncDatabaseConnection, version: str
) -> list[DbConditionBase]:
    """
    Queries the database and retrieves a list of all conditions matching a specific version string.
    """

    query = """
            SELECT
                id,
                display_name,
                canonical_url,
                version
            FROM conditions
            WHERE version = %s
            ORDER BY display_name ASC;
            """

    params = (version,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbConditionBase)) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return rows


async def get_latest_conditions_db(
    db: AsyncDatabaseConnection,
) -> list[DbConditionBase]:
    """
    For each unique condition, retrieves the one with the highest semantic version.

    This function fetches all conditions and performs the version filtering in
    Python to ensure correct semantic versioning. It is used to populate the
    "Set up new configuration" dropdown so that users can only create
    configurations based on the most up-to-date value sets.
    """

    # STEP 1: FETCH ALL CONDITIONS
    # this query is simple, fast, and offloads the complex logic to python
    query = """
        SELECT
            id,
            display_name,
            canonical_url,
            version
        FROM conditions;
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbConditionBase)) as cur:
            await cur.execute(query)
            all_conditions = await cur.fetchall()

    if not all_conditions:
        return []

    # STEP 2: GROUP CONDITIONS BY CANONICAL URL
    # this creates a dictionary where each key is a unique `canonical_url`
    # and the value is a list of all condition objects with that URL
    grouped_conditions: dict[str, list[DbConditionBase]] = defaultdict(list)
    for cond in all_conditions:
        grouped_conditions[cond.canonical_url].append(cond)

    # STEP 3: HIGHLIGHT LATEST VERSION FOR EACH GROUP
    # iterate through the dictionary and use `max()` with `packaging.version.parse`
    # as the key to correctly identify the latest version for each condition
    latest_conditions: list[DbConditionBase] = [
        max(cond_group, key=lambda c: parse(c.version))
        for cond_group in grouped_conditions.values()
    ]

    # STEP 4: SORT/PACKAGE FINAL LIST
    # sort the final list alphabetically by `display_name` for a
    # consistent and user-friendly order in the ui dropdown
    latest_conditions.sort(key=lambda c: c.display_name)

    return latest_conditions


async def get_condition_by_id_db(
    id: UUID, db: AsyncDatabaseConnection
) -> DbCondition | None:
    """
    Gets a single, specific condition from the database by its primary key (UUID).
    """

    query = """
            SELECT
                id,
                canonical_url,
                display_name,
                version,
                child_rsg_snomed_codes,
                snomed_codes,
                loinc_codes,
                icd10_codes,
                rxnorm_codes
            FROM conditions
            WHERE id = %s
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
    (LOINC, SNOMED, ICD-10, RxNorm) from their respective JSONB columns
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
            id,
            display_name,
            canonical_url,
            version,
            child_rsg_snomed_codes,
            snomed_codes,
            loinc_codes,
            icd10_codes,
            rxnorm_codes
        FROM conditions
        WHERE child_rsg_snomed_codes && %s::text[];
    """

    params = (codes,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return [DbCondition.from_db_row(row) for row in rows]


async def get_included_conditions_db(
    included_conditions: list[DbConfigurationCondition], db: AsyncDatabaseConnection
) -> list[DbCondition]:
    """
    Fetches all conditions given an id.
    """

    # Extract UUIDs (as strings) from the included_conditions list
    condition_ids = [
        str(cond.id) for cond in included_conditions if getattr(cond, "id", None)
    ]

    if not condition_ids:
        return []  # nothing to fetch

    query = """
        SELECT *
        FROM conditions
        WHERE id = ANY(%s::uuid[]);
    """

    params = (condition_ids,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return [DbCondition.from_db_row(row) for row in rows]
