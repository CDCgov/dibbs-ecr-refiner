from typing import Final, Literal

from lxml.etree import _Element

from app.services.format import remove_element

from ..model import HL7_NS, NamespaceMap
from .constants import (
    MINIMAL_SECTION_MESSAGE,
    REFINER_OUTPUT_TITLE,
    REMOVE_NARRATIVE_MESSAGE,
    REMOVE_SECTION_MESSAGE,
)
from .elements import (
    _ensure_text_element,
    _make_element,
    _sub_element,
    remove_all_comments,
)

# NOTE:
# INTERNAL CONSTANTS
# =============================================================================

_MESSAGE_MAP: Final[dict[str, str]] = {
    "no_match": MINIMAL_SECTION_MESSAGE,
    "configured": REMOVE_SECTION_MESSAGE,
}


# NOTE:
# NARRATIVE PLACEMENT
# =============================================================================
# every "swap the section's <text>" operation--removal notice, generic-path
# restoration, reconstruction--must land the new element in the same place:
# replacing the existing <text>, or, when absent, inserted per the CDA R2
# xs:sequence (after <title>, else after <code>, else appended). one helper
# owns that placement so all three writers stay consistent


def _place_section_text(
    section: _Element,
    new_text: _Element,
    namespaces: NamespaceMap,
) -> None:
    current_text = section.find("hl7:text", namespaces=namespaces)
    if current_text is not None:
        section.replace(current_text, new_text)
        return

    title_element = section.find("hl7:title", namespaces=namespaces)
    if title_element is not None:
        title_element.addnext(new_text)
        return

    code_element = section.find("hl7:code", namespaces=namespaces)
    if code_element is not None:
        code_element.addnext(new_text)
        return

    section.append(new_text)


# NOTE:
# NARRATIVE REMOVAL NOTICE
# =============================================================================


def replace_narrative_with_removal_notice(
    section: _Element,
    namespaces: NamespaceMap = HL7_NS,
) -> None:
    """
    Replace the section's `<text>` with a notice explaining the removal.

    Produces a `<text>` containing a single `<paragraph>` carrying the
    REMOVE_NARRATIVE_MESSAGE. This is used when a jurisdiction has
    configured a section to have its narrative stripped while keeping
    the clinical entries intact for machine processing.

    The replacement is performed via `section.replace()` to preserve
    the element's position in the CDA R2 xs:sequence. If no `<text>`
    element exists, one is created via `_ensure_text_element`.

    The provenance footnote that will be appended afterward by
    refine_eicr is not this function's responsibility — this function
    only writes the removal-notice paragraph.
    """

    new_text = _make_element("text")
    paragraph = _sub_element(new_text, "paragraph")
    paragraph.text = REMOVE_NARRATIVE_MESSAGE

    _place_section_text(section, new_text, namespaces)


# NOTE:
# NARRATIVE RECONSTRUCTION SWAP
# =============================================================================


def replace_narrative_with_reconstruction(
    section: _Element,
    reconstructed_text: _Element,
    namespaces: NamespaceMap = HL7_NS,
) -> None:
    """
    Swap in a reconstructed `<text>` built from the section's surviving entries.

    The reconstructed element is produced (pure, detached) by
    `reconstruction.reconstruct_narrative`; this writer only places it
    into the section per the CDA R2 xs:sequence, mirroring the removal
    and restoration swaps.
    """

    _place_section_text(section, reconstructed_text, namespaces)


# NOTE:
# NARRATIVE RESTORATION (GENERIC PATH)
# =============================================================================


def restore_narrative(
    section: _Element,
    original_text: _Element,
    namespaces: NamespaceMap = HL7_NS,
) -> None:
    """
    Restore a previously-saved `<text>` element into a section.

    Used by the generic matching path, which clears the section's
    `<text>` during processing (to prevent inline narrative codes from
    producing false matches) and then restores the original deep copy
    afterward.

    Replaces the current `<text>` element with the provided deep copy.
    If no `<text>` element currently exists, the original is inserted
    per the CDA R2 xs:sequence.
    """

    _place_section_text(section, original_text, namespaces)


# NOTE:
# MINIMAL SECTION STUB
# =============================================================================


def create_minimal_section(
    section: _Element,
    removal_reason: Literal["no_match", "configured"] = "no_match",
) -> None:
    """
    Reduce a section to a minimal stub with an explanation message.

    Updates the `<text>` element with a single-row status table, removes
    all `<entry>` elements, and sets nullFlavor="NI" on the section. The
    message displayed in the stub varies based on why the section was
    reduced:

      - "no_match":   No clinical information matched the configured
                      code sets. Uses MINIMAL_SECTION_MESSAGE.
      - "configured": Jurisdiction configured the section to be removed.
                      Uses REMOVE_SECTION_MESSAGE.

    The stub table uses proper `<thead>`/`<th>` header semantics and
    `<tbody>`/`<tr>`/`<td>` body rows rather than the HTML-invalid
    ``<thead>`/`<tr>`/`<td>`` structure the previous implementation used.

    If the section has no `<text>` element at all, one is created via
    `_ensure_text_element`, which inserts it in the correct xs:sequence
    position.

    Args:
        section: The section element to reduce.
        removal_reason: Which message to display in the stub.
    """

    section_message = _MESSAGE_MAP[removal_reason]

    text_element = _ensure_text_element(section)

    # clear whatever was in <text> and rebuild it as a stub table
    text_element.clear()

    table = _sub_element(text_element, "table", border="1")

    caption = _sub_element(table, "caption")
    caption.text = REFINER_OUTPUT_TITLE

    thead = _sub_element(table, "thead")
    header_row = _sub_element(thead, "tr")
    th = _sub_element(header_row, "th")
    th.text = "Status"

    tbody = _sub_element(table, "tbody")
    body_row = _sub_element(tbody, "tr")
    td = _sub_element(body_row, "td")
    td.text = section_message

    # remove all <entry> elements from the section
    for entry in section.findall("hl7:entry", namespaces=HL7_NS):
        remove_element(entry)

    # clean up any comments left inside the section
    remove_all_comments(section)

    # mark the section as nullFlavor="NI"
    section.attrib["nullFlavor"] = "NI"
