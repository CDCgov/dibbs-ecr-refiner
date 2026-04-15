import re
from typing import Final, Literal

from lxml import etree
from lxml.etree import _Element

from app.services.format import remove_element

from ..model import (
    HL7_NAMESPACE,
    HL7_NS,
    NamespaceMap,
    SectionProvenanceRecord,
)
from .constants import (
    CLINICAL_DATA_TABLE_HEADERS,
    MINIMAL_SECTION_MESSAGE,
    PROVENANCE_LABEL,
    PROVENANCE_OUTCOME_NOTES,
    PROVENANCE_SOURCE_NOTES,
    PROVENANCE_TABLE_HEADERS,
    REFINER_OUTPUT_TITLE,
    REMOVE_NARRATIVE_MESSAGE,
    REMOVE_SECTION_MESSAGE,
)

# NOTE:
# INTERNAL CONSTANTS
# =============================================================================

_MESSAGE_MAP: Final[dict[str, str]] = {
    "no_match": MINIMAL_SECTION_MESSAGE,
    "configured": REMOVE_SECTION_MESSAGE,
}


# NOTE:
# ELEMENT FACTORY HELPERS
# =============================================================================
# every element emitted into <text> must be qualified with the HL7 v3
# namespace for NarrativeBlock.xsd validation to pass


def _make_element(local_name: str, **attribs: str) -> _Element:
    """
    Create a namespace-qualified narrative element.

    Returns a detached element in the urn:hl7-org:v3 namespace. Use
    `_sub_element` instead when the new element should be appended
    to an existing parent.
    """

    element = etree.Element(f"{{{HL7_NAMESPACE}}}{local_name}")
    for key, value in attribs.items():
        element.set(key, value)
    return element


def _sub_element(parent: _Element, local_name: str, **attribs: str) -> _Element:
    """
    Create a namespace-qualified child element appended to `parent`.

    Thin wrapper around etree.SubElement that applies Clark notation
    for the HL7 v3 namespace, matching the pattern used in augment.py.
    """

    element = etree.SubElement(parent, f"{{{HL7_NAMESPACE}}}{local_name}")
    for key, value in attribs.items():
        element.set(key, value)
    return element


# NOTE:
# TEXT PLACEMENT HELPERS
# =============================================================================


def _ensure_text_element(section: _Element) -> _Element:
    """
    Return the section's <text> element, creating one if absent.

    If the section has no <text>, a new empty <text> is created and
    inserted after <title> per the CDA R2 xs:sequence for
    StrucDoc.Section: templateId -> id -> code -> title -> text ->
    confidentialityCode -> languageCode -> subject -> author ->
    informant -> entry -> component.

    If there is no <title> either, the <text> is inserted after
    <code>, which is the next-earliest required element in the
    sequence. Last resort: append to the section.
    """

    text_element = section.find("hl7:text", namespaces=HL7_NS)
    if text_element is not None:
        return text_element

    text_element = _make_element("text")

    title_element = section.find("hl7:title", namespaces=HL7_NS)
    if title_element is not None:
        title_element.addnext(text_element)
        return text_element

    code_element = section.find("hl7:code", namespaces=HL7_NS)
    if code_element is not None:
        code_element.addnext(text_element)
        return text_element

    section.append(text_element)
    return text_element


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
# whether a refiner policy override fired — most rows show the outcome
# confirming the configuration, but the no-match policy override
# produces an outcome that diverges from the configured action


def _build_footnote_id(
    loinc_code: str,
    augmentation_timestamp: str,
    occurrence_index: int = 0,
) -> str:
    """
    Build a document-unique xs:ID for a refiner provenance footnote.

    The ID is of the form
    `ecr-refinement-{loinc}-{timestamp-digits}`, optionally with a
    `-{n}` suffix for the rare case where the same LOINC appears on
    multiple top-level sections in a single document. The timestamp
    digits are extracted from the augmentation author's <time> value
    (HL7 V3 ``YYYYMMDDHHMMSS±ZZZZ`` format) by keeping the leading
    run of digits — the timezone offset is stripped because ``+`` and
    the offset digits are not wanted in the ID.

    xs:ID cannot start with a digit or hyphen, so the ``ecr-refinement-``
    prefix is load-bearing: it ensures the resulting string always
    satisfies the XML Name production.

    Args:
        loinc_code: The section's LOINC code (e.g., "46240-8").
        augmentation_timestamp: The augmentation author's time value,
            shared across all footnotes in this refinement run.
        occurrence_index: Zero-based disambiguator for the rare case
            where the same LOINC appears on multiple top-level
            sections. Zero (the normal case) produces no suffix;
            nonzero values append ``-N``.

    Returns:
        A document-unique xs:ID-safe string.
    """

    match = re.match(r"^\d+", augmentation_timestamp)
    timestamp_digits = match.group(0) if match else ""
    base = f"ecr-refinement-{loinc_code}-{timestamp_digits}"
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
    _add_provenance_cell(row, "Yes" if provenance.narrative else "No")
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


# NOTE:
# NARRATIVE REMOVAL NOTICE
# =============================================================================


def replace_narrative_with_removal_notice(
    section: _Element,
    namespaces: NamespaceMap = HL7_NS,
) -> None:
    """
    Replace the section's <text> with a notice explaining the removal.

    Produces a <text> containing a single <paragraph> carrying the
    REMOVE_NARRATIVE_MESSAGE. This is used when a jurisdiction has
    configured a section to have its narrative stripped while keeping
    the clinical entries intact for machine processing.

    The replacement is performed via `section.replace()` to preserve
    the element's position in the CDA R2 xs:sequence. If no <text>
    element exists, one is created via `_ensure_text_element`.

    The provenance footnote that will be appended afterward by
    refine_eicr is not this function's responsibility — this function
    only writes the removal-notice paragraph.
    """

    new_text = _make_element("text")
    paragraph = _sub_element(new_text, "paragraph")
    paragraph.text = REMOVE_NARRATIVE_MESSAGE

    existing_text = section.find("hl7:text", namespaces=namespaces)
    if existing_text is not None:
        section.replace(existing_text, new_text)
        return

    # no existing <text>; insert after <title> (or <code>) per xs:sequence
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
# NARRATIVE RESTORATION (GENERIC PATH)
# =============================================================================


def restore_narrative(
    section: _Element,
    original_text: _Element,
    namespaces: NamespaceMap = HL7_NS,
) -> None:
    """
    Restore a previously-saved <text> element into a section.

    Used by the generic matching path, which clears the section's
    <text> during processing (to prevent inline narrative codes from
    producing false matches) and then restores the original deep copy
    afterward.

    Replaces the current <text> element with the provided deep copy.
    If no <text> element currently exists, the original is inserted
    per the CDA R2 xs:sequence.
    """

    current_text = section.find("hl7:text", namespaces=namespaces)
    if current_text is not None:
        section.replace(current_text, original_text)
        return

    title_element = section.find("hl7:title", namespaces=namespaces)
    if title_element is not None:
        title_element.addnext(original_text)
        return

    code_element = section.find("hl7:code", namespaces=namespaces)
    if code_element is not None:
        code_element.addnext(original_text)
        return

    section.append(original_text)


# NOTE:
# MINIMAL SECTION STUB
# =============================================================================


def create_minimal_section(
    section: _Element,
    removal_reason: Literal["no_match", "configured"] = "no_match",
) -> None:
    """
    Reduce a section to a minimal stub with an explanation message.

    Updates the <text> element with a single-row status table, removes
    all <entry> elements, and sets nullFlavor="NI" on the section. The
    message displayed in the stub varies based on why the section was
    reduced:

      - "no_match":   No clinical information matched the configured
                      code sets. Uses MINIMAL_SECTION_MESSAGE.
      - "configured": Jurisdiction configured the section to be removed.
                      Uses REMOVE_SECTION_MESSAGE.

    The stub table uses proper <thead>/<th> header semantics and
    <tbody>/<tr>/<td> body rows rather than the HTML-invalid
    `<thead>/<tr>/<td>` structure the previous implementation used.

    If the section has no <text> element at all, one is created via
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


# NOTE:
# CLINICAL DATA TABLE (REFINED PATH)
# =============================================================================
# used by the generic and section-aware matching paths to replace a
# section's <text> with a table summarizing the refined clinical
# content. each row describes one matched clinical element with
# trigger-code elements rendered in bold


def update_text_element(
    section: _Element,
    clinical_elements: list[_Element],
    trigger_code_elements: set[int],
) -> None:
    """
    Replace the section's <text> with a refined clinical data table.

    The new <text> contains a single <table> with one row per element
    in `clinical_elements`. Elements whose `id()` appears in
    `trigger_code_elements` are rendered in bold and placed at the
    top of the table so trigger codes are visually prominent.

    If no <text> exists, one is created in the correct xs:sequence
    position.

    Args:
        section: The section whose <text> is being replaced.
        clinical_elements: The clinical elements to render as rows.
        trigger_code_elements: Set of Python ``id()`` values identifying
            which elements are trigger codes. Using id() rather than
            element equality because lxml elements don't hash stably
            across tree mutations.
    """

    new_text = _build_clinical_data_text(clinical_elements, trigger_code_elements)

    existing_text = section.find("hl7:text", namespaces=HL7_NS)
    if existing_text is not None:
        section.replace(existing_text, new_text)
        return

    title_element = section.find("hl7:title", namespaces=HL7_NS)
    if title_element is not None:
        title_element.addnext(new_text)
        return

    code_element = section.find("hl7:code", namespaces=HL7_NS)
    if code_element is not None:
        code_element.addnext(new_text)
        return

    section.append(new_text)


def _build_clinical_data_text(
    clinical_elements: list[_Element],
    trigger_code_elements: set[int],
) -> _Element:
    """
    Build a <text> element containing a refined clinical data table.

    Returns a detached <text> ready to be inserted into a section.
    """

    text_element = _make_element("text")

    table = _sub_element(text_element, "table", border="1")

    caption = _sub_element(table, "caption")
    caption.text = REFINER_OUTPUT_TITLE

    thead = _sub_element(table, "thead")
    header_row = _sub_element(thead, "tr")
    for header in CLINICAL_DATA_TABLE_HEADERS:
        th = _sub_element(header_row, "th")
        th.text = header

    tbody = _sub_element(table, "tbody")

    # put trigger code rows first so reviewers see them without scanning
    trigger_rows = [el for el in clinical_elements if id(el) in trigger_code_elements]
    other_rows = [el for el in clinical_elements if id(el) not in trigger_code_elements]

    for clinical_element in trigger_rows:
        _add_clinical_data_row(tbody, clinical_element, is_trigger=True)
    for clinical_element in other_rows:
        _add_clinical_data_row(tbody, clinical_element, is_trigger=False)

    return text_element


def _add_clinical_data_row(
    tbody: _Element,
    clinical_element: _Element,
    is_trigger: bool,
) -> None:
    """
    Append one <tr> to ``tbody`` describing a single clinical element.
    """

    data = _extract_clinical_data(clinical_element)
    row = _sub_element(tbody, "tr")

    # display text cell
    display_td = _sub_element(row, "td")
    display_text = data.get("display_text") or "Not specified"
    if is_trigger:
        bold = _sub_element(display_td, "content", styleCode="Bold")
        bold.text = display_text
    else:
        display_td.text = display_text

    # code cell
    code_td = _sub_element(row, "td")
    code_value = data.get("code") or "Not specified"
    if is_trigger:
        bold = _sub_element(code_td, "content", styleCode="Bold")
        bold.text = code_value
    else:
        code_td.text = code_value

    # code system cell
    code_system_td = _sub_element(row, "td")
    code_system_td.text = data.get("code_system") or "Not specified"

    # is trigger code cell
    trigger_td = _sub_element(row, "td")
    trigger_td.text = "YES" if is_trigger else "NO"

    # matching condition code cell
    matching_td = _sub_element(row, "td")
    matching_td.text = "YES"


def _extract_clinical_data(
    clinical_element: _Element,
) -> dict[str, str | None]:
    """
    Extract display text, code, and code system from a clinical element.

    Inspects the element itself if it is a ``code``/``value``/``translation``
    element with a ``@code`` attribute; otherwise searches for a
    descendant ``<code>`` element. Trigger-code status is handled
    separately by the caller.

    Returns:
        Dictionary with ``display_text``, ``code``, and ``code_system``
        keys, each either a string or None.
    """

    tag_local = (
        clinical_element.tag.split("}")[-1]
        if "}" in clinical_element.tag
        else clinical_element.tag
    )

    if tag_local in ("code", "value", "translation") and clinical_element.get("code"):
        code_element: _Element | None = clinical_element
    else:
        code_element = clinical_element.find(".//hl7:code", namespaces=HL7_NS)

    display_text: str | None = None
    code: str | None = None
    code_system: str | None = None

    if code_element is not None:
        display_text_raw = code_element.get("displayName")
        if isinstance(display_text_raw, str):
            display_text = display_text_raw

        code_raw = code_element.get("code")
        if isinstance(code_raw, str):
            code = code_raw

        code_system_raw = code_element.get("codeSystemName")
        if isinstance(code_system_raw, str):
            code_system = code_system_raw

    return {
        "display_text": display_text,
        "code": code,
        "code_system": code_system,
    }


# NOTE:
# COMMENT CLEANUP
# =============================================================================


def remove_all_comments(section: _Element) -> None:
    """
    Remove all XML comments from a processed section.

    After refining a section, inline comments left over from the source
    document may no longer be accurate or relevant. This scrubs them
    so the refined output doesn't carry misleading annotations forward.
    """

    xpath_result = section.xpath(".//comment()")
    if isinstance(xpath_result, list):
        for comment in xpath_result:
            if isinstance(comment, etree._Element):
                remove_element(comment)
