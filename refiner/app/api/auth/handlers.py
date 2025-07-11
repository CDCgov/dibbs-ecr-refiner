from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from .config import oauth

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
    return await oauth.keycloak.authorize_redirect(request, redirect_uri)


@auth_router.get("/auth/callback")
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
    user = request.session.get("user")
    if not user:
        return JSONResponse(content=user)
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

    # Redirect to client
    post_logout_redirect_uri = "http://localhost:8081"

    id_token = request.session.get("id_token")
    if not id_token:
        # Fallback if user is not logged in
        return RedirectResponse(post_logout_redirect_uri)

    # Clear the session
    request.session.clear()

    # Logout from auth provider
    auth_provider_logout_url = (
        "http://localhost:8082/realms/refiner/protocol/openid-connect/logout"
        f"?post_logout_redirect_uri=http://localhost:8081"
        f"&id_token_hint={id_token}"
    )

    return RedirectResponse(url=auth_provider_logout_url)


# def get_current_user(request: Request):
#     user = request.session.get("user")
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
#         )
#     return user
