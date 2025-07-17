import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .api.auth.config import get_session_secret_key
from .api.auth.handlers import auth_router
from .api.auth.middleware import get_logged_in_user
from .api.auth.session import run_expired_session_cleanup_task
from .api.middleware.spa import SPAFallbackMiddleware
from .api.v1.demo import run_expired_file_cleanup_task
from .api.v1.v1_router import router as v1_router
from .core.app.base import BaseService
from .core.app.openapi import create_custom_openapi
from .core.config import ENVIRONMENT
from .db.pool import db

# create router
router = APIRouter(prefix="/api")

# Public routes
router.include_router(auth_router)

# Private routes
router.include_router(v1_router, dependencies=[Depends(get_logged_in_user)])


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
    # Start the DB connection
    await db.connect()
    # Start the cleanup tasks in the background
    asyncio.create_task(run_expired_file_cleanup_task())
    asyncio.create_task(run_expired_session_cleanup_task())
    yield
    # Release the DB connection
    await db.close()


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
    StaticFiles(directory="dist", html=True, check_dir=ENVIRONMENT["ENV"] == "prod"),
    name="dist",
)

if ENVIRONMENT["ENV"] == "local":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8081"],  # Client dev server
        allow_credentials=True,  # Allow sending session cookies
        allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
        allow_headers=["*"],  # Allow all headers (Authorization, Content-Type, etc.)
    )
app.add_middleware(SPAFallbackMiddleware)
app.add_middleware(SessionMiddleware, secret_key=get_session_secret_key())
