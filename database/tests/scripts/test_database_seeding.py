import scripts.database_seeding as db_seed


def test_seed_database_runs(mocker):
    """
    Test that seed_database() can be called without DB side effects.
    """

    # patch get_db_connection to avoid DB
    mocker.patch(
        "scripts.database_seeding.get_db_connection",
        return_value=MockPsycopgConnection(),
    )
    # patch populate_refinement_cache to no-op
    mocker.patch(
        "scripts.database_seeding.populate_refinement_cache", return_value=None
    )
    # should not raise
    db_seed.seed_database()


class MockPsycopgConnection:
    """
    Mock for database connection object.
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
