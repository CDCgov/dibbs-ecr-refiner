from typing import Any
from uuid import UUID

from psycopg import AsyncCursor
from psycopg.rows import dict_row

from app.db.configurations.db import (
    get_active_config_db,
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
    *,
    cur: AsyncCursor[CursorType],
) -> DbConfiguration | None:
    query = """
            UPDATE configurations
            SET
                status = 'active',
                last_activated_by = %s
            WHERE id = %s
                RETURNING
                id,
                name,
                status,
                jurisdiction_id,
                condition_id,
                included_conditions,
                custom_codes,
                local_codes,
                section_processing,
                version,
                last_activated_at,
                last_activated_by,
                created_by,
                condition_canonical_url;
        """

    params = (
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

    return DbConfiguration.from_db_row(row)


async def _deactivate_configuration_db(
    configuration_id: UUID,
    user_id: UUID,
    jurisdiction_id: str,
    *,
    cur: AsyncCursor[CursorType],
) -> DbConfiguration | None:
    query = """
        WITH updated AS (
            UPDATE configurations
            SET status = 'inactive'
            WHERE id = %s
            AND status = 'active'
            RETURNING
                id,
                name,
                status,
                jurisdiction_id,
                condition_id,
                included_conditions,
                custom_codes,
                local_codes,
                section_processing,
                version,
                last_activated_at,
                last_activated_by,
                created_by,
                condition_canonical_url
        ),
        unchanged AS (
            SELECT
                id,
                name,
                status,
                jurisdiction_id,
                condition_id,
                included_conditions,
                custom_codes,
                local_codes,
                section_processing,
                version,
                last_activated_at,
                last_activated_by,
                created_by,
                condition_canonical_url
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

    return DbConfiguration.from_db_row(row)


async def activate_configuration_db(
    configuration_id: UUID,
    activated_by_user_id: UUID,
    canonical_url: str,
    jurisdiction_id: str,
    db: AsyncDatabaseConnection,
) -> DbConfiguration | None:
    """
    Activate the specified configuration and return relevant status info.

    If there's an active configuration already for the given canonical url,
    deactivate it first to maintain the rules around a condition having a single
    active configuration.
    """

    current_active_config = await get_active_config_db(
        jurisdiction_id=jurisdiction_id,
        condition_canonical_url=canonical_url,
        db=db,
    )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            if not current_active_config:
                # just activate the configuration without deactivating
                activated_config = await _activate_configuration_db(
                    configuration_id=configuration_id,
                    activated_by_user_id=activated_by_user_id,
                    jurisdiction_id=jurisdiction_id,
                    cur=cur,
                )
                if activated_config:
                    return activated_config
            else:
                # perform deactivation and activation in a single transaction so we don't run into half-deactivation states
                deactivated_config = await _deactivate_configuration_db(
                    configuration_id=current_active_config.id,
                    user_id=activated_by_user_id,
                    jurisdiction_id=jurisdiction_id,
                    cur=cur,
                )
                if not deactivated_config:
                    raise Exception(
                        "Couldn't deactivate configuration that needed to be deactivated before activating new configuration.",
                    )

                activated_config = await _activate_configuration_db(
                    configuration_id=configuration_id,
                    activated_by_user_id=activated_by_user_id,
                    jurisdiction_id=jurisdiction_id,
                    cur=cur,
                )
                if activated_config:
                    return activated_config

    return None


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
            return await _deactivate_configuration_db(
                configuration_id=configuration_id,
                user_id=user_id,
                jurisdiction_id=jurisdiction_id,
                cur=internal_cur,
            )
