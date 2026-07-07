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
# Variables are defined this way to allow Orval to codegen and ship them to the
# frontend so that the user-facing strings are driven by the definitions here.


KeepOriginalLiteral = Literal["Keep original"]
RefineLiteral = Literal["Refine"]
ExcludeLiteral = Literal["Exclude"]
ReconstructLiteral = Literal["Reconstruct"]
KeepOnMatchLiteral = Literal["Keep on match"]

RETAIN_LABEL = get_args(KeepOriginalLiteral)[0]
REFINE_LABEL = get_args(RefineLiteral)[0]
KEEP_ON_MATCH_LABEL = get_args(KeepOnMatchLiteral)[0]
RECONSTRUCT_LABEL = get_args(ReconstructLiteral)[0]
REMOVE_LABEL = get_args(ExcludeLiteral)[0]


@dataclass
class NarrativeDataLabels:
    """
    Enum class to type the narrative actions possible for the frontend.
    """

    retain: KeepOriginalLiteral = RETAIN_LABEL
    keep_on_match: KeepOnMatchLiteral = KEEP_ON_MATCH_LABEL
    reconstruct: ReconstructLiteral = RECONSTRUCT_LABEL
    remove: ExcludeLiteral = REMOVE_LABEL


@dataclass
class CodedDataLabels:
    """
    Enum class to type the narrative actions possible for the frontend.
    """

    retain: KeepOriginalLiteral = RETAIN_LABEL
    refine: RefineLiteral = REFINE_LABEL


NARRATIVE_DATA_LABELS: Final[dict[DbNarrativeAction, str]] = {
    "retain": RETAIN_LABEL,
    "keep_on_match": KEEP_ON_MATCH_LABEL,
    "reconstruct": RECONSTRUCT_LABEL,
    "remove": REMOVE_LABEL,
}

CODED_DATA_LABELS: Final[dict[DbSectionAction, str]] = {
    "retain": RETAIN_LABEL,
    "refine": REFINE_LABEL,
}
