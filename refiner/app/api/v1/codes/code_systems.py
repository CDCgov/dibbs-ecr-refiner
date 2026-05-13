from fastapi import APIRouter

from app.api.v1.codes.model import GetSupportedCodeSystemsReponse
from app.services.terminology import SupportedCodeSystems

router = APIRouter()


@router.get(
    "/",
    response_model=list[GetSupportedCodeSystemsReponse],
    tags=["code-systems"],
    operation_id="getCodeSystems",
)
async def get_code_systems() -> list[GetSupportedCodeSystemsReponse]:
    """
    Returns a list of supported code systems.

    Returns:
        List of code system.
    """
    return [
        GetSupportedCodeSystemsReponse(
            name=system_data.name,
            display_name=system_data.display_name,
            oid=system_data.oid,
            id=system_data.id,
        )
        for system_data in SupportedCodeSystems.all()
    ]
