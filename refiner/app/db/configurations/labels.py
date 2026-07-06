from dataclasses import dataclass
from typing import Final, Literal, get_args

from .model import (
    DbNarrativeAction,
    DbSectionAction,
)

# NOTE:
# CONFIG DISPLAY LABELS
# =============================================================================
# canonical human-readable labels for the configuration enums. shared by the
# CSV config export (api/v1/configurations/exports.py) and the per-section
# provenance footnote (services/ecr/narrative/footnote.py) so the two never
# drift from each other.
#
# these MUST stay in sync with the client's option labels — see
# client/src/pages/Configurations/ConfigBuild/Sections/NarrativeSelect.tsx and
# .../Sections/index.tsx. there is no automated guard yet; if these grow or
# change often, promote them to an API-provided map the client consumes.


Retain = Literal["Keep original"]
Refine = Literal["Refine"]
Remove = Literal["Exclude"]
Reconstruct = Literal["Reconstruct"]
KeepOnMatch = Literal["Keep on match"]

RETAIN = get_args(Retain)[0]
REFINE = get_args(Refine)[0]
KEEP_ON_MATCH = get_args(Remove)[0]
RECONSTRUCT = get_args(Reconstruct)[0]
REMOVE = get_args(KeepOnMatch)[0]


@dataclass
class NarrativeDataLabels:
    """
    Enum class to type the narrative actions possible for the frontend.
    """

    retain: Retain = RETAIN
    keep_on_match: KeepOnMatch = KEEP_ON_MATCH
    reconstruct: Reconstruct = RECONSTRUCT
    remove: Remove = REMOVE


@dataclass
class CodedDataLabels:
    """
    Enum class to type the narrative actions possible for the frontend.
    """

    retain: Retain = RETAIN
    refine: Refine = REFINE


NARRATIVE_DATA_LABELS: Final[dict[DbNarrativeAction, str]] = {
    "retain": RETAIN,
    "keep_on_match": KEEP_ON_MATCH,
    "reconstruct": RECONSTRUCT,
    "remove": REMOVE,
}

CODED_DATA_LABELS: Final[dict[DbSectionAction, str]] = {
    "retain": RETAIN,
    "refine": REFINE,
}
