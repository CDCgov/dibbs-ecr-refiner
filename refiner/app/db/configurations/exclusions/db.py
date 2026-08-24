from collections import defaultdict
from uuid import UUID

from psycopg.rows import dict_row

from app.db.pool import AsyncDatabaseConnection

type CodeSystemKey = str
type ExcludedCodesByCondition = dict[UUID, set[tuple[CodeSystemKey, str]]]


async def get_code_exclusions_db(
    configuration_id: UUID, db: AsyncDatabaseConnection
) -> ExcludedCodesByCondition:
    """
    Fetches the codes a configuration has excluded, grouped by condition.

    Exclusions are stored as `code_id` references, but the projection that
    consumes them (`convert_config_to_storage_payload`) reads condition codes
    from the `conditions` JSONB columns, which carry no code ID. Resolving to
    `(system key, code)` here is what bridges the two representations; the
    `codes` table's UNIQUE (system_id, code) makes that resolution lossless.

    Args:
        configuration_id (UUID): The configuration whose exclusions to fetch
        db (AsyncDatabaseConnection): The async database connection

    Returns:
        ExcludedCodesByCondition: Excluded (system key, code) pairs keyed by
            condition ID. Conditions with no exclusions are absent.
    """

    query = """
    SELECT
        e.condition_id,
        s.key AS system_key,
        c.code
    FROM configurations_conditions_code_exclusions e
    JOIN codes c ON c.id = e.code_id
    JOIN systems s ON s.id = c.system_id
    WHERE e.configuration_id = %(configuration_id)s
    """
    params = {"configuration_id": configuration_id}

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

    excluded: ExcludedCodesByCondition = defaultdict(set)
    for row in rows:
        excluded[row["condition_id"]].add((row["system_key"], row["code"]))

    return dict(excluded)
