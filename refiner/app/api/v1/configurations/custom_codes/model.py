from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, Field


class UploadCustomCodesCsvInput(BaseModel):
    """
    Input model for Custom Code CSV.
    """

    csv_text: str = Field(..., description="Full CSV contents as UTF-8 text")
    filename: str | None = None


class AddCustomCodeInput(BaseModel):
    """
    Input model for adding a custom code to a configuration.
    """

    code: str
    display: str
    system_id: UUID


class UploadCustomCodesPreviewItem(BaseModel):
    """Validated CSV row ready for confirmation."""

    id: UUID
    code: str
    system_id: UUID
    system_name: str
    display: str
    row: int | None = None


class ConfirmUploadCustomCodesInput(BaseModel):
    """Payload used to confirm a previously validated CSV import."""

    custom_codes: list[AddCustomCodeInput]


@dataclass(frozen=True)
class CustomCodeResponse:
    """
    Custom code object to return to the client.
    """

    id: UUID
    display: str
    code: str
    system_id: UUID
    system_name: str
