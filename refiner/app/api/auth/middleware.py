from typing import Any

from fastapi import HTTPException, Request, status


# This function can be used as an auth check for handlers or routers
def get_logged_in_user(request: Request) -> dict[str, Any]:
    """
    Gets the current user from the session. Throws an error if the user is unauthenticated.

    Args:
        request (Request): Request to check for user info

    Raises:
        HTTPException: 401 Unauthorized is thrown if no user info exists

    Returns:
        _type_: Returns the user information if it's available
    """
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return user
