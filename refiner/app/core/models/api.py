from typing import Literal

from pydantic import BaseModel

from ...services.file_io import read_json_asset

ECR_REQUEST_EXAMPLES = read_json_asset("sample_refine_ecr_request.json")
ECR_RESPONSE_EXAMPLES = read_json_asset("sample_refine_ecr_response.json")


# response models
class StatusResponse(BaseModel):
    """Health check response."""

    status: Literal["OK"]


class XMLUploadResponse(BaseModel):
    """XML upload response."""

    eicr: str
    rr: str
    reportable_conditions: str | None = None


class RefineECRResponse(BaseModel):
    """ECR refinement response."""

    refined_message: str
