from uuid import UUID

from psycopg.rows import class_row

from app.core.exceptions import InputValidationError, ValidationError
from app.db.pool import AsyncDatabaseConnection
from app.db.tes.model import (
    ConditionDiffExportData,
    DbTes,
    DbTesConditionUpdate,
    DbTesConfigsToUpdateResponse,
    TesConfigToUpdate,
)


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


async def _get_latest_tes_record_db(
    db: AsyncDatabaseConnection,
) -> DbTes:
    """
    Return the most recently loaded TES release.

    Args:
        db: The database connection pool.

    Returns:
        The newest TES database record.

    Raises:
        ValueError: If no TES releases have been loaded.
    """
    query = """
        SELECT
            id,
            version,
            created_at,
            updated_at
        FROM tes
        ORDER BY created_at DESC, version DESC
        LIMIT 1
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbTes)) as cur:
            await cur.execute(query)
            record = await cur.fetchone()

            if record is None:
                raise ValueError("No TES releases have been loaded.")

            return record


async def _get_tes_by_version_number_db(
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
    WHERE version = %(version)s
    ORDER BY version
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbTes)) as cur:
            await cur.execute(query=query, params={"version": version})
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
        FROM conditions_codes_temp cc
        JOIN conditions c ON cc.condition_id = c.id
        WHERE c.tes_id = %(tes_id)s
        GROUP BY c.canonical_url, c.display_name
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbTesConditionUpdate)) as cur:
            await cur.execute(query, {"tes_id": tes_id})
            result = await cur.fetchall()
            return result


async def _get_baseline_tes_update_condition_diff_db(
    db: AsyncDatabaseConnection,
    tes_record: DbTes,
    cond_url: str,
) -> ConditionDiffExportData:
    query = """
        SELECT DISTINCT
            cond.canonical_url,
            cond.display_name AS condition_name,
            COALESCE(
                jsonb_agg(
                    jsonb_build_object(
                        'code', c.code,
                        'system_name', s.display_name,
                        'system_id', s.id,
                        'display', c.display
                    )
                ) FILTER (WHERE c.id IS NOT NULL),
                '[]'::jsonb
            ) AS added_codes,
            '{}'::text[] as removed_codes
        FROM conditions_codes_temp cc
        LEFT JOIN conditions cond ON cc.condition_id = cond.id
        LEFT JOIN codes c ON cc.code_id = c.id
        LEFT JOIN tes t ON cond.tes_id = t.id
        LEFT JOIN systems s ON c.system_id = s.id
        WHERE cond.tes_id = %(tes_id)s AND cond.canonical_url = %(cond_url)s
        GROUP BY
            cond.canonical_url,
            cond.display_name;
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(ConditionDiffExportData)) as cur:
            await cur.execute(
                query,
                {
                    "tes_id": tes_record.id,
                    "cond_url": cond_url,
                },
            )
            result = await cur.fetchone()
            if not result:
                raise ValueError(
                    f"Condition with URL {cond_url} not found for TES versions {tes_record.version} "
                )
            return result


async def get_tes_update_condition_diff_db(
    db: AsyncDatabaseConnection,
    cur_version: str,
    prev_version: str,
    cond_url: str,
) -> ConditionDiffExportData:
    """
    Returns an array of codes for a specified condition within the specified TES diff.

    Args:
        db (AsyncDatabaseConnection): The DB connection pool.
        cur_version(str): The ceiling TES version to diff against
        prev_version(str): The floor TES version to diff against
        cond_url(str): The condition URL to retrieve the diff from

    Returns:
        list[DbTes]: A list of all the relevant TES details needed for the diff page
    """
    (cur_tes_record, prev_tes_record) = await _get_cur_and_prev_tes_records_db(
        db=db, cur_version=cur_version, prev_version=prev_version
    )

    if cur_tes_record.id == prev_tes_record.id:
        return await _get_baseline_tes_update_condition_diff_db(
            db=db, tes_record=cur_tes_record, cond_url=cond_url
        )

    query = """
        WITH cur AS (
            SELECT DISTINCT
                cond.canonical_url,
                cond.display_name as condition_name,
                c.code,
                s.display_name as system_name,
                s.id as system_id,
                c.display as code_name,
                c.id as code_id
            FROM conditions_codes_temp cc
            LEFT JOIN conditions cond ON cc.condition_id = cond.id
            LEFT JOIN codes c ON cc.code_id = c.id
            LEFT JOIN tes t ON cond.tes_id = t.id
            LEFT JOIN systems s ON c.system_id = s.id
            WHERE cond.tes_id = %(cur_tes_id)s AND cond.canonical_url = %(cond_url)s
        ),
        prev AS (
            SELECT DISTINCT
                cond.canonical_url,
                cond.display_name as condition_name,
                c.code,
                s.display_name as system_name,
                s.id as system_id,
                c.display as code_name,
                c.id as code_id
            FROM conditions_codes_temp cc
            LEFT JOIN conditions cond ON cc.condition_id = cond.id
            LEFT JOIN codes c ON cc.code_id = c.id
            LEFT JOIN tes t ON cond.tes_id = t.id
            LEFT JOIN systems s ON c.system_id = s.id
            WHERE cond.tes_id = %(prev_tes_id)s AND cond.canonical_url = %(cond_url)s
        )
        SELECT
            COALESCE (prev.canonical_url, cur.canonical_url) AS canonical_url,
            MAX(COALESCE(cur.condition_name, prev.condition_name)) AS condition_name,
            COALESCE(JSONB_AGG(
                JSONB_BUILD_OBJECT(
                    'code', cur.code,
                    'system_name', cur.system_name,
                    'system_id', cur.system_id,
                    'display', cur.code_name
                ))
            FILTER (WHERE prev.code_id IS NULL), '[]'::jsonb) as added_codes,
            COALESCE(JSONB_AGG(
                JSONB_BUILD_OBJECT(
                    'code', prev.code,
                    'system_name', prev.system_name,
                    'system_id', prev.system_id,
                    'display', prev.code_name
                ))
            FILTER (WHERE cur.code_id IS NULL), '[]'::jsonb) as removed_codes
        FROM cur
        FULL OUTER JOIN prev
            ON cur.canonical_url = prev.canonical_url
            AND cur.code_id = prev.code_id
        GROUP BY
            COALESCE (prev.canonical_url, cur.canonical_url)
        HAVING
            COUNT(cur.code_id) FILTER (WHERE prev.code_id IS NULL) > 0
            OR COUNT(prev.code_id) FILTER (WHERE cur.code_id IS NULL) > 0;
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(ConditionDiffExportData)) as cur:
            await cur.execute(
                query,
                {
                    "cur_tes_id": cur_tes_record.id,
                    "prev_tes_id": prev_tes_record.id,
                    "cond_url": cond_url,
                },
            )
            result = await cur.fetchone()
            if not result:
                raise ValueError(
                    f"Condition with URL {cond_url} not found for TES versions {cur_version} or {prev_version} "
                )
            return result


async def _get_tes_update_diff_db(
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
   WITH tes_records AS (
        SELECT
            c.canonical_url,
            c.display_name,
            cc.code_id,
            BOOL_OR(c.tes_id = %(cur_tes_id)s) AS in_cur,
            BOOL_OR(c.tes_id = %(prev_tes_id)s) AS in_prev
        FROM conditions_codes_temp cc
        JOIN conditions c ON cc.condition_id = c.id
        WHERE c.tes_id IN (%(cur_tes_id)s, %(prev_tes_id)s)
        GROUP BY c.canonical_url, c.display_name, cc.code_id
    )
    SELECT
        canonical_url,
        display_name,
        COALESCE(ARRAY_AGG(code_id) FILTER (WHERE in_cur AND NOT in_prev), '{}'::uuid[]) AS added_code_ids,
        COALESCE(ARRAY_AGG(code_id) FILTER (WHERE in_prev AND NOT in_cur), '{}'::uuid[]) AS removed_code_ids,
        NOT BOOL_OR(in_prev) AS is_new
    FROM tes_records
    GROUP BY canonical_url, display_name
    HAVING
        COUNT(*) FILTER (WHERE in_cur AND NOT in_prev) > 0
        OR COUNT(*) FILTER (WHERE in_prev AND NOT in_cur) > 0;
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbTesConditionUpdate)) as cur:
            await cur.execute(
                query, {"cur_tes_id": cur_tes_id, "prev_tes_id": prev_tes_id}
            )
            rows = await cur.fetchall()
            return rows


async def get_tes_version_diff_db(
    db: AsyncDatabaseConnection, cur_version: str, prev_version: str
) -> list[DbTesConditionUpdate]:
    """
    Returns an array off all loaded TES version records.
    """
    (cur_tes_record, prev_tes_record) = await _get_cur_and_prev_tes_records_db(
        db=db, cur_version=cur_version, prev_version=prev_version
    )
    return await _get_tes_update_diff_db(
        db=db, cur_tes_id=cur_tes_record.id, prev_tes_id=prev_tes_record.id
    )


async def _get_cur_and_prev_tes_records_db(
    db: AsyncDatabaseConnection, cur_version: str, prev_version: str
) -> tuple[DbTes, DbTes]:
    """Get current and previous TES records, setting prev to the current if it's the baseline."""
    cur_tes_record = await _get_tes_by_version_number_db(db=db, version=cur_version)
    prev_tes_record = (
        await _get_tes_by_version_number_db(db=db, version=prev_version)
        if prev_version
        else cur_tes_record
    )

    return (cur_tes_record, prev_tes_record)


async def get_configurations_set_to_tes_version(
    db: AsyncDatabaseConnection,
    jurisdiction_id: str,
) -> DbTesConfigsToUpdateResponse:
    """
    Return drafts and active configurations that use an older TES release.

    Existing drafts can be updated in place. Active configurations must first
    be copied into a new draft before applying the latest TES release.

    Args:
        db: The database connection pool.
        jurisdiction_id: The jurisdiction belonging to the current user.

    Returns:
        Existing outdated drafts and outdated active configurations.
    """
    latest_tes_record = await _get_latest_tes_record_db(db=db)

    query = """
        SELECT
            conf.id AS configuration_id,
            conf.name AS configuration_name,
            COALESCE(
                array_agg(
                    DISTINCT cond.display_name
                    ORDER BY cond.display_name
                ) FILTER (WHERE cond.display_name IS NOT NULL),
                '{}'::text[]
            ) AS codesets_to_update,
            MAX(t.version) AS configuration_tes_version
        FROM configurations conf
        JOIN configurations_conditions cc
            ON cc.configuration_id = conf.id
        JOIN conditions cond
            ON cond.id = cc.condition_id
        JOIN tes t
            ON t.id = cond.tes_id
        WHERE cond.tes_id <> %(latest_tes_id)s
            AND conf.status = %(status)s
            AND conf.jurisdiction_id = %(jurisdiction_id)s
            AND (
                %(status)s <> 'active'
                OR NOT EXISTS (
                    SELECT 1
                    FROM configurations draft_conf
                    JOIN configurations_conditions draft_cc
                        ON draft_cc.configuration_id = draft_conf.id
                        AND draft_cc.is_primary = true
                    JOIN conditions draft_cond
                        ON draft_cond.id = draft_cc.condition_id
                    WHERE draft_conf.status = 'draft'
                        AND draft_conf.jurisdiction_id = conf.jurisdiction_id
                        AND draft_cond.canonical_url = cond.canonical_url
                )
            )
        GROUP BY
            conf.id,
            conf.name
        ORDER BY
            conf.name
    """

    params = {
        "latest_tes_id": latest_tes_record.id,
        "jurisdiction_id": jurisdiction_id,
    }

    async with (
        db.get_connection() as conn,
        conn.cursor(row_factory=class_row(TesConfigToUpdate)) as cur,
    ):
        await cur.execute(
            query,
            {
                **params,
                "status": "draft",
            },
        )
        draft_rows = await cur.fetchall()

        await cur.execute(
            query,
            {
                **params,
                "status": "active",
            },
        )
        active_rows = await cur.fetchall()

    return DbTesConfigsToUpdateResponse(
        existing_drafts=draft_rows,
        drafts_to_create=active_rows,
    )


async def _raise_if_invalid_draft_configurations(
    db: AsyncDatabaseConnection,
    configuration_ids: list[UUID],
    jurisdiction_id: str,
) -> None:
    """
    Validate that all configurations are drafts, exist, and belong to the jurisdiction.

    Args:
        db (AsyncDatabaseConnection): The DB connection pool.
        configuration_ids (list[UUID]): Draft configuration IDs to validate.
        jurisdiction_id (str): The jurisdiction belonging to the current user.

    Raises:
        InputValidationError: If one or more selected configurations could not be
            updated because they do not exist, are not drafts, or do not belong to
            the current jurisdiction.
    """
    async with db.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                    SELECT id
                    FROM configurations
                    WHERE id = ANY(%(configuration_ids)s)
                        AND status = 'draft'
                        AND jurisdiction_id = %(jurisdiction_id)s
                    FOR UPDATE
                    """,
                {
                    "configuration_ids": configuration_ids,
                    "jurisdiction_id": jurisdiction_id,
                },
            )

            eligible_ids = {row[0] for row in await cur.fetchall()}

            if eligible_ids != set(configuration_ids):
                raise InputValidationError(
                    "One or more selected configurations could not be "
                    "updated because they do not exist, are not drafts, "
                    "or do not belong to the current jurisdiction."
                )


async def _raise_if_conditions_missing_in_latest_tes(
    db: AsyncDatabaseConnection,
    configuration_ids: list[UUID],
    latest_tes_id: UUID,
) -> None:
    """
    Ensure every old condition has a corresponding condition in the latest TES release.

    Args:
        db (AsyncDatabaseConnection): The DB connection pool.
        configuration_ids (list[UUID]): Configuration IDs to validate.
        latest_tes_id (UUID): The ID of the latest TES release.

    Raises:
        ValidationError: If one or more conditions are missing from the latest TES release.
    """
    async with db.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                    SELECT DISTINCT
                        old_condition.canonical_url
                    FROM configurations_conditions cc
                    JOIN conditions old_condition
                        ON old_condition.id = cc.condition_id
                    LEFT JOIN conditions latest_condition
                        ON latest_condition.canonical_url =
                            old_condition.canonical_url
                        AND latest_condition.tes_id = %(latest_tes_id)s
                    WHERE cc.configuration_id =
                        ANY(%(configuration_ids)s)
                        AND old_condition.tes_id <> %(latest_tes_id)s
                        AND latest_condition.id IS NULL
                    ORDER BY old_condition.canonical_url
                    """,
                {
                    "configuration_ids": configuration_ids,
                    "latest_tes_id": latest_tes_id,
                },
            )

            missing_condition_urls = [row[0] for row in await cur.fetchall()]

            if missing_condition_urls:
                raise ValidationError(
                    "The following conditions could not be found in the "
                    "latest TES release: " + ", ".join(missing_condition_urls)
                )


async def _raise_if_conflicting_condition_links(
    db: AsyncDatabaseConnection,
    configuration_ids: list[UUID],
    latest_tes_id: UUID,
) -> None:
    """
    Prevent primary-key conflicts if a configuration is linked to both old and latest conditions.

    Args:
        db (AsyncDatabaseConnection): The DB connection pool.
        configuration_ids (list[UUID]): Configuration IDs to validate.
        latest_tes_id (UUID): The ID of the latest TES release.

    Raises:
        ValidationError: If conflicting condition links are present.
    """
    async with db.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                    SELECT DISTINCT
                        old_link.configuration_id,
                        old_condition.canonical_url
                    FROM configurations_conditions old_link
                    JOIN conditions old_condition
                        ON old_condition.id = old_link.condition_id
                    JOIN conditions latest_condition
                        ON latest_condition.canonical_url =
                            old_condition.canonical_url
                        AND latest_condition.tes_id = %(latest_tes_id)s
                    JOIN configurations_conditions latest_link
                        ON latest_link.configuration_id =
                            old_link.configuration_id
                        AND latest_link.condition_id =
                            latest_condition.id
                    WHERE old_link.configuration_id =
                        ANY(%(configuration_ids)s)
                        AND old_link.condition_id <> latest_condition.id
                    """,
                {
                    "configuration_ids": configuration_ids,
                    "latest_tes_id": latest_tes_id,
                },
            )

            conflicting_links = await cur.fetchall()

            if conflicting_links:
                raise ValidationError(
                    "One or more configurations already contain both old "
                    "and current versions of the same TES condition."
                )


async def apply_latest_tes_to_existing_drafts_db(
    db: AsyncDatabaseConnection,
    configuration_ids: list[UUID],
    jurisdiction_id: str,
) -> list[UUID]:
    """
    Update selected draft configurations to use the latest TES conditions.

    A condition is matched between TES releases using its canonical URL.
    Updating the configuration's condition ID causes the configuration to use
    the codes connected to the condition in the latest TES release.

    Args:
        db: The database connection pool.
        configuration_ids: Draft configuration IDs selected by the user.
        jurisdiction_id: The jurisdiction belonging to the current user.

    Returns:
        IDs of configurations that were updated.

    Raises:
        ValueError: If a selected configuration is not an eligible draft, a
            latest condition cannot be found, or conflicting condition links
            are present.
    """
    requested_ids = list(dict.fromkeys(configuration_ids))

    if not requested_ids:
        return []

    latest_tes_record = await _get_latest_tes_record_db(db=db)

    await _raise_if_invalid_draft_configurations(
        db=db, configuration_ids=requested_ids, jurisdiction_id=jurisdiction_id
    )
    await _raise_if_conditions_missing_in_latest_tes(
        db=db, configuration_ids=requested_ids, latest_tes_id=latest_tes_record.id
    )
    await _raise_if_conflicting_condition_links(
        db=db, configuration_ids=requested_ids, latest_tes_id=latest_tes_record.id
    )

    async with db.get_connection() as conn, conn.transaction():
        async with conn.cursor() as cur:
            # Replace each old condition link with the corresponding
            # condition from the latest TES release.
            #
            # is_primary remains unchanged because only condition_id is
            # updated.
            await cur.execute(
                """
                    WITH condition_replacements AS (
                        SELECT
                            cc.configuration_id,
                            cc.condition_id AS old_condition_id,
                            latest_condition.id AS latest_condition_id
                        FROM configurations_conditions cc
                        JOIN conditions old_condition
                            ON old_condition.id = cc.condition_id
                        JOIN conditions latest_condition
                            ON latest_condition.canonical_url =
                                old_condition.canonical_url
                            AND latest_condition.tes_id =
                                %(latest_tes_id)s
                        WHERE cc.configuration_id =
                            ANY(%(configuration_ids)s)
                            AND old_condition.tes_id <>
                                %(latest_tes_id)s
                    )
                    UPDATE configurations_conditions cc
                    SET condition_id =
                        replacements.latest_condition_id
                    FROM condition_replacements replacements
                    WHERE cc.configuration_id =
                        replacements.configuration_id
                        AND cc.condition_id =
                            replacements.old_condition_id
                    RETURNING cc.configuration_id
                    """,
                {
                    "configuration_ids": requested_ids,
                    "latest_tes_id": latest_tes_record.id,
                },
            )

            updated_id_set = {row[0] for row in await cur.fetchall()}

            # Updating configurations_conditions does not fire the
            # configurations updated_at trigger, so explicitly touch the
            # configurations that changed.
            if updated_id_set:
                await cur.execute(
                    """
                        UPDATE configurations
                        SET updated_at = NOW()
                        WHERE id = ANY(%(configuration_ids)s)
                        """,
                    {
                        "configuration_ids": list(updated_id_set),
                    },
                )

    # Keep the response in the same order as the request.
    return [
        configuration_id
        for configuration_id in requested_ids
        if configuration_id in updated_id_set
    ]


async def _raise_if_invalid_active_configurations(
    db: AsyncDatabaseConnection,
    configuration_ids: list[UUID],
    jurisdiction_id: str,
) -> list[tuple[UUID, str]]:
    """
    Validate that all configurations are active, exist, and belong to the jurisdiction.

    Args:
        db (AsyncDatabaseConnection): The DB connection pool.
        configuration_ids (list[UUID]): Active configuration IDs to validate.
        jurisdiction_id (str): The jurisdiction belonging to the current user.

    Returns:
        list[tuple[UUID, str]]: A list of (configuration_id, canonical_url) tuples.

    Raises:
        InputValidationError: If one or more selected configurations could not be
            cloned because they do not exist, are not active, or do not belong to
            the current jurisdiction.
    """
    async with db.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id,
                       (SELECT cond.canonical_url
                        FROM configurations_conditions cc
                        JOIN conditions cond ON cond.id = cc.condition_id
                        WHERE cc.configuration_id = configurations.id
                        AND cc.is_primary = true
                        LIMIT 1) as canonical_url
                FROM configurations
                WHERE id = ANY(%(configuration_ids)s)
                    AND status = 'active'
                    AND jurisdiction_id = %(jurisdiction_id)s
                FOR UPDATE
                """,
                {
                    "configuration_ids": configuration_ids,
                    "jurisdiction_id": jurisdiction_id,
                },
            )

            active_configs = await cur.fetchall()
            if len(active_configs) != len(configuration_ids):
                raise InputValidationError(
                    "One or more selected configurations could not be "
                    "cloned because they do not exist, are not active, "
                    "or do not belong to the current jurisdiction."
                )
            return active_configs


async def _raise_if_drafts_already_exist(
    db: AsyncDatabaseConnection,
    active_configs: list[tuple[UUID, str]],
    jurisdiction_id: str,
) -> None:
    """
    Check that no drafts already exist for each condition.

    Args:
        db (AsyncDatabaseConnection): The DB connection pool.
        active_configs (list[tuple[UUID, str]]): List of (configuration_id, canonical_url).
        jurisdiction_id (str): The jurisdiction belonging to the current user.

    Raises:
        ValidationError: If a draft configuration already exists for the
            condition associated with a configuration.
    """
    for row in active_configs:
        config_id, canonical_url = row
        # Local import to avoid circular dependency: tes.db -> configurations.db -> conditions.db -> tes.db
        from app.db.configurations.db import is_config_valid_to_insert_db

        if not await is_config_valid_to_insert_db(
            condition_canonical_url=canonical_url,
            jurisdiction_id=jurisdiction_id,
            db=db,
        ):
            raise ValidationError(
                f"A draft configuration already exists for the "
                f"condition associated with configuration {config_id}."
            )


async def create_drafts_from_active_configurations_db(
    db: AsyncDatabaseConnection,
    configuration_ids: list[UUID],
    jurisdiction_id: str,
    user_id: UUID,
) -> list[UUID]:
    """
    Create draft configurations from selected active configurations.

    Args:
        db: The database connection pool.
        configuration_ids: Active configuration IDs to clone.
        jurisdiction_id: The jurisdiction belonging to the current user.
        user_id: The user creating the drafts.

    Returns:
        IDs of the created draft configurations.

    Raises:
        ValueError: If a selected configuration is not an active config,
            does not belong to the jurisdiction, or a draft already exists
            for the condition.
    """
    from app.db.configurations.db import get_configuration_by_id_db

    requested_ids = list(dict.fromkeys(configuration_ids))

    if not requested_ids:
        return []

    active_configs = await _raise_if_invalid_active_configurations(
        db=db, configuration_ids=requested_ids, jurisdiction_id=jurisdiction_id
    )
    await _raise_if_drafts_already_exist(
        db=db, active_configs=active_configs, jurisdiction_id=jurisdiction_id
    )

    async with db.get_connection() as conn:
        async with conn.transaction():
            # Create drafts.
            created_ids = []
            for row in active_configs:
                config_id, _ = row

                config_to_clone = await get_configuration_by_id_db(
                    id=config_id, jurisdiction_id=jurisdiction_id, db=db
                )

                from app.db.conditions.db import get_primary_condition_db

                primary_condition = await get_primary_condition_db(
                    configuration_id=config_id, db=db
                )

                if not primary_condition:
                    raise ValueError(
                        f"Primary condition not found for configuration {config_id}"
                    )

                # Local import to avoid circular dependency: tes.db -> configurations.db -> conditions.db -> tes.db
                from app.db.configurations.db import insert_configuration_db

                new_config = await insert_configuration_db(
                    condition=primary_condition,
                    user_id=user_id,
                    jurisdiction_id=jurisdiction_id,
                    db=db,
                    config_to_clone=config_to_clone,
                )

                if not new_config:
                    raise ValueError(
                        f"Failed to create draft for configuration {config_id}"
                    )

                created_ids.append(new_config.id)

                # NOTE: In the future, this could be enhanced to allow partial success
                # by returning a list of successfully created drafts and a list of errors.

    return created_ids
