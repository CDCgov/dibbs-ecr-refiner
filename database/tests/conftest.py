import os

import psycopg
import pytest
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))


@pytest.fixture(scope="session")
def db_conn():
    conn = psycopg.connect(
        os.getenv(
            "TEST_DB_URL", "postgresql://postgres:postgres@localhost:5432/refiner"
        )
    )
    yield conn
    conn.close()
