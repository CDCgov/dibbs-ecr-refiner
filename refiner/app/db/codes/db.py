from uuid import UUID

from psycopg.rows import class_row

from app.core.models.terminology import CodeLabel, Coding
from app.db.pool import AsyncDatabaseConnection


async def get_rsg_codes_by_condition_id_db(
    condition_id: UUID, db: AsyncDatabaseConnection
) -> list[CodeLabel]:
    """
    Return the SNOMED codes that name a condition's child RSGs, with their labels.

    One row per `(code, label)`; the system is not carried because every child-RSG
    code is SNOMED by construction -- `is_child_rsg` means "this code is the SNOMED
    that names its own RSG". Callers render these, they do not match on them, which
    is why the return type is `CodeLabel` rather than `Coding`.
    """

    query = """
        SELECT c.code, c.display_name
        FROM conditions_codes_temp as cc
        LEFT JOIN codes c on c.id = cc.code_id
        WHERE cc.condition_id = %(condition_id)s AND cc.is_child_rsg;
    """
    async with (
        db.get_connection() as conn,
        conn.cursor(row_factory=class_row(CodeLabel)) as cur,
    ):
        await cur.execute(query, {"condition_id": condition_id})

        return await cur.fetchall()


async def get_pruned_configuration_codes_db(
    configuration_id: UUID, db: AsyncDatabaseConnection
) -> list[Coding]:
    """
    Every code a configuration contributes to `active.json`, minus its exclusions.

    Returns `Coding`, so the system arrives **resolved to an OID** rather than as a
    `systems.id` the caller has to look up again. The refiner matches on
    `(code, system_oid)`, which is the whole reason this shape exists.

    `system_oid` is the literal `"Other"` for custom codes in the catch-all system;
    that is a routing key into `OID_TO_SYSTEM_KEY_MAP`, not an identifier.

    Custom codes appear here only for configurations that have at least one row in
    `configurations_conditions` -- the branch below joins through it. Callers add
    `configuration.custom_codes` as well, which is why that belt-and-braces exists.
    """

    query = """
       SELECT DISTINCT code, display_name, system_oid
        FROM (
            -- Standard codes
            SELECT c.code, c.display_name, s.oid AS system_oid
            FROM configurations_conditions as cc
            JOIN conditions_codes_temp cond_codes ON cond_codes.condition_id = cc.condition_id
            JOIN codes c ON c.id = cond_codes.code_id
            JOIN systems s ON c.system_id = s.id
            WHERE cc.configuration_id = %(configuration_id)s
            AND NOT EXISTS (
                SELECT 1
                FROM configurations_conditions_code_exclusions ce
                WHERE ce.configuration_id = %(configuration_id)s AND ce.code_id = c.id
            )

            UNION ALL

            -- Custom codes
            SELECT cc_code.code, cc_code.display_name, s.oid AS system_oid
            FROM configurations_conditions cc
            JOIN custom_codes cc_code ON cc_code.configuration_id = cc.configuration_id
            JOIN systems s ON cc_code.system_id = s.id

            WHERE cc.configuration_id = %(configuration_id)s
        ) combined_codes
        ORDER BY code, system_oid, display_name;
    """

    async with (
        db.get_connection() as conn,
        conn.cursor(row_factory=class_row(Coding)) as cur,
    ):
        await cur.execute(query, {"configuration_id": configuration_id})

        return await cur.fetchall()
