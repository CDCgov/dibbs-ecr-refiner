import asyncio
import os
import urllib
from contextlib import asynccontextmanager
from pathlib import Path

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .api.middleware.spa import SPAFallbackMiddleware
from .api.v1.demo import run_expired_file_cleanup_task
from .api.v1.v1_router import router as v1_router
from .core.app.base import BaseService
from .core.app.openapi import create_custom_openapi
from .core.config import ENVIRONMENT

SECRET_KEY = "super-secret-key"

# environment configuration
is_production = os.getenv("PRODUCTION", "false").lower() == "true"

# create router
router = APIRouter(prefix="/api")
router.include_router(v1_router)


oauth = OAuth()
oauth.register(
    name=ENVIRONMENT["AUTH_PROVIDER"],
    client_id=ENVIRONMENT["AUTH_CLIENT_ID"],
    client_secret=ENVIRONMENT["AUTH_CLIENT_SECRET"],
    server_metadata_url=f"{ENVIRONMENT['AUTH_ISSUER']}/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


# define health check endpoint at the service level
@router.get("/healthcheck")
async def health_check() -> dict[str, str]:
    """
    Check service health status.

    Returns:
        dict[str, str]: Service status response:
            - {"status": "OK"} with HTTP 200 if service is healthy
    """

    return {"status": "OK"}


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    """
    Initiates the OAuth2 login flow by redirecting the user to the authorization endpoint.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        RedirectResponse: A redirect response that sends the user to the OAuth provider's login page.
    """
    redirect_uri = "http://localhost:8080/api/auth/callback"
    return await oauth.keycloak.authorize_redirect(request, redirect_uri)


@router.get("/auth/callback")
async def auth_callback(request: Request) -> dict[str, str]:
    """
    Handles the OAuth2 callback by exchanging the authorization code for tokens, parsing the ID token, and returning the user information.

    Args:
        request (Request): The incoming HTTP request containing the authorization code.

    Returns:
        dict[str, str]: A dictionary of user claims extracted from the ID token.

    Raises:
        Exception: If token exchange or ID token parsing fails.
    """

    try:
        token = await oauth.keycloak.authorize_access_token(request)
        nonce = request.session.get("nonce")
        user = await oauth.keycloak.parse_id_token(token, nonce)

        request.session["id_token"] = token["id_token"]
        request.session["user"] = user

        # print(dict(user))

        return RedirectResponse(url="http://localhost:8081")
    except Exception as e:
        print("Callback error:", e)
        raise e


@router.get("/user")
async def get_user(request: Request) -> JSONResponse:
    """
    Returns the current logged-in user's information.

    Reads user info from the session or token.

    Returns:
        JSON object with user claims if authenticated.

    Raises:
        HTTPException 401 if user not authenticated.
    """
    user = request.session.get("user")
    if not user:
        return JSONResponse(content=user)
    return JSONResponse(content=user)


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """
    Logs the user out by clearing the session and redirecting to the auth provider logout endpoint.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        RedirectResponse: A redirect to the auth provider logout endpoint and back to the frontend.
    """
    # Clear the session
    request.session.clear()

    # Redirect to client
    post_logout_redirect_uri = "http://localhost:8081"

    # Logout from auth provider
    auth_provider_logout_url = (
        "http://localhost:8082/realms/refiner/protocol/openid-connect/logout?"
        + urllib.parse.urlencode({"redirect_uri": post_logout_redirect_uri})
    )

    return RedirectResponse(url=auth_provider_logout_url)


@asynccontextmanager
async def _lifespan(_: FastAPI):
    # Start the cleanup task in the background
    asyncio.create_task(run_expired_file_cleanup_task())
    yield


# Instantiate FastAPI via DIBBs' BaseService class
app = BaseService(
    service_name="Message Refiner",
    service_path="/refiner",
    description_path=Path(__file__).parent.parent / "README.md",
    include_health_check_endpoint=False,
    openapi_url="/api/openapi.json",
    lifespan=_lifespan,
).start()

# set service_path in app state
# add open api configuration
app.state.service_path = "/api"
app.openapi = lambda: create_custom_openapi(app)  # type: ignore

# include the router in the app
app.include_router(router)
app.mount(
    "/dist",
    StaticFiles(directory="dist", html=True, check_dir=is_production),
    name="dist",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SPAFallbackMiddleware)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
