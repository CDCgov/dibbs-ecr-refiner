from dataclasses import dataclass, field


@dataclass
class FilterInput:
    """
    Filter input from the client.
    """

    code_systems: list[str | int] = field(default_factory=list)
    sources: list[str | int] = field(default_factory=list)
    statuses: list[str | int] = field(default_factory=list)
