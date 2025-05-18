import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


class DatabaseConnection:
    """
    Database connection configuration and context manager.
    """

    db_path: Path

    def __init__(self) -> None:
        """
        Initialize database connection with fixed path to app/terminology.db.

        Raises:
            FileNotFoundError: If terminology.db is not found in the app directory.
        """

        # app/terminology.db
        current_dir = Path(__file__).parent
        self.db_path = current_dir.parent / "terminology.db"

        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection]:
        """
        Create a database connection with proper configuration.
        """

        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        try:
            # enable foreign key support and row factory
            # assign to _ to indicate intentionally unused result
            _ = conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row

            yield conn
        finally:
            conn.close()

    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor]:
        """
        Get a cursor with an active connection.
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
