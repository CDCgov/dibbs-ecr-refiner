from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...db.conditions.db import (
    GetConditionCode,
    get_condition_by_id_db,
    get_condition_codes_by_condition_id_db,
    get_conditions_by_configuration_id_db,
    get_conditions_db,
)
from ...db.pool import AsyncDatabaseConnection, get_db

router = APIRouter(prefix="/conditions")


class GetConditionsWithAssociationResponse(BaseModel):
    """
    Conditions response model with association flag.
    """

    id: UUID
    display_name: str
    associated: bool


class GetConditionsResponse(BaseModel):
    """
    Conditions response model.
    """

    id: UUID
    display_name: str


@router.get(
    "/by-configuration/{configuration_id}",
    response_model=list[GetConditionsWithAssociationResponse],
    tags=["conditions"],
    operation_id="getConditionsByConfiguration",
)
async def get_conditions_by_configuration_id(
    configuration_id: UUID,
    db: AsyncDatabaseConnection = Depends(get_db),
) -> list[GetConditionsWithAssociationResponse]:
    """
    Fetch all conditions and indicate whether each is associated with the given configuration ID.

    Args:
        configuration_id (UUID): ID of the configuration.
        db (AsyncDatabaseConnection): Database connection.

    Returns:
        list[GetConditionsWithAssociationResponse]: List of all conditions, each with an 'associated' boolean field set to True if the condition is associated with the given configuration.
    """
    all_conditions = await get_conditions_db(db=db)
    associated_conditions = await get_conditions_by_configuration_id_db(
        configuration_id=configuration_id, db=db
    )
    associated_ids = {condition.id for condition in associated_conditions}
    return [
        GetConditionsWithAssociationResponse(
            id=condition.id,
            display_name=condition.display_name,
            associated=condition.id in associated_ids,
        )
        for condition in all_conditions
    ]


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


class GetConditionResponse(BaseModel):
    """
    Condition response model.
    """

    id: UUID
    display_name: str
    available_systems: list[str]
    codes: list[GetConditionCode]


@router.get(
    "/{condition_id}",
    response_model=GetConditionResponse,
    tags=["conditions"],
    operation_id="getCondition",
)
async def get_condition(
    condition_id: UUID, db: AsyncDatabaseConnection = Depends(get_db)
) -> GetConditionResponse:
    """
    Returns information about a given condition.

    Args:
        condition_id (UUID): ID of the condition
        db (AsyncDatabaseConnection): Database connection.

    Raises:
        HTTPException: 404 if no condition is found

    Returns:
        GetCondition: Info about the condition
    """
    condition = await get_condition_by_id_db(id=condition_id, db=db)

    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found."
        )

    condition_codes = await get_condition_codes_by_condition_id_db(
        id=condition.id, db=db
    )

    # Get all systems in a list (['LOINC', 'SNOMED'])
    available_systems = sorted({code.system for code in condition_codes})

    return GetConditionResponse(
        id=condition.id,
        display_name=condition.display_name,
        available_systems=available_systems,
        codes=condition_codes,
    )
