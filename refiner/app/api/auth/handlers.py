import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from logging import Logger
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.db.tes.db import get_loaded_tes_versions_db
from app.services.tes import get_latest_tes_version

from ...api.v1.releases import get_latest_release_created_at
from ...db.jurisdictions.db import upsert_jurisdiction_db
from ...db.jurisdictions.model import DbJurisdiction
from ...db.pool import AsyncDatabaseConnection, get_db
from ...db.users.db import (
    IdpUserResponse,
    upsert_user_db,
)
from ...db.users.model import DbUser
from ...services.logger import get_logger
from .config import ENVIRONMENT, get_oauth_provider
from .session import (
    create_session,
    delete_session,
    get_user_from_session,
    set_session_cookie,
)

auth_router = APIRouter()


@auth_router.get("/login", tags=["auth", "internal"], include_in_schema=False)
async def login(
    request: Request, logger: Logger = Depends(get_logger)
) -> RedirectResponse:
    """
    Initiates the OAuth2 login flow by redirecting the user to the authorization endpoint.

    Args:
        request (Request): The incoming HTTP/S request.
        logger (Logger): The standard logger.

    Returns:
        RedirectResponse: A redirect response that sends the user to the OAuth provider's login page.
    """
    env = ENVIRONMENT["ENV"]

    redirect_uri = (
        request.url_for("auth_callback").replace(
            scheme="https"
        )  # Assumes https in non-local env
        if env != "local"
        else "http://localhost:8080/api/auth/callback"
    )

    logger.info(f"Login redirect URI: {redirect_uri}")

    nonce = secrets.token_urlsafe(16)
    request.session["nonce"] = nonce
    return await get_oauth_provider().authorize_redirect(
        request, redirect_uri, nonce=nonce
    )


@auth_router.get(
    "/auth/callback",
    name="auth_callback",
    tags=["auth", "internal"],
    include_in_schema=False,
)
async def auth_callback(
    request: Request,
    logger: Logger = Depends(get_logger),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> RedirectResponse:
    """
    Handles the OAuth2 callback by exchanging the authorization code for tokens, parsing the ID token, and returning the user information.

    Args:
        request (Request): The incoming HTTP request containing the authorization code.
        logger (Logger): The standard logger.
        db (AsyncDatabaseConnection): The DB connection pool.

    Returns:
        dict[str, str]: A dictionary of user claims extracted from the ID token.

    Raises:
        Exception: If token exchange or ID token parsing fails.
    """

    try:
        token = await get_oauth_provider().authorize_access_token(request)
        nonce = request.session.get("nonce")

        # This should be set during the login flow
        if not nonce:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Missing login nonce"
            )

        oidc_user = await get_oauth_provider().parse_id_token(token, nonce)

        # Clear Starlette session once logged in
        request.session.clear()

        idp_user_id = oidc_user.get("sub", None)
        idp_username = oidc_user.get("preferred_username", None)
        idp_email = oidc_user.get("email", None)

        # Demo environment jurisdiction ID will come from the first value in the `roles` array
        idp_roles = oidc_user.get("roles", None)

        # Keycloak (and potentially other IdPs) will pass this value via a user attribute mapping
        idp_jurisdiction_id = oidc_user.get("jurisdiction_id", None)

        # Determine whether to grab the JD from the roles array, if it's present,
        # or use the jurisdiction ID directly sent from the IdP
        idp_jurisdiction_id = (
            idp_roles[0]
            if isinstance(idp_roles, list)
            and len(idp_roles) > 0
            and isinstance(idp_roles[0], str)
            else idp_jurisdiction_id
        )

        if not idp_user_id:
            logger.error(msg="Unable to get user ID from IdP.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="IdP response missing required field: 'user_id'",
            )

        if not idp_username:
            logger.error(msg="Unable to get username from IdP.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="IdP response missing required field: 'preferred_username'",
            )

        if not idp_email:
            logger.error(msg="Unable to get email address from IdP.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="IdP response missing required field: 'email'",
            )

        # TODO: If the IdP does not send `jurisdiction_id` we fall back to "SDDH"
        # Do we want to no longer allow this fallback eventually?
        if not idp_jurisdiction_id:
            idp_jurisdiction_id = "SDDH"
            logger.warning(
                msg="No value for `jurisdiction_id` was received from the IdP, defaulting to fallback value",
                extra={"fallback_jurisdiction_id": idp_jurisdiction_id},
            )

        logger.info(
            "User logging in from IdP",
            extra={
                "user_id": idp_user_id,
                "username": idp_username,
                "jurisdiction_id": idp_jurisdiction_id,
                "email": idp_email,
            },
        )

        # Upsert the user's jurisdiction if needed
        # TODO: Should we no longer collect name and state_code?
        jurisdiction_id = await upsert_jurisdiction_db(
            DbJurisdiction(
                id=str(idp_jurisdiction_id),
                name="Placeholder Jurisdiction",
                state_code="PLACEHOLDER",
            ),
            db=db,
        )

        user = IdpUserResponse(
            user_id=str(idp_user_id),
            username=str(idp_username),
            email=str(idp_email),
            jurisdiction_id=jurisdiction_id,
        )

        user_id = await upsert_user_db(oidc_user_info=user, db=db)

        # Create a session for the user
        session_token = await create_session(user_id=user_id, db=db)

        env = ENVIRONMENT["ENV"]
        redirect_uri = "/" if env != "local" else "http://localhost:8081"
        response = RedirectResponse(url=redirect_uri)

        logger.info("Set cookie for user", extra={"username": user.username})

        # Delete temporary Starlette auth cookie
        response.delete_cookie(
            key="oidc",
            path="/",
            samesite="lax",
            secure=env != "local",
        )

        set_session_cookie(response=response, session_token=session_token)
        return response

    except Exception:
        logger.error("IdP callback error")
        raise


def _map_to_aware_dt(val: str | datetime) -> datetime:
    """Ensures value is a datetime, mapping to UTC timezone."""
    dt = datetime.fromisoformat(val) if isinstance(val, str) else val
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class NotificationKeys(StrEnum):
    """
    Enum class to type the values of the notifications possible for actioning on the frontend.
    """

    MOST_RECENT_APP_UPDATE = "most_recent_app_update"
    MOST_RECENT_TES_UPDATE = "most_recent_tes_update"


@dataclass(frozen=True)
class NotificationsToRender:
    """
    Map of booleans for each of the notificaiton keys as to whether to render frontend banners.
    """

    to_render: dict[NotificationKeys, bool]


class UserResponse(BaseModel):
    """
    User information to send to the client.
    """

    id: UUID
    username: str
    jurisdiction_id: str
    notifications: NotificationsToRender

    @classmethod
    async def from_db_user(
        cls, user: DbUser, db: AsyncDatabaseConnection
    ) -> "UserResponse":
        """
        Mapping method to layer notification information into base db info.
        """

        latest_release_dt = _map_to_aware_dt(get_latest_release_created_at())

        app_update_ack_str = user.notifications.get(
            NotificationKeys.MOST_RECENT_APP_UPDATE
        )
        app_update_ack_dt = _map_to_aware_dt(
            app_update_ack_str if app_update_ack_str else datetime.min
        )

        should_show_app_update = latest_release_dt > app_update_ack_dt

        latest_tes_version = get_latest_tes_version(
            await get_loaded_tes_versions_db(db=db)
        )
        latest_tes_release_dt = _map_to_aware_dt(latest_tes_version.created_at)

        tes_update_ack_str = user.notifications.get(
            NotificationKeys.MOST_RECENT_TES_UPDATE
        )

        tes_update_ack_dt = _map_to_aware_dt(
            tes_update_ack_str if tes_update_ack_str else datetime.min
        )

        should_show_tes_update = latest_tes_release_dt > tes_update_ack_dt

        return cls(
            id=user.id,
            username=user.username,
            jurisdiction_id=user.jurisdiction_id,
            notifications=NotificationsToRender(
                to_render={
                    NotificationKeys.MOST_RECENT_APP_UPDATE: should_show_app_update,
                    NotificationKeys.MOST_RECENT_TES_UPDATE: should_show_tes_update,
                }
            ),
        )


@auth_router.get(
    "/user", response_model=(UserResponse | None), tags=["user"], operation_id="getUser"
)
async def get_user(
    request: Request,
    db: AsyncDatabaseConnection = Depends(get_db),
) -> UserResponse | None:
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
        return None

    user = await get_user_from_session(token=session_token, db=db)

    if not user:
        return None

    return await UserResponse.from_db_user(user=user, db=db)


@auth_router.get("/logout", tags=["auth", "internal"], include_in_schema=False)
async def logout(
    request: Request,
    logger: Logger = Depends(get_logger),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> RedirectResponse:
    """
    Logs the user out by clearing the session and redirecting to the auth provider logout endpoint.

    Args:
        request (Request): The incoming HTTP request.
        logger (Logger): The standard logger.
        db (AsyncDatabaseConnection): The database connection.

    Returns:
        RedirectResponse: A redirect to the auth provider logout endpoint and back to the frontend.
    """

    # Redirect to client
    env = ENVIRONMENT["ENV"]
    post_logout_redirect_uri = "/" if env != "local" else "http://localhost:8081"

    session_token = request.cookies.get("refiner-session")

    if session_token:
        user = await get_user_from_session(token=session_token, db=db)

        if user:
            logger.info("Logging out user", extra={"user_id": user.id})

        await delete_session(token=session_token, db=db)

    response = RedirectResponse(url=post_logout_redirect_uri)

    # Starlette's session shouldn't exist by this point but just to be safe we'll clear/delete it.
    request.session.clear()
    response.delete_cookie(
        key="oidc",
        path="/",
        samesite="lax",
        secure=env != "local",
    )

    response.delete_cookie(
        key="refiner-session",
        httponly=True,
        samesite="lax",
        secure=env != "local",  # We'll be serving over https in live envs
    )
    return response
