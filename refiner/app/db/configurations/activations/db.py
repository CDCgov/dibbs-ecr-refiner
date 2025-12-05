from uuid import UUID

from fastapi import HTTPException, status
from psycopg import AsyncCursor
from psycopg.rows import class_row

from app.db.configurations.db import (
    GetConfigurationResponseVersion,
    get_active_config_db,
    get_configuration_by_id_db,
)
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
    user_jurisdiction_id: str,
    canonical_url: str,
    db: AsyncDatabaseConnection,
) -> GetConfigurationResponseVersion | None:
    """
    Activate the specified configuration and return relevant status info.
    """

    config_to_activate = await get_configuration_by_id_db(
        id=configuration_id,
        jurisdiction_id=user_jurisdiction_id,
        db=db,
    )
    if not config_to_activate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Configuration is not found or isn't editable by the specified user jurisdiction permissions.",
        )

    current_active_config = await get_active_config_db(
        jurisdiction_id=user_jurisdiction_id,
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
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Couldn't deactivate configuration that needed to be deactivated before activating new configuration.",
                        )

                    active_config = await _activate_configuration_db(
                        configuration_id=config_to_activate.id, cur=cur
                    )
                    if not active_config:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Configuration can't be activated.",
                        )
                    await conn.commit()
                    return active_config
                except Exception as e:
                    await conn.rollback()

                    # bubble up exception to the API layer to return to the client
                    raise e
                finally:
                    await cur.close()
                    await conn.close()


async def deactivate_configuration_db(
    configuration_id: UUID,
    db: AsyncDatabaseConnection,
    user_jurisdiction_id: str,
) -> GetConfigurationResponseVersion | None:
    """
    Deactivate the specified configuration and return relevant status info.
    """
    config_to_deactivate = await get_configuration_by_id_db(
        id=configuration_id,
        jurisdiction_id=user_jurisdiction_id,
        db=db,
    )
    if not config_to_deactivate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Configuration to deactivate can't be found or isn't editable by the current user jurisdiction permissions.",
        )

    async with db.get_connection() as conn:
        async with conn.cursor(
            row_factory=class_row(GetConfigurationResponseVersion)
        ) as internal_cur:
            return await _deactivate_configuration_db(
                configuration_id, cur=internal_cur
            )
