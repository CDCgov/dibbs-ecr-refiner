from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from ..conditions.model import DbCondition
from ..pool import AsyncDatabaseConnection
from .model import DbConfiguration


async def insert_configuration(
    condition: DbCondition, jurisdiction_id: str, db: AsyncDatabaseConnection
) -> DbConfiguration | None:
    """
    Inserts a configuration into the database.
    """

    query = """
    INSERT INTO configurations (
        family_id,
        version,
        jurisdiction_id,
        name,
        description,
        included_conditions,
        loinc_codes_additions,
        snomed_codes_additions,
        icd10_codes_additions,
        rxnorm_codes_additions,
        custom_codes,
        sections_to_include,
        cloned_from_configuration_id
    )
    VALUES (
        %s,
        %s,
        %s,
        %s,
        %s,
        %s::jsonb,
        %s::jsonb,
        %s::jsonb,
        %s::jsonb,
        %s::jsonb,
        %s::jsonb,
        %s::text[],
        %s
    )
    RETURNING
        id,
        family_id,
        jurisdiction_id,
        name,
        description,
        included_conditions,
        loinc_codes_additions,
        snomed_codes_additions,
        icd10_codes_additions,
        rxnorm_codes_additions,
        custom_codes,
        sections_to_include,
        cloned_from_configuration_id
    """

    params = (
        1000,  # family_id
        1,  # version
        jurisdiction_id,
        condition.display_name,
        condition.display_name,
        Jsonb(
            [
                {
                    "canonical_url": condition.canonical_url,
                    "version": condition.version,
                }
            ]
        ),  # included_conditions
        Jsonb([]),  # loinc_codes_additions
        Jsonb([]),  # snomed_codes_additions
        Jsonb([]),  # icd10_codes_additions
        Jsonb([]),  # rxnorm_codes_additions
        Jsonb([]),  # custom_codes
        [""],  # sections_to_include
        None,  # cloned_from_configuration_id
    )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbConfiguration)) as cur:
            await cur.execute(query, params)
            return await cur.fetchone()
