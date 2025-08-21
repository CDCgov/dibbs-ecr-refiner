import os
from collections.abc import Callable
from typing import Literal

from fastapi import FastAPI, Request, Response
from starlette.types import Lifespan

from ..config import DIBBS_CONTACT, LICENSES
from ..models.api import StatusResponse


class BaseService:
    """
    Base service class for DIBBs FastAPI applications.

    This reusable class provides common functionality for DIBBs services including:
    - FastAPI application setup with standard metadata
    - Path rewriting middleware for gateway compatibility
    - Optional health check endpoint
    - License and OpenAPI configuration

    Note:
        Middlewares and endpoints must be added after class instantiation by
        calling the start() method, which calls add_path_rewrite_middleware()
        and add_health_check_endpoint().
    """

    def __init__(
        self,
        service_name: str,
        service_path: str,
        description: str,
        lifespan: Lifespan[FastAPI],
        include_health_check_endpoint: bool = True,
        license_info: Literal["CreativeCommonsZero", "MIT"] = "CreativeCommonsZero",
        openapi_url: str = "/openapi.json",
    ):
        """
        Initialize a BaseService instance.

        Args:
            service_name: Name of the service.
            service_path: Path used to access the service from a gateway.
            description: Service description.
            lifespan: A Starlette `Lifespan` object
            include_health_check_endpoint: Whether to add standard DIBBs health
                check endpoint. Defaults to True.
            license_info: License to use for the service. Options:
                - "CreativeCommonsZero" (default): CC0 v1.0 Universal
                - "MIT": MIT License
            openapi_url: URL for OpenAPI.json used by FastAPI for /redoc.
                For services behind gateways, use "/{service-name}/openapi.json".
                Defaults to "/openapi.json".
        """

        description = description
        self.service_path = service_path
        self.include_health_check_endpoint = include_health_check_endpoint
        self.app = FastAPI(
            title=service_name,
            version=os.getenv("APP_VERSION", "1.0.0"),
            contact=DIBBS_CONTACT,
            license_info=LICENSES[license_info],
            description=description,
            openapi_url=openapi_url,
            lifespan=lifespan,
        )

    def add_path_rewrite_middleware(self) -> None:
        """
        Add path rewriting middleware for gateway compatibility.

        Adds middleware to strip service_path from URL paths when present.
        Useful for services behind gateways using path-based routing.
        """

        @self.app.middleware("http")
        async def rewrite_path(request: Request, call_next: Callable) -> Response:
            if (
                request.url.path.startswith(self.service_path)
                and "api/openapi.json" not in request.url.path
            ):
                request.scope["path"] = request.scope["path"].replace(
                    self.service_path, ""
                )
            if request.scope["path"] == "":
                request.scope["path"] = "/"
            return await call_next(request)

    def add_health_check_endpoint(self) -> None:
        """
        Adds a health check endpoint to the web service.
        """

        @self.app.get("/", response_model=StatusResponse)
        async def health_check():
            """Check service health status.

            Returns:
                StatusResponse: {"status": "OK"} with HTTP 200 if service is healthy.
            """

            return {"status": "OK"}

    def start(self) -> FastAPI:
        """
        Initialize and return the configured FastAPI instance.

        Adds middleware and optional health check endpoint before returning
        the FastAPI application instance.

        Returns:
            FastAPI: Configured FastAPI instance with DIBBs metadata.
        """

        self.add_path_rewrite_middleware()
        if self.include_health_check_endpoint:
            self.add_health_check_endpoint()
        return self.app
