import os
from pathlib import Path

import psycopg
import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="session")
def db_url() -> str:
    """
    Loads the database connection URL from the .env file.
    This is a session-scoped fixture, so it only runs once.
    """

    env_path = Path(__file__).parent.parent / ".env"

    # use override=True to ensure the database/.env file takes precedence
    # over any variables that might be loaded from the root .env file
    load_dotenv(dotenv_path=env_path, override=True)

    db_connection_url = "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host="localhost",
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
    )

    return db_connection_url


@pytest.fixture(scope="function")
def db_cursor(db_url: str) -> psycopg.Cursor:
    """
    Creates a database connection and a cursor for a single test function.
    It also cleans up the tables after the test is done.
    """

    # tables to clear before each test run
    tables_to_truncate = [
        "tes_condition_grouper_references",
        "tes_reporting_spec_groupers",
        "tes_condition_groupers",
        "configurations",
        "users",
        "jurisdictions",
    ]

    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                # truncate tables to ensure a clean state for the test
                cur.execute(
                    f"TRUNCATE {', '.join(tables_to_truncate)} RESTART IDENTITY CASCADE;"
                )
                conn.commit()

                # yield the cursor to the test function
                yield cur

                # teardown: truncate tables again after the test
                cur.execute(
                    f"TRUNCATE {', '.join(tables_to_truncate)} RESTART IDENTITY CASCADE;"
                )
                conn.commit()
    except psycopg.OperationalError as e:
        pytest.fail(
            f"Failed to connect to the database at {db_url}. "
            f"Please ensure the Docker container is running and the .env file is correct. "
            f"Original error: {e}"
        )
