import os
from pathlib import Path

import psycopg
import pytest
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def db_connection():
    """
    Manages the database lifecycle for the entire test session using testcontainers.
    """

    database_root = Path(__file__).resolve().parent.parent
    sql_files = [
        *sorted(database_root.glob("schema/*.sql")),
        *sorted(database_root.glob("functions/*.sql")),
        *sorted(database_root.glob("triggers/*.sql")),
    ]

    print("🚀 Starting PostgreSQL container for tests...")
    with PostgresContainer(
        "postgres:16-alpine",
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
        dbname=os.getenv("POSTGRES_DB", "test_db"),
    ) as postgres:
        connection_url = postgres.get_connection_url().replace("+psycopg2", "")
        with psycopg.connect(connection_url) as connection:
            with connection.cursor() as cursor:
                print("🏗️  Applying database schema, functions, and triggers...")
                for sql_file in sql_files:
                    print(f"  -> Executing {sql_file.name}")
                    cursor.execute(sql_file.read_text())
                connection.commit()
                print("✅ Database setup complete.")

                def get_clean_cursor():
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT table_name
                            FROM information_schema.tables
                            WHERE table_schema = 'public'
                        """)
                        tables = [row[0] for row in cursor.fetchall()]

                        # only run TRUNCATE if there are tables to truncate
                        if tables:
                            table_list = ", ".join([f"public.{t}" for t in tables])
                            cursor.execute(
                                f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE;"
                            )

                        connection.commit()
                        yield cursor
                        connection.commit()

                yield get_clean_cursor

    print("\n🧹 PostgreSQL container stopped.")


@pytest.fixture(scope="function")
def db_cursor(db_connection):
    """
    Provides a clean cursor for a single test function by calling the session-scoped generator.
    """

    yield from db_connection()
