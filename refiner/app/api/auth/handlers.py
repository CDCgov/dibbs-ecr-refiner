from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from .config import get_oauth_provider
from .session import create_session, delete_session, get_user_from_session, upsert_user

auth_router = APIRouter()


@auth_router.get("/login")
async def login(request: Request) -> RedirectResponse:
    """
    Initiates the OAuth2 login flow by redirecting the user to the authorization endpoint.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        RedirectResponse: A redirect response that sends the user to the OAuth provider's login page.
    """
    redirect_uri = "http://localhost:8080/api/auth/callback"
    return await get_oauth_provider().authorize_redirect(request, redirect_uri)


@auth_router.get("/auth/callback")
async def auth_callback(request: Request) -> RedirectResponse:
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
        token = await get_oauth_provider().authorize_access_token(request)
        nonce = request.session.get("nonce")
        oidc_user = await get_oauth_provider().parse_id_token(token, nonce)

        # Add or updater user in the Refiner DB
        user_id = await upsert_user(oidc_user)

        # Create a session for the user
        session_token = await create_session(user_id)

        response = RedirectResponse(url="http://localhost:8081")
        print("Setting browser cookie for user:", user_id)
        response.set_cookie(
            key="refiner-session",
            value=session_token,
            httponly=True,
            max_age=3600,
            samesite="lax",
        )
        return response

    except Exception as e:
        print("Callback error:", e)
        raise e


@auth_router.get("/user")
async def get_user(request: Request) -> JSONResponse:
    """
    Returns the current logged-in user's information.

    Reads user info from the session or token.

    Returns:
        JSON object with user claims if authenticated.

    Raises:
        HTTPException 401 if user not authenticated.
    """
    session_token = request.cookies.get("refiner-session")

    if not session_token:
        return JSONResponse(content=None)

    user = await get_user_from_session(session_token)

    if not user:
        return JSONResponse(content=None)

    return JSONResponse(content=user)


@auth_router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """
    Logs the user out by clearing the session and redirecting to the auth provider logout endpoint.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        RedirectResponse: A redirect to the auth provider logout endpoint and back to the frontend.
    """

    post_logout_redirect_uri = "http://localhost:8081"

    # Logout from auth provider
    # Do we want to do this?
    # auth_provider_logout_url = (
    #     "http://localhost:8082/realms/refiner/protocol/openid-connect/logout"
    #     f"?post_logout_redirect_uri=http://localhost:8081"
    #     f"&id_token_hint={id_token}"
    # )

    # Redirect to client
    post_logout_redirect_uri = "http://localhost:8081"

    session_token = request.cookies.get("refiner-session")

    if session_token:
        await delete_session(session_token)

    response = RedirectResponse(url=post_logout_redirect_uri)
    response.delete_cookie(
        key="refiner-session",
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return response
