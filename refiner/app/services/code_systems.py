from logging import Logger

from fastapi import Depends
from pydantic import BaseModel

from app.db.code_systems.db import (
    CodeSystemKey,
    DbCodeSystem,
    get_all_code_systems_db,
    get_code_system_by_key_db,
    get_code_system_by_key_or_raise_db,
    get_code_system_by_oid_db,
)
from app.db.pool import AsyncDatabaseConnection, get_db
from app.services.logger import get_logger


class CodeSystems(BaseModel):
    """
    An registry for code system data that pulls values from the db.
    """

    db: AsyncDatabaseConnection = Depends(get_db)

    @classmethod
    async def all(cls) -> list[DbCodeSystem]:
        """
        Get all code system values.
        """

        return list((await get_all_code_systems_db(cls.db)).values())

    @classmethod
    async def allowed_display_names(cls):
        """
        Get all allowed display names for supported systems.
        """
        allowed_code_systems = await cls.all()

        return [s.display_name for s in allowed_code_systems]

    @classmethod
    async def allowed_keys(cls):
        """
        Get all allowed display names for supported systems.
        """
        allowed_code_systems = await cls.all()

        return [s.key for s in allowed_code_systems]

    @classmethod
    async def get_by_key(cls, key: str) -> DbCodeSystem | None:
        """
        Get a specific code system based on its id.
        """

        return await get_code_system_by_key_db(key=key, db=cls.db)

    @classmethod
    async def get_by_key_or_raise(cls, key: CodeSystemKey) -> DbCodeSystem:
        """
        Get a specific code system based on its key, raising otherwise.
        """

        return await get_code_system_by_key_or_raise_db(key=key, db=cls.db)

    @classmethod
    async def get_by_oid(
        cls,
        oid: str,
    ) -> DbCodeSystem | None:
        """
        Get a specific code system based on its name.
        """

        return await get_code_system_by_oid_db(db=cls.db, oid=oid)

    @classmethod
    async def get_by_display_name(
        cls, display_name: str, logger: Logger = Depends(get_logger)
    ) -> DbCodeSystem | None:
        """
        Get a specific code system based on its display name.
        """
        all_code_systems = await cls.all()
        display_name_candidates = [
            s for s in all_code_systems if s.display_name == display_name
        ]
        if len(display_name_candidates) == 0:
            return None

        if len(display_name_candidates) > 1:
            logger.warning(
                "Display name matched on more than one candidate system. Returning the first"
            )

        return display_name_candidates[0]
