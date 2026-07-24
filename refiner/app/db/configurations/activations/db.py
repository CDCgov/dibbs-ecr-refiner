from typing import Any
from uuid import UUID

from psycopg import AsyncCursor
from psycopg.rows import dict_row

from app.core.exceptions import ConfigurationActivationError
from app.db.configurations.db import (
    get_active_config_db,
    get_configuration_by_id_db,
)
from app.db.configurations.model import DbConfiguration
from app.db.events.db import insert_event_db
from app.db.events.model import EventInput
from app.db.pool import AsyncDatabaseConnection

type CursorType = dict[str, Any]


async def _activate_configuration_db(
    configuration_id: UUID,
    activated_by_user_id: UUID,
    jurisdiction_id: str,
    s3_url: str,
    *,
    cur: AsyncCursor[CursorType],
) -> UUID | None:
    query = """
            UPDATE configurations
            SET
                status = 'active',
                s3_url = %s,
                last_activated_by = %s
            WHERE id = %s
                RETURNING
                id
        """

    params = (
        s3_url,
        activated_by_user_id,
        configuration_id,
    )
    await cur.execute(query, params)
    row = await cur.fetchone()

    if not row:
        return None

    await insert_event_db(
        event=EventInput(
            configuration_id=configuration_id,
            user_id=activated_by_user_id,
            jurisdiction_id=jurisdiction_id,
            event_type="activate_configuration",
            action_text="Activated configuration",
        ),
        cursor=cur,
    )

    return row["id"]


async def _deactivate_configuration_db(
    configuration_id: UUID,
    user_id: UUID,
    jurisdiction_id: str,
    *,
    cur: AsyncCursor[CursorType],
) -> UUID | None:
    query = """
        WITH updated AS (
            UPDATE configurations
            SET
                status = 'inactive',
                s3_url = NULL
            WHERE id = %s
            AND status = 'active'
            RETURNING
                id
        ),
        unchanged AS (
            SELECT
                id
            FROM configurations
            WHERE id = %s
            AND NOT EXISTS (SELECT 1 FROM updated)
        )
        SELECT * FROM updated
        UNION ALL
        SELECT * FROM unchanged;
        """

    params = (configuration_id, configuration_id)
    await cur.execute(query, params)
    row = await cur.fetchone()

    if not row:
        return None

    await insert_event_db(
        event=EventInput(
            configuration_id=configuration_id,
            user_id=user_id,
            jurisdiction_id=jurisdiction_id,
            event_type="deactivate_configuration",
            action_text="De-activated configuration",
        ),
        cursor=cur,
    )

    return row["id"]


async def get_active_config_by_original_condition_id_db(
    jurisdiction_id: str,
    original_condition_id: UUID,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Given a jurisdiction ID and original_condition_id, find the active configuration version, if any.

    This is used for zero-code-set (ZCS) configurations that don't have a canonical_url.
    """
    query = """
        SELECT c.id
        FROM configurations c
        WHERE c.jurisdiction_id = %s
        AND c.original_condition_id = %s
        AND c.status = 'active'
        AND c.canonical_url IS NULL;
    """
    params = (jurisdiction_id, original_condition_id)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if not row:
        return None

    return await get_configuration_by_id_db(
        id=row["id"], jurisdiction_id=jurisdiction_id, db=db
    )


async def activate_configuration_db(
    configuration_id: UUID,
    activated_by_user_id: UUID,
    canonical_url: str | None,
    original_condition_id: UUID | None,
    jurisdiction_id: str,
    s3_url: str,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Activate the specified configuration and return relevant status info.

    If there's an active configuration already for the given canonical url,
    deactivate it first to maintain the rules around a condition having a single
    active configuration.

    For zero-code-set (ZCS) configurations (canonical_url is None), the
    original_condition_id is used to find and deactivate the prior active ZCS
    configuration for the same condition.

    Args:
        configuration_id: The ID of the configuration to activate
        activated_by_user_id: The ID of the user performing the activation
        canonical_url: The canonical URL of the condition (None for ZCS)
        original_condition_id: The original condition ID (used for ZCS deactivation)
        jurisdiction_id: The jurisdiction ID
        s3_url: The S3 URL for the configuration
        db: Database connection

    Returns:
        DbConfiguration | None: The activated configuration or None if activation failed
    """

    activated_config_id = None

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            if canonical_url:
                current_active_config = await get_active_config_db(
                    jurisdiction_id=jurisdiction_id,
                    condition_canonical_url=canonical_url,
                    db=db,
                )

                if current_active_config:
                    # perform deactivation and activation in a single transaction so we don't run into half-deactivation states
                    deactivated_config = await _deactivate_configuration_db(
                        configuration_id=current_active_config.id,
                        user_id=activated_by_user_id,
                        jurisdiction_id=jurisdiction_id,
                        cur=cur,
                    )
                    if not deactivated_config:
                        raise ConfigurationActivationError(
                            "Couldn't deactivate configuration that needed to be deactivated before activating new configuration.",
                        )
            elif original_condition_id:
                # For ZCS (zero-code-set) configs, deactivate the prior active ZCS for the same condition
                current_active_config = (
                    await get_active_config_by_original_condition_id_db(
                        jurisdiction_id=jurisdiction_id,
                        original_condition_id=original_condition_id,
                        db=db,
                    )
                )

                if current_active_config:
                    deactivated_config = await _deactivate_configuration_db(
                        configuration_id=current_active_config.id,
                        user_id=activated_by_user_id,
                        jurisdiction_id=jurisdiction_id,
                        cur=cur,
                    )
                    if not deactivated_config:
                        raise ConfigurationActivationError(
                            "Couldn't deactivate prior active ZCS configuration before activating new version.",
                        )

            activated_config_id = await _activate_configuration_db(
                configuration_id=configuration_id,
                activated_by_user_id=activated_by_user_id,
                jurisdiction_id=jurisdiction_id,
                s3_url=s3_url,
                cur=cur,
            )
    if not activated_config_id:
        return None

    return await get_configuration_by_id_db(
        id=activated_config_id, jurisdiction_id=jurisdiction_id, db=db
    )


async def deactivate_configuration_db(
    configuration_id: UUID,
    user_id: UUID,
    jurisdiction_id: str,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Deactivate the specified configuration and return relevant status info.
    """

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as internal_cur:
            deactivated_config_id = await _deactivate_configuration_db(
                configuration_id=configuration_id,
                user_id=user_id,
                jurisdiction_id=jurisdiction_id,
                cur=internal_cur,
            )
            if not deactivated_config_id:
                return None

    return await get_configuration_by_id_db(
        id=deactivated_config_id, jurisdiction_id=jurisdiction_id, db=db
    )
