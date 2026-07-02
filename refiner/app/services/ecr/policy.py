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

from enum import StrEnum

from app.db.configurations.model import DbNarrativeAction, DbSectionAction

# NOTE:
# SECTIONS ALWAYS RETAINED REGARDLESS OF JURISDICTION CONFIGURATION
# =============================================================================


class DisabledSection(StrEnum):
    """
    These sections are preserved intact in every refined document.

    They sit outside the normal refinement workflow not because the
    refiner needs to protect them, but because we don't yet have a
    real-world authoring contract to refine against:

    - Reportability Response Information (88085-6) is defined by the
      eICR STU 3.1.1 IG as a section the PHA populates after eICR
      receipt, as part of internal data integration -- not something
      the HCO authors at eICR generation time. It's sketched in the
      IG but is not part of eICRs flowing through AIMS today.

    - Emergency Outbreak Information (83910-0) has a defined section
      template and a deliberately generic Observation structure
      ("unknown until the time of the outbreak," per the IG). There
      is no settled EHR implementation pattern, and the next outbreak
      will likely shape how this section actually appears in
      production.

    Skipping is the easier path for now and produces Schematron-valid
    output. We can revisit -- per section, independently -- if and
    when either becomes something we actually see in real documents.

    The Enum is the single source of truth: used at runtime to derive
    SECTION_PROCESSING_SKIP, and at the API boundary so Orval ships
    the concrete LOINC codes to the frontend as const values rather
    than as plain `string[]`.
    """

    EMERGENCY_OUTBREAK = "83910-0"
    REPORTABILITY_RESPONSE = "88085-6"


SECTION_PROCESSING_SKIP = [section.value for section in DisabledSection]


class NarrativeOnlySection(StrEnum):
    """
    These sections have no entry match rules in the eICR specification.

    They are conveyed via the narrative block only. Configuring them for
    "refine" is meaningless (there is nothing to match against), so the UI
    disables the refine toggle for them and the refinement plan normalizes
    "refine" -> "retain" for these codes (see refine.py). The Enum values
    remain the single source of truth shipped to the frontend. A unit test
    guards that this enum stays in sync with the spec catalog (every code
    listed here has has_match_rules=False in the catalog, and every catalog
    section with has_match_rules=False is listed here).
    """

    CHIEF_COMPLAINT = "10154-3"
    REASON_FOR_VISIT = "29299-5"
    HISTORY_OF_PRESENT_ILLNESS = "10164-2"
    REVIEW_OF_SYSTEMS = "10187-3"


NARRATIVE_ONLY_SECTIONS = [section.value for section in NarrativeOnlySection]


class ReconstructableSection(StrEnum):
    """
    These sections support the "reconstruct" narrative action.

    Results, Problems, Immunizations, and Medications Administered are
    enabled. Make sure to update unit tests to ensure only certain sections
    are reconstructable.
    """

    RESULTS = "30954-2"
    PROBLEM = "11450-4"
    IMMUNIZATIONS = "11369-6"
    MEDICATIONS_ADMINISTERED = "29549-3"


RECONSTRUCTABLE_SECTIONS = [section.value for section in ReconstructableSection]


# NOTE:
# SECTION POLICY PREDICATES AND NORMALIZATION
# =============================================================================
# Predicates and a single normalizer used by both the API validators
# (which reject invalid combos up front) and the clone-path / future
# data-backfill paths (which coerce invalid combos to a safe baseline).
# Keeping the rules in one place ensures the API and the clone/migration
# paths never drift.


# narrative values that only make sense when the coded action is "refine".
# "reconstruct" rebuilds <text> from refined entries; "keep_on_match"
# decides narrative disposition based on the matching outcome. neither
# has meaning on a retained (untouched) section.
NARRATIVE_ACTION_REQUIRES_REFINE: frozenset[DbNarrativeAction] = frozenset(
    {"reconstruct", "keep_on_match"}
)


def is_disabled_section(code: str) -> bool:
    """Return True if the LOINC code identifies a system-skipped section."""

    return code in SECTION_PROCESSING_SKIP


def is_narrative_only_section(code: str) -> bool:
    """Return True if the LOINC code identifies a narrative-only section."""

    return code in NARRATIVE_ONLY_SECTIONS


def is_reconstructable_section(code: str) -> bool:
    """
    Return True if the LOINC code has a registered narrative reconstructor.
    """

    return code in RECONSTRUCTABLE_SECTIONS


def narrative_requires_refine(narrative_action: DbNarrativeAction) -> bool:
    """
    Return True if the narrative setting only makes sense with action="refine".
    """

    return narrative_action in NARRATIVE_ACTION_REQUIRES_REFINE


def normalize_section_narrative(
    code: str,
    section_action: DbSectionAction,
    narrative_action: DbNarrativeAction,
) -> tuple[DbSectionAction, DbNarrativeAction, list[str]]:
    """
    Coerce an `(action, narrative)` pair into a valid combination.

    Used by non-user-initiated paths (the clone path during config
    activation, and one-shot data backfill migrations) that cannot
    raise on a stale invalid combo without disrupting unrelated work.
    User-initiated paths (the PATCH section endpoint) raise via the
    sibling validators in `api/v1/configurations/sections.py` instead.

    Rules applied in order:

      1. Narrative-only sections must have action="retain".
      2. Disabled sections must have action="retain" (they are always
         system-skipped at refinement; storing anything else is
         misleading).
      3. `narrative in NARRATIVE_ACTION_REQUIRES_REFINE` requires
         action="refine". When action is not "refine" after the
         earlier coercions, narrative is downgraded to "retain".
      4. `narrative == "reconstruct"` is only valid on
         `ReconstructableSection` codes. Otherwise narrative is
         downgraded to "retain".

    Returns:
        Tuple of `(coerced_action, coerced_narrative, notes)`. `notes`
        is a list of human-readable strings describing each coercion
        applied — empty when the input was already valid. Callers
        should log non-empty notes so jurisdictions can audit what
        the system fixed up.
    """

    notes: list[str] = []
    coerced_action: DbSectionAction = section_action
    coerced_narrative_action: DbNarrativeAction = narrative_action

    # rule 1 + 2: action-forcing for narrative-only and disabled sections
    if is_narrative_only_section(code) and coerced_action != "retain":
        notes.append(
            f"section '{code}' is narrative-only; coerced action "
            f"'{coerced_action}' to 'retain'"
        )
        coerced_action = "retain"

    if is_disabled_section(code) and coerced_action != "retain":
        notes.append(
            f"section '{code}' is system-skipped; coerced action "
            f"'{coerced_action}' to 'retain'"
        )
        coerced_action = "retain"

    # rule 3: narrative values that require action="refine"
    if (
        narrative_requires_refine(coerced_narrative_action)
        and coerced_action != "refine"
    ):
        notes.append(
            f"narrative '{coerced_narrative_action}' requires action='refine' for "
            f"section '{code}'; coerced narrative to 'retain'"
        )
        coerced_narrative_action = "retain"

    # rule 4: reconstruct only on reconstructable sections
    if coerced_narrative_action == "reconstruct" and not is_reconstructable_section(
        code
    ):
        notes.append(
            f"section '{code}' does not support narrative reconstruction; "
            f"coerced narrative to 'retain'"
        )
        coerced_narrative_action = "retain"

    return coerced_action, coerced_narrative_action, notes
