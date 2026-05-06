from dataclasses import dataclass

from app.api.validation.file_validation import (
    DIFF_RENDERING_MAX_MB,
    UNCOMPRESSED_MAX_MB,
    DiffMax,
    UncompressedMax,
)


@dataclass(frozen=True)
class Condition:
    """
    Model for a Condition.
    """

    code: str
    display_name: str
    refined_eicr: str
    refined_rr: str
    stats: list[str]
    render_diff: bool


@dataclass
class FileInfoResponse:
    """
    Utility class to help Orval ship these values to the frontend.
    """

    max_for_diff_rendering_mb: DiffMax = DIFF_RENDERING_MAX_MB
    max_for_uncompressed_mb: UncompressedMax = UNCOMPRESSED_MAX_MB


@dataclass(frozen=True)
class IndependentTestUploadResponse:
    """
    Model for the response when uploading a document in the testing suite.
    """

    message: str
    conditions_without_matching_configs: list[str]
    conditions_without_active_configs: list[str]
    refined_conditions_found: int
    refined_conditions: list[Condition]
    unrefined_eicr: str
    refined_download_key: str
    file_info_response: FileInfoResponse
