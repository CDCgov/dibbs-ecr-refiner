from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

type EicrVersion = Literal["1.1", "3.1", "3.1.1"]


@dataclass(frozen=True)
class TriggerCode:
    """
    Represents a specific trigger code definition within a section.

    `element_tag` here means something like: "observation", "act",
    "manufacturedProduct"
    """

    oid: str
    display_name: str
    element_tag: str


__all__ = [
    "EicrVersion",
    "TriggerCode",
]
