from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


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
