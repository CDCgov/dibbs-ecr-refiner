from typing import Final

from .model import DbNarrativeAction, DbSectionAction

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

CODED_DATA_LABELS: Final[dict[DbSectionAction, str]] = {
    "retain": "Keep original",
    "refine": "Refine",
}

NARRATIVE_DATA_LABELS: Final[dict[DbNarrativeAction, str]] = {
    "retain": "Keep original",
    "keep_on_match": "Keep on match",
    "reconstruct": "Reconstruct",
    "remove": "Exclude",
}
