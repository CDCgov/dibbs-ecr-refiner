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
    "refine" is meaningless (there is nothing to match against), so the
    UI disables the refine toggle for them and the refinement plan
    normalizes "refine" -> "retain" for these codes (see refine.py).
    The Enum values remain the single source of truth shipped to the frontend.
    A unit test guards that this enum stays in sync with the spec catalog
    (every code listed here has has_match_rules=False in the catalog, and
    every catalog section with has_match_rules=False is listed here).
    """

    CHIEF_COMPLAINT = "10154-3"
    REASON_FOR_VISIT = "29299-5"
    HISTORY_OF_PRESENT_ILLNESS = "10164-2"
    REVIEW_OF_SYSTEMS = "10187-3"


NARRATIVE_ONLY_SECTIONS = [section.value for section in NarrativeOnlySection]
