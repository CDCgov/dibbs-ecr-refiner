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

    Results, Problems, Immunizations, Medications Administered, and Plan of
    Treatment are enabled. Make sure to update unit tests to ensure only
    certain sections are reconstructable.
    """

    RESULTS = "30954-2"
    PROBLEM = "11450-4"
    IMMUNIZATIONS = "11369-6"
    MEDICATIONS_ADMINISTERED = "29549-3"
    PLAN_OF_TREATMENT = "18776-5"


RECONSTRUCTABLE_SECTIONS = [section.value for section in ReconstructableSection]


class TriggerCodeSection(StrEnum):
    """
    These sections can carry an eICR trigger code template.

    The eICR IG defines trigger code templates for these sections, so a
    trigger code — the coded evidence of *why* the document was
    generated — can appear in any of them. Removing a section strips
    every `<entry>` it holds and marks it `nullFlavor="NI"` (see
    `create_minimal_section`), so a jurisdiction that turned all of
    these off would emit a document with no trigger codes anywhere and
    fail Schematron validation.

    In practice this is unlikely: nearly all RCTC codes from the eRSD
    are carried in the reporting specification groupers, and the
    additional context groupers widen that further, so a configuration
    would normally match the trigger code and keep the section. This
    policy exists to close the foot-gun, not because we expect
    jurisdictions to walk into it.

    The refiner therefore forces `include=True` for these sections.
    Every other setting stays under jurisdiction control — coded data
    may still be refined or retained, and the narrative may be
    retained, removed, kept on match, or reconstructed.

    Membership is IG-derived, not a judgement call: the codes here are
    the union of `specification.get_trigger_code_sections()` across
    every supported eICR version. The union matters because a
    configuration is authored once and applied to whichever version
    arrives. The Enum is spelled out rather than computed so Orval
    ships concrete LOINC codes to the frontend, and so a change to the
    IG manifest surfaces as a failing drift test rather than silently
    relaxing every jurisdiction's configuration. A unit test guards
    that this enum stays in sync with the specification.
    """

    MEDICATIONS = "10160-0"
    IMMUNIZATIONS = "11369-6"
    PROBLEM = "11450-4"
    PLAN_OF_TREATMENT = "18776-5"
    MEDICATIONS_ADMINISTERED = "29549-3"
    RESULTS = "30954-2"
    ADMISSION_MEDICATIONS = "42346-7"
    ENCOUNTERS = "46240-8"
    PROCEDURES = "47519-4"


TRIGGER_CODE_SECTIONS = [section.value for section in TriggerCodeSection]


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


def is_trigger_code_section(code: str) -> bool:
    """Return True if the LOINC code identifies a trigger code section."""

    return code in TRIGGER_CODE_SECTIONS


def narrative_requires_refine(narrative_action: DbNarrativeAction) -> bool:
    """
    Return True if the narrative setting only makes sense with action="refine".
    """

    return narrative_action in NARRATIVE_ACTION_REQUIRES_REFINE


def normalize_section_processing(
    code: str,
    include: bool,
    section_action: DbSectionAction,
    narrative_action: DbNarrativeAction,
) -> tuple[bool, DbSectionAction, DbNarrativeAction, list[str]]:
    """
    Coerce an `(include, action, narrative)` triple into a valid combination.

    Used by non-user-initiated paths (the clone path during config
    activation, and one-shot data backfill migrations) that cannot
    raise on a stale invalid combo without disrupting unrelated work.
    User-initiated paths (the PATCH section endpoint) raise via the
    sibling validators in `api/v1/configurations/sections.py` instead.

    Rules applied in order:

      1. Trigger code sections must have include=True. Removing them
         risks emitting a document with no trigger codes at all.
         Their action and narrative settings are left alone.
      2. Narrative-only sections must have action="retain".
      3. Disabled sections must have action="retain" (they are always
         system-skipped at refinement; storing anything else is
         misleading).
      4. `narrative in NARRATIVE_ACTION_REQUIRES_REFINE` requires
         action="refine". When action is not "refine" after the
         earlier coercions, narrative is downgraded to "retain".
      5. `narrative == "reconstruct"` is only valid on
         `ReconstructableSection` codes. Otherwise narrative is
         downgraded to "retain".

    Returns:
        Tuple of `(coerced_include, coerced_action, coerced_narrative,
        notes)`. `notes` is a list of human-readable strings describing
        each coercion applied — empty when the input was already valid.
        Callers should log non-empty notes so jurisdictions can audit
        what the system fixed up.
    """

    notes: list[str] = []
    coerced_include: bool = include
    coerced_action: DbSectionAction = section_action
    coerced_narrative_action: DbNarrativeAction = narrative_action

    # rule 1: trigger code sections are always included
    if is_trigger_code_section(code) and not coerced_include:
        notes.append(
            f"section '{code}' can carry a trigger code; coerced include "
            f"'False' to 'True'"
        )
        coerced_include = True

    # rule 2 + 3: action-forcing for narrative-only and disabled sections
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

    # rule 4: narrative values that require action="refine"
    if (
        narrative_requires_refine(coerced_narrative_action)
        and coerced_action != "refine"
    ):
        notes.append(
            f"narrative '{coerced_narrative_action}' requires action='refine' for "
            f"section '{code}'; coerced narrative to 'retain'"
        )
        coerced_narrative_action = "retain"

    # rule 5: reconstruct only on reconstructable sections
    if coerced_narrative_action == "reconstruct" and not is_reconstructable_section(
        code
    ):
        notes.append(
            f"section '{code}' does not support narrative reconstruction; "
            f"coerced narrative to 'retain'"
        )
        coerced_narrative_action = "retain"

    return coerced_include, coerced_action, coerced_narrative_action, notes
