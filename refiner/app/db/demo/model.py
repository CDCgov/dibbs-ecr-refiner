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


@dataclass(frozen=True)
class IndependentTestUploadResponse:
    """
    Model for the response when uploading a document in the testing suite.
    """

    message: str
    conditions_without_matching_configs: list[str]
    refined_conditions_found: int
    refined_conditions: list[Condition]
    unrefined_eicr: str
    refined_download_url: str
