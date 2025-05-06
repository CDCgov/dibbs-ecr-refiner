import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from .api.v1 import demo, ecr
from .core.base_service import BaseService
from .core.examples import ECR_REQUEST_EXAMPLES

is_production = os.getenv("PRODUCTION", "false").lower() == "true"

# Instantiate FastAPI via DIBBs' BaseService class
app = BaseService(
    service_name="Message Refiner",
    service_path="/message-refiner",
    description_path=Path(__file__).parent.parent / "README.md",
    include_health_check_endpoint=False,
    openapi_url="/openapi.json",
).start()

router = APIRouter(prefix="/api/v1")
router.include_router(demo.router)
router.include_router(ecr.router)


def custom_openapi():
    """
    This customizes the FastAPI response to allow example requests given that the
    raw Request cannot have annotations.
    """
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    path = openapi_schema["paths"]["/api/v1/ecr"]["post"]
    path["requestBody"] = {
        "content": {
            "application/xml": {
                "schema": {"type": "Raw eCR XML payload"},
                "examples": ECR_REQUEST_EXAMPLES,
            }
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@router.get("/healthcheck")
async def health_check():
    """
    This endpoint checks service status. If an HTTP 200 status code is returned
    along with `{"status": "OK"}'` then the Message Refiner is available and
    running properly.
    """
    return {"status": "OK"}


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
