from pydantic import BaseModel


class Configuration(BaseModel):
    """
    Model for a user-defined configuration.
    """

    id: str
    name: str
    is_active: bool
