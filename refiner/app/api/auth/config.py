from authlib.integrations.starlette_client import OAuth

from ...core.config import ENVIRONMENT

SESSION_SECRET_KEY = "super-secret-key"

oauth = OAuth()
oauth.register(
    name=ENVIRONMENT["AUTH_PROVIDER"],
    client_id=ENVIRONMENT["AUTH_CLIENT_ID"],
    client_secret=ENVIRONMENT["AUTH_CLIENT_SECRET"],
    server_metadata_url=f"{ENVIRONMENT['AUTH_ISSUER']}/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
