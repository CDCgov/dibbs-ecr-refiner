import logging

from pythonjsonlogger.json import JsonFormatter

from ..core.config import ENVIRONMENT

logger = logging.getLogger("refiner")


def setup_logger() -> None:
    """
    Called to initially configure the logger.
    """
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(defaults={"env": ENVIRONMENT["ENV"]}))

    logger.addHandler(handler)

    logger.info("Logger initialized.")


def get_logger() -> logging.Logger:
    """
    A configured logger that can be used anywhere throughout the API.

    Returns:
        logging.Logger: An instance of a configured Logger.
    """
    return logger
