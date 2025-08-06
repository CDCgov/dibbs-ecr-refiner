from pydantic import BaseModel


class User(BaseModel):
    """
    Model for a logged-in user.
    """

    id: str
    username: str
