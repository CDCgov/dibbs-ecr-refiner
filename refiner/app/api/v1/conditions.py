from fastapi import APIRouter, Depends

from ...db.conditions.db import get_all_conditions
from ...db.conditions.model import Condition
from ...db.pool import AsyncDatabaseConnection, get_db

router = APIRouter(prefix="/conditions")


@router.get("/", response_model=list[Condition])
async def get_conditions(
    db: AsyncDatabaseConnection = Depends(get_db),
) -> list[Condition]:
    """
    Fetches all available conditions from the database.

    Args:
        db (AsyncDatabaseConnection): Database connection.

    Returns:
        list[Condition]: List of all conditions.
    """
    conditions = await get_all_conditions(db=db)
    return conditions
