from uuid import UUID

from psycopg.rows import class_row
from pydantic import BaseModel

from ..pool import AsyncDatabaseConnection
from .model import DbCondition


async def get_conditions_db(db: AsyncDatabaseConnection) -> list[DbCondition]:
    """
    Queries the database and retrieves a list of conditions with version 2.0.0.

    Args:
        db (AsyncDatabaseConnection): Database connection.

    Returns:
        list[Condition]: List of conditions.
    """
    query = """
            SELECT
                id,
                display_name,
                canonical_url,
                version
            FROM conditions
            WHERE version = '2.0.0'
            ORDER BY display_name ASC;
            """
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCondition)) as cur:
            await cur.execute(query)
            rows = await cur.fetchall()

    if not rows:
        raise Exception("No conditions found for version 2.0.0.")

    return rows


async def get_condition_by_id_db(
    id: UUID, db: AsyncDatabaseConnection
) -> DbCondition | None:
    """
    Gets a condition from the database with the provided ID.
    """

    query = """
        SELECT id,
        canonical_url,
        display_name,
        version
        FROM conditions
        WHERE version = '2.0.0'
        AND id = %s
        """
    params = (id,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCondition)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    return row


class GetConditionCode(BaseModel):
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
    Queries the database to collect code info about a given condition.
    """
    query = """
        WITH c AS (
            SELECT *
            FROM conditions
            WHERE id = %s
        )
        SELECT code, system, description
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
