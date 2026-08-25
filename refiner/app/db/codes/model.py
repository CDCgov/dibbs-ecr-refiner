from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CodedConcept:
    """
    Code / display name minimal representation of a codeable concept.
    """

    code: str
    display: str


@dataclass(frozen=True)
class CodeDisplay(CodedConcept):
    """
    Display representation of a codeable concept.
    """

    system_name: str


@dataclass(frozen=True)
class DbCode(CodedConcept):
    """
    DB model for code stored in the codes table.
    """

    system_id: UUID
