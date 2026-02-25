from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from datetime import datetime as dt
from logging import Logger

from fastapi import Depends, HTTPException, Request, status
from psycopg.rows import dict_row

from app.db.pool import AsyncDatabaseConnection, get_db

from ...core.exceptions import DatabaseConnectionError, DatabaseQueryError
from ...db.users.model import DbUser
from ...services.logger import get_logger
from .session import SESSION_TTL, get_hashed_token

RENEW_THRESHOLD = timedelta(minutes=15)


@dataclass(frozen=True)
class DbUserWithSessionExpiryTime(DbUser):
    """
    DbUser model that includes the `expires_at` field.
    """

    expires_at: datetime

    def to_db_user(self) -> DbUser:
        """
        Transform DbUserWithSessionExpiryTime to a DbUser.

        Returns:
            DbUser: the user object
        """
        data = asdict(self)
        data.pop("expires_at", None)
        return DbUser(**data)


# This function can be used as an auth check for handlers or routers
async def get_logged_in_user(
    request: Request,
    logger: Logger = Depends(get_logger),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> DbUser:
    """
    Gets the current user from the session. Throws an error if the user is unauthenticated.

    Args:
        request (Request): Request to check for user info
        logger (Logger): The standard logger
        db (AsyncDatabaseConnection): The database connection

    Raises:
        HTTPException: 401 Unauthorized is thrown if no user info exists
        HTTPException: 500 Internal Server Error is thrown for DB or unknown issues

    Returns:
        DbUser: Returns the user information
    """
    session_token = request.cookies.get("refiner-session")
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing session token",
        )

    token_hash = get_hashed_token(session_token)
    db_user = None
    try:
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
                db_user = await cur.fetchone()
    except (DatabaseConnectionError, DatabaseQueryError) as db_err:
        logger.error(
            "Database error occurred while getting user information",
            extra={"error": str(db_err), "error_details": db_err.details},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error.",
        )

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
        )

    user = DbUserWithSessionExpiryTime(**db_user)
    expires_at = user.expires_at

    # Renew session if it's close to expiring
    await update_session_expiry_time(
        expires_at=expires_at, token_hash=token_hash, logger=logger, db=db
    )

    # Create a DbUser from the DbUserWithSessionExpiryTime to return
    return user.to_db_user()


async def update_session_expiry_time(
    expires_at: datetime, token_hash: str, logger: Logger, db: AsyncDatabaseConnection
) -> None:
    """
    Updates a user's session expiration if it is set to expire soon.

    Args:
        expires_at (datetime): Current expiration time
        token_hash (str): Hashed session token
        logger (Logger): Standard logger
        db (AsyncDatabaseConnection): The database connection

    Raises:
        HTTPException: 500 if there is an error while updating the session
    """
    now = dt.now(UTC)
    if expires_at - now < RENEW_THRESHOLD:
        new_expiration = now + SESSION_TTL
        try:
            async with db.get_connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(
                        "UPDATE sessions SET expires_at = %s WHERE token_hash = %s",
                        (new_expiration, token_hash),
                    )

        except (DatabaseConnectionError, DatabaseQueryError) as db_err:
            logger.error(
                "Database error occurred while getting user information",
                extra={"error": str(db_err), "error_details": db_err.details},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error.",
            )
