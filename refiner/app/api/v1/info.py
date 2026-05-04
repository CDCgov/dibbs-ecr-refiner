from dataclasses import dataclass

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from packaging.version import parse

from app.api.auth.middleware import get_logged_in_user
from app.api.validation.file_validation import (
    MAX_MB_FOR_DIFF_RENDERING,
    MAX_MB_FOR_UNCOMPRESSED,
    MAX_MB_FOR_UPLOAD,
)
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

    return JSONResponse(
        content={
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
    )


@dataclass
class FileInfoResponse:
    """
    Response for file upload thresholds.
    """

    max_mb_for_diff_rendering: int
    max_mb_for_upload: int
    max_mb_for_uncompressed: int


@router.get(
    "/file-thresholds",
    tags=["info"],
    response_model=FileInfoResponse,
    operation_id="getFileUploadThresholds",
    include_in_schema=True,
)
async def get_file_upload_limits() -> FileInfoResponse:
    """
    Fetch application file upload information for frontend display.

    Returns:
        FileInfoResponse: Application state information.
    """
    return FileInfoResponse(
        max_mb_for_diff_rendering=MAX_MB_FOR_DIFF_RENDERING,
        max_mb_for_upload=MAX_MB_FOR_UPLOAD,
        max_mb_for_uncompressed=MAX_MB_FOR_UNCOMPRESSED,
    )
