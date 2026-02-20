import csv
from datetime import UTC, datetime
from io import StringIO
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.auth.middleware import get_logged_in_user
from app.db.conditions.db import (
    get_condition_codes_by_condition_id_db,
    get_included_conditions_db,
)
from app.db.configurations.db import get_configuration_by_id_db
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.configuration_locks import ConfigurationLock

router = APIRouter(prefix="/{configuration_id}/export")


@router.get(
    "",
    tags=["configurations"],
    operation_id="getConfigurationExport",
    response_class=Response,
)
async def get_configuration_export(
    configuration_id: UUID,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> Response:
    """
    Create a CSV export of a configuration and all associated codes.
    """

    # --- Validate configuration ---
    jd = user.jurisdiction_id
    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=jd, db=db
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found.",
        )

    lock = await ConfigurationLock.get_lock(configuration_id, db)
    if (
        lock
        and str(lock.user_id) != str(user.id)
        and lock.expires_at.timestamp() > datetime.now(UTC).timestamp()
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{user.username}/{user.email} currently has this configuration open.",
        )
    # Determine included conditions
    included_conditions = await get_included_conditions_db(
        included_conditions=config.included_conditions, db=db
    )

    # Write CSV to StringIO (text)
    with StringIO() as csv_text:
        writer = csv.writer(csv_text)
        writer.writerow(
            [
                "Code Type",
                "Code System",
                "Code",
                "Display Name",
            ]
        )
        for cond in included_conditions:
            codes = await get_condition_codes_by_condition_id_db(id=cond.id, db=db)
            for code_obj in codes:
                writer.writerow(
                    [
                        "TES condition grouper code",
                        code_obj.system or "",
                        code_obj.code or "",
                        code_obj.description or "",
                    ]
                )
        for custom in config.custom_codes or []:
            writer.writerow(
                [
                    "Custom code",
                    custom.system or "",
                    custom.code or "",
                    custom.name or "",
                ]
            )

        csv_bytes = csv_text.getvalue().encode("utf-8")

    # Replace spaces with underscores in the config name
    safe_name = config.name.replace(" ", "_")

    # Format current date/time as YYMMDD HH:MM:SS
    timestamp = datetime.now().strftime("%m%d%y_%H:%M:%S")

    # Build final filename
    filename = f"{safe_name}_Code Export_{timestamp}.csv"

    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
