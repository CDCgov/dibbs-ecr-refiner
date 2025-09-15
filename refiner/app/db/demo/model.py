from dataclasses import dataclass


@dataclass(frozen=True)
class ConditionProcessingInfo:
    """
    Model for a Condition's processing information.
    """

    condition_specific: bool
    sections_processed: str
    method: str


@dataclass(frozen=True)
class Condition:
    """
    Model for a Condition.
    """

    code: str
    display_name: str
    refined_eicr: str
    stats: list[str]
    processing_info: ConditionProcessingInfo


@dataclass(frozen=True)
class RefinedTestingDocument:
    """
    Model for the response when uploading a document in the testing suite.
    """

    message: str
    conditions_found: int
    conditions: list[Condition]
    unrefined_eicr: str
    processing_notes: list[str]
    refined_download_url: str
