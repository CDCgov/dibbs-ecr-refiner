from dataclasses import dataclass
from uuid import UUID

from fastapi import APIRouter, Depends

from app.db.code_systems.db import get_code_systems_db
from app.db.code_systems.model import DbCodeSystem
from app.db.pool import AsyncDatabaseConnection, get_db

router = APIRouter(prefix="/code-systems")


@dataclass(frozen=True)
class CodeSystemResponse:
    """
    Display information needed for code system information on the frontend.
    """

    id: UUID
    key: str
    display_name: str
    oid: str


def _to_code_system_response(row: DbCodeSystem) -> CodeSystemResponse:
    return CodeSystemResponse(
        id=row.id, key=row.key, display_name=row.display_name, oid=row.oid
    )


@router.get(
    "/",
    response_model=list[CodeSystemResponse],
    tags=["code-systems"],
    operation_id="getCodeSystems",
)
async def get_code_systems(
    db: AsyncDatabaseConnection = Depends(get_db),
) -> list[CodeSystemResponse]:
    """
    Returns a list of supported code systems.

    Returns:
        List of code system.
    """
    code_systems = await get_code_systems_db(db)
    return [_to_code_system_response(s) for s in code_systems]
