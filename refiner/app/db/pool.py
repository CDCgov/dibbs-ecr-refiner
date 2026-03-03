from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import psycopg
from fastapi import Request
from psycopg_pool import AsyncConnectionPool

from app.core.exceptions import (
    DatabaseConnectionError,
)


class AsyncDatabaseConnection:
    """
    Async Database connection using a connection pool.
    """

    def __init__(
        self,
        db_url: str,
        db_password: str,
        min_size: int = 1,
        max_size: int = 10,
        prepare_threshold: int | None = 5,
    ) -> None:
        """
        Initializes the connection pool with the given database URL and size limits.

        Args:
            db_url (str): The PostgreSQL connection string.
            db_password (str): The PostgreSQL password.
            min_size (int, optional): Minimum number of connections to maintain in the pool. Defaults to 1.
            max_size (int, optional): Maximum number of connections allowed in the pool. Defaults to 10.
            prepare_threshold (int, optional): Number of times a query is executed before it is prepared. Defaults to 5.
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
                "prepare_threshold": prepare_threshold,
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


def create_db(
    db_url: str, db_password: str, prepare_threshold: int | None = 5
) -> AsyncDatabaseConnection:
    """
    Creates a new database connection.

    Args:
        db_url (str): The database connection URL
        db_password (str): The database password
        prepare_threshold (int | None): Number of times a query is executed before it is prepared. Defaults to 5.

    Returns:
        AsyncDatabaseConnection: The database connection
    """
    return AsyncDatabaseConnection(
        db_url=db_url, db_password=db_password, prepare_threshold=prepare_threshold
    )


def get_db(request: Request) -> AsyncDatabaseConnection:
    """
    Gets a connection to the database.

    Raises:
        RuntimeError: Database has not yet been initialized.

    Returns:
        AsyncDatabaseConnection: connection to the database
    """
    db = getattr(request.app.state, "db", None)
    if db is None:
        raise RuntimeError("Database not initialized. Ensure the lifespan has started.")
    return db
