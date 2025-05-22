import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

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

    db_path: Path

    def __init__(self) -> None:
        """
        Initialize database connection with fixed path to app/terminology.db.

        Raises:
            ResourceNotFoundError: If terminology.db is not found in the app directory.
        """

        # app/terminology.db
        current_dir = Path(__file__).parent
        self.db_path = current_dir.parent / "terminology.db"

        if not self.db_path.exists():
            raise ResourceNotFoundError(
                message="Database file not found",
                details={"path": str(self.db_path)},
            )

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection]:
        """
        Create a database connection with proper configuration.

        Raises:
            DatabaseConnectionError
        """

        try:
            conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
            try:
                # enable foreign key support and row factory
                # assign to _ to indicate intentionally unused result
                _ = conn.execute("PRAGMA foreign_keys = ON")
                conn.row_factory = sqlite3.Row

                yield conn
            finally:
                conn.close()
        except sqlite3.Error as e:
            raise DatabaseConnectionError(
                message="Failed to connect to database",
                details={"path": str(self.db_path), "error": str(e)},
            )

    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor]:
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
                cursor = conn.cursor()
                try:
                    yield cursor
                    conn.commit()
                except sqlite3.Error as e:
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
