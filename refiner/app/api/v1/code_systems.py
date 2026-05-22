from dataclasses import dataclass
from uuid import UUID

from fastapi import APIRouter, Depends

from app.db.code_systems.db import get_all_code_systems_db
from app.db.pool import AsyncDatabaseConnection, get_db

router = APIRouter(prefix="/code-systems")


@dataclass(frozen=True)
class CodeSystemsReponse:
    """
    Display information needed for code system information on the frontend.
    """

    id: UUID
    key: str
    display_name: str
    oid: str | None


@router.get(
    "/",
    response_model=list[CodeSystemsReponse],
    tags=["code-systems"],
    operation_id="getCodeSystems",
)
async def get_code_systems(
    db: AsyncDatabaseConnection = Depends(get_db),
) -> list[CodeSystemsReponse]:
    """
    Returns a list of supported code systems.

    Returns:
        List of code system.
    """
    all_code_systems = await get_all_code_systems_db(db)
    return [
        CodeSystemsReponse(
            key=system_data.key,
            display_name=system_data.display_name,
            oid=system_data.oid,
            id=system_data.id,
        )
        for system_data in all_code_systems.values()
    ]
