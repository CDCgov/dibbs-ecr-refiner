import csv
from datetime import UTC, datetime
from io import StringIO
from logging import Logger
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from app.api.auth.middleware import get_logged_in_user
from app.db.conditions.db import (
    get_condition_codes_by_condition_id_db,
    get_included_conditions_db,
)
from app.db.conditions.model import DbCondition
from app.db.configurations.db import get_configuration_by_id_db
from app.db.configurations.model import (
    DbConfiguration,
    DbConfigurationSectionProcessing,
    DbNarrativeAction,
    DbSectionAction,
)
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.code_systems import get_all_code_systems_by_key
from app.services.file_io import ZipFileItem, ZipFilePackage
from app.services.logger import get_logger

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
    logger: Logger = Depends(get_logger),
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

    codes_csv_content = await _build_config_csv(
        config=config, conditions=included_conditions, logger=logger, db=db
    )
    sections_csv_content = _build_sections_csv(sections=config.section_processing)

    timestamp = _get_timestamp()

    zip_package = ZipFilePackage(
        name=_build_export_filename(
            filename="Configuration_Export",
            type="zip",
            config_name=config.name,
            config_version=config.version,
            timestamp=timestamp,
        )
    )

    zip_package.add(
        ZipFileItem(
            file_name=_build_export_filename(
                filename="Code_Export",
                type="csv",
                config_name=config.name,
                config_version=config.version,
                timestamp=timestamp,
            ),
            file_content=codes_csv_content,
        )
    )

    zip_package.add(
        ZipFileItem(
            file_name=_build_export_filename(
                filename="Section_Export",
                type="csv",
                config_name=config.name,
                config_version=config.version,
                timestamp=timestamp,
            ),
            file_content=sections_csv_content,
        )
    )

    return StreamingResponse(
        content=zip_package.iter_chunks(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_package.get_name()}"'
        },
    )


def _build_sections_csv(
    sections: list[DbConfigurationSectionProcessing],
) -> str:
    """Build a CSV summarizing configuration section information."""
    with StringIO() as csv_text:
        writer = csv.writer(csv_text)
        writer.writerow(
            ["Section Name", "LOINC", "Include", "Coded Data", "Narrative Data"]
        )

        for section in sorted(sections, key=lambda r: r.name.lower()):
            writer.writerow(
                [
                    section.name,
                    section.code,
                    "Yes" if section.include else "No",
                    _get_coded_data_value(
                        action=section.action, included=section.include
                    ),
                    _get_narrative_data_value(
                        narrative=section.narrative, included=section.include
                    ),
                ]
            )
        return csv_text.getvalue()


def _get_coded_data_value(action: DbSectionAction, included: bool) -> str:
    if not included:
        return "N/A"

    if action == "retain":
        return "Keep original"

    if action == "refine":
        return "Refine"

    return "N/A"


def _get_narrative_data_value(narrative: DbNarrativeAction, included: bool) -> str:
    if not included:
        return "N/A"

    if narrative == "retain":
        return "Keep original"

    if narrative == "remove":
        return "Exclude"

    return "Reconstruct"


async def _build_config_csv(
    config: DbConfiguration,
    conditions: list[DbCondition],
    logger: Logger,
    db: AsyncDatabaseConnection,
) -> str:
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
            code_system = code_systems.get(cc.system_key)
            if code_system is None:
                logger.warning(
                    "Could not find code system for custom code, skipping",
                    extra={"system_key": cc.system_key, "code": cc.code},
                )
                continue

            writer.writerow(
                [
                    "Custom code",
                    "",
                    code_system.display_name,
                    cc.code,
                    cc.name,
                ]
            )

        return csv_text.getvalue()


def _get_timestamp() -> str:
    now = datetime.now(UTC)
    timestamp = now.strftime("%m%d%y_%H_%M_%S")
    return timestamp


def _build_export_filename(
    filename: str,
    type: Literal["csv", "zip"],
    config_name: str,
    config_version: int,
    timestamp: str,
) -> str:
    """Build a timestamped filename for a configuration export."""
    condition_grouper = config_name.replace(" ", "_")
    return f"{condition_grouper}_v{config_version}_{filename}_{timestamp}.{type}"
