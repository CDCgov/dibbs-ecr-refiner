import psycopg
from config import logger


def get_db_connection(db_url: str, db_password: str) -> psycopg.Connection:
    """
    Open a connection to the refiner database.

    Args:
        db_url: PostgreSQL connection URL.
        db_password: Password for that connection.

    Returns:
        An open connection.

    Raises:
        psycopg.OperationalError: The connection could not be established; logged
            before re-raising so the failure is visible in seeding output.
    """

    try:
        return psycopg.connect(db_url, password=db_password)
    except psycopg.OperationalError as error:
        logger.error(f"❌ Database connection failed: {error}")
        raise
