from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends

from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.tes.db import (
    get_loaded_tes_versions_db,
    get_tes_version_diff_db,
)
from app.db.tes.model import TesUpdate
from app.services.tes import sort_tes_updates_by_version

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
    conditions_changed = await get_tes_version_diff_db(
        db=db, cur_tes_version=cur_version, prev_tes_version=prev_version
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
