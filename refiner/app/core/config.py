import os
from functools import lru_cache

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


def get_env_variable(name: str) -> str:
    """
    Grabs a variable by name from the environment. Throws an error if the variable is not present.

    Args:
        name (str): Name of the environment variable

    Raises:
        OSError: raised if environment variable is not present

    Returns:
        str: Name of the environment variable
    """
    value = os.getenv(name)
    if value is None:
        raise OSError(f"Missing environment variable: {name}")
    return value


class AppConfig:
    """Core variables needed by all entry points."""

    def __init__(self) -> None:  # noqa: D107
        self.ENV: str = get_env_variable("ENV")
        self.VERSION: str = get_env_variable("VERSION")


class DbConfig:
    """Database config. Needed by API and Ops."""

    def __init__(self) -> None:  # noqa: D107
        self.DB_URL: str = get_env_variable("DB_URL")
        self.DB_PASSWORD: str = get_env_variable("DB_PASSWORD")


class AuthConfig:
    """Auth config. Needed by API."""

    def __init__(self) -> None:  # noqa: D107
        self.SESSION_SECRET_KEY: str = get_env_variable("SESSION_SECRET_KEY")
        self.AUTH_PROVIDER: str = get_env_variable("AUTH_PROVIDER")
        self.AUTH_CLIENT_ID: str = get_env_variable("AUTH_CLIENT_ID")
        self.AUTH_CLIENT_SECRET: str = get_env_variable("AUTH_CLIENT_SECRET")
        self.AUTH_ISSUER: str = get_env_variable("AUTH_ISSUER")


class S3Config:
    """S3 config. Needed by API, Lambda, Ops."""

    def __init__(self) -> None:  # noqa: D107
        self.S3_BUCKET_CONFIG: str = get_env_variable("S3_BUCKET_CONFIG")
        self.AWS_REGION: str = get_env_variable("AWS_REGION")


@lru_cache
def get_app_config() -> AppConfig:
    """
    Creates an instance of an AppConfig.
    """
    return AppConfig()


@lru_cache
def get_db_config() -> DbConfig:
    """
    Creates an instance of a DbConfig.
    """
    return DbConfig()


@lru_cache
def get_auth_config() -> AuthConfig:
    """
    Creates an instance of an AuthConfig.
    """
    return AuthConfig()


@lru_cache
def get_s3_config() -> S3Config:
    """
    Creates an instance of an S3Config.
    """
    return S3Config()
