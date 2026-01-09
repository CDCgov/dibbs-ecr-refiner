from datetime import UTC, datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.db.pool import AsyncDatabaseConnection, db

LOCK_TIMEOUT_MINUTES = 30


class ConfigurationLock:
    """
    Represents a lock for a configuration to prevent concurrent edits.
    """

    def __init__(self, configuration_id: UUID, user_id: UUID, expires_at: datetime):
        """
        Initialize a ConfigurationLock instance.
        """
        self.configuration_id = configuration_id
        self.user_id = user_id
        self.expires_at = expires_at

    @staticmethod
    async def get_lock(
        configuration_id: UUID, db: AsyncDatabaseConnection = db
    ) -> Optional["ConfigurationLock"]:
        """
        Retrieve the current lock for a configuration, if any.
        """
        query = "SELECT configuration_id, user_id, expires_at FROM configurations_locks WHERE configuration_id = %s"
        params = (configuration_id,)
        async with db.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                row = await cur.fetchone()
                if row:
                    return ConfigurationLock(row[0], row[1], row[2])
        return None

    @staticmethod
    async def acquire_lock(
        configuration_id: UUID,
        user_id: UUID,
        db: AsyncDatabaseConnection = db,
    ) -> bool:
        """
        Acquire a lock for a configuration, replacing any expired or released lock.
        """
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=LOCK_TIMEOUT_MINUTES)
        existing = await ConfigurationLock.get_lock(configuration_id, db)
        if existing and existing.expires_at.timestamp() > now.timestamp():
            # Lock is active
            return existing.user_id == str(user_id)  # Only allow if same user
        # Acquire or replace lock
        query = (
            "INSERT INTO configurations_locks (configuration_id, user_id, expires_at) VALUES (%s, %s, %s) "
            "ON CONFLICT (configuration_id) DO UPDATE SET user_id = EXCLUDED.user_id, expires_at = EXCLUDED.expires_at"
        )
        params = (configuration_id, user_id, expires_at)
        async with db.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
        return True

    @staticmethod
    async def release_lock(
        configuration_id: UUID,
        user_id: UUID,
        db: AsyncDatabaseConnection = db,
    ) -> bool:
        """
        Release the lock for a configuration if held by the user.
        """
        query = "DELETE FROM configurations_locks WHERE configuration_id = %s AND user_id = %s"
        params = (configuration_id, user_id)
        async with db.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
        return True

    @staticmethod
    async def renew_lock(
        configuration_id: UUID,
        user_id: UUID,
        db: AsyncDatabaseConnection = db,
    ) -> bool:
        """
        Renew the lock for a configuration, extending its expiration.
        """
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=LOCK_TIMEOUT_MINUTES)
        query = "UPDATE configurations_locks SET expires_at = %s WHERE configuration_id = %s AND user_id = %s"
        params = (expires_at, configuration_id, user_id)
        async with db.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
        return True

    @staticmethod
    async def raise_if_locked_by_other(
        configuration_id: UUID,
        user_id: UUID,
        username: str | None = None,
        email: str | None = None,
        db: AsyncDatabaseConnection = db,
    ):
        """
        Raises an HTTP status of 409 if the configuration is locked by another user.
        """
        lock = await ConfigurationLock.get_lock(configuration_id, db)
        if (
            lock
            and str(lock.user_id) != str(user_id)
            and lock.expires_at.timestamp() > datetime.now(UTC).timestamp()
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{username}/{email} currently has this configuration open.",
            )
