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
    "db_name": _get_env_variable("DB_NAME"),
    "db_user": _get_env_variable("DB_USER"),
    "db_password": _get_env_variable("DB_PASSWORD"),
    "db_host": _get_env_variable("DB_HOST"),
    "db_port": _get_env_variable("DB_PORT"),
}
