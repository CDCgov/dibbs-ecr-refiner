import asyncio
import json
import time
import uuid
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from datetime import UTC
from datetime import datetime as dt
from logging import Logger
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from psycopg.rows import dict_row
from starlette.middleware.sessions import SessionMiddleware
from starlette.types import Lifespan, Scope

from .api.auth.config import get_session_secret_key
from .api.auth.handlers import auth_router
from .api.auth.middleware import get_logged_in_user
from .api.auth.session import run_expired_session_cleanup_task
from .api.v1.v1_router import router as v1_router
from .core.app.base import BaseService
from .core.app.openapi import create_custom_openapi
from .core.config import ENVIRONMENT
from .db.pool import AsyncDatabaseConnection, get_db
from .services.logger import get_logger, set_request_id

# Define a set of text-based media types that commonly use charset
TEXT_TYPES = {
    "text/html",
    "text/css",
    "text/javascript",
    "text/plain",
    "application/json",
    "application/xml",
}


class CharsetStaticFiles(StaticFiles):
    """
    Custom class to fill in charset information for Static Files.

    Created to mitigate an issue that got flagged during the DAST scan from APHL.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        """
        Method that checks and adds charset information if it doesn't exist.
        """
        response = await super().get_response(path, scope)
        content_type = response.headers.get("content-type", "")

        # Check if the content type is text-based and lacks a charset
        if content_type.split(";")[0] in TEXT_TYPES and "charset" not in content_type:
            response.headers["content-type"] = f"{content_type}; charset=utf-8"

        return response


def create_lifespan(
    db: AsyncDatabaseConnection, logger: Logger
) -> Callable[[FastAPI], AbstractAsyncContextManager]:
    """
    Creates a FastAPI lifespan.

    Args:
        db (AsyncDatabaseConnection): The database connection
        logger (Logger): The application logger

    Returns:
        Lifespan: FastAPI Lifespan
    """

    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        # Write OpenAPI doc
        if ENVIRONMENT["ENV"] == "local":
            schema = create_custom_openapi(app)
            with open("openapi.json", "w") as f:
                json.dump(schema, f)
        # Start the DB connection
        app.state.db = db
        await db.connect()
        logger.info("Database pool opened", extra={"db_pool_stats": db.get_stats()})
        # Start the cleanup tasks in the background
        asyncio.create_task(run_expired_session_cleanup_task(logger, db=db))
        yield
        # Release the DB connection
        await db.close()
        logger.info("Database pool closed")

    return _lifespan


def create_fastapi_app(lifespan: Lifespan[FastAPI]) -> FastAPI:
    """
    Configures and initializes the FastAPI application.

    Args:
        lifespan (Lifespan[FastAPI]): A FastAPI Lifespan object

    Returns:
        FastAPI: the app
    """

    # create router
    router = APIRouter(prefix="/api")

    # Public routes
    router.include_router(auth_router)

    # Private routes
    router.include_router(v1_router, dependencies=[Depends(get_logged_in_user)])

    # define health check endpoint at the service level
    @router.get("/healthcheck", tags=["internal"], include_in_schema=False)
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
            async with db.get_connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cursor:
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

    # Instantiate FastAPI via DIBBs' BaseService class
    app = BaseService(
        service_name="DIBBs eCR Refiner",
        service_path="/refiner",
        description="Please visit the repo for more info: https://github.com/CDCgov/dibbs-ecr-refiner",
        include_health_check_endpoint=False,
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    ).start()

    # set service_path in app state
    # add open api configuration
    app.state.service_path = "/api"
    app.openapi = lambda: create_custom_openapi(app)  # type: ignore

    # include the router in the app
    app.include_router(router)
    # Use custom CharsetStaticFiles class to fill in charset information
    # in the Content-Type HTTP header for HTTPHeaders (Charset / Content-Type Issues)
    app.mount(
        "/dist/assets",
        CharsetStaticFiles(
            directory="dist/assets", html=True, check_dir=ENVIRONMENT["ENV"] == "prod"
        ),
        name="assets",
    )

    @app.get(
        "/{full_path:path}",
        response_class=HTMLResponse,
        tags=["internal"],
        include_in_schema=False,
    )
    async def serve_index(full_path: str) -> HTMLResponse:
        """
        Intercept incoming requests.

        Modifies the `dist/index.html` file to include the enviroment, and return the file.

        Args:
            full_path (str): incoming URL

        Returns:
            HTMLResponse: Modified `dist/index.html` file
        """

        index_file = Path("dist/index.html").read_text()
        app_env = ENVIRONMENT["ENV"]
        html = index_file.replace("%APP_ENV%", app_env)
        return HTMLResponse(content=html)

    if ENVIRONMENT["ENV"] == "local":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:8081"],  # Client dev server
            allow_credentials=True,  # Allow sending session cookies
            allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
            allow_headers=[
                "*"
            ],  # Allow all headers (Authorization, Content-Type, etc.)
        )

    app.add_middleware(SessionMiddleware, secret_key=get_session_secret_key())
    app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)

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

    @app.middleware("http")
    async def add_security_response_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response: Response = await call_next(request)

        if ENVIRONMENT["ENV"] != "local":
            # HSTS Policy
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains"
            )
            # SecureAttribute
            response.set_cookie(
                key="session_secure_value",
                value=get_session_secret_key(),
                secure=True,
                samesite="lax",
            )
            # BrowserCacheCheck, BrowserCacheInfoCheck
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

            # X-Content-Type-Options
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none';"
            )

        return response

    return app
