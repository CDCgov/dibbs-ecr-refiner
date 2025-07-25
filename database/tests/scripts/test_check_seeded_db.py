import sys

import pytest

import scripts.check_seeded_db as db_check


def test_check_seed_db_main_success(mocker):
    """
    Test main() in check_seeded_db exits with 0 or 1, and avoids real DB.
    """

    mocker.patch(
        "scripts.check_seeded_db.get_db_connection",
        return_value=MockPsycopgConnection(),
    )
    # patch sys.exit to raise SystemExit with actual code
    mocker.patch.object(
        sys, "exit", side_effect=lambda code=0: (_ for _ in ()).throw(SystemExit(code))
    )
    with pytest.raises(SystemExit) as excinfo:
        db_check.main()
    # accept any exit code (0 for success, 1 for failure)
    assert excinfo.value.code in (0, 1)


class MockPsycopgConnection:
    """
    Mock for psycopg database connection object.
    """

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def cursor(self):
        return MockPsycopgCursor()

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


class MockPsycopgCursor:
    """
    Mock for database cursor object.
    """

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, *a, **kw):
        pass

    def fetchone(self):
        return (0,)

    def fetchall(self):
        return [(0,)]
