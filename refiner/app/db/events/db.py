from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from psycopg.rows import class_row

from ..pool import AsyncDatabaseConnection


@dataclass
class CreateConfigurationEvent:
    """
    Model to represent a "create configuration" event in the database.
    """

    id: UUID
    jurisdiction_id: UUID
    configuration_id: UUID
    event_type: Literal["create_configuration"]
    action_text: Literal["Created configuration"]


async def log_create_configuration_event_db(
    user_id: UUID,
    jurisdiction_id: UUID,
    configuration_id: UUID,
    db: AsyncDatabaseConnection,
) -> None:
    """
    Adds a log to the events table when a configuration is created.
    """
    query = """
        INSERT INTO events (
            user_id,
            jurisdiction_id,
            configuration_id,
            event_type,
            action_text
        )
        VALUES (
            %s,
            %s,
            %s,
            'create_configuration',
            'Created configuration'
        )
    """
    params = (
        user_id,
        jurisdiction_id,
        configuration_id,
    )

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(CreateConfigurationEvent)) as cur:
            await cur.execute(query, params)
