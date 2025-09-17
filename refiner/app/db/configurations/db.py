from dataclasses import dataclass
from uuid import UUID

from psycopg.rows import class_row, dict_row
from psycopg.types.json import Jsonb

from ..conditions.model import DbCondition
from ..pool import AsyncDatabaseConnection
from .model import (
    DbConfiguration,
    DbConfigurationCustomCode,
)

EMPTY_JSONB = Jsonb([])


async def insert_configuration_db(
    condition: DbCondition,
    jurisdiction_id: str,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Inserts a configuration into the database.

    The `name` field is always set to the display_name of the associated condition at creation time,
    for easier display and searching. The authoritative clinical context is still given by `condition_id`.
    """

    query = """
    INSERT INTO configurations (
        jurisdiction_id,
        condition_id,
        name,
        included_conditions,
        custom_codes,
        local_codes,
        sections_to_include,
        version
    )
    VALUES (
        %s,
        %s,
        %s,
        %s::jsonb,
        %s::jsonb,
        %s::jsonb,
        %s::text[],
        %s
    )
    RETURNING
        id,
        name,
        jurisdiction_id,
        condition_id,
        included_conditions,
        custom_codes,
        local_codes,
        sections_to_include,
        version
    """

    params = (
        jurisdiction_id,
        # always link a configuration to a primary condition
        condition.id,
        # always set name to condition display name
        condition.display_name,
        # included_conditions: always start with primary
        Jsonb(
            [
                {
                    "canonical_url": condition.canonical_url,
                    "version": condition.version,
                }
            ]
        ),
        # custom_codes
        EMPTY_JSONB,
        # local_codes
        EMPTY_JSONB,
        # sections_to_include (empty array)
        [],
        # version (start at 1 for new configs)
        1,
    )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if not row:
        return None

    return DbConfiguration.from_db_row(row)


async def get_configurations_db(
    jurisdiction_id: str, db: AsyncDatabaseConnection
) -> list[DbConfiguration]:
    """
    Fetch all configurations from the DB for a given jurisdiction.
    """

    query = """
        SELECT
            id,
            name,
            jurisdiction_id,
            condition_id,
            included_conditions,
            custom_codes,
            local_codes,
            sections_to_include,
            version
        FROM configurations
        WHERE jurisdiction_id = %s
        ORDER BY name asc;
        """

    params = (jurisdiction_id,)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    return [DbConfiguration.from_db_row(row) for row in rows]


async def get_configuration_by_id_db(
    id: UUID, jurisdiction_id: str, db: AsyncDatabaseConnection
) -> DbConfiguration | None:
    """
    Fetch a configuration by the given ID.
    """

    query = """
        SELECT
            id,
            name,
            jurisdiction_id,
            condition_id,
            included_conditions,
            custom_codes,
            local_codes,
            sections_to_include,
            version
        FROM configurations
        WHERE id = %s
        AND jurisdiction_id = %s
        """

    params = (
        id,
        jurisdiction_id,
    )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if not row:
        return None

    return DbConfiguration.from_db_row(row)


async def is_config_valid_to_insert_db(
    condition_id: UUID, jurisdiction_id: str, db: AsyncDatabaseConnection
) -> bool:
    """
    Query the database to check if a configuration can be created. If a config for a condition already exists, returns False.
    """

    query = """
        SELECT id
        from configurations
        WHERE condition_id = %s
        AND jurisdiction_id = %s
        """

    params = (
        condition_id,
        jurisdiction_id,
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

    NOTE: If the primary condition ever changes, you should also update the `name` field to match the new condition's display_name.

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
                FROM new_condition,
                     jsonb_array_elements(new_condition.val) elem
                WHERE NOT EXISTS (
                SELECT 1
                FROM jsonb_array_elements(included_conditions) existing
                WHERE existing->>'canonical_url' = elem->>'canonical_url'
                    AND existing->>'version' = elem->>'version'
                )
            ) s
            )
            WHERE id = %s
            RETURNING
                id,
                name,
                jurisdiction_id,
                condition_id,
                included_conditions,
                custom_codes,
                local_codes,
                sections_to_include,
                version
            ;
            """

    new_condition = Jsonb(
        [{"canonical_url": condition.canonical_url, "version": condition.version}]
    )
    params = (new_condition, config.id)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if not row:
        return None

    return DbConfiguration.from_db_row(row)


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
        RETURNING
            id,
            name,
            jurisdiction_id,
            condition_id,
            included_conditions,
            custom_codes,
            local_codes,
            sections_to_include,
            version
    """
    params = (
        condition.canonical_url,
        condition.version,
        config.id,
    )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if not row:
        return None

    return DbConfiguration.from_db_row(row)


@dataclass(frozen=True)
class DbTotalConditionCodeCount:
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
            RETURNING
                id,
                name,
                jurisdiction_id,
                condition_id,
                included_conditions,
                custom_codes,
                local_codes,
                sections_to_include,
                version
            ;
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
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if not row:
        return None
    return DbConfiguration.from_db_row(row)


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
            RETURNING
                id,
                name,
                jurisdiction_id,
                condition_id,
                included_conditions,
                custom_codes,
                local_codes,
                sections_to_include,
                version
            ;
            """

    updated_custom_codes = [
        {"code": cc.code, "system": cc.system, "name": cc.name}
        for cc in config.custom_codes
        if not (cc.system == system and cc.code == code)
    ]

    params = (Jsonb(updated_custom_codes), config.id)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if not row:
        return None

    return DbConfiguration.from_db_row(row)


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
            RETURNING
                id,
                name,
                jurisdiction_id,
                condition_id,
                included_conditions,
                custom_codes,
                local_codes,
                sections_to_include,
                version
            ;
            """

    json_codes = [
        {"code": cc.code, "system": cc.system, "name": cc.name}
        for cc in updated_custom_codes
    ]

    params = (Jsonb(json_codes), config.id)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if not row:
        return None

    return DbConfiguration.from_db_row(row)
