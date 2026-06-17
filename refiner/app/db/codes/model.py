from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DbCoding:
    """
    Minimal representation of a codeable concept from the DB, used for search on the configurations screen.
    """

    code: str
    display: str


@dataclass(frozen=True)
class DbCode(DbCoding):
    """
    DB model for code stored in the codes table.
    """

    version: str
    system_id: UUID
