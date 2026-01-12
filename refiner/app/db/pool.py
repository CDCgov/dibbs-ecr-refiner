from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import psycopg
from psycopg_pool import AsyncConnectionPool

from app.core.config import ENVIRONMENT
from app.core.exceptions import (
    DatabaseConnectionError,
)


class AsyncDatabaseConnection:
    """
    Async Database connection using a connection pool.
    """

    def __init__(
        self, db_url: str, db_password: str, min_size: int = 1, max_size: int = 10
    ) -> None:
        """
        Initializes the connection pool with the given database URL and size limits.

        Args:
            db_url (str): The PostgreSQL connection string.
            db_password (str): The PostgreSQL password.
            min_size (int, optional): Minimum number of connections to maintain in the pool. Defaults to 1.
            max_size (int, optional): Maximum number of connections allowed in the pool. Defaults to 10.
        """
        self.connection_url = db_url
        self.db_password = db_password

        self.pool = AsyncConnectionPool(
            self.connection_url,
            min_size=min_size,
            max_size=max_size,
            open=False,
            kwargs={
                "password": self.db_password,
            },
        )

    async def connect(self) -> None:
        """
        Opens the connection pool for use. Should be called once upon app startup.

        Raises:
            DatabaseConnectionError: If the connection pool cannot be opened.
        """

        try:
            await self.pool.open()
        except Exception as e:
            raise DatabaseConnectionError(
                message="Could not open connection pool",
                details={"error": str(e)},
            )

    async def close(self) -> None:
        """
        Closes all connections in the pool and shuts it down cleanly. Should be called once upon app shutdown.
        """
        await self.pool.close()

    def get_stats(self) -> dict[str, int]:
        """
        Returns database pool stats (min connections, max connections, pool size, etc.).
        """
        return self.pool.get_stats()

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[psycopg.AsyncConnection]:
        """
        Provides a connection from the pool within an async context manager.

        Yields:
            psycopg.AsyncConnection: A pooled PostgreSQL async connection.

        Raises:
            DatabaseConnectionError: If a connection cannot be retrieved from the pool.
        """
        try:
            async with self.pool.connection() as conn:
                yield conn
        except Exception as e:
            raise DatabaseConnectionError(
                message="Failed to get connection from pool",
                details={"error": str(e)},
            )


db = AsyncDatabaseConnection(
    db_url=ENVIRONMENT["DB_URL"], db_password=ENVIRONMENT["DB_PASSWORD"]
)


async def get_db() -> AsyncDatabaseConnection:
    """
    Gets a connection to the database.

    Returns:
        AsyncDatabaseConnection: connection to the database
    """
    return db
