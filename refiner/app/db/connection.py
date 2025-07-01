from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.core.config import ENVIRONMENT
from app.core.exceptions import (
    DatabaseConnectionError,
    DatabaseQueryError,
    InputValidationError,
    ProcessingError,
    ResourceNotFoundError,
)


class DatabaseConnection:
    """
    Database connection configuration and context manager.
    """

    def __init__(self) -> None:
        """
        Initialize database connection.
        """

        self.connection_config: dict[str, str] = {
            "dbname": ENVIRONMENT["db_name"],
            "user": ENVIRONMENT["db_user"],
            "password": ENVIRONMENT["db_password"],
            "host": ENVIRONMENT["db_host"],
            "port": ENVIRONMENT["db_port"],
        }

    @contextmanager
    def get_connection(self) -> Generator[psycopg.Connection]:
        """
        Create a database connection with proper configuration.

        Raises:
            DatabaseConnectionError
        """

        with psycopg.connect(
            dbname=self.connection_config["dbname"],
            user=self.connection_config["user"],
            password=self.connection_config["password"],
            host=self.connection_config["host"],
            port=self.connection_config["port"],
        ) as conn:
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
