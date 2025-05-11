from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings

# create a class with the DIBBs default Creative Commons Zero v1.0 and
# MIT license to be used by the BaseService class
LICENSES = {
    "CreativeCommonsZero": {
        "name": "Creative Commons Zero v1.0 Universal",
        "url": "https://creativecommons.org/publicdomain/zero/1.0/",
    },
    "MIT": {"name": "The MIT License", "url": "https://mit-license.org/"},
}

DIBBS_CONTACT = {
    "name": "CDC Public Health Data Infrastructure",
    "url": "https://cdcgov.github.io/dibbs-site/",
    "email": "dibbs@cdc.gov",
}


class Settings(BaseSettings):
    """
    Configuration settings loaded from environment variables.

    Manages service URLs and configuration values that must be defined
    in a .env file at the root level of the project.
    """

    TRIGGER_CODE_REFERENCE_URL: str = Field(
        description="The URL for the Trigger Code Reference service.",
        json_schema_extra={"env": "TRIGGER_CODE_REFERENCE_URL"},
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings from environment variables.

    Creates and caches a Settings instance to reduce overhead when
    accessing configuration values.

    Returns:
        Settings: Application settings loaded from environment variables.
    """

    return Settings().model_dump()
