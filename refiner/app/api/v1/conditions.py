from dataclasses import dataclass
from typing import Literal, TypeAlias
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.code_systems import CodeSystemsReponse
from app.db.code_systems.db import get_all_code_systems_db
from app.db.conditions.model import DbConditionsContextGrouper

from ...db.conditions.db import (
    GetConditionCode,
    get_condition_by_id_db,
    get_condition_codes_by_condition_id_db,
    get_context_groupers_by_condition_id_db,
    get_latest_conditions_db,
)
from ...db.pool import AsyncDatabaseConnection, get_db

router = APIRouter(prefix="/conditions")


@dataclass(frozen=True)
class GetConditionsResponse:
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

    conditions = await get_latest_conditions_db(db=db)
    return [
        GetConditionsResponse(
            id=condition.id,
            display_name=condition.display_name,
        )
        for condition in conditions
    ]


type CodeSetStatus = Literal["not expanded", "partially complete", "fully complete"]

CodeCategoryStatus: TypeAlias = Literal[
    "not included",
    "partially complete",
    "fully complete",
]

@dataclass
class CodeCategoryCompletenessStatus:
    """
    Code category completeness status model.
    """

    category: str
    name: str
    completeness: CodeCategoryStatus

@dataclass
class CompletenessStatus:
    """
    Condition completeness status model.
    """

    code_set_status: CodeSetStatus
    code_category_statuses: list[CodeCategoryCompletenessStatus]


@dataclass(frozen=True)
class GetConditionResponse:
    """
    Condition response model.
    """

    id: UUID
    display_name: str
    completeness_status: CompletenessStatus
    codes: list[GetConditionCode]
    systems: list[CodeSystemsReponse]


def _get_code_set_status(coverage_level: str | None) -> CodeSetStatus:
    if coverage_level == "complete":
        return "fully complete"

    if coverage_level == "partial":
        return "partially complete"

    return "not expanded"


def _get_code_category_statuses(
    groupers: list[DbConditionsContextGrouper],
) -> list[CodeCategoryCompletenessStatus]:
    category_names = {
        "symptom": "Symptom codes",
        "medication": "Medication codes",
        "diagnosis": "Diagnosis codes",
        "clinical_lab_result": "Clinical lab result codes",
        "immunization": "Immunization codes",
        "specimen_source": "Specimen source codes",
    }

    completeness_by_category = {
        row.category: row.completeness for row in groupers
    }

    return [
        CodeCategoryCompletenessStatus(
            category=category,
            name=name,
            completeness=completeness_by_category.get(
                category,
                "not included",
            ),
        )
        for category, name in category_names.items()
    ]


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

    code_set_status = _get_code_set_status(condition.coverage_level)

    groupers = await get_context_groupers_by_condition_id_db(
        condition_id=condition.id, db=db
    )

    code_category_statuses = _get_code_category_statuses(groupers=groupers)
    systems = await get_all_code_systems_db(db)
    return GetConditionResponse(
        id=condition.id,
        display_name=condition.display_name,
        completeness_status=CompletenessStatus(
            code_set_status=code_set_status,
            code_category_statuses=code_category_statuses,
        ),
        codes=condition_codes,
        systems=[
            CodeSystemsReponse(
                id=s.id, key=s.key, display_name=s.display_name, oid=s.oid
            )
            for s in systems.values()
        ],
    )
