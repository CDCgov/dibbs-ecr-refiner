import os

import psycopg
import pytest
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "refiner")

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


@pytest.fixture(scope="module")
def db_conn():
    conn = psycopg.connect(DB_URL)
    yield conn
    conn.close()


def test_conditions_table_populated(db_conn):
    with db_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM conditions;")
        count = cur.fetchone()[0]
        assert count > 0, (
            "Conditions table should have at least one entry after seeding."
        )


def test_configurations_table_populated(db_conn):
    with db_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM configurations;")
        count = cur.fetchone()[0]
        assert count > 0, (
            "Configurations table should have at least one entry after seeding."
        )


def test_sample_configuration_exists(db_conn):
    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT name FROM configurations WHERE name = 'COVID-19 Surveillance';"
        )
        row = cur.fetchone()
        assert row is not None, (
            "'COVID-19 Surveillance' configuration should exist in seed data."
        )


def test_configuration_families_populated(db_conn):
    with db_conn.cursor() as cur:
        cur.execute("SELECT COUNT(DISTINCT family_id) FROM configurations;")
        count = cur.fetchone()[0]
        assert count > 0, "configurations table should have at least one family."


def test_activations_populated(db_conn):
    with db_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM activations;")
        count = cur.fetchone()[0]
        assert count > 0, "activations table should have at least one entry."
