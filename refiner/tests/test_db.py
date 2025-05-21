import sqlite3
from pathlib import Path

import pytest

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
    with pytest.raises(FileNotFoundError):
        _ = DatabaseConnection()

    # also test that the error message contains the expected path
    try:
        _ = DatabaseConnection()
    except FileNotFoundError as e:
        expected_db_path = tmp_path / "terminology.db"
        assert str(expected_db_path) in str(e)


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

    # accept either sqlite3.DatabaseError or sqlite3.Error, and print debug info if it fails
    try:
        with pytest.raises((sqlite3.DatabaseError, sqlite3.Error)):
            with db.get_connection() as conn:
                # this pragma is more likely to consistently trigger a DB error
                conn.execute("PRAGMA integrity_check")
    except AssertionError:
        # print debug info if the test fails in CI
        import sys

        print("Python version:", sys.version)
        print("sqlite3 version:", sqlite3.sqlite_version)
        raise


def test_cursor_error_handling_and_cleanup(mock_db_connection: None) -> None:
    """
    Test cursor error handling and cleanup scenarios.
    """

    ops = GrouperOperations()

    # test 1: cursor errors after connection close
    with ops.db.get_connection() as conn:
        _ = conn.execute("SELECT 1")
        conn.close()
        with pytest.raises(sqlite3.Error):
            _ = conn.execute("SELECT 1")

    # test 2: cursor cleanup after error
    cursor = None
    try:
        with ops.db.get_cursor() as cursor:
            _ = cursor.execute("SELECT 1")
            raise ValueError("Test error")
    except ValueError:
        pass
    assert cursor is not None
    with pytest.raises(sqlite3.Error):
        _ = cursor.execute("SELECT 1")


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
    result = ops.get_grouper_by_condition("nonexistent")
    assert result is None


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
    try:
        with db.get_cursor() as cursor:
            _ = cursor.execute("INSERT INTO test VALUES (1)")  # This will succeed
            _ = cursor.execute(
                "INSERT INTO test VALUES (1)"
            )  # This will fail (duplicate primary key)
    except sqlite3.Error:
        pass

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
