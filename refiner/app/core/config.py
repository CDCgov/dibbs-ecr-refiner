import os

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


def _get_env_variable(name: str) -> str:
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


ENVIRONMENT: dict[str, str] = {
    "ENV": _get_env_variable("ENV"),
    "DB_URL": _get_env_variable("DB_URL"),
    "SESSION_SECRET_KEY": _get_env_variable("SESSION_SECRET_KEY"),
    "AUTH_PROVIDER": _get_env_variable("AUTH_PROVIDER"),
    "AUTH_CLIENT_ID": _get_env_variable("AUTH_CLIENT_ID"),
    "AUTH_CLIENT_SECRET": _get_env_variable("AUTH_CLIENT_SECRET"),
    "AUTH_ISSUER": _get_env_variable("AUTH_ISSUER"),
    "AWS_ACCESS_KEY_ID": _get_env_variable("AWS_ACCESS_KEY_ID"),
    "AWS_SECRET_ACCESS_KEY": _get_env_variable("AWS_SECRET_ACCESS_KEY"),
    "AWS_REGION": _get_env_variable("AWS_REGION"),
    "S3_UPLOADED_FILES_BUCKET_NAME": _get_env_variable("S3_UPLOADED_FILES_BUCKET_NAME"),
    "CONFIG_LOCK_TIMEOUT_MINUTES": os.getenv("CONFIG_LOCK_TIMEOUT_MINUTES", "30"),
}
