import asyncio
import hashlib
import hmac
import secrets
from datetime import UTC, timedelta
from datetime import datetime as dt
from logging import Logger
from uuid import UUID

from pydantic import BaseModel

from ...core.config import ENVIRONMENT
from ...db.pool import db

SESSION_TTL = timedelta(hours=1)
SESSION_SECRET_KEY = ENVIRONMENT["SESSION_SECRET_KEY"].encode("utf-8")


def get_hashed_token(token: str) -> str:
    """
    Given a session token, calculates a hash using the session secret key.

    Args:
        token (str): Session token

    Returns:
        str: Hashed session token
    """
    return hmac.new(
        SESSION_SECRET_KEY, token.encode("utf-8"), hashlib.sha256
    ).hexdigest()


async def create_session(user_id: str) -> str:
    """
    Upon log in, create a session and associate it with a user ID.

    Args:
        user_id (str): The ID of the user to create a session for.

    Returns:
        str: Session token
    """
    # Create a strong token and hash it using the secret key
    token = secrets.token_urlsafe(32)
    token_hash = get_hashed_token(token)
    expires = dt.now(UTC) + SESSION_TTL

    query = "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (%s, %s, %s)"
    params = (
        token_hash,
        user_id,
        expires,
    )
    async with db.get_cursor() as cur:
        await cur.execute(query, params)

    return token


class UserResponse(BaseModel):
    """
    User response model.
    """

    id: UUID
    username: str


async def get_user_from_session(token: str) -> UserResponse | None:
    """
    Given a session token, find the user associated with the session.

    Args:
        token (str): Token of the session connected to the user.
    """
    token_hash = get_hashed_token(token)
    now = dt.now(UTC)
    query = """
        SELECT u.id, u.username FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token_hash = %s AND s.expires_at > %s
    """
    params = (token_hash, now)

    async with db.get_cursor() as cur:
        await cur.execute(query, params)
        user = await cur.fetchone()

        if user:
            return UserResponse(id=user["id"], username=user["username"])
    return None


async def _delete_expired_sessions() -> None:
    """
    Removes expired sessions from the database.

    This function will run as a task rather than being called on its own.
    """
    now = dt.now(UTC)
    query = "DELETE FROM sessions where expires_at < %s"
    params = (now,)
    async with db.get_cursor() as cur:
        await cur.execute(query, params)


async def run_expired_session_cleanup_task(logger: Logger) -> None:
    """
    Task that can be scheduled to run session cleanup once per hour.
    """
    cleanup_interval_seconds = 3600  # Run once per hour
    while True:
        try:
            await _delete_expired_sessions()
            logger.info("Expired sessions cleaned up.")
        except Exception as e:
            logger.error(
                "Expired sessions could not be cleaned up", extra={"error": str(e)}
            )
        await asyncio.sleep(cleanup_interval_seconds)


async def delete_session(token: str) -> None:
    """
    Given a token, deletes a session from the database.

    Args:
        token (str): Token of the session to be deleted
    """
    token_hash = get_hashed_token(token)
    query = "DELETE FROM sessions WHERE token_hash = %s"
    params = (token_hash,)
    async with db.get_cursor() as cur:
        await cur.execute(query, params)
