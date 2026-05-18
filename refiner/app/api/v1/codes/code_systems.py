from fastapi import APIRouter
from refiner.app.services.code_systems import CodeSystems

from app.api.v1.codes.model import GetCodeSystemsReponse

router = APIRouter()


@router.get(
    "/",
    response_model=list[GetCodeSystemsReponse],
    tags=["code-systems"],
    operation_id="getCodeSystems",
)
async def get_code_systems() -> list[GetCodeSystemsReponse]:
    """
    Returns a list of supported code systems.

    Returns:
        List of code system.
    """
    all_code_systems = await CodeSystems.all()
    return [
        GetCodeSystemsReponse(
            key=system_data.key,
            display_name=system_data.display_name,
            oid=system_data.oid,
            id=system_data.id,
        )
        for system_data in all_code_systems
    ]
