import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

from .api.v1.v1_router import router as v1_router
from .core.app.base import BaseService
from .core.app.openapi import create_custom_openapi

# environment configuration
is_production = os.getenv("PRODUCTION", "false").lower() == "true"

# create router
router = APIRouter(prefix="/api")
router.include_router(v1_router)


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


# Instantiate FastAPI via DIBBs' BaseService class
app = BaseService(
    service_name="Message Refiner",
    service_path="/message-refiner",
    description_path=Path(__file__).parent.parent / "README.md",
    include_health_check_endpoint=False,
    openapi_url="/api/openapi.json",
).start()

# set service_path in app state
# add open api configuration
app.state.service_path = "/api"
app.openapi = lambda: create_custom_openapi(app)

# include the router in the app
app.include_router(router)

# When running the application in production we will mount the static client files from the
# "dist" directory. This directory will typically not exist during development since the client
# runs separately in its own Docker container.
if is_production:
    app.mount(
        "/",
        StaticFiles(directory="dist", html=True, check_dir=is_production),
        name="dist",
    )
