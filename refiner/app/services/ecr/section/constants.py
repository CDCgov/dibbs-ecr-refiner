from typing import Final

from ..model import SectionOutcome, SectionSource

# NOTE:
# OUTPUT MESSAGES
# =============================================================================
# human-readable strings emitted by the refiner into the refined document's
# narrative. these are what a jurisdiction reviewer sees when they open a
# refined eICR in a CDA stylesheet.

REFINER_OUTPUT_TITLE: Final[str] = (
    "Output from CDC eCR Refiner application by request of jurisdiction."
)

REMOVE_SECTION_MESSAGE: Final[str] = (
    "Section details have been removed as requested by jurisdiction for this condition."
)

REMOVE_NARRATIVE_MESSAGE: Final[str] = (
    "Section narrative has been removed from this refined document as "
    "configured by jurisdiction. Clinical entries are preserved for "
    "machine processing."
)

MINIMAL_SECTION_MESSAGE: Final[str] = (
    "No clinical information matches the configured code sets for this condition."
)

PROVENANCE_LABEL: Final[str] = "eCR Refiner — Jurisdiction Configuration"


# NOTE:
# TABLE HEADERS
# =============================================================================
# column headers for the narrative tables the refiner writes. the clinical
# data table headers describe the columns for the refined clinical content
# table; the provenance table headers describe the columns for the
# per-section provenance footnote table

CLINICAL_DATA_TABLE_HEADERS: Final[list[str]] = [
    "Display Text",
    "Code",
    "Code System",
    "Is Trigger Code",
    "Matching Condition Code",
]

PROVENANCE_TABLE_HEADERS: Final[list[str]] = [
    "Section (LOINC)",
    "Section Name",
    "Included",
    "Action",
    "Retain Narrative",
    "Config Version",
    "Source",
    "Outcome",
]


# NOTE:
# PROVENANCE SOURCE NOTES
# =============================================================================
# human-readable notes per SectionSource classification. rendered in the
# "Source" column of the per-section provenance footnote table

PROVENANCE_SOURCE_NOTES: Final[dict[SectionSource, str]] = {
    SectionSource.CONFIGURED: "Configured by jurisdiction",
    SectionSource.SYSTEM_SKIP: "System rule — always retained",
    SectionSource.UNCONFIGURED: "Not in jurisdiction configuration — retained as-is",
}


# NOTE:
# PROVENANCE OUTCOME NOTES
# =============================================================================
# human-readable notes per SectionOutcome value. rendered in the "Outcome"
# column of the per-section provenance footnote table

PROVENANCE_OUTCOME_NOTES: Final[dict[SectionOutcome, str]] = {
    SectionOutcome.REMOVED_BY_CONFIG: "Removed by configuration",
    SectionOutcome.RETAINED: "Retained as-is",
    SectionOutcome.RETAINED_NARRATIVE_REMOVED: "Retained; narrative removed",
    SectionOutcome.REFINED_WITH_MATCHES: "Refined; matches found",
    SectionOutcome.REFINED_NARRATIVE_REMOVED: "Refined; narrative removed",
    SectionOutcome.REFINED_NARRATIVE_RECONSTRUCTED: "Refined; narrative reconstructed",
    SectionOutcome.REFINED_NO_MATCHES_STUBBED: "Refined; no matches found",
}
