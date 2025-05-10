from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from .examples import ECR_REQUEST_EXAMPLES


def create_custom_openapi(app: FastAPI) -> dict:
    """
    Create a custom OpenAPI schema for the service.

    Args:
        app: The FastAPI application instance from BaseService

    Returns:
        dict: Customized OpenAPI schema with enhanced XML payload specifications
              and example requests for the ECR endpoint
    """

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # get service path from app state
    service_path = app.state.service_path
    ecr_path = f"{service_path}/api/v1/ecr"

    # safely get and modify the '/ecr' endpoint schema
    if "paths" in openapi_schema and ecr_path in openapi_schema["paths"]:
        post_schema = openapi_schema["paths"][ecr_path].get("post")
        if post_schema:
            post_schema["requestBody"] = {
                "required": True,
                "content": {
                    "application/xml": {
                        "schema": {
                            "type": "string",
                            "format": "xml",
                            "description": "Raw eCR XML payload containing clinical document",
                        },
                        "examples": ECR_REQUEST_EXAMPLES,
                    }
                },
            }

            # enhance response schema
            post_schema["responses"] = {
                "200": {
                    "description": "Successfully processed eCR document",
                    "content": {
                        "application/xml": {
                            "schema": {
                                "type": "string",
                                "format": "xml",
                                "description": "Refined eCR document",
                            }
                        }
                    },
                },
                "400": {
                    "description": "Invalid XML document",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detail": {
                                        "type": "object",
                                        "properties": {
                                            "message": {"type": "string"},
                                            "details": {"type": "object"},
                                        },
                                    }
                                },
                            }
                        }
                    },
                },
                "422": {
                    "description": "Invalid section codes or parameters",
                },
            }

    app.openapi_schema = openapi_schema
    return app.openapi_schema
