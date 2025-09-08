from uuid import UUID

from psycopg.rows import class_row
from psycopg.types.json import Jsonb
from pydantic import BaseModel

from ..conditions.model import DbCondition
from ..pool import AsyncDatabaseConnection
from .model import DbConfiguration, DbConfigurationCustomCode


async def insert_configuration_db(
    condition: DbCondition, jurisdiction_id: str, db: AsyncDatabaseConnection
) -> DbConfiguration | None:
    """
    Inserts a configuration into the database.
    """

    query = """
    INSERT INTO configurations (
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


async def get_configurations_db(
    jurisdiction_id: str, db: AsyncDatabaseConnection
) -> list[DbConfiguration]:
    """
    Fetch all configurations from the DB for a given jurisdiction.
    """
    query = """
        SELECT
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
        FROM configurations
        WHERE jurisdiction_id = %s
        ORDER BY name asc;
        """
    params = (jurisdiction_id,)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbConfiguration)) as cur:
            await cur.execute(query, params)
            return await cur.fetchall()


async def get_configuration_by_id_db(
    id: UUID, jurisdiction_id: str, db: AsyncDatabaseConnection
) -> DbConfiguration | None:
    """
    Fetch a configuration by the given ID.
    """
    query = """
        SELECT
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
        FROM configurations
        WHERE id = %s
        AND jurisdiction_id = %s
        ORDER BY name asc;
        """
    params = (
        id,
        jurisdiction_id,
    )
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbConfiguration)) as cur:
            await cur.execute(query, params)
            return await cur.fetchone()


async def is_config_valid_to_insert_db(
    condition_name: str, jurisidiction_id: str, db: AsyncDatabaseConnection
) -> bool:
    """
    Query the database to check if a configuration can be created. If a config for a condition already exists, returns False.
    """
    query = """
        SELECT id
        from configurations
        WHERE name = %s
        AND jurisdiction_id = %s
        """
    params = (
        condition_name,
        jurisidiction_id,
    )
    async with db.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchall()

    if not row:
        return True

    return False


async def associate_condition_codeset_with_configuration_db(
    config: DbConfiguration, condition: DbCondition, db: AsyncDatabaseConnection
) -> DbConfiguration | None:
    """
    Given a condition, associate its set of codes with the specified configuration. Prevents the addition of duplicate conditions.

    Args:
        config (DbConfiguration): The configuration
        condition (DbCondition): The condition
        db (AsyncDatabaseConnection): Database connection

    Returns:
        DbConfiguration: The updated configuration
    """

    query = """
            WITH new_condition AS (
                SELECT %s::jsonb AS val
            )
            UPDATE configurations
            SET included_conditions = (
            SELECT jsonb_agg(elem)
            FROM (
                SELECT elem
                FROM jsonb_array_elements(included_conditions) elem
                UNION ALL
                SELECT elem
                FROM jsonb_array_elements(nc.val) elem
                WHERE NOT EXISTS (
                SELECT 1
                FROM jsonb_array_elements(included_conditions) existing
                WHERE existing->>'canonical_url' = elem->>'canonical_url'
                    AND existing->>'version' = elem->>'version'
                )
            ) s
            )
            FROM new_condition nc
            WHERE id = %s
            RETURNING *;
            """
    new_condition = Jsonb(
        [{"canonical_url": condition.canonical_url, "version": condition.version}]
    )
    params = (new_condition, config.id)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbConfiguration)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            return row


async def disassociate_condition_codeset_with_configuration_db(
    config: DbConfiguration, condition: DbCondition, db: AsyncDatabaseConnection
) -> DbConfiguration | None:
    """
    Given a condition, remove its codeset from the specified configuration.

    This is the opposite of associate_condition_codeset_with_configuration_db.

    Args:
        config (DbConfiguration): The configuration
        condition (DbCondition): The condition to remove
        db (AsyncDatabaseConnection): Database connection

    Returns:
        DbConfiguration: The updated configuration
    """

    query = """
        UPDATE configurations
        SET included_conditions = (
            SELECT COALESCE(jsonb_agg(elem), '[]'::jsonb)
            FROM (
                SELECT elem
                FROM jsonb_array_elements(included_conditions) elem
                WHERE NOT (
                    elem->>'canonical_url' = %s AND elem->>'version' = %s
                )
            ) filtered
        )
        WHERE id = %s
        RETURNING *;
    """
    params = (
        condition.canonical_url,
        condition.version,
        config.id,
    )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbConfiguration)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            return row


class DbTotalConditionCodeCount(BaseModel):
    """
    Total code count model.
    """

    condition_id: UUID
    display_name: str
    total_codes: int


async def get_total_condition_code_counts_by_configuration_db(
    config_id: UUID, db: AsyncDatabaseConnection
) -> list[DbTotalConditionCodeCount]:
    """
    Given a config ID, returns the total associated code count by condition.
    """

    query = """
            WITH conds AS (
                SELECT jsonb_array_elements(included_conditions) AS cond
                FROM configurations
                WHERE id = %s
            ),
            codes AS (
                SELECT
                    c.id AS condition_id,
                    code_elem->>'code' AS code
                FROM conds
                JOIN conditions c
                    ON c.canonical_url = cond->>'canonical_url'
                    AND c.version = cond->>'version'
                CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.loinc_codes, '[]'::jsonb)) AS code_elem
                UNION
                SELECT
                    c.id AS condition_id,
                    code_elem->>'code' AS code
                FROM conds
                JOIN conditions c
                    ON c.canonical_url = cond->>'canonical_url'
                    AND c.version = cond->>'version'
                CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.snomed_codes, '[]'::jsonb)) AS code_elem
                UNION
                SELECT
                    c.id AS condition_id,
                    code_elem->>'code' AS code
                FROM conds
                JOIN conditions c
                    ON c.canonical_url = cond->>'canonical_url'
                    AND c.version = cond->>'version'
                CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.icd10_codes, '[]'::jsonb)) AS code_elem
                UNION
                SELECT
                    c.id AS condition_id,
                    code_elem->>'code' AS code
                FROM conds
                JOIN conditions c
                    ON c.canonical_url = cond->>'canonical_url'
                    AND c.version = cond->>'version'
                CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.rxnorm_codes, '[]'::jsonb)) AS code_elem
            )
            SELECT
                c.id AS condition_id,
                c.display_name,
                COUNT(DISTINCT code) AS total_codes
            FROM conditions c
            JOIN codes cd ON c.id = cd.condition_id
            GROUP BY c.id, c.display_name
            ORDER BY c.display_name;
            """
    params = (config_id,)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbTotalConditionCodeCount)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchall()
            return row


async def add_custom_code_to_configuration_db(
    config: DbConfiguration,
    custom_code: DbConfigurationCustomCode,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Given a config, adds a user-defined custom code to the configuration.
    """
    query = """
            UPDATE configurations
            SET custom_codes = %s::jsonb
            WHERE id = %s
            RETURNING *;
            """

    custom_codes = config.custom_codes

    exists = any(
        (c.code == custom_code.code and c.system == custom_code.system)
        for c in custom_codes
    )

    if not exists:
        custom_codes.append(custom_code)

    json = [
        {"code": cc.code, "system": cc.system, "name": cc.name} for cc in custom_codes
    ]

    params = (Jsonb(json), config.id)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbConfiguration)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            return row


async def delete_custom_code_from_configuration_db(
    config: DbConfiguration,
    system: str,
    code: str,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Given a config, system, and custom code, deletes the custom code from the configuration.
    """

    query = """
            UPDATE configurations
            SET custom_codes = %s::jsonb
            WHERE id = %s
            RETURNING *;
            """

    updated_custom_codes = [
        {"code": cc.code, "system": cc.system, "name": cc.name}
        for cc in config.custom_codes
        if not (cc.system == system and cc.code == code)
    ]

    params = (Jsonb(updated_custom_codes), config.id)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbConfiguration)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            return row


async def edit_custom_code_from_configuration_db(
    config: DbConfiguration,
    updated_custom_codes: list[DbConfigurationCustomCode],
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Given a config and a list of custom codes, updates the configuration's custom codes using the provided list.
    """

    query = """
            UPDATE configurations
            SET custom_codes = %s::jsonb
            WHERE id = %s
            RETURNING *;
            """

    json_codes = [
        {"code": cc.code, "system": cc.system, "name": cc.name}
        for cc in updated_custom_codes
    ]

    params = (Jsonb(json_codes), config.id)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbConfiguration)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            return row
