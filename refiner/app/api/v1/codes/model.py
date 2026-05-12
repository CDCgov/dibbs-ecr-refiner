from dataclasses import dataclass


@dataclass(frozen=True)
class GetSupportedCodeSystemsReponse:
    """
    Display information needed for code system information on the frontend.
    """

    name: str
    display_name: str
    oid: str
