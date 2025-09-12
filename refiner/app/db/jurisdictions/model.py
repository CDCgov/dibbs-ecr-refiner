from dataclasses import dataclass


@dataclass(frozen=True)
class DbJurisdiction:
    """
    Jurisdiction info.
    """

    id: str
    name: str
    state_code: str
