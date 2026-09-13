import psycopg
import pytest

from app.core.config import get_db_config
from tes.verify.database import run_checks


@pytest.mark.integration
class TestTesVerify:
    """
    Assert the seeded database is a faithful projection of the processed tables.

    The rest of the integration suite exercises behaviour on top of seeded data;
    this checks the seeding itself. It is the same code `python -m
    tes.verify.database` runs, so a failure here and a failure in ops mean the
    same thing.
    """

    def test_database_matches_processed_data(self, setup):
        config = get_db_config()
        with psycopg.connect(config.DB_URL, password=config.DB_PASSWORD) as connection:
            results = run_checks(connection)

        failures = [
            f"{result.title}: {result.detail}"
            + "".join(f"\n    - {item}" for item in result.failures[:5])
            for result in results
            if not result.passed
        ]

        assert not failures, (
            "seeded database does not match the processed tables:\n"
            + "\n".join(failures)
        )

        # a passing run with no checks would be vacuous
        assert len(results) == 4
