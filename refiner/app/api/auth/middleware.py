from datetime import UTC, timedelta
from datetime import datetime as dt
from typing import Any

from fastapi import HTTPException, Request, status

from ...core.exceptions import DatabaseConnectionError, DatabaseQueryError
from ...db.pool import db
from .session import SESSION_TTL, get_hashed_token

RENEW_THRESHOLD = timedelta(minutes=15)


# This function can be used as an auth check for handlers or routers
async def get_logged_in_user(request: Request) -> dict[str, Any]:
    """
    Gets the current user from the session. Throws an error if the user is unauthenticated.

    Args:
        request (Request): Request to check for user info

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

        async with db.get_cursor() as cur:
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
        print("Database error occurred while getting user information:", db_err.details)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error.",
        )
