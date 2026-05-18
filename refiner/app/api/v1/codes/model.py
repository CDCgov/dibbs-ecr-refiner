from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetCodeSystemsReponse:
    """
    Display information needed for code system information on the frontend.
    """

    id: UUID
    key: str
    display_name: str
    oid: str
