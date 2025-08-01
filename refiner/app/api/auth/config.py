from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App

from ...core.config import ENVIRONMENT

_SESSION_SECRET_KEY = ENVIRONMENT["SESSION_SECRET_KEY"]

_oauth = OAuth()
_oauth.register(
    name=ENVIRONMENT["AUTH_PROVIDER"],
    client_id=ENVIRONMENT["AUTH_CLIENT_ID"],
    client_secret=ENVIRONMENT["AUTH_CLIENT_SECRET"],
    server_metadata_url=f"{ENVIRONMENT['AUTH_ISSUER']}/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

_OAUTH_PROVIDER = getattr(_oauth, ENVIRONMENT["AUTH_PROVIDER"])


def get_oauth_provider() -> StarletteOAuth2App:
    """
    Retrieve the configured OAuth provider client.

    This function returns the `StarletteOAuth2App` instance that was
    registered using the `authlib` OAuth integration. The specific provider
    (Keycloak, Identity center, etc.) is determined by the `AUTH_PROVIDER`
    environment configuration.

    Returns:
        StarletteOAuth2App: The configured OAuth client used to initiate
        authentication flows.
    """
    return _OAUTH_PROVIDER


def get_session_secret_key() -> str:
    """
    Retrieves the session secret key.

    Returns:
        str: Session secret key
    """
    return _SESSION_SECRET_KEY
