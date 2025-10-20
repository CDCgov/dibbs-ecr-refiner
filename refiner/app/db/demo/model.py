from dataclasses import dataclass


@dataclass(frozen=True)
class Condition:
    """
    Model for a Condition.
    """

    code: str
    display_name: str
    refined_eicr: str
    stats: list[str]
    # Optionally: html_files for per-condition HTML


@dataclass(frozen=True)
class IndependentTestUploadResponse:
    """
    Model for the response when uploading a document in the testing suite.

    Now includes metadata for HTML output files as well as XML.
    """

    message: str
    conditions_without_matching_configs: list[str]
    refined_conditions_found: int
    refined_conditions: list[Condition]
    unrefined_eicr: str
    refined_download_url: str
    html_files: list[
        str
    ]  # List of HTML filenames included in the ZIP output, mirrors XML naming
