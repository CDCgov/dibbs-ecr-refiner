from uuid import UUID

from psycopg.rows import class_row, dict_row
from pydantic import BaseModel

from ..pool import AsyncDatabaseConnection
from .model import DbUser


class IdpUserResponse(BaseModel):
    """
    Expected user information coming from the IdP response.
    """

    user_id: str
    username: str
    email: str
    jurisdiction_id: str


async def upsert_user_db(
    oidc_user_info: IdpUserResponse, db: AsyncDatabaseConnection
) -> str:
    """
    Upserts a user to the refiner's database upon successful login.

    Args:
        oidc_user_info (IdpUserResponse): User information from the IdP.
        db (AsyncDatabaseConnection): The DB connection pool.

    Returns:
        str: User ID of the created or modified user.
    """
    query = """
        INSERT INTO users (username, email, jurisdiction_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (username)
        DO UPDATE SET
            email = EXCLUDED.email,
            jurisdiction_id = EXCLUDED.jurisdiction_id
        RETURNING id;
        """
    params = (
        oidc_user_info.username,
        oidc_user_info.email,
        oidc_user_info.jurisdiction_id,
    )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if row is None:
        raise Exception("Failed to upsert user and retrieve id.")

    return str(row["id"])


async def get_users_by_jd_id_db(
    jurisdiction_id: UUID, db: AsyncDatabaseConnection
) -> list[DbUser]:
    """
    Gets all users within a specific jurisdiction.
    """
    query = """
            SELECT *
            FROM users
            WHERE jurisdiction_id = %s
            """
    params = (jurisdiction_id,)
    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbUser)) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()
            return rows


async def get_user_by_id_db(id: UUID, db: AsyncDatabaseConnection) -> DbUser:
    """
    Gets a user from the database with the provided ID.
    """
    query = """
            SELECT *
            FROM users
            WHERE id = %s
            """
    params = (id,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbUser)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if not row:
        raise Exception(f"User with ID {id} not found.")

    return row
