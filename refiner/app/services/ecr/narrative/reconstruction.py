from collections.abc import Callable
from typing import Literal, NamedTuple

from lxml import etree
from lxml.etree import _Element

from app.services.ecr.policy import ReconstructableSection

from ..model import HL7_NS, HL7_XSI_NS
from .elements import _make_element, _sub_element

# a section reconstructor takes a post-prune section and returns the
# (columns, rows) for its narrative table
type SectionReconstructor = Callable[[_Element], tuple[list[str], list[dict[str, str]]]]

# NOTE:
# RECONSTRUCTION OVERVIEW
# =============================================================================
# rebuild a section's human-readable <text> from the entries that SURVIVED
# refinement, so the narrative reflects what the document still contains
# rather than the stale story the source EHR authored against the full entry
# set
#
# three layers, drawn at the honest DRY seam:
#   1. shared primitives (typed-value renderer, field extractor, table
#      builder)--closed-set mechanical work, written once, section-agnostic
#   2. field maps (data)--per-statement (label, relative-xpath, kind) lists
#   3. per-section joins (code)--the structural quirks: row anchor + the
#      ancestor/sibling context a row reaches for
#
# sections relate by convention, not container: a flat LOINC -> function
# dispatch dict. adding a section is "one field map + one function + one
# dict entry"

_XSI: str = HL7_XSI_NS["xsi"]


# NOTE:
# LAYER 1 — SHARED PRIMITIVE: typed-value renderer
# =============================================================================
# CDA data types are a CLOSED set, so every "render a value element to a
# string" branch lives here, in one place. Field maps never mention xsi:type;
# they hand the element to this function and let it decide
#
# it absorbs two flavours of polymorphism:
#   - <value xsi:type="PQ"/> is polymorphic: the type rides on xsi:type
#   - <doseQuantity value= unit=/> is monomorphic: PQ by the CDA model, with
#     no xsi:type at all
# this is also the logic the displayName enrichment performs by hand today;
# it is the primitive most likely to be reused when the template-aware
# matching engine lands


def render_typed_value(el: _Element | None) -> str:
    """
    Render a CDA value-bearing element to a display string.

    Branches over the closed CDA R2 abstract data-type set (CD, PQ, ST,
    IVL_TS, PIVL_TS) plus a bare value/text fallback. Handles both
    xsi:type-tagged polymorphic values and monomorphic elements that are a
    given type by the CDA model (e.g. doseQuantity is PQ with no xsi:type).

    Args:
        el: The element to render, or None.

    Returns:
        A human-readable string, or "" when there is nothing to render.
    """

    if el is None:
        return ""

    xsi_type = el.get(f"{{{_XSI}}}type")

    # coded value (CD)--declared via xsi:type, or monomorphic (a coded
    # element such as interpretationCode that carries @code with no xsi:type)
    if xsi_type == "CD" or (xsi_type is None and el.get("code")):
        disp, code = el.get("displayName"), el.get("code")
        if disp and code:
            return f"{disp} ({code})"
        return disp or code or ""

    # physical quantity (PQ)--declared via xsi:type, or monomorphic
    # (doseQuantity and friends are PQ by the model)
    if xsi_type == "PQ" or (xsi_type is None and el.get("unit") is not None):
        val, unit = el.get("value"), el.get("unit")
        return f"{val} {unit}".strip() if val else ""

    # simple text (ST)
    if xsi_type == "ST":
        return (el.text or "").strip()

    # interval of time (IVL_TS)--low/high children
    low, high = el.find("hl7:low", HL7_NS), el.find("hl7:high", HL7_NS)
    if low is not None or high is not None:
        lo = low.get("value") if low is not None else None
        hi = high.get("value") if high is not None else None
        if lo and hi:
            return f"{lo} to {hi}"
        return lo or hi or ""

    # periodic interval (PIVL_TS)--frequency
    period = el.find("hl7:period", HL7_NS)
    if period is not None:
        return f"every {period.get('value')} {period.get('unit')}".strip()

    # bare timestamp / value, or text
    return el.get("value") or (el.text or "").strip()


# NOTE:
# LAYER 1 — SHARED PRIMITIVE: field extractor + the field-spec record
# =============================================================================
# FieldSpec is a data record (NamedTuple), not a behaviour-bearing class:
# "data record yes, extractor class hierarchy no." `kind` tells the extractor
# how to stringify whatever the xpath lands on:
#   "attr"  -> xpath ends at an attribute; lxml returns the string directly
#   "typed" -> xpath ends at an element; hand it to render_typed_value
#   "text"  -> xpath ends at an element; take its text content


class FieldSpec(NamedTuple):
    """
    One field to read off an anchor element: header, relative xpath, kind.
    """

    label: str  # becomes the column header
    xpath: str  # RELATIVE to the anchor element passed to extract_fields
    kind: Literal["attr", "typed", "text"]


def extract_fields(anchor: _Element, field_map: list[FieldSpec]) -> dict[str, str]:
    """
    Read a flat list of fields off ONE anchor element.

    No joining happens here — every xpath is relative to ``anchor``. This is
    reused at every structural level by the join functions (organizer,
    procedure, observation all flow through this same call).

    Args:
        anchor: The element each field xpath is evaluated against.
        field_map: The fields to read.

    Returns:
        A label -> value mapping; missing fields render as "".
    """

    row: dict[str, str] = {}
    for spec in field_map:
        results = anchor.xpath(spec.xpath, namespaces=HL7_NS)
        if not isinstance(results, list) or not results:
            row[spec.label] = ""
            continue

        first = results[0]
        if spec.kind == "attr":
            row[spec.label] = str(first)
        elif spec.kind == "typed":
            row[spec.label] = (
                render_typed_value(first) if isinstance(first, _Element) else ""
            )
        elif spec.kind == "text":
            row[spec.label] = (
                (first.text or "").strip() if isinstance(first, _Element) else ""
            )
        else:
            row[spec.label] = ""
    return row


# NOTE:
# LAYER 1 — SHARED PRIMITIVE: CDA narrative table builder
# =============================================================================
# builds a <text><table>...</table> narrative block via the namespace-aware
# element helpers (the same ones the footnote/stub writers use, so the output
# is NarrativeBlock.xsd-valid rather than bare HTML — the failure mode that
# disconnected the previous reconstruction attempt)
# * the block-level "machine-derived" marker goes HERE, on the whole block;
# not smeared across individual fields
# * this is the seam that later grows into <author> participation provenance

_RECONSTRUCTION_MARKER: str = (
    " Narrative reconstructed by the eCR Refiner from surviving clinical "
    "entries: machine-derived, not clinician-attested. "
)


def build_table(columns: list[str], rows: list[dict[str, str]]) -> _Element:
    """
    Build a detached narrative <text> containing a reconstruction table.

    The <text> carries a block-level comment marking it as machine-derived,
    then a <table> with one row per entry in ``rows``.

    Args:
        columns: Ordered column headers; also the keys read from each row.
        rows: One mapping per table row (column -> value).

    Returns:
        A detached, namespace-qualified <text> element.
    """

    text = _make_element("text")
    text.append(etree.Comment(_RECONSTRUCTION_MARKER))

    table = _sub_element(text, "table", border="1")

    thead = _sub_element(table, "thead")
    header_row = _sub_element(thead, "tr")
    for col in columns:
        th = _sub_element(header_row, "th")
        th.text = col

    tbody = _sub_element(table, "tbody")
    for row in rows:
        tr = _sub_element(tbody, "tr")
        for col in columns:
            td = _sub_element(tr, "td")
            td.text = row.get(col, "") or ""

    return text


# NOTE:
# LAYER 2 — DATA: field maps (the part refiner_narrative.xlsx pins down)
# =============================================================================
# each map is "given THIS anchor element, here are its fields." None of them
# mention joins or xsi:type. In the future template-aware engine these become
# keyed by templateId and fold in unchanged

# anchor: <organizer> (the panel context, reached UP to from each result row)
PANEL_FIELDS: list[FieldSpec] = [
    FieldSpec("Panel", "hl7:code/@displayName", "attr"),
]

# anchor: <procedure> (the specimen context, reached SIDEWAYS via a sibling)
SPECIMEN_FIELDS: list[FieldSpec] = [
    FieldSpec(
        "Specimen",
        "hl7:participant/hl7:participantRole/hl7:playingEntity/hl7:code/@displayName",
        "attr",
    ),
]

# anchor: <observation> (the result row's OWN fields)
RESULT_FIELDS: list[FieldSpec] = [
    FieldSpec("Test", "hl7:code/@displayName", "attr"),
    FieldSpec("Result", "hl7:value", "typed"),  # PQ or CD — renderer decides
    FieldSpec("Interpretation", "hl7:interpretationCode", "typed"),  # coded CE
    FieldSpec("Date", "hl7:effectiveTime/@value", "attr"),
]


# NOTE:
# LAYER 3 — PER-SECTION JOINS (the part kept as code)
# =============================================================================


def reconstruct_results(
    section: _Element,
) -> tuple[list[str], list[dict[str, str]]]:
    """
    Reconstruct the Results section rows.

    JOIN section: the row is each result observation, but a complete row
    needs context from two other structural levels — the PANEL, reached UP
    to the enclosing organizer, and the SPECIMEN, reached SIDEWAYS to a
    sibling procedure. Each level flows through the same extract_fields
    primitive against its own field map; the per-organizer merge is the join.

    Args:
        section: The post-prune Results <section>.

    Returns:
        (columns, rows) for build_table.
    """

    columns = ["Panel", "Specimen"] + [f.label for f in RESULT_FIELDS]
    rows: list[dict[str, str]] = []

    for organizer in section.findall("hl7:entry/hl7:organizer", HL7_NS):
        panel = extract_fields(organizer, PANEL_FIELDS)  # reach UP

        procedure = organizer.find("hl7:component/hl7:procedure", HL7_NS)
        specimen = (
            extract_fields(procedure, SPECIMEN_FIELDS)  # reach SIDEWAYS
            if procedure is not None
            else {"Specimen": ""}
        )

        for obs in organizer.findall("hl7:component/hl7:observation", HL7_NS):
            result = extract_fields(obs, RESULT_FIELDS)  # the row's own fields
            rows.append({**panel, **specimen, **result})  # the join

    return columns, rows


# NOTE:
# DISPATCH + PUBLIC ENTRY
# =============================================================================
# convention over container: a flat LOINC -> function dict relates the
# per-section reconstructors. Adding a section is one field map + one
# function + one entry here, touching no Layer 1 primitive

# TODO:
# next we will need to add problems, immunizations, and medications
SECTION_RECONSTRUCTORS: dict[str, SectionReconstructor] = {
    ReconstructableSection.RESULTS.value: reconstruct_results,
    # ReconstructableSection.PROBLEM.value: reconstruct_results,
    # ReconstructableSection.IMMUNIZATIONS.value: reconstruct_results,
    # ReconstructableSection.MEDICATIONS_ADMINISTERED.value: reconstruct_results,
}


def reconstruct_narrative(section: _Element) -> _Element | None:
    """
    Reconstruct a section's narrative <text> from its surviving entries.

    Dispatches on the section's LOINC code. Returns a detached, namespace-
    qualified <text> ready to replace the section's existing narrative, or
    None when the section has no registered reconstructor or nothing
    survived to reconstruct — in which case the caller should fall back to
    retaining the original narrative.

    This function is pure: it reads the section and returns a new element;
    it does not mutate ``section``.

    Args:
        section: The post-prune, post-enrich <section>.

    Returns:
        A detached <text>, or None.
    """

    loinc_codes = section.xpath("hl7:code/@code", namespaces=HL7_NS)
    loinc = (
        str(loinc_codes[0]) if isinstance(loinc_codes, list) and loinc_codes else None
    )

    reconstruct = SECTION_RECONSTRUCTORS.get(loinc) if loinc else None
    if reconstruct is None:
        return None

    columns, rows = reconstruct(section)
    if not rows:
        return None

    return build_table(columns, rows)
