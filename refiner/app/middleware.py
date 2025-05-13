from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class SPAFallbackMiddleware(BaseHTTPMiddleware):
    """
    Middleware class designed to handle serving the built SPA files.
    """

    INDEX_FILE = Path("dist") / "index.html"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> FileResponse | Response:
        """
        Middleware that serves the index.html file for unknown non-API routes, enabling client-side routing to kick in.

        If a request results in a 404, does not target the API, and does not
        appear to be for a static file (i.e., lacks a file extension), this
        middleware returns index.html so the client-side router can handle the route.
        """

        response = await call_next(request)

        path = request.url.path

        if (
            response.status_code == 404
            and not path.startswith("/api")
            and "." not in Path(path).name
        ):
            if self.INDEX_FILE.exists():
                return FileResponse(self.INDEX_FILE)

        return response
