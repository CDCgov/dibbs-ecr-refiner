import asyncio
from datetime import UTC, timedelta
from datetime import datetime as dt
from uuid import uuid4

from ...db.pool import db

SESSION_TTL = timedelta(hours=1)


async def upsert_user(oidc_user_info: dict) -> str:
    """
    Upserts a user to the refiner's database upon successful login.

    Args:
        oidc_user_info (dict): User information from the OIDC.

    Returns:
        str: User ID of the created or modified user.
    """
    user_id = oidc_user_info["sub"]
    username = oidc_user_info.get("preferred_username", "")
    email = oidc_user_info.get("email", "")

    query = """
        INSERT INTO users (id, username, email)
        VALUES (%s, %s, %s)
        ON CONFLICT (id)
        DO UPDATE SET
            username = EXCLUDED.username,
            email = EXCLUDED.email
        """
    params = (user_id, username, email)

    async with db.get_cursor() as cur:
        await cur.execute(query, params)

    return user_id


async def create_session(user_id: str) -> str:
    """
    Upon log in, create a session and associate it with a user ID.

    Args:
        user_id (str): The ID of the user to create a session for.

    Returns:
        str: Session token
    """
    token = str(uuid4())
    expires = dt.now(UTC) + SESSION_TTL

    query = "INSERT INTO sessions (token, user_id, expires_at) VALUES (%s, %s, %s)"
    params = (
        token,
        user_id,
        expires,
    )
    async with db.get_cursor() as cur:
        await cur.execute(query, params)

    return token


async def get_user_from_session(token: str) -> dict[str, str] | None:
    """
    Given a session token, find the user associated with the session.

    Args:
        token (str): Token of the session connected to the user.
    """
    now = dt.now(UTC)
    query = """
        SELECT u.id, u.username FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = %s AND s.expires_at > %s
    """
    params = (token, now)

    async with db.get_cursor() as cur:
        await cur.execute(query, params)
        user = await cur.fetchone()

        print("User from session:", user)
        if user:
            return {"id": user["id"], "username": user["username"]}
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


async def run_expired_session_cleanup_task() -> None:
    """
    Task that can be scheduled to run session cleanup once per hour.
    """
    cleanup_interval_seconds = 3600  # Run once per hour
    while True:
        try:
            await _delete_expired_sessions()
        except Exception as e:
            print(f"[Session Cleanup] Error: {e}")
        await asyncio.sleep(cleanup_interval_seconds)


async def delete_session(token: str) -> None:
    """
    Given a token, deletes a session from the database.

    Args:
        token (str): Token of the session to be deleted
    """
    query = "DELETE FROM sessions WHERE token = %s"
    params = (token,)
    async with db.get_cursor() as cur:
        await cur.execute(query, params)
