from dataclasses import dataclass, field
from typing import Literal


@dataclass
class FilterInput:
    """
    Filter input from the client.
    """

    search: str | None = None
    code_systems: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    statuses: list[str] = field(default_factory=list)


type CodeStatus = Literal["included", "excluded"]
