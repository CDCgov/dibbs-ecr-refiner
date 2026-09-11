import csv
import sys
from io import StringIO
from logging import Logger
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from app.api.auth.middleware import get_logged_in_user
from app.api.v1.configurations.codes.model import FilterInput
from app.db.configurations.codes.db import get_codes_db
from app.db.configurations.db import get_configuration_by_id_db
from app.db.configurations.labels import CODED_DATA_LABELS, NARRATIVE_DATA_LABELS
from app.db.configurations.model import (
    DbConfiguration,
    DbConfigurationSectionProcessing,
    DbNarrativeAction,
    DbSectionAction,
)
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.ecr.policy import NARRATIVE_ONLY_SECTIONS
from app.services.file_exports import get_export_timestamp
from app.services.file_io import ZipFileItem, ZipFilePackage

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

    codes_csv_content = await _build_config_csv(config=config, db=db)
    sections_csv_content = _build_sections_csv(sections=config.section_processing)

    timestamp = get_export_timestamp()

    zip_package = ZipFilePackage(
        name=_build_export_filename(
            filename="Configuration_Export",
            extension="zip",
            config_name=config.name,
            config_version=config.version,
            timestamp=timestamp,
        )
    )

    zip_package.add(
        ZipFileItem(
            file_name=_build_export_filename(
                filename="Code_Export",
                extension="csv",
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
                extension="csv",
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
            "Content-Disposition": f'attachment; filename="{zip_package.get_name()}"',
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
                        loinc=section.code,
                        action=section.action,
                        included=section.include,
                    ),
                    _get_narrative_data_value(
                        narrative=section.narrative, included=section.include
                    ),
                ]
            )
        return csv_text.getvalue()


def _get_coded_data_value(loinc: str, action: DbSectionAction, included: bool) -> str:
    if not included:
        return "N/A"

    if loinc in NARRATIVE_ONLY_SECTIONS:
        return "N/A"

    return CODED_DATA_LABELS.get(action, "N/A")


def _get_narrative_data_value(narrative: DbNarrativeAction, included: bool) -> str:
    if not included:
        return "N/A"

    return NARRATIVE_DATA_LABELS.get(narrative, "N/A")


async def _build_config_csv(
    config: DbConfiguration, db: AsyncDatabaseConnection
) -> str:
    """Build the CSV export content for a configuration."""

    with StringIO() as csv_text:
        writer = csv.writer(csv_text)
        writer.writerow(["Code System", "Code", "Status", "Display Name", "Source(s)"])
        cursor: str | None = None

        while True:
            codes, cursor = await get_codes_db(
                config=config,
                db=db,
                limit=1000,
                filters=FilterInput(
                    code_systems=[],
                    sources=[],
                    statuses=[],
                ),
                cursor=cursor,
            )
            for code in codes:
                writer.writerow(
                    [
                        code.system_name,
                        code.code,
                        code.status,
                        code.description,
                        ", ".join(code.source),
                    ]
                )

            if not cursor:
                break

        return csv_text.getvalue()


def _build_export_filename(
    filename: str,
    extension: Literal["csv", "zip"],
    config_name: str,
    config_version: int,
    timestamp: str,
) -> str:
    """Build a timestamped filename for a configuration export."""
    condition_grouper = config_name.replace(" ", "_")
    return f"{condition_grouper}_v{config_version}_{filename}_{timestamp}.{extension}"
