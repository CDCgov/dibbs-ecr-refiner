from pydantic import BaseModel


class DbJurisdiction(BaseModel):
    """
    Jurisdiction info.
    """

    id: str
    name: str
    state_code: str
