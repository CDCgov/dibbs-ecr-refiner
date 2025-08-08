from logging import Logger

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from ...services.logger import get_logger
from .config import ENVIRONMENT, get_oauth_provider
from .session import (
    IdpUserResponse,
    create_session,
    delete_session,
    get_user_from_session,
    upsert_user,
)

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
    env = ENVIRONMENT["ENV"]
    redirect_uri = (
        request.url_for("auth_callback")
        if env != "local"
        else "http://localhost:8080/api/auth/callback"
    )

    return await get_oauth_provider().authorize_redirect(request, redirect_uri)


@auth_router.get("/auth/callback", name="auth_callback")
async def auth_callback(
    request: Request, logger: Logger = Depends(get_logger)
) -> RedirectResponse:
    """
    Handles the OAuth2 callback by exchanging the authorization code for tokens, parsing the ID token, and returning the user information.

    Args:
        request (Request): The incoming HTTP request containing the authorization code.
        logger (Logger): The standard logger.

    Returns:
        dict[str, str]: A dictionary of user claims extracted from the ID token.

    Raises:
        Exception: If token exchange or ID token parsing fails.
    """

    try:
        token = await get_oauth_provider().authorize_access_token(request)
        nonce = request.session.get("nonce")
        oidc_user = await get_oauth_provider().parse_id_token(token, nonce)

        idp_user_id = oidc_user.get("sub", None)
        idp_username = oidc_user.get("preferred_username", None)
        idp_email = oidc_user.get("email", None)

        if not idp_user_id:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="IdP response missing required field: 'user_id'",
            )

        if not idp_username:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="IdP response missing required field: 'preferred_username'",
            )

        if not idp_email:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="IdP response missing required field: 'email'",
            )

        logger.info(
            "User logging in",
            extra={
                "user_id": idp_user_id,
                "username": idp_username,
                "email": idp_email,
            },
        )

        # Add or update user in the Refiner DB
        user = IdpUserResponse(
            user_id=idp_user_id, username=idp_username, email=idp_email
        )
        user_id = await upsert_user(user)

        # Create a session for the user
        session_token = await create_session(user_id)

        env = ENVIRONMENT["ENV"]
        redirect_uri = "/" if env != "local" else "http://localhost:8081"
        response = RedirectResponse(url=redirect_uri)

        logger.info("Set cookie for user", extra={"username": user.username})
        response.set_cookie(
            key="refiner-session",
            value=session_token,
            httponly=True,
            max_age=3600,
            samesite="lax",
            secure=env != "local",  # We'll be serving over https in live envs
        )
        return response

    except Exception as e:
        logger.error("IdP callback error", extra={"error": str(e)})
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
async def logout(
    request: Request, logger: Logger = Depends(get_logger)
) -> RedirectResponse:
    """
    Logs the user out by clearing the session and redirecting to the auth provider logout endpoint.

    Args:
        request (Request): The incoming HTTP request.
        logger (Logger): The standard logger.

    Returns:
        RedirectResponse: A redirect to the auth provider logout endpoint and back to the frontend.
    """

    # Redirect to client
    env = ENVIRONMENT["ENV"]
    post_logout_redirect_uri = "/" if env != "local" else "http://localhost:8081"

    session_token = request.cookies.get("refiner-session")

    if session_token:
        user = await get_user_from_session(session_token)

        if user:
            logger.info("Logging out user", extra={"user_id": user.get("id", None)})

        await delete_session(session_token)

    response = RedirectResponse(url=post_logout_redirect_uri)
    response.delete_cookie(
        key="refiner-session",
        httponly=True,
        samesite="lax",
        secure=env != "local",  # We'll be serving over https in live envs
    )
    return response
