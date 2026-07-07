from dataclasses import asdict, dataclass
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends

from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.tes_version.db import get_tes_updates_db

router = APIRouter(prefix="/tes")


@dataclass
class TesUpdate:
    """
    All metadata for a TES update needed for the frontend.
    """

    id: UUID
    version: str
    created_at: datetime


@dataclass
class TesResponse:
    """
    Response needed for the TES updates page.
    """

    tes_updates: list[TesUpdate]


@router.get(
    "/",
    response_model=TesResponse,
    tags=["tes_updates"],
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
    updates = await get_tes_updates_db(db=db)

    return TesResponse(tes_updates=[TesUpdate(**asdict(t)) for t in updates])
