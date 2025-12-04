from typing import overload
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


async def update_configuration_activation_db(
    canonical_url: str,
    configuration_id: UUID,
    user_jurisdiction_id: str,
    db: AsyncDatabaseConnection,
) -> GetConfigurationResponseVersion:
    """
    Function that activates the specified config and orchestrates side effects.

    Overall function that checks for the requested configuration to activate and
    orchestrates any deactivations needed via the passed in canonical URL. In the case of a deactivation, we
    roll things into a single transaction to ensure any deactivation requests
    only happen if the corresponding activation also completes successfully.

    Args:
        configuration_id (UUID): The ID of the configuration we want to activate
        canonical_url (): The (potential) current active configuration
        user_jurisdiction_id (UUID): The jurisdiction ID of the user performing the action, used to check permissions
        db (AsyncDatabaseConnection): Database connection

    Raises:
        HTTPException: 403 if configuration is not found in JD
        HTTPException: 500 if configuration cannot be updated


    Returns:
        GetConfigurationResponseVersion: The updated configuration
    """
    # check to see if the config 1) exists and 2) is editable by the user
    # by checking via jurisdiction ID
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

    if current_active_config and current_active_config.id != configuration_id:
        # if there is an active config, roll the deactivate step and the activate step into a singular transaction
        # so we don't get into a half deactivated / half activated state
        async with db.get_connection() as conn:
            async with conn.cursor(
                row_factory=class_row(GetConfigurationResponseVersion)
            ) as transaction_cur:
                try:
                    # perform deactivation and activation in a single transaction so we don't run into half-deactivation states
                    deactivated_config = await deactivate_configuration_db(
                        configuration_id=current_active_config.id, cur=transaction_cur
                    )
                    if not deactivated_config:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Couldn't deactivate configuration that needed to be deactivated before activating new configuration.",
                        )

                    active_config = await activate_configuration_db(
                        configuration_id=config_to_activate.id, cur=transaction_cur
                    )
                    if not active_config:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Configuration can't be activated.",
                        )

                    return active_config
                except Exception as e:
                    await conn.rollback()

                    # bubble up exception to the API layer to return to the client
                    raise e
                finally:
                    await transaction_cur.close()
                    await conn.close()
    else:
        # if there's no current active config, then we can just activate
        # the specified config
        active_config = await activate_configuration_db(
            configuration_id=config_to_activate.id, db=db
        )
        if not active_config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Configuration can't be activated.",
            )

        return active_config


@overload
async def activate_configuration_db(
    configuration_id: UUID, *, db: AsyncDatabaseConnection, cur: None = None
) -> GetConfigurationResponseVersion | None:
    async with db.get_connection() as conn:
        async with conn.cursor(
            row_factory=class_row(GetConfigurationResponseVersion)
        ) as internal_cur:
            return await activate_configuration_db(configuration_id, cur=internal_cur)


@overload
async def activate_configuration_db(
    configuration_id: UUID,
    *,
    db: None = None,
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
    db: AsyncDatabaseConnection | None = None,
    cur: AsyncCursor[GetConfigurationResponseVersion] | None = None,
) -> GetConfigurationResponseVersion | None:
    """
    Activate the specified configuration and return relevant status info.
    """
    if db is None and cur is None:
        raise ValueError("Provide either a db connection or a cur")

    if cur is not None:
        # Set configuration to inactive if active, otherwise fallback and return the unupdated configuration
        return await activate_configuration_db(
            configuration_id=configuration_id, cur=cur
        )
    elif db is not None:
        return await activate_configuration_db(configuration_id=configuration_id, db=db)


@overload
async def deactivate_configuration_db(
    configuration_id: UUID, *, db: AsyncDatabaseConnection, cur: None = None
) -> GetConfigurationResponseVersion | None:
    async with db.get_connection() as conn:
        async with conn.cursor(
            row_factory=class_row(GetConfigurationResponseVersion)
        ) as internal_cur:
            return await deactivate_configuration_db(configuration_id, cur=internal_cur)


@overload
async def deactivate_configuration_db(
    configuration_id: UUID,
    *,
    db: None = None,
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


async def deactivate_configuration_db(
    configuration_id: UUID,
    db: AsyncDatabaseConnection | None = None,
    cur: AsyncCursor[GetConfigurationResponseVersion] | None = None,
) -> GetConfigurationResponseVersion | None:
    """
    Deactivate the specified configuration and return relevant status info.
    """

    if db is None and cur is None:
        raise ValueError("Provide either a db connection or a cur")

    if cur is not None:
        # Set configuration to inactive if active, otherwise fallback and return the unupdated configuration
        return await deactivate_configuration_db(
            configuration_id=configuration_id, cur=cur
        )
    elif db is not None:
        return await deactivate_configuration_db(
            configuration_id=configuration_id, db=db
        )
