import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.middleware.spa import SPAFallbackMiddleware
from .api.v1.demo import run_expired_file_cleanup_task
from .api.v1.v1_router import router as v1_router
from .core.app.base import BaseService
from .core.app.openapi import create_custom_openapi
from .core.config import ENVIRONMENT
from .db.connection import DatabaseConnection

# environment configuration
is_production = os.getenv("PRODUCTION", "false").lower() == "true"

# create router
router = APIRouter(prefix="/api")
router.include_router(v1_router)


# define health check endpoint at the service level
@router.get("/healthcheck")
async def health_check() -> JSONResponse:
    """
    Check service health status.

    Returns:
        JSONResponse: Service status response:
            - {"status": "OK", "db": "OK"} with HTTP 200 if service is healthy
            - {"status": "FAIL", "db": "FAIL"} with HTTP 503 if service
              database connection cannot be made
    """

    db = DatabaseConnection(db_url=ENVIRONMENT["DB_URL"])

    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT 1")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=jsonable_encoder({"status": "OK", "db": "OK"}),
            )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=jsonable_encoder({"status": "FAIL", "db": "FAIL"}),
        )


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
app.add_middleware(SPAFallbackMiddleware)
