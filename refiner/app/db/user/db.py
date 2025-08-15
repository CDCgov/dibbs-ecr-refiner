from psycopg.rows import class_row

from ..pool import AsyncDatabaseConnection
from .model import DbUser


async def get_user_by_id_db(id: str, db: AsyncDatabaseConnection) -> DbUser:
    """
    Gets a user from the database with the provided ID.
    """
    query = """
            SELECT id, username, email, jurisdiction_id
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
