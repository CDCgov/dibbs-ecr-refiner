from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetSupportedCodeSystemsReponse:
    """
    Display information needed for code system information on the frontend.
    """

    id: UUID
    name: str
    display_name: str
    oid: str
