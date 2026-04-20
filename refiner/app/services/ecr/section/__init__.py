"""
section module __init__ file
"""

from lxml.etree import _Element

from app.services.terminology import CodeSystemSets

from ..model import NamespaceMap, SectionRunResult, SectionSpecification
from . import entry_matching as _entry_matching
from . import generic_matching as _generic_matching
from .narrative import append_section_provenance_footnote, create_minimal_section
from .traversal import get_section_by_code, get_section_loinc_codes

# NOTE:
# PUBLIC DISPATCHER
# =============================================================================


def process_section(
    section: _Element,
    codes_to_match: set[str],
    namespaces: NamespaceMap,
    section_specification: SectionSpecification | None,
    code_system_sets: CodeSystemSets | None,
    include_narrative: bool = True,
) -> SectionRunResult:
    """
    Dispatch a section to the right matching engine.

    Chooses between the section-aware and generic paths based on
    whether the section's SectionSpecification declares entry match
    rules:

      - section-aware (entry_matching.process): used when the
        specification is present and has non-empty entry_match_rules.
        These are the IG-driven rules for sections where the eICR
        Implementation Guide defines clear entry structure and code
        constraints (Problems, Results, Medications, Immunizations,
        Plan of Treatment, Encounters, Admission Diagnosis, Discharge
        Diagnosis, Admission Medications, Past Medical History,
        Vital Signs).

      - generic (generic_matching.process): used for all other
        sections — narrative-only sections, patient-context sections,
        and sections whose structure has not yet been characterized.

    Both engines mutate the section in place and return a
    `SectionRunResult` describing what happened. The dispatcher
    passes the result through to the caller unchanged — it does not
    interpret the result into a user-facing outcome. That interpretation
    lives in `refine._interpret_run_result`.

    TODO: `include_narrative` is still a bool here. When the
    configuration's narrative field migrates to a three-way enum
    (`retain`/`remove`/`refine`), this parameter's type and
    the downstream calls to the engines will need to update in
    lockstep.

    Args:
        section: The section element being processed.
        codes_to_match: Flat set of condition codes for the generic
            fallback engine.
        namespaces: HL7 namespace map for XPath evaluation.
        section_specification: The section's specification, or None.
            If present with entry_match_rules, routes to the
            section-aware engine.
        code_system_sets: Structured per-system code lookup used by
            the section-aware engine and for displayName enrichment
            in the generic engine.
        include_narrative: Whether to keep the original section
            narrative. When False, narrative is replaced with a
            removal notice. Ignored when matches are zero; the
            engine stubs the section regardless per the no-match
            policy override.

    Returns:
        SectionRunResult describing what the engine did. Consumed
        by refine_eicr to compute the user-facing SectionOutcome.
    """

    if (
        section_specification is not None
        and section_specification.has_match_rules
        and code_system_sets is not None
    ):
        return _entry_matching.process(
            section=section,
            code_system_sets=code_system_sets,
            section_specification=section_specification,
            namespaces=namespaces,
            include_narrative=include_narrative,
        )

    return _generic_matching.process(
        section=section,
        codes_to_match=codes_to_match,
        namespaces=namespaces,
        section_specification=section_specification,
        code_system_sets=code_system_sets,
        include_narrative=include_narrative,
    )


__all__ = [
    "append_section_provenance_footnote",
    "create_minimal_section",
    "get_section_by_code",
    "get_section_loinc_codes",
    "process_section",
]
