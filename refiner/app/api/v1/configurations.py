from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg.rows import class_row
from pydantic import BaseModel

from ...api.auth.middleware import get_logged_in_user
from ...db.conditions.model import DbCondition
from ...db.configurations.db import insert_configuration
from ...db.configurations.model import Configuration
from ...db.pool import AsyncDatabaseConnection, get_db
from ...db.user.model import DbUser

router = APIRouter(prefix="/configurations")


@router.get(
    "/",
    response_model=list[Configuration],
    tags=["configurations"],
    operation_id="getConfigurations",
)
def get_configurations() -> list[Configuration]:
    """
    Returns a list of configurations based on the logged-in user.

    Returns:
        List of configuration objects.
    """
    sample_configs = [
        Configuration(id="1", name="Chlamydia trachomatis infection", is_active=True),
        Configuration(id="2", name="Disease caused by Enterovirus", is_active=False),
        Configuration(
            id="3", name="Human immunodeficiency virus infection (HIV)", is_active=False
        ),
        Configuration(id="4", name="Syphilis", is_active=True),
        Configuration(id="5", name="Viral hepatitis, type A", is_active=True),
    ]
    return sample_configs


class CreateConfigInput(BaseModel):
    """
    Body required to create a new configuration.
    """

    condition_id: str


class CreateConfigurationResponse(BaseModel):
    """
    Configuration creation response model.
    """

    id: UUID
    name: str


@router.post(
    "/",
    response_model=CreateConfigurationResponse,
    tags=["configurations"],
    operation_id="createConfiguration",
)
async def create_configuration(
    body: CreateConfigInput,
    user: dict[str, Any] = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> CreateConfigurationResponse:
    """
    Create a new configuration for a jurisdiction.
    """

    # get condition by ID
    condition = await get_condition_by_id(id=body.condition_id, db=db)

    # get user jurisdiction
    db_user = await get_user_by_id(id=str(user["id"]), db=db)
    jd = db_user.jurisdiction_id

    # check that there isn't already a config for the condition + JD
    if not await is_valid_to_create(
        condition_name=condition.display_name, jurisidiction_id=jd, db=db
    ):
        raise HTTPException(
            status_code=500, detail="Configuration for condition already exists."
        )

    config = await insert_configuration(condition=condition, jurisdiction_id=jd, db=db)

    if config is None:
        raise HTTPException(status_code=500, detail="Unable to create configuration")

    return CreateConfigurationResponse(id=config.id, name=config.name)


async def get_user_by_id(id: str, db: AsyncDatabaseConnection) -> DbUser:
    """
    Gets a user from the database with the provided ID.
    """
    query = """
            SELECT id, username, email, jurisdiction_id
            FROM users
            WHERE id = %s
            """
    params = (id,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbUser)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if not row:
        raise Exception(f"User with ID {id} not found.")

    return row


async def get_condition_by_id(id: str, db: AsyncDatabaseConnection) -> DbCondition:
    """
    Gets a condition from the database with the provided ID.
    """

    query = """
        SELECT id,
        canonical_url,
        display_name,
        version
        FROM conditions
        WHERE version = '2.0.0'
        AND id = %s
        """
    params = (id,)

    async with db.get_connection() as conn:
        async with conn.cursor(row_factory=class_row(DbCondition)) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

    if not row:
        raise Exception(f"Condition with ID {id} not found.")

    return row


async def is_valid_to_create(
    condition_name: str, jurisidiction_id: str, db: AsyncDatabaseConnection
) -> bool:
    """
    Query the database to check if a configuration can be created. If a config for a condition already exists, returns False.
    """
    query = """
        SELECT id
        from configurations
        WHERE name = %s
        AND jurisdiction_id = %s
        """
    params = (
        condition_name,
        jurisidiction_id,
    )
    async with db.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchall()

    if not row:
        return True

    return False
