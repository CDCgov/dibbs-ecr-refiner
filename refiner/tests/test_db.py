import sqlite3
from pathlib import Path

import pytest

from app.core.exceptions import (
    DatabaseConnectionError,
    DatabaseQueryError,
    InputValidationError,
    ProcessingError,
    ResourceNotFoundError,
)
from app.db.connection import DatabaseConnection
from app.db.models import GrouperRow
from app.db.operations import GrouperOperations

# test data from grouper table
SAMPLE_GROUPER = {
    "condition": "38362002",
    "display_name": "Dengue Virus Infection",
    "loinc_codes": '[{"code": "25459-9", "display": "Dengue virus Ab panel"}]',
    "snomed_codes": '[{"code": "38362002", "display": "Dengue (disorder)"}]',
    "icd10_codes": '[{"code": "A97", "display": "Dengue fever"}]',
    "rxnorm_codes": "[]",
}


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """
    Create a temporary test database.
    """

    db_path = tmp_path / "test_terminology.db"
    conn = sqlite3.connect(db_path)
    _ = conn.executescript("""
        CREATE TABLE groupers (
            condition TEXT PRIMARY KEY,
            display_name TEXT,
            loinc_codes TEXT DEFAULT '[]',
            snomed_codes TEXT DEFAULT '[]',
            icd10_codes TEXT DEFAULT '[]',
            rxnorm_codes TEXT DEFAULT '[]'
        );
    """)

    # insert test data
    _ = conn.execute(
        """
        INSERT INTO groupers (
            condition, display_name, loinc_codes, snomed_codes,
            icd10_codes, rxnorm_codes
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            SAMPLE_GROUPER["condition"],
            SAMPLE_GROUPER["display_name"],
            SAMPLE_GROUPER["loinc_codes"],
            SAMPLE_GROUPER["snomed_codes"],
            SAMPLE_GROUPER["icd10_codes"],
            SAMPLE_GROUPER["rxnorm_codes"],
        ),
    )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def mock_db_connection(monkeypatch: pytest.MonkeyPatch, test_db_path: Path) -> None:
    """
    Mock the database connection to use our test database.
    """

    def mock_init(self: DatabaseConnection) -> None:
        self.db_path = test_db_path

    monkeypatch.setattr("app.db.connection.DatabaseConnection.__init__", mock_init)


@pytest.fixture
def monkeypatched_sqlite_connect(monkeypatch):
    """
    Fixture to monkeypatch sqlite3.connect with a dummy connection.
    """

    class DummyCursor:
        def execute(self, query, *args, **kwargs):
            return self

        def fetchall(self):
            return [("some", "data")]

        def fetchone(self):
            return ("some",)

        def close(self):
            pass

    class DummyConnection:
        def cursor(self):
            return DummyCursor()

        def close(self):
            pass

        def commit(self):
            pass

        def execute(self, *args, **kwargs):
            return DummyCursor()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

    def dummy_connect(*args, **kwargs):
        return DummyConnection()

    monkeypatch.setattr(sqlite3, "connect", dummy_connect)


def test_grouper_operations_logic(monkeypatched_sqlite_connect, monkeypatch):
    # patch DatabaseConnection to avoid setting any path, but set a dummy db_path
    def dummy_init(self):
        self.db_path = ":memory:"

    monkeypatch.setattr("app.db.connection.DatabaseConnection.__init__", dummy_init)
    from app.db.operations import GrouperOperations

    ops = GrouperOperations()
    with ops.db.get_connection() as conn:
        result = conn.cursor().execute("SELECT 1").fetchall()
    assert result == [("some", "data")]


def test_connection_file_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Test database connection when file doesn't exist.
    """

    test_file = tmp_path / "db" / "connection.py"
    test_file.parent.mkdir(parents=True)
    monkeypatch.setattr("app.db.connection.__file__", str(test_file))
    with pytest.raises(ResourceNotFoundError):
        _ = DatabaseConnection()

    # also test that the error message contains the expected path
    try:
        _ = DatabaseConnection()
    except ResourceNotFoundError as e:
        expected_db_path = tmp_path / "terminology.db"

        # check the message is correct
        assert "Database file not found" == e.message

        # check the details contain the correct path
        assert "path" in e.details
        assert str(expected_db_path) == e.details["path"]


def test_connection_error_handling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Test error handling in connection context manager.
    """

    test_file = tmp_path / "db" / "connection.py"
    test_file.parent.mkdir(parents=True)
    monkeypatch.setattr("app.db.connection.__file__", str(test_file))
    db_path = tmp_path / "terminology.db"
    db_path.write_text("not a database")

    db = DatabaseConnection()

    with pytest.raises(DatabaseConnectionError) as exc_info:
        with db.get_connection() as conn:
            conn.execute("PRAGMA integrity_check")

    assert "Failed to connect to database" == exc_info.value.message
    assert "path" in exc_info.value.details


def test_cursor_error_handling_and_cleanup(mock_db_connection: None) -> None:
    """
    Test cursor error handling and cleanup scenarios.
    """

    ops = GrouperOperations()

    # test 1: database query errors are correctly wrapped
    with pytest.raises(DatabaseQueryError) as exc_info:
        with ops.db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM nonexistent_table")

    assert "Database operation failed" == exc_info.value.message
    assert "error_type" in exc_info.value.details

    # test 2: other exceptions are wrapped as ProcessingError
    with pytest.raises(ProcessingError):
        with ops.db.get_cursor() as cursor:
            _ = cursor.execute("SELECT 1")
            # Force a non-database error
            raise ValueError("Test error")


def test_get_grouper_successful_retrieval(mock_db_connection: None) -> None:
    """
    Test successful grouper retrieval with type checking and validation.
    """

    ops = GrouperOperations()
    result = ops.get_grouper_by_condition(SAMPLE_GROUPER["condition"])

    # test 1: correct data retrieved
    assert result is not None
    assert isinstance(result, dict)
    for key, value in SAMPLE_GROUPER.items():
        assert result[key] == value

    # test 2: correct types
    assert isinstance(result["condition"], str)
    assert isinstance(result["display_name"], str)
    assert isinstance(result["loinc_codes"], str)
    assert isinstance(result["snomed_codes"], str)
    assert isinstance(result["icd10_codes"], str)
    assert isinstance(result["rxnorm_codes"], str)

    # test 3: TypedDict compatibility
    grouper_row = GrouperRow(**result)
    assert isinstance(grouper_row, dict)


def test_get_grouper_by_condition_not_found(mock_db_connection: None) -> None:
    """
    Test retrieving a non-existent grouper.
    """

    ops = GrouperOperations()

    with pytest.raises(ResourceNotFoundError) as exc_info:
        ops.get_grouper_by_condition("nonexistent")

    assert "Grouper with condition not found" == exc_info.value.message
    assert "condition" in exc_info.value.details
    assert "nonexistent" == exc_info.value.details["condition"]


def test_get_grouper_input_validation(mock_db_connection: None) -> None:
    """
    Test input validation for get_grouper_by_condition.
    """

    ops = GrouperOperations()

    # test with empty string
    with pytest.raises(InputValidationError) as exc_info:
        ops.get_grouper_by_condition("")

    assert "Invalid condition code" == exc_info.value.message

    # test with None
    with pytest.raises(InputValidationError):
        ops.get_grouper_by_condition(None)  # type: ignore

    # test with non-string
    with pytest.raises(InputValidationError):
        ops.get_grouper_by_condition(123)


def test_connection_rollback_on_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Test that transaction is rolled back on error.
    """

    test_file = tmp_path / "db" / "connection.py"
    test_file.parent.mkdir(parents=True)
    monkeypatch.setattr("app.db.connection.__file__", str(test_file))
    db_path = tmp_path / "terminology.db"
    conn = sqlite3.connect(db_path)
    conn.close()
    db = DatabaseConnection()

    # first create the table outside the transaction we want to test
    with db.get_cursor() as cursor:
        _ = cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")

    # try to execute an invalid insert in a transaction
    with pytest.raises(DatabaseQueryError):
        with db.get_cursor() as cursor:
            _ = cursor.execute("INSERT INTO test VALUES (1)")  # This will succeed
            _ = cursor.execute(
                "INSERT INTO test VALUES (1)"
            )  # This will fail (duplicate primary key)

    # verify the first insert was rolled back
    with db.get_cursor() as cursor:
        _ = cursor.execute("SELECT COUNT(*) FROM test")
        row = cursor.fetchone()
        assert row is not None
        count: int = row[0]
        assert count == 0, "Transaction should have been rolled back"


def test_connection_commit_on_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Test that transaction is committed on success.
    """

    test_file = tmp_path / "db" / "connection.py"
    test_file.parent.mkdir(parents=True)
    monkeypatch.setattr("app.db.connection.__file__", str(test_file))
    db_path = tmp_path / "terminology.db"
    conn = sqlite3.connect(db_path)
    conn.close()
    db = DatabaseConnection()

    # execute a valid query in a transaction
    with db.get_cursor() as cursor:
        _ = cursor.execute("CREATE TABLE test2 (id INTEGER PRIMARY KEY)")
        _ = cursor.execute("INSERT INTO test2 VALUES (1)")

    # verify the data was inserted
    with db.get_cursor() as cursor:
        _ = cursor.execute("SELECT COUNT(*) FROM test2")
        row = cursor.fetchone()
        assert row is not None
        count: int = row[0]
        assert count == 1, "Transaction should have been committed"
