from fastapi import APIRouter, Depends

from app.api.v1.codes.model import GetSupportedCodeSystemsReponse
from app.db.pool import AsyncDatabaseConnection
from app.services.terminology import SupportedCodeSystems

router = APIRouter()


@router.get(
    "/",
    response_model=list[GetSupportedCodeSystemsReponse],
    tags=["code-systems"],
    operation_id="getCodeSystems",
)
async def get_code_systems(
    db: AsyncDatabaseConnection = Depends(get_db),
) -> list[GetSupportedCodeSystemsReponse]:
    """
    Returns a list of supported code systems based.

    Returns:
        List of code system.
    """
    all_supported_codes = SupportedCodeSystems.all()
    if len(all_supported_codes) == 0:
        await SupportedCodeSystems.load_from_db(db)
    return [
        GetSupportedCodeSystemsReponse(
            name=system_data.name,
            display_name=system_data.display_name,
            oid=system_data.oid,
        )
        for system_data in SupportedCodeSystems.all()
    ]
