"""ASGI application entry point."""

from fastapi import FastAPI

from app.core.config import ENVIRONMENT
from app.db.pool import create_db
from app.main import _create_lifespan, create_fastapi_app
from app.services.logger import setup_logger


def start_app() -> FastAPI:
    """
    Starts the production FastAPI application.

    Returns:
        FastAPI: the app
    """
    db = create_db(db_url=ENVIRONMENT["DB_URL"], db_password=ENVIRONMENT["DB_PASSWORD"])
    logger = setup_logger()
    return create_fastapi_app(lifespan=_create_lifespan(db=db, logger=logger))


app = start_app()
