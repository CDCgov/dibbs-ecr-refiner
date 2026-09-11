from dataclasses import dataclass
from uuid import UUID

from app.db.configurations.model import ConfigurationCodeStatus


@dataclass(frozen=True)
class CodedConcept:
    """
    Code / display name minimal representation of a codeable concept.
    """

    code: str
    display: str


@dataclass(frozen=True)
class DbCode(CodedConcept):
    """
    Model for all coded information stored in the codes table.
    """

    system_id: UUID
    system_name: str


@dataclass(frozen=True)
class ConfigurationCode(DbCode):
    """
    Model for all coded information in a configuration, including status.
    """

    status: ConfigurationCodeStatus
