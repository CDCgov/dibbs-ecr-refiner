from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Coding:
    """
    Code / display name minimal representation of a codeable concept.
    """

    code: str
    display: str


@dataclass(frozen=True)
class DbCode(Coding):
    """
    DB model for code stored in the codes table.
    """

    version: str
    system_id: UUID
