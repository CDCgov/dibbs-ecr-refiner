import logging
from contextvars import ContextVar
from uuid import UUID

from pythonjsonlogger.json import JsonFormatter

from ..core.config import ENVIRONMENT

logger = logging.getLogger("refiner")

# https://docs.python.org/3/library/contextvars.html#asyncio-support
request_id_ctx_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(request_id: UUID) -> None:
    """
    Sets the current request ID.

    Args:
        request_id (str): The generated request ID
    """
    request_id_ctx_var.set(str(request_id))


def get_request_id() -> str | None:
    """
    Gets the current request ID.

    Returns:
        str | None: The current request ID, or None
    """
    return request_id_ctx_var.get()


class RequestIdFilter(logging.Filter):
    """
    Adds additional info to the standard logger.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Adds the request ID to the logger if one exists, else adds "unknown".
        """
        record.request_id = get_request_id() or "unknown"
        return True


def setup_logger() -> None:
    """
    Called to initially configure the logger.
    """
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(
        JsonFormatter(defaults={"service": "refiner", "env": ENVIRONMENT["ENV"]})
    )

    handler.addFilter(RequestIdFilter())

    logger.addHandler(handler)

    logger.info("Logger initialized.")


def get_logger() -> logging.Logger:
    """
    A configured logger that can be used anywhere throughout the API.

    Returns:
        logging.Logger: An instance of a configured Logger.
    """
    return logger
