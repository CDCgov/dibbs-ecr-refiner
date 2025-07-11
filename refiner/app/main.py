import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .api.auth.config import SESSION_SECRET_KEY
from .api.auth.handlers import auth_router
from .api.middleware.spa import SPAFallbackMiddleware
from .api.v1.demo import run_expired_file_cleanup_task
from .api.v1.v1_router import router as v1_router
from .core.app.base import BaseService
from .core.app.openapi import create_custom_openapi

# environment configuration
is_production = os.getenv("PRODUCTION", "false").lower() == "true"

# create router
router = APIRouter(prefix="/api")
router.include_router(auth_router)
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
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)
