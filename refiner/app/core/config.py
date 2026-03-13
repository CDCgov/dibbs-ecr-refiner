from app.core.utils import get_env_variable

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


ENVIRONMENT: dict[str, str] = {
    "ENV": get_env_variable("ENV"),
    "VERSION": get_env_variable("VERSION"),
    "DB_URL": get_env_variable("DB_URL"),
    "DB_PASSWORD": get_env_variable("DB_PASSWORD"),
    "SESSION_SECRET_KEY": get_env_variable("SESSION_SECRET_KEY"),
    "AUTH_PROVIDER": get_env_variable("AUTH_PROVIDER"),
    "AUTH_CLIENT_ID": get_env_variable("AUTH_CLIENT_ID"),
    "AUTH_CLIENT_SECRET": get_env_variable("AUTH_CLIENT_SECRET"),
    "AUTH_ISSUER": get_env_variable("AUTH_ISSUER"),
    "AWS_REGION": get_env_variable("AWS_REGION"),
    "S3_BUCKET_CONFIG": get_env_variable("S3_BUCKET_CONFIG"),
}
