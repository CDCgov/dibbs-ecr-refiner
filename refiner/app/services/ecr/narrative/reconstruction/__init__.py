from typing import NamedTuple

from lxml.etree import _Element

from app.services.ecr.policy import ReconstructableSection

from ...model import HL7_NS
from .blocks import (
    Block,
    DetailRow,
    SectionReconstructor,
    _inline_original_text_references,
    _mark_entries_derived,
    _strip_row_references,
    render_section_text,
)
from .fields import PANEL_FIELDS, RESULT_FIELDS, FieldSource, FieldSpec, extract_fields
from .renderers import (
    format_ts,
    render_code_display,
    render_coded_concept,
    render_entry_concept,
    render_interpretation,
    render_performer,
    render_performer_org,
    render_typed_value,
)
from .sections import (
    _generic_block,
    _unrepresented_statements,
    reconstruct_immunizations,
    reconstruct_medications,
    reconstruct_plan_of_treatment,
    reconstruct_problems,
    reconstruct_results,
)

__all__ = [
    "PANEL_FIELDS",
    "RESULT_FIELDS",
    "SECTION_RECONSTRUCTORS",
    "Block",
    "DetailRow",
    "FieldSource",
    "FieldSpec",
    "ReconstructedNarrative",
    "SectionReconstructor",
    "extract_fields",
    "format_ts",
    "reconstruct_immunizations",
    "reconstruct_medications",
    "reconstruct_narrative",
    "reconstruct_plan_of_treatment",
    "reconstruct_problems",
    "reconstruct_results",
    "render_code_display",
    "render_coded_concept",
    "render_entry_concept",
    "render_interpretation",
    "render_performer",
    "render_performer_org",
    "render_section_text",
    "render_typed_value",
]

SECTION_RECONSTRUCTORS: dict[str, SectionReconstructor] = {
    ReconstructableSection.RESULTS.value: reconstruct_results,
    ReconstructableSection.PROBLEM.value: reconstruct_problems,
    ReconstructableSection.IMMUNIZATIONS.value: reconstruct_immunizations,
    ReconstructableSection.MEDICATIONS_ADMINISTERED.value: reconstruct_medications,
    ReconstructableSection.PLAN_OF_TREATMENT.value: reconstruct_plan_of_treatment,
}


class ReconstructedNarrative(NamedTuple):
    """
    A rebuilt `<text>` plus how much of it the generic fallback had to cover.

    `reduced_entry_count` is what the caller turns into the section's
    provenance outcome: zero means every surviving entry was reconstructed by
    the section's own reconstructor, and anything higher means that many
    entries are present in reduced form and the reader should know it.
    """

    text: _Element
    reduced_entry_count: int


def reconstruct_narrative(
    section: _Element,
    *,
    augmentation_timestamp: str,
) -> ReconstructedNarrative | None:
    """
    Reconstruct a section's narrative <text> from its surviving entries.

    Dispatches on the section's LOINC code, then sweeps up whatever the
    dispatched reconstructor did not cover into a captioned reduced-form
    block (see LAYER 3 above), so every surviving entry is represented.

    Returns a `ReconstructedNarrative` carrying the detached, namespace-
    qualified <text> and how many entries needed the reduced form, or None
    when no narrative could be produced -- the section has no registered
    reconstructor, or it holds no entries at all. Both mean the same thing to
    every caller ("keep what is already there"), so they are one return value
    rather than two.

    This function MUTATES `section`: it strips the now-dangling narrative
    references off the surviving entries, relinks each one to the row that
    represents it, and stamps every entry with typeCode="DRIV" (the narrative
    is derived from the entries). See ADR 0011. It is no longer a pure read.

    Args:
        section: The post-prune, post-enrich <section>.
        augmentation_timestamp: The refinement run's HL7 V3 time value,
            used to stamp the minted row IDs to the same run as the
            section's provenance footnote.

    Returns:
        A `ReconstructedNarrative`, or None when none could be produced.
    """

    loinc_codes = section.xpath("hl7:code/@code", namespaces=HL7_NS)
    loinc = (
        str(loinc_codes[0]) if isinstance(loinc_codes, list) and loinc_codes else None
    )

    reconstruct = SECTION_RECONSTRUCTORS.get(loinc) if loinc else None
    if reconstruct is None or loinc is None:
        return None

    # inline BEFORE extracting: a sender's plain-English label may be sitting
    # in the narrative behind an originalText reference, and the field
    # extractor can only read it once it is by-value. lossless, so it is safe
    # on the path where nothing turns out to be reconstructable
    _inline_original_text_references(section)

    blocks = reconstruct(section)

    # anything the section's own reconstructor did not cover goes into the
    # captioned reduced-form block, so no surviving entry is left out of the
    # narrative the document is about to call DRIV
    if reduced := _unrepresented_statements(section, blocks):
        blocks = [*blocks, _generic_block(reduced)]

    # only reachable for a section with no entries at all: the sweep above
    # gives every surviving entry a row, so "entries survived but produced
    # nothing" cannot happen
    if not any(block.rows for block in blocks):
        return None

    _strip_row_references(section)
    _mark_entries_derived(section)
    return ReconstructedNarrative(
        text=render_section_text(
            blocks, loinc=loinc, augmentation_timestamp=augmentation_timestamp
        ),
        reduced_entry_count=len(reduced),
    )
