from pydantic import BaseModel


class ConditionProcessingInfo(BaseModel):
    """
    Model for a Condition's processing information.
    """

    condition_specific: bool
    sections_processed: str
    method: str


class Condition(BaseModel):
    """
    Model for a Condition.
    """

    code: str
    display_name: str
    refined_eicr: str
    stats: list[str]
    processing_info: ConditionProcessingInfo


class RefinedTestingDocument(BaseModel):
    """
    Model for the response when uploading a document in the testing suite.
    """

    message: str
    conditions_found: int
    conditions: list[Condition]
    unrefined_eicr: str
    processing_notes: list[str]
    refined_download_url: str
