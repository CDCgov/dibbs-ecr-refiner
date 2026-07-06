import re

from lxml.etree import _Element

from ..model import SectionProvenanceRecord
from .constants import (
    PROVENANCE_LABEL,
    PROVENANCE_OUTCOME_NOTES,
    PROVENANCE_SOURCE_NOTES,
    PROVENANCE_TABLE_HEADERS,
)
from .elements import _ensure_text_element, _sub_element

# NOTE:
# PROVENANCE FOOTNOTE
# =============================================================================
# every section in the refined document carries a trailing <footnote>
# documenting how the refiner treated it. the footnote is unanchored:
# no <footnoteRef> points to it. This represents "annotation attached
# to the section as a whole" — valid per NarrativeBlock.xsd's
# StrucDoc.Text and StrucDoc.Footnote content models (both allow
# footnote as an optional child with no anchoring requirement) and
# sidesteps the need to walk arbitrary source narrative looking for
# anchor points, which would be fragile across eICR vendors
#
# the footnote's xs:ID ties it to the augmentation run's timestamp,
# giving the two structural consistency that a consumer can verify
# programmatically (e.g., "every refiner footnote ID should contain
# the timestamp present in the augmentation author's <time> value")
#
# the footnote's data row carries both the configured action ("what
# the jurisdiction asked for") and the runtime outcome ("what the
# refiner actually did"). the two columns let a reader see at a glance
# how the section was handled — most rows show the outcome confirming
# the configuration, with the no-match variants documenting what was
# done when matching produced nothing


def _build_footnote_id(
    loinc_code: str,
    augmentation_timestamp: str,
    occurrence_index: int = 0,
) -> str:
    """
    Build a document-unique xs:ID for a refiner provenance footnote.

    The ID is of the form
    `ecr-refiner-{loinc}-{timestamp-digits}`, optionally with a
    `-{n}` suffix for the rare case where the same LOINC appears on
    multiple top-level sections in a single document. The timestamp
    digits are extracted from the augmentation author's <time> value
    (HL7 V3 `YYYYMMDDHHMMSS±ZZZZ` format) by keeping the leading
    run of digits — the timezone offset is stripped because `+` and
    the offset digits are not wanted in the ID.

    xs:ID cannot start with a digit or hyphen, so the `ecr-refiner-`
    prefix is load-bearing: it ensures the resulting string always
    satisfies the XML Name production.

    Args:
        loinc_code: The section's LOINC code (e.g., "46240-8").
        augmentation_timestamp: The augmentation author's time value,
            shared across all footnotes in this refinement run.
        occurrence_index: Zero-based disambiguator for the rare case
            where the same LOINC appears on multiple top-level
            sections. Zero (the normal case) produces no suffix;
            nonzero values append `-N`.

    Returns:
        A document-unique xs:ID-safe string.
    """

    match = re.match(r"^\d+", augmentation_timestamp)
    timestamp_digits = match.group(0) if match else ""
    base = f"ecr-refiner-{loinc_code}-{timestamp_digits}"
    return base if occurrence_index == 0 else f"{base}-{occurrence_index}"


def append_section_provenance_footnote(
    section: _Element,
    provenance: SectionProvenanceRecord,
    augmentation_timestamp: str,
    occurrence_index: int = 0,
) -> None:
    """
    Append an unanchored <footnote> carrying refiner provenance.

    Called by refine_eicr after processing every section (refine,
    retain, remove, narrative-removed) so that every section in the
    refined document carries a consistent provenance record.

    The footnote contains a bolded label paragraph followed by a
    single-row table summarizing the jurisdiction's configuration
    and the runtime outcome for this section. The table follows
    NarrativeBlock.xsd's StrucDoc.Table content model with proper
    <thead>/<th> header semantics and <tbody>/<tr>/<td> body rows.

    The provenance record passed in must have its `outcome` field
    finalized — refine_eicr does this via dataclasses.replace before
    calling this function. If the field still holds its default
    value at render time, that's a bug in refine_eicr's
    interpretation logic, not in this function.

    If the section has no <text> element (e.g., a retained section
    where the source document omitted it), one is created and inserted
    per `_ensure_text_element`'s CDA R2 xs:sequence rules.

    Args:
        section: The section element to annotate.
        provenance: The SectionProvenanceRecord built during plan
            creation and finalized by refine_eicr.
        augmentation_timestamp: The augmentation run's <time> value,
            shared across all footnotes in this refinement run.
        occurrence_index: Disambiguator for repeated-LOINC sections;
            zero for the normal case.
    """

    text_element = _ensure_text_element(section)

    footnote_id = _build_footnote_id(
        loinc_code=provenance.loinc_code,
        augmentation_timestamp=augmentation_timestamp,
        occurrence_index=occurrence_index,
    )
    footnote = _sub_element(text_element, "footnote", ID=footnote_id)

    # bolded label paragraph
    label_paragraph = _sub_element(footnote, "paragraph")
    label_content = _sub_element(label_paragraph, "content", styleCode="Bold")
    label_content.text = PROVENANCE_LABEL

    # provenance table
    table = _sub_element(footnote, "table", border="1")
    thead = _sub_element(table, "thead")
    header_row = _sub_element(thead, "tr")
    for header in PROVENANCE_TABLE_HEADERS:
        th = _sub_element(header_row, "th")
        th.text = header

    tbody = _sub_element(table, "tbody")
    row = _sub_element(tbody, "tr")
    _add_provenance_cell(row, provenance.loinc_code)
    _add_provenance_cell(row, provenance.display_name)
    _add_provenance_cell(row, "Yes" if provenance.include else "No")
    _add_provenance_cell(row, provenance.action)
    _add_provenance_cell(row, "Yes" if provenance.narrative == "retain" else "No")
    _add_provenance_cell(
        row,
        f"v{provenance.config_version}"
        if provenance.config_version is not None
        else "—",
    )
    _add_provenance_cell(
        row,
        PROVENANCE_SOURCE_NOTES.get(provenance.source, str(provenance.source)),
    )
    _add_provenance_cell(
        row,
        PROVENANCE_OUTCOME_NOTES.get(provenance.outcome, str(provenance.outcome)),
    )


def _add_provenance_cell(row: _Element, text: str) -> None:
    """
    Append a single <td> with text content to a provenance table row.
    """

    td = _sub_element(row, "td")
    td.text = text
