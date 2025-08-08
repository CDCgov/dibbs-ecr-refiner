import asyncio
import time
import uuid
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC
from datetime import datetime as dt
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
from .db.pool import AsyncDatabaseConnection, db, get_db
from .services.logger import get_logger, set_request_id, setup_logger

# create router
router = APIRouter(prefix="/api")

# Public routes
router.include_router(auth_router)

# Private routes
router.include_router(v1_router, dependencies=[Depends(get_logged_in_user)])


# define health check endpoint at the service level
@router.get("/healthcheck")
async def health_check(
    db: AsyncDatabaseConnection = Depends(get_db),
) -> JSONResponse:
    """
    Check service health status.

    Returns:
        JSONResponse: Service status response:
            - {"status": "OK", "db": "OK"} with HTTP 200 if service is healthy
            - {"status": "FAIL", "db": "FAIL"} with HTTP 503 if service
              database connection cannot be made
    """

    try:
        async with db.get_cursor() as cursor:
            await cursor.execute("SELECT 1")
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
    # Setup logging
    setup_logger()
    logger = get_logger()
    # Start the DB connection
    await db.connect()
    logger.info("Database pool opened", extra={"db_pool_stats": db.get_stats()})
    # Start the cleanup tasks in the background
    asyncio.create_task(run_expired_file_cleanup_task())
    asyncio.create_task(run_expired_session_cleanup_task(logger))
    yield
    # Release the DB connection
    await db.close()
    logger.info("Database pool closed")


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


@app.middleware("http")
async def log_request(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Middleware to log details about a request.

    Args:
        request (Request): The incoming request
        call_next (Callable[[Request], Awaitable[Response]): Continue the path of the original request

    Returns:
        Response: The response of the original request
    """
    request_id = uuid.uuid4()
    set_request_id(request_id)
    logger = get_logger()
    start = time.time()

    logger.info(
        "Request start",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "timestamp": dt.now(UTC).isoformat(),
        },
    )

    response = await call_next(request)

    duration_ms = (time.time() - start) * 1000

    logger.info(
        "Request end",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "status_code": response.status_code,
            "method": request.method,
            "timestamp": dt.now(UTC).isoformat(),
            "duration_ms": round(duration_ms, 2),
        },
    )
    return response
