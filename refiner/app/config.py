from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Settings confirms the URLs for each of the services being called;
    These urls need to live in a .env file at the root level and should be set.
    """

    TRIGGER_CODE_REFERENCE_URL: str = Field(
        description="The URL for the Trigger Code Reference service.",
        json_schema_extra={"env": "TRIGGER_CODE_REFERENCE_URL"},
    )


@lru_cache
def get_settings() -> Settings:
    """
    Load the values specified in the Settings class from the environment and return a
    dictionary containing them. The dictionary is cached to reduce overhead accessing
    these values.

    :return: the specified Settings. The value of each key is read from the
    corresponding environment variable.
    """
    return Settings().model_dump()
