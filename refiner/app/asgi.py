"""ASGI application entry point."""

from fastapi import FastAPI

from app.core.config import get_app_config, get_db_config
from app.db.pool import create_db
from app.main import create_fastapi_app, create_lifespan
from app.services.logger import setup_logger


def start_app() -> FastAPI:
    """
    Starts the production FastAPI application.

    Returns:
        FastAPI: the app
    """
    db = create_db(
        db_url=get_db_config().DB_URL, db_password=get_db_config().DB_PASSWORD
    )
    logger = setup_logger(app_config=get_app_config())
    return create_fastapi_app(lifespan=create_lifespan(db=db, logger=logger))


app = start_app()
