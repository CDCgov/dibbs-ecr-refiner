from collections import defaultdict
from dataclasses import asdict, dataclass
from logging import Logger
from uuid import UUID

from fastapi import APIRouter, Depends

from app.db.code_systems.db import get_code_systems_db
from app.db.code_systems.model import DbCodeSystem
from app.db.codes.model import DbCode
from app.db.configurations.custom_codes.model import DbCustomCode
from app.db.pool import AsyncDatabaseConnection, get_db
from app.services.ecr.specification.constants import OID_TO_SYSTEM_KEY_MAP, OTHER_OID
from app.services.terminology import CodeSystemKey, Coding

router = APIRouter(prefix="/code-systems")


@dataclass(frozen=True)
class CodeSystemsReponse:
    """
    Display information needed for code system information on the frontend.
    """

    id: UUID
    key: str
    display_name: str
    oid: str


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
    code_systems = await get_code_systems_db(db)
    return [
        CodeSystemsReponse(
            key=system_data.key,
            display_name=system_data.display_name,
            oid=system_data.oid,
            id=system_data.id,
        )
        for system_data in code_systems
    ]


def index_code_list_by_system_key(
    codes: list[DbCode | DbCustomCode],
    code_systems: dict[UUID, DbCodeSystem],
    logger: Logger = Depends(Logger),
) -> dict[CodeSystemKey, list[dict]]:
    """
    Utility method to index condition code lists as stored into the DB by the ID values. Useful for various processing jobs processing.
    """
    result: dict[CodeSystemKey, list[dict]] = defaultdict(list)
    for c in codes:
        if c.system_id not in code_systems:
            logger.warning(
                f"Code system id of {c.system_id} not found in map, defaulting to other to {OTHER_OID}"
            )
            system_oid = OTHER_OID
            system_key = OID_TO_SYSTEM_KEY_MAP[OTHER_OID]
        else:
            system_oid = code_systems[c.system_id].oid
            system_key = code_systems[c.system_id].key

        result[system_key].append(
            asdict(Coding(code=c.code, display=c.display, system_oid=system_oid))
        )

    return result
