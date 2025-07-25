from psycopg import Cursor


def test_database_connection(db_cursor: Cursor) -> None:
    """
    Tests that a connection to the database can be successfully established.
    """

    assert db_cursor is not None
    assert not db_cursor.closed


def test_tables_exist(db_cursor: Cursor) -> None:
    """
    Tests that the core tables have been created by the schema scripts.
    """

    db_cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in db_cursor.fetchall()]

    expected_tables = [
        "configurations",
        "jurisdictions",
        "refinement_cache",
        "tes_condition_grouper_references",
        "tes_condition_groupers",
        "tes_reporting_spec_groupers",
        "users",
    ]

    assert tables == expected_tables
