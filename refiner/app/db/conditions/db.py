from dataclasses import dataclass
from uuid import UUID

from psycopg.rows import class_row, dict_row

from ..pool import AsyncDatabaseConnection
from .model import DbCondition

# TES and refiner are currently using version 3.0.0 for CGs and its child RSGs
CURRENT_VERSION = "3.0.0"


async def get_conditions_db(db: AsyncDatabaseConnection) -> list[DbCondition]:
    """
    Queries the database and retrieves a list of conditions matching CURRENT_VERSION.

    Args:
        db (AsyncDatabaseConnection): Database connection.

    Returns:
        list[DbCondition]: List of conditions.
    """

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
            WHERE version = %s
            ORDER BY display_name ASC;
            """

    params = (CURRENT_VERSION,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    if not rows:
        raise Exception("No conditions found for version {CURRENT_VERSION}.")

    return [DbCondition.from_db_row(row) for row in rows]


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
            WHERE id = %s AND version = %s
            """

    params = (id, CURRENT_VERSION)

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

    if not rows:
        raise Exception(
            "Error: Codes were not unpacked from conditions table correctly."
        )

    return list(rows)


async def get_conditions_by_child_rsg_snomed_codes(
    db: AsyncDatabaseConnection, codes: list[str]
) -> list[DbCondition]:
    """
    Given a list of RC SNOMED codes, find their assocaited CG rows.

    Finds all conditions that are associated with the given list of child RSG SNOMED codes,
    matching CURRENT_VERSION.

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
        WHERE child_rsg_snomed_codes && %s::text[]
        AND version = %s;
    """

    params = (
        codes,
        CURRENT_VERSION,
    )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    if not rows:
        raise Exception(
            f"Did not find any matchng conditions for these RC SNOMED codes: {codes}"
        )

    return [DbCondition.from_db_row(row) for row in rows]
