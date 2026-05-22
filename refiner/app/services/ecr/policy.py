"""
Refiner policy constants.

This module holds constants that represent *policy decisions* made by the
refiner — things that are not derived from the eICR Implementation Guide
itself, but from how the refiner has chosen to behave.

The distinction matters: `specification/` models what the IGs say, and is
IG-traceable. This module models what the refiner does, and is
refiner-traceable. A reader wondering "why does the refiner skip this
section?" should find the answer here, not in the specification, because
the IG doesn't tell us to skip it — we decided to.
"""

from typing import Final, Literal, get_args

# NOTE:
# SECTIONS ALWAYS RETAINED REGARDLESS OF JURISDICTION CONFIGURATION
# =============================================================================
# These sections are preserved intact in every refined document, even if a
# jurisdiction has not configured them. They exist outside the normal
# refinement workflow because their content is either public-health
# infrastructure (outbreak information) or downstream routing metadata
# (reportability response content) that jurisdictions expect to see
# untouched in the refined output.
#
# In the future we may decide to implement new ways to handle these sections
# but for now skipping them is easier and produces valid (Schematron-valid)
# output.
#
# The Literal-typed tuple alias below is the single source of truth: it is
# used both at runtime (to derive SECTION_PROCESSING_SKIP) and at the API
# boundary (so Orval ships the concrete LOINC codes to the frontend as
# const values rather than as plain `string[]`).

DisabledSections = tuple[
    Literal["83910-0"],  # emergency outbreak information section
    Literal["88085-6"],  # reportability response information section
]

DISABLED_SECTIONS: Final[DisabledSections] = tuple(
    get_args(a)[0] for a in get_args(DisabledSections)
)  # type: ignore[assignment]

SECTION_PROCESSING_SKIP: Final[set[str]] = set(DISABLED_SECTIONS)


# NOTE:
# NARRATIVE-ONLY SECTIONS
# =============================================================================
# These sections have no entry match rules in the eICR specification —
# they are conveyed via the narrative block only. Configuring them for
# "refine" is meaningless (there is nothing to match against), so the
# UI disables the refine toggle for them and the refinement plan
# normalizes "refine" -> "retain" for these codes (see refine.py).
#
# The Literal-typed tuple alias is the single source of truth shipped to
# the frontend. A unit test guards that this tuple stays in sync with
# the spec catalog (every code listed here has has_match_rules=False in
# the catalog, and every catalog section with has_match_rules=False is
# listed here).

NarrativeOnlySections = tuple[
    Literal["10154-3"],  # Chief Complaint
    Literal["29299-5"],  # Reason for Visit
    Literal["10164-2"],  # History of Present Illness
    Literal["10187-3"],  # Review of Systems
]

NARRATIVE_ONLY_SECTIONS: Final[NarrativeOnlySections] = tuple(
    get_args(a)[0] for a in get_args(NarrativeOnlySections)
)  # type: ignore[assignment]
