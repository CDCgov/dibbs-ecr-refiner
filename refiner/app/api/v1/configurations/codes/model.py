from dataclasses import dataclass, field


@dataclass
class FilterInput:
    """
    Filter input from the client.
    """

    code_systems: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    statuses: list[str] = field(default_factory=list)
