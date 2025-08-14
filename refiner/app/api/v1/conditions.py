from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...db.conditions.db import get_conditions_db
from ...db.pool import AsyncDatabaseConnection, get_db

router = APIRouter(prefix="/conditions")


class GetConditionsResponse(BaseModel):
    """
    Conditions response model.
    """

    id: UUID
    display_name: str


@router.get(
    "/",
    response_model=list[GetConditionsResponse],
    tags=["conditions"],
    operation_id="getConditions",
)
async def get_conditions(
    db: AsyncDatabaseConnection = Depends(get_db),
) -> list[GetConditionsResponse]:
    """
    Fetches all available conditions from the database.

    Args:
        db (AsyncDatabaseConnection): Database connection.

    Returns:
        list[Condition]: List of all conditions.
    """
    conditions = await get_conditions_db(db=db)
    return [
        GetConditionsResponse(id=condition.id, display_name=condition.display_name)
        for condition in conditions
    ]
