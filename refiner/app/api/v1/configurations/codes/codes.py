from dataclasses import dataclass
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.middleware import get_logged_in_user
from app.db.configurations.codes.db import DbCodeResult, get_configuration_codes_db
from app.db.configurations.db import get_configuration_by_id_db
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser

router = APIRouter(prefix="/{configuration_id}")


@dataclass
class CodesResponse:
    """
    Codes and metadata to return to the client.
    """

    codes: list[DbCodeResult]  # TODO: Don't use this directly
    next_cursor: str | None
    total_code_count: int
    total_code_sets_count: int
    total_excluded_codes_count: int


@router.get(
    "/codes",
    response_model=CodesResponse,
    tags=["configurations"],
    operation_id="getCodes",
)
async def get_codes(
    configuration_id: UUID,
    cursor: str | None = None,
    db: AsyncDatabaseConnection = Depends(get_db),
    user: DbUser = Depends(get_logged_in_user),
) -> CodesResponse:
    """
    Fetches all codes associated with a configuration.

    Args:
        configuration_id (UUID): ID of the configuration to update
        cursor (str | None): The cursor for the page to start from
        user (DbUser): The logged-in user
        logger (Logger): The standard logger
        db (AsyncDatabaseConnection): Database connection
    """

    CODES_LIMIT = 1

    config = await get_configuration_by_id_db(
        id=configuration_id,
        jurisdiction_id=user.jurisdiction_id,
        db=db,
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration cannot be found.",
        )

    codes, next_cursor = await get_configuration_codes_db(
        configuration=config, db=db, limit=CODES_LIMIT, cursor=cursor
    )

    return CodesResponse(
        codes=codes,
        next_cursor=next_cursor,
        total_code_count=len(codes),
        total_code_sets_count=len({code.condition_id for code in codes}),
        total_excluded_codes_count=sum(
            1 for code in codes if code.status == "excluded"
        ),
    )
