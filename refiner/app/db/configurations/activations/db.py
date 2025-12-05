from typing import overload
from uuid import UUID

from psycopg import AsyncCursor
from psycopg.rows import class_row

from app.db.configurations.db import (
    GetConfigurationResponseVersion,
)
from app.db.pool import AsyncDatabaseConnection


@overload
async def activate_configuration_db(
    configuration_id: UUID, *, db: AsyncDatabaseConnection, cur: None = None
) -> GetConfigurationResponseVersion | None: ...


@overload
async def activate_configuration_db(
    configuration_id: UUID,
    *,
    db: None = None,
    cur: AsyncCursor[GetConfigurationResponseVersion],
) -> GetConfigurationResponseVersion | None: ...


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
    if db is not None:
        async with db.get_connection() as conn:
            async with conn.cursor(
                row_factory=class_row(GetConfigurationResponseVersion)
            ) as internal_cur:
                return await activate_configuration_db(
                    configuration_id, cur=internal_cur
                )
    elif cur is not None:
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


@overload
async def deactivate_configuration_db(
    configuration_id: UUID, *, db: AsyncDatabaseConnection, cur: None = None
) -> GetConfigurationResponseVersion | None: ...


@overload
async def deactivate_configuration_db(
    configuration_id: UUID,
    *,
    db: None = None,
    cur: AsyncCursor[GetConfigurationResponseVersion],
) -> GetConfigurationResponseVersion | None: ...


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

    if db is not None:
        async with db.get_connection() as conn:
            async with conn.cursor(
                row_factory=class_row(GetConfigurationResponseVersion)
            ) as internal_cur:
                return await deactivate_configuration_db(
                    configuration_id, cur=internal_cur
                )

    elif cur is not None:
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
