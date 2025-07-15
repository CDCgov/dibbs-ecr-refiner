from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App

from ...core.config import ENVIRONMENT

SESSION_SECRET_KEY = "super-secret-key"

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
