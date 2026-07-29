import os

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App

from app.core.config import get_app_config, get_auth_config

_SESSION_SECRET_KEY = get_auth_config().SESSION_SECRET_KEY

_oauth = OAuth()

if get_app_config().ENV == "local":
    _oauth.register(
        name=get_auth_config().AUTH_PROVIDER,
        client_id=get_auth_config().AUTH_CLIENT_ID,
        client_secret=get_auth_config().AUTH_CLIENT_SECRET,
        # FOR THE BROWSER:
        # this is the url the user is redirected to for logging in
        # It **must** be the public url
        authorization_endpoint=f"{get_auth_config().AUTH_ISSUER}/protocol/openid-connect/auth",
        # FOR THE BACKEND:
        # these are for server-to-server communication
        # they **must** be the internal urls
        token_endpoint=f"{os.getenv('AUTH_ISSUER_INTERNAL')}/protocol/openid-connect/token",
        userinfo_endpoint=f"{os.getenv('AUTH_ISSUER_INTERNAL')}/protocol/openid-connect/userinfo",
        jwks_uri=f"{os.getenv('AUTH_ISSUER_INTERNAL')}/protocol/openid-connect/certs",
        client_kwargs={"scope": "openid email profile"},
    )
else:
    _oauth.register(
        name=get_auth_config().AUTH_PROVIDER,
        client_id=get_auth_config().AUTH_CLIENT_ID,
        client_secret=get_auth_config().AUTH_CLIENT_SECRET,
        server_metadata_url=f"{get_auth_config().AUTH_ISSUER}/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

_OAUTH_PROVIDER = getattr(_oauth, get_auth_config().AUTH_PROVIDER)


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
