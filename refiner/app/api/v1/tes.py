from dataclasses import dataclass
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.tes.db import (
    get_configurations_set_to_tes_version,
    get_loaded_tes_versions_db,
    get_tes_update_condition_diff_db,
    get_tes_version_diff_db,
)
from app.db.tes.model import TesConfigToUpdate, TesUpdate
from app.services.tes import build_tes_export_csv, sort_tes_updates_by_version

router = APIRouter(prefix="/tes")


@dataclass
class TesResponse:
    """
    Response needed for the TES updates page.
    """

    tes_updates: list[TesUpdate]


@router.get(
    "/diff-details",
    response_model=TesResponse,
    tags=["tes"],
    operation_id="getTesUpdates",
)
async def get_tes_updates(
    db: AsyncDatabaseConnection = Depends(get_db),
) -> TesResponse:
    """
    Returns a list of all TES updates, ordered from newest to oldest.

    Args:
        db (AsyncDatabaseConnection): Database connection.

    Returns:
        TesResponse: A bundle with a list of TesUpdates, including
            - The version
            - The when it was created
    """
    updates = await get_loaded_tes_versions_db(db=db)
    return TesResponse(sort_tes_updates_by_version(updates))


@dataclass
class TesDiffConditionDetails:
    """
    A condition within a TES diff, with details for the diff page to display.
    """

    canonical_url: str
    display_name: str
    added_code_total: int
    removed_code_total: int
    is_new: bool


@router.get(
    "/",
    response_model=list[TesDiffConditionDetails],
    tags=["tes"],
    operation_id="getTesDiffDetails",
)
async def get_tes_diff_details(
    cur_version: str,
    prev_version: str,
    db: AsyncDatabaseConnection = Depends(get_db),
) -> list[TesDiffConditionDetails]:
    """
    Returns a list of all TES updates, ordered from newest to oldest.

    Args:
        cur_version: Version to compare on.
        prev_version: Version to compare against. Potentially an empty string if we're in the "baseline" TES version
        db (AsyncDatabaseConnection): Database connection.

    Returns:
        list[TesDiffResponse]: A bundle with a list of TesDiffResponse, including
            - The condition metadata across the versions
            - The number of added and removed codes
    """
    try:
        conditions_changed = await get_tes_version_diff_db(
            db=db, cur_version=cur_version, prev_version=prev_version
        )

        return [
            TesDiffConditionDetails(
                canonical_url=c.canonical_url,
                display_name=c.display_name,
                added_code_total=len(c.added_code_ids),
                removed_code_total=len(c.removed_code_ids),
                is_new=c.is_new,
            )
            for c in sorted(conditions_changed, key=lambda x: x.display_name)
        ]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specified TES version(s) {cur_version} or {prev_version} not found.",
        )


@router.get(
    "/export",
    tags=["tes"],
    operation_id="exportConditionDiff",
)
async def export_tes_condition_diff(
    cur_version: str,
    prev_version: str,
    canonical_url: str,
    db: AsyncDatabaseConnection = Depends(get_db),
) -> Response:
    """
    Generates and exports a CSV of condition diffs between specified TES versions.

    Args:
        cur_version(str) : The ceiling TES version to compare against
        prev_version(str) : The floor TES version to compare against
        canonical_url(str) : The condition diff being requested
        db (AsyncDatabaseConnection) : The db connection.

    Returns:
            Response: an HTTP response that gives the browser a CSV file to download

    """
    try:
        condition_diff = await get_tes_update_condition_diff_db(
            cur_version=cur_version,
            prev_version=prev_version,
            cond_url=canonical_url,
            db=db,
        )

        (file_name, file_contents) = build_tes_export_csv(
            diff_data=condition_diff, cur_version=cur_version
        )

        return Response(
            content=file_contents,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Condition with URL {canonical_url} not found for TES versions {cur_version} or {prev_version}.",
        )


@dataclass
class TesConfigsToUpdateResponse:
    """
    The response needed for rendering of the TES update configuration page.
    """

    existing_drafts: list[TesConfigToUpdate]
    drafts_to_create: list[TesConfigToUpdate]


@router.get(
    "/configurations-to-update",
    tags=["tes"],
    operation_id="getConfigurationsToUpdate",
)
async def get_configurations_to_update(
    cur_tes_version: str,
    db: AsyncDatabaseConnection = Depends(get_db),
) -> TesConfigsToUpdateResponse:
    """
    Collects information needed to render the TES configs that need updating for a given TES release.

    Args:
        cur_tes_version(str) : The current TES version
        db (AsyncDatabaseConnection) : The db connection.

    Returns:
        TesConfigsToUpdateResponse: information about TES configs to update,
        with a list of existing drafts and drafts to create

    """
    try:
        configs_to_update = await get_configurations_set_to_tes_version(
            db=db, latest_tes_version=cur_tes_version
        )
        return TesConfigsToUpdateResponse(
            existing_drafts=configs_to_update.existing_drafts,
            drafts_to_create=configs_to_update.drafts_to_create,
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TES record for version {cur_tes_version} not found.",
        )
