from pydantic import BaseModel


class ApplyUpdatesRequest(BaseModel):
    """
    Request model for applying TES updates to configurations.
    """

    configuration_ids: list[str]


class ApplyUpdatesResponse(BaseModel):
    """
    Response model for applying TES updates to configurations.
    """

    total_processed: int
    drafts_updated: int
    drafts_created: int
    updated_configuration_ids: list[str]
    created_configuration_ids: list[str]
