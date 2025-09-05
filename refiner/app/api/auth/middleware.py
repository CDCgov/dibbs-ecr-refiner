from datetime import UTC, timedelta
from datetime import datetime as dt
from logging import Logger
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from psycopg.rows import dict_row

from ...core.exceptions import DatabaseConnectionError, DatabaseQueryError
from ...db.pool import db
from ...services.logger import get_logger
from .session import SESSION_TTL, get_hashed_token

RENEW_THRESHOLD = timedelta(minutes=15)


# This function can be used as an auth check for handlers or routers
async def get_logged_in_user(
    request: Request, logger: Logger = Depends(get_logger)
) -> dict[str, Any]:
    """
    Gets the current user from the session. Throws an error if the user is unauthenticated.

    Args:
        request (Request): Request to check for user info
        logger (Logger): The standard logger

    Raises:
        HTTPException: 401 Unauthorized is thrown if no user info exists
        HTTPException: 500 Internal Server Error is thrown for DB or unknown issues

    Returns:
        dict[str, Any]: Returns the user information if it's available
    """
    session_token = request.cookies.get("refiner-session")
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing session token",
        )

    try:
        token_hash = get_hashed_token(session_token)

        async with db.get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                now = dt.now(UTC)
                await cur.execute(
                    """
                    SELECT users.*, sessions.expires_at
                    FROM sessions
                    JOIN users ON sessions.user_id = users.id
                    WHERE sessions.token_hash = %s AND sessions.expires_at > %s
                    """,
                    (token_hash, now),
                )

                result = await cur.fetchone()

                if not result:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired session token",
                    )

                # Grab user info without `expires_at`
                user = {k: v for k, v in result.items() if k != "expires_at"}
                expires_at = result["expires_at"]

                # Renew session if it's close to expiring
                if expires_at - now < RENEW_THRESHOLD:
                    new_expiration = now + SESSION_TTL
                    await cur.execute(
                        "UPDATE sessions SET expires_at = %s WHERE token_hash = %s",
                        (new_expiration, token_hash),
                    )

            return user
    except (DatabaseConnectionError, DatabaseQueryError) as db_err:
        logger.error(
            "Database error occurred while getting user information",
            extra={"error": str(db_err), "error_details": db_err.details},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error.",
        )
    except Exception as e:
        logger.error(
            "Error occurred when fetching logged-in user",
            extra={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error.",
        )
