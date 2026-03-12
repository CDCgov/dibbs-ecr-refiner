from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from packaging.version import parse

from app.api.auth.middleware import get_logged_in_user
from app.core.config import ENVIRONMENT
from app.db.conditions.db import get_loaded_tes_versions_db
from app.db.configurations.db import get_configurations_db
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.schema_migrations.db import get_latest_migration_db
from app.db.users.model import DbUser

router = APIRouter(prefix="/info")


@router.get("", tags=["info", "internal"], include_in_schema=False)
async def get_info(
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> JSONResponse:
    """
    Fetch application state information for debugging purposes.

    Args:
        user (DbUser, optional): The logged-in user.
        db (AsyncDatabaseConnection, optional): The database connection.
        logger (Logger, optional): The app logger.

    Returns:
        JSONResponse: Application state information.
    """

    configs = await get_configurations_db(jurisdiction_id=user.jurisdiction_id, db=db)
    total_config_count = len(configs)
    total_active_config_count = len([c for c in configs if c.status == "active"])

    # minimal response to send to the client
    config_details = [
        {"name": config.name, "status": config.status, "version": config.version}
        for config in configs
    ]

    tes_versions = await get_loaded_tes_versions_db(db=db)
    latest_tes_version = max(tes_versions, key=lambda v: parse(v))

    return {
        "app": {
            "environment": ENVIRONMENT["ENV"],
            "version": ENVIRONMENT["VERSION"],
        },
        "data": {
            "revision": await get_latest_migration_db(db=db),
            "tes_versions": tes_versions,
            "latest_tes_version": latest_tes_version,
        },
        "session": {
            "username": user.username,
            "jurisdiction_id": user.jurisdiction_id,
            "configurations": {
                "total_count": total_config_count,
                "active_count": total_active_config_count,
                "detail": config_details,
            },
        },
    }
