# ruff: noqa
# mypy: ignore-errors
import functools
import time

from app.services.logger import get_logger

logger = get_logger()


def log_query_perf(slow_threshold: float = 1.0):
    """
    This is a utility to log how long a function takes to execute and is intended for
    database related functions.

    Usage:
        ```
        @log_query_perf(slow_threshold=2.0)
        async def get_conditions_by_ids_db(
            ids: list[UUID], db: AsyncDatabaseConnection
        ) -> list[DbCondition]:
        ...
        ```

    Args:
        slow_threshold (float, optional): Time in seconds. If function call exceeds slow_threshold
            the logger will log this as a warning.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = time.perf_counter() - start
                log = logger.warning if elapsed > slow_threshold else logger.info
                log(f"{func.__name__} took {elapsed:.3f}s")

        return wrapper

    return decorator
