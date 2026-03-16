from typing import Any
from uuid import UUID

from psycopg import AsyncCursor
from psycopg.rows import dict_row

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
    s3_urls: list[str],
    *,
    cur: AsyncCursor[CursorType],
) -> UUID | None:
    query = """
            UPDATE configurations
            SET
                status = 'active',
                s3_urls = %s,
                last_activated_by = %s
            WHERE id = %s
                RETURNING
                id
        """

    params = (
        s3_urls,
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
                s3_urls = NULL
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


async def activate_configuration_db(
    configuration_id: UUID,
    activated_by_user_id: UUID,
    canonical_url: str,
    jurisdiction_id: str,
    s3_urls: list[str],
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

    activated_config_id = None

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            if not current_active_config:
                # just activate the configuration without deactivating
                activated_config_id = await _activate_configuration_db(
                    configuration_id=configuration_id,
                    activated_by_user_id=activated_by_user_id,
                    jurisdiction_id=jurisdiction_id,
                    s3_urls=s3_urls,
                    cur=cur,
                )
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

                activated_config_id = await _activate_configuration_db(
                    configuration_id=configuration_id,
                    activated_by_user_id=activated_by_user_id,
                    jurisdiction_id=jurisdiction_id,
                    s3_urls=s3_urls,
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
) -> UUID | None:
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
