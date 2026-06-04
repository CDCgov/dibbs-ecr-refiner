import csv
from datetime import datetime
from io import StringIO
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.auth.middleware import get_logged_in_user
from app.db.conditions.db import (
    get_condition_codes_by_condition_id_db,
    get_included_conditions_db,
)
from app.db.conditions.model import DbCondition
from app.db.configurations.db import get_configuration_by_id_db
from app.db.configurations.model import DbConfiguration
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.code_systems import get_all_code_systems_by_key

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

    config = await get_configuration_by_id_db(
        id=configuration_id, jurisdiction_id=user.jurisdiction_id, db=db
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found.",
        )

    included_conditions = await get_included_conditions_db(
        included_conditions=config.included_conditions, db=db
    )

    csv_bytes = await _build_config_csv(
        config=config, conditions=included_conditions, db=db
    )
    filename = _build_export_filename(config_name=config.name)

    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _build_config_csv(
    config: DbConfiguration,
    conditions: list[DbCondition],
    db: AsyncDatabaseConnection,
) -> bytes:
    """Build the CSV export content for a configuration."""

    code_systems = await get_all_code_systems_by_key(db=db)

    with StringIO() as csv_text:
        writer = csv.writer(csv_text)
        writer.writerow(
            ["Code Type", "Condition", "Code System", "Code", "Display Name"]
        )

        for cond in conditions:
            codes = await get_condition_codes_by_condition_id_db(id=cond.id, db=db)
            for code in codes:
                writer.writerow(
                    [
                        "TES condition grouper code",
                        cond.display_name,
                        code.system,
                        code.code,
                        code.description,
                    ]
                )

        for cc in config.custom_codes or []:
            writer.writerow(
                [
                    "Custom code",
                    "",
                    code_systems[cc.system_key].display_name,
                    cc.code,
                    cc.name,
                ]
            )

        return csv_text.getvalue().encode("utf-8")


def _build_export_filename(config_name: str) -> str:
    """Build a timestamped filename for a configuration export."""
    safe_name = config_name.replace(" ", "_")
    timestamp = datetime.now().strftime("%m%d%y_%H:%M:%S")
    return f"{safe_name}_Code_Export_{timestamp}.csv"
