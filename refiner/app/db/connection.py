from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.core.exceptions import (
    DatabaseConnectionError,
    DatabaseQueryError,
    InputValidationError,
    ProcessingError,
    ResourceNotFoundError,
)

from ..core.config import ENVIRONMENT


class DatabaseConnection:
    """
    Database connection configuration and context manager.
    """

    def __init__(self, db_url: str) -> None:
        """
        Initialize database connection.
        """

        self.connection_url = db_url

    @contextmanager
    def get_connection(self) -> Generator[psycopg.Connection]:
        """
        Create a database connection with proper configuration.

        Raises:
            DatabaseConnectionError
        """

        with psycopg.connect(self.connection_url) as conn:
            try:
                yield conn
            except Exception as e:
                raise DatabaseConnectionError(
                    message="Failed to connect to database",
                    details={"error": str(e)},
                )

    @contextmanager
    def get_cursor(self) -> Generator[psycopg.Cursor[dict[str, Any]]]:
        """
        Get a cursor with an active connection.

        Raises:
            DatabaseConnectionError: If database connection fails
            DatabaseQueryError: If database operations fail
            ProcessingError: If an unexpected error occurs during database operations
            ResourceNotFoundError: If a resource is not found
            InputValidationError: If input validation fails
        """

        try:
            with self.get_connection() as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    try:
                        yield cursor
                        conn.commit()
                    except psycopg.Error as e:
                        conn.rollback()
                        raise DatabaseQueryError(
                            message="Database operation failed",
                            details={
                                "error_type": type(e).__name__,
                                "error_message": str(e),
                            },
                        )
                    except (ResourceNotFoundError, InputValidationError):
                        # let these exceptions pass through unchanged
                        conn.rollback()
                        raise
                    except Exception as e:
                        conn.rollback()
                        raise ProcessingError(
                            message="Unexpected error during database operation",
                            details={
                                "error_type": type(e).__name__,
                                "error_message": str(e),
                            },
                        )
        except DatabaseConnectionError:
            # re-raise database connection errors
            raise


# Don't use this directly, call the function below
# TODO: set up the connection in Lambda instead
_db_connection = DatabaseConnection(ENVIRONMENT["DB_URL"])


def get_db_connection() -> DatabaseConnection:
    """
    Gets an established, sync database connection.

    Returns:
        DatabaseConnection: The established connection
    """
    return _db_connection
