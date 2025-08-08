from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.core.config import ENVIRONMENT
from app.core.exceptions import (
    DatabaseConnectionError,
    DatabaseQueryError,
    InputValidationError,
    ProcessingError,
    ResourceNotFoundError,
)


class AsyncDatabaseConnection:
    """
    Async Database connection using a connection pool.
    """

    def __init__(self, db_url: str, min_size: int = 1, max_size: int = 10) -> None:
        """
        Initializes the connection pool with the given database URL and size limits.

        Args:
            db_url (str): The PostgreSQL connection string.
            min_size (int, optional): Minimum number of connections to maintain in the pool. Defaults to 1.
            max_size (int, optional): Maximum number of connections allowed in the pool. Defaults to 10.
        """
        self.connection_url = db_url
        self.pool = AsyncConnectionPool(
            self.connection_url,
            min_size=min_size,
            max_size=max_size,
            open=False,
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

    def get_stats(self) -> dict[str, str]:
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

    @asynccontextmanager
    async def get_cursor(self) -> AsyncGenerator[psycopg.AsyncCursor[dict[str, Any]]]:
        """
        Provides a database cursor within an async context manager.

        Yields:
            psycopg.AsyncCursor[dict[str, Any]]: A PostgreSQL cursor that returns rows as dictionaries.

        Raises:
            DatabaseConnectionError: If the connection cannot be established.
            DatabaseQueryError: If a psycopg-specific error occurs during query execution.
            ResourceNotFoundError: If raised explicitly during query logic.
            InputValidationError: If raised explicitly during query logic.
            ProcessingError: For unexpected exceptions during query execution.
        """

        try:
            async with self.get_connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cursor:
                    try:
                        yield cursor
                        await conn.commit()
                    except psycopg.Error as e:
                        await conn.rollback()
                        raise DatabaseQueryError(
                            message="Database operation failed",
                            details={
                                "error_type": type(e).__name__,
                                "error_message": str(e),
                            },
                        )
                    except (ResourceNotFoundError, InputValidationError):
                        await conn.rollback()
                        raise
                    except Exception as e:
                        await conn.rollback()
                        raise ProcessingError(
                            message="Unexpected error during database operation",
                            details={
                                "error_type": type(e).__name__,
                                "error_message": str(e),
                            },
                        )
        except DatabaseConnectionError:
            raise


db = AsyncDatabaseConnection(db_url=ENVIRONMENT["DB_URL"])


async def get_db() -> AsyncDatabaseConnection:
    """
    Gets a connection to the database.

    Returns:
        AsyncDatabaseConnection: connection to the database
    """
    return db
