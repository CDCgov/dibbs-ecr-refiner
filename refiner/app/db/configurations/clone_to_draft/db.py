import dataclasses
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from psycopg import AsyncCursor
from psycopg.rows import DictRow, dict_row

from app.db.configurations.custom_codes.model import DbCustomCode
from app.db.configurations.model import (
    DbConfiguration,
    DbConfigurationSectionProcessing,
)
from app.db.pool import AsyncDatabaseConnection
from app.services.configurations import (
    clone_section_processing_instructions,
    get_default_sections,
)
from app.services.logger import get_logger


async def insert_configuration_sections_db(
    configuration_id: UUID,
    sections_to_insert: list[DbConfigurationSectionProcessing],
    cursor: AsyncCursor[DictRow],
) -> None:
    """
    Inserts sections into the configurations_sections table.
    """

    query = """
        INSERT INTO configurations_sections (
            configuration_id,
            code,
            name,
            action,
            include,
            narrative,
            versions,
            section_type
        )
        VALUES (
            %(configuration_id)s,
            %(code)s,
            %(name)s,
            %(action)s,
            %(include)s,
            %(narrative)s,
            %(versions)s,
            %(section_type)s
        )

    """

    params = [
        {
            "configuration_id": configuration_id,
            "code": s.code,
            "name": s.name,
            "action": s.action,
            "include": s.include,
            "narrative": s.narrative,
            "versions": s.versions,
            "section_type": s.section_type,
        }
        for s in sections_to_insert
    ]

    await cursor.executemany(query, params)


async def _clone_custom_codes(
    cur: AsyncCursor[DictRow],
    new_config_id: UUID,
    custom_codes_to_clone: list[DbCustomCode],
) -> None:
    await cur.executemany(
        """
        INSERT INTO custom_codes (configuration_id, code, display, system_id)
        VALUES (%(config_id)s, %(code)s, %(display)s, %(system_id)s)
        """,
        [
            {
                "config_id": new_config_id,
                "code": cc.code,
                "display": cc.display,
                "system_id": cc.system_id,
            }
            for cc in custom_codes_to_clone
        ],
    )


@asynccontextmanager
async def _get_cursor(
    db: AsyncDatabaseConnection | None,
    cur: AsyncCursor[DictRow] | None,
) -> AsyncGenerator[AsyncCursor[DictRow]]:
    """Yields an active cursor, creating a new connection if needed."""
    if cur:
        yield cur
    elif db:
        async with db.get_connection() as conn, conn.cursor(row_factory=dict_row) as c:
            yield c
    else:
        raise ValueError("No database connection supplied")


async def clone_to_to_new_draft_db(
    config_to_clone: DbConfiguration,
    new_config_id: UUID,
    db: AsyncDatabaseConnection | None = None,
    cur: AsyncCursor[DictRow] | None = None,
) -> DbConfiguration:
    """
    Clones the information of a passed-in config into the DB and returns the updated draft configuration.

    Args:
        config_to_clone (DbConfiguration): Configuration to clone
        new_config_id (uuid): Target configuration ID
        cur (AsyncCursor[DictRow] | None): A live cursor database connection
        db: (AsyncDatabaseConnection | None): The pooled database connection

    Returns:
        DbConfiguration: Updated draft configuration

    """

    new_sections = clone_section_processing_instructions(
        clone_from=config_to_clone.section_processing,
        clone_to=get_default_sections(),
        logger=get_logger(),
    )

    async with _get_cursor(db, cur) as active_cur:
        await insert_configuration_sections_db(
            configuration_id=new_config_id,
            sections_to_insert=new_sections,
            cursor=active_cur,
        )

        if config_to_clone.custom_codes:
            await _clone_custom_codes(
                new_config_id=new_config_id,
                cur=active_cur,
                custom_codes_to_clone=config_to_clone.custom_codes,
            )

    return dataclasses.replace(
        config_to_clone,
        section_processing=new_sections,
    )
