from dataclasses import dataclass
from typing import Literal

from ...services.file_io import read_json_asset

ECR_REQUEST_EXAMPLES = read_json_asset("sample_refine_ecr_request.json")
ECR_RESPONSE_EXAMPLES = read_json_asset("sample_refine_ecr_response.json")


# response models
@dataclass(frozen=True)
class StatusResponse:
    """Health check response."""

    status: Literal["OK"]


@dataclass(frozen=True)
class XMLUploadResponse:
    """XML upload response."""

    eicr: str
    rr: str
    reportable_conditions: str | None = None


@dataclass(frozen=True)
class RefineECRResponse:
    """ECR refinement response."""

    refined_message: str
