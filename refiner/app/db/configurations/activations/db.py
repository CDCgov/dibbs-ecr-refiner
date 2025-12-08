from uuid import UUID

from psycopg import AsyncCursor
from psycopg.rows import class_row

from app.db.configurations.db import (
    GetConfigurationResponseVersion,
    get_active_config_db,
)
from app.db.configurations.model import DbConfiguration
from app.db.pool import AsyncDatabaseConnection


async def _activate_configuration_db(
    configuration_id: UUID,
    *,
    cur: AsyncCursor[GetConfigurationResponseVersion],
) -> GetConfigurationResponseVersion | None:
    query = """
            UPDATE configurations
            SET status = 'active'
            WHERE id = %s
            RETURNING
                id,
                version,
                status,
                condition_canonical_url;
        """

    params = (configuration_id,)
    await cur.execute(query, params)
    row = await cur.fetchone()

    if not row:
        return None

    return GetConfigurationResponseVersion(
        id=row.id,
        version=row.version,
        status=row.status,
        condition_canonical_url=row.condition_canonical_url,
    )


async def _deactivate_configuration_db(
    configuration_id: UUID,
    *,
    cur: AsyncCursor[GetConfigurationResponseVersion],
) -> GetConfigurationResponseVersion | None:
    query = """
            WITH updated AS (
                UPDATE configurations
                SET status = 'inactive'
                WHERE id = %s
                AND status = 'active'
                RETURNING id, version, status, condition_canonical_url
            )
            SELECT id, version, status, condition_canonical_url
            FROM updated
            UNION ALL
            SELECT id, version, status, condition_canonical_url
            FROM configurations
            WHERE id = %s
            AND NOT EXISTS (SELECT 1 FROM updated);
        """

    params = (configuration_id, configuration_id)
    await cur.execute(query, params)
    row = await cur.fetchone()

    if not row:
        return None

    return GetConfigurationResponseVersion(
        id=row.id,
        version=row.version,
        status=row.status,
        condition_canonical_url=row.condition_canonical_url,
    )


async def activate_configuration_db(
    configuration_id: UUID,
    config_to_activate: DbConfiguration,
    canonical_url: str,
    jurisdiction_id: str,
    db: AsyncDatabaseConnection,
) -> GetConfigurationResponseVersion | None:
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
        async with conn.cursor(
            row_factory=class_row(GetConfigurationResponseVersion)
        ) as cur:
            if not current_active_config:
                # just activate the configuration without deactivating
                return await _activate_configuration_db(configuration_id, cur=cur)
            else:
                # set up the deactivation and activation in a transaction
                try:
                    # perform deactivation and activation in a single transaction so we don't run into half-deactivation states
                    deactivated_config = await _deactivate_configuration_db(
                        configuration_id=current_active_config.id, cur=cur
                    )
                    if not deactivated_config:
                        raise Exception(
                            "Couldn't deactivate configuration that needed to be deactivated before activating new configuration.",
                        )

                    active_config = await _activate_configuration_db(
                        configuration_id=config_to_activate.id, cur=cur
                    )
                    await conn.commit()
                    return active_config
                except Exception:
                    await conn.rollback()
                    return None

                finally:
                    await cur.close()
                    await conn.close()


async def deactivate_configuration_db(
    configuration_id: UUID,
    db: AsyncDatabaseConnection,
) -> GetConfigurationResponseVersion | None:
    """
    Deactivate the specified configuration and return relevant status info.
    """

    async with db.get_connection() as conn:
        async with conn.cursor(
            row_factory=class_row(GetConfigurationResponseVersion)
        ) as internal_cur:
            return await _deactivate_configuration_db(
                configuration_id=configuration_id,
                cur=internal_cur,
            )
