import re
from collections.abc import Callable
from typing import Literal, NamedTuple, cast

from lxml import etree
from lxml.etree import _Element

from app.services.ecr.policy import ReconstructableSection
from app.services.format import remove_element

from ..model import HL7_NS, HL7_XSI_NS
from ..specification.constants import (
    CODE_SYSTEM_DISPLAY_NAMES,
    OBSERVATION_INTERPRETATION_DISPLAY,
)
from ..specification.template_oids import (
    LABORATORY_RESULT_STATUS_ID,
)
from .elements import _make_element, _sub_element
from .identifiers import REFINER_ID_PREFIX, run_id_digits


class DetailRow(NamedTuple):
    """
    One detail-table row plus a handle to the entry it represents.

    `source` is retained so the assembler can mint an `xs:ID` for the
    row and relink the surviving entry to it; per-section reconstructors
    never mutate it.

    `negated` carries the anchor's `@negationInd`. A negated
    `substanceAdministration` is a statement that the act did NOT happen--
    "No Known Medications", a refused or contraindicated vaccine--so the
    row must read as a negative, not as an administered product. The flag
    is annotated onto the row rather than dropped: the entry survived
    pruning, and under `DRIV` a surviving entry must have a narrative
    representation. Only the flat `substanceAdministration` reconstructors
    set it today; the trigger-template matcher half that would also drop
    retracted Problem trigger observations is not yet developed.
    """

    source: _Element
    values: dict[str, str]
    negated: bool = False


class Block(NamedTuple):
    """
    One grouping entry's self-contained narrative: context + detail rows.

    A join section emits one block per organizer/act (context carries the
    panel/concern + specimen lines; rows are the child observations). A
    flat section emits a single block with empty context and one row per
    entry. Unlike patterns are never collapsed into a shared grid.
    """

    context: dict[str, str]
    columns: list[str]
    rows: list[DetailRow]


# a section reconstructor takes a post-prune section and returns one
# self-contained Block per grouping entry
type SectionReconstructor = Callable[[_Element], list[Block]]

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


def _normalize(text: str | None) -> str:
    """
    Collapse internal whitespace and trim a narrative string.

    Real EHR narrative carries label text across wrapped lines (a value
    like "Not Detected" arrives split by a newline and indentation); a
    reconstructed cell wants it collapsed to single spaces.

    Args:
        text: The raw string, or None.

    Returns:
        The whitespace-normalized string, or "" when there is nothing.
    """

    return " ".join(text.split()) if text else ""


# HL7 V3 TS: YYYY[MM[DD[HH[MM[SS]]]]][.frac][±ZZZZ] — any prefix precision
_TS_RE = re.compile(
    r"^(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?(?:\.\d+)?([+-]\d{4})?$"
)


def format_ts(raw: str | None) -> str:
    """
    Render an HL7 V3 TS string as a human-readable date/time.

    Preserves the source precision (never fabricates missing components)
    and presents the timezone offset exactly as given (no conversion):

        2020             -> 2020
        202011           -> 2020-11
        20201107         -> 2020-11-07
        202011071159     -> 2020-11-07 11:59
        20201107115930   -> 2020-11-07 11:59:30
        202011071159-0700 -> 2020-11-07 11:59 -07:00

    A value that is not a recognizable TS (or is empty) is returned
    unchanged, so this is safe to apply to any rendered @value.

    Args:
        raw: The raw TS string, or None.

    Returns:
        The formatted date/time, the input unchanged if not a TS, or "".
    """

    if not raw:
        return ""

    match = _TS_RE.match(raw.strip())
    if match is None:
        return raw

    year, month, day, hour, minute, second, offset = match.groups()
    out = year
    if month:
        out += f"-{month}"
    if day:
        out += f"-{day}"
    if hour:
        time = hour
        if minute:
            time += f":{minute}"
        if second:
            time += f":{second}"
        out += f" {time}"
    if offset:
        out += f" {offset[:3]}:{offset[3:]}"
    return out


# NOTE:
# LAYER 1 — SHARED PRIMITIVE: code-display resolver
# =============================================================================
# real EHR data does NOT put the human label on @displayName. The Epic Results
# example carries no displayName on its <code> elements at all--the label lives
# in <originalText> ("Stool Pathogens, NAAT, Parasite") and/or
# <translation @displayName>. Resolving a coded element to a display string is
# its own closed-set concern, so it lives here and every coded field flows
# through it. originalText frequently wraps a <reference> into
# the narrative, so we take its text content, not its full string


def _first_xpath_str(el: _Element, xpath: str) -> str:
    """
    Return the first string result of `xpath`, normalized, or "".
    """

    results = el.xpath(xpath, namespaces=HL7_NS)
    if isinstance(results, list) and results:
        return _normalize(str(results[0]))
    return ""


def render_code_display(el: _Element | None) -> str:
    """
    Resolve a coded element to its human display string.

    Tries, in order: the @displayName attribute, the text of an
    <originalText> child (ignoring any <reference> it wraps), the
    @displayName of the first <translation>, the bare @code, and finally
    the @code of the first <translation>. Returns "" when none resolve.

    The translation fallbacks matter for immunizations and medications: a
    sender may put a nullFlavor on the primary CVX/RxNorm code and carry the
    real code (and sometimes its display) in a <translation> (NDC, RxNorm,
    CVX). Resolving translation @displayName *and* @code keeps those rows from
    rendering blank.

    Args:
        el: A coded element (<code>, <value xsi:type="CD">, etc.), or None.

    Returns:
        A human-readable display string, or "".
    """

    if el is None:
        return ""

    if display := _normalize(el.get("displayName")):
        return display

    original_text = el.find("hl7:originalText", HL7_NS)
    if original_text is not None:
        # normalize-space gathers descendant text (skipping the <reference>
        # child, which has none) and collapses whitespace in one step
        if text := str(original_text.xpath("normalize-space(.)")):
            return text

    if display := _first_xpath_str(el, "hl7:translation/@displayName"):
        return display

    return el.get("code") or _first_xpath_str(el, "hl7:translation/@code")


# NOTE:
# LAYER 1 — SHARED PRIMITIVE: interpretation-flag renderer
# =============================================================================
# interpretationCode is HL7 ObservationInterpretation--a closed result-flag
# vocabulary ("A", "H", "L"). it stays display-only (no code suffix), but real
# senders frequently omit @displayName, leaving a bare letter that reads as
# noise to a PHA; we prefer whatever human display the sender gave (via the
# full render_code_display chain) and only reach for the map when we
# would otherwise be showing the raw @code


def render_interpretation(el: _Element | None) -> str:
    """
    Render an ObservationInterpretation coded element to its flag display.

    Defers to `render_code_display`; only when that resolves to nothing but
    the bare `@code` does it substitute the canonical HL7 display ("A" ->
    "Abnormal", "H" -> "High", "L" -> "Low"). An unmapped code is returned
    as-is, so this never hides an interpretation it does not recognize.

    Args:
        el: An `<interpretationCode>` element, or None.

    Returns:
        The interpretation display string, or "".
    """

    if el is None:
        return ""

    display = render_code_display(el)
    code = el.get("code")
    if code and display == code:
        return OBSERVATION_INTERPRETATION_DISPLAY.get(code, code)
    return display


# NOTE:
# LAYER 1 — SHARED PRIMITIVE: clinical coded-concept renderer
# =============================================================================
# clinical-terminology concepts (LOINC panels, SNOMED findings, RxNorm/CVX
# products) surface their authoritative half--code + system--alongside the
# editable displayName, so a reader of the stylesheet-rendered HTML who never
# opens the structured entries still gets a verifiable concept identifier;
# the system name is resolved from the codeSystem OID, **not** the unreliable
# codeSystemName attribute. HL7 admin/status vocabularies (statusCode,
# interpretationCode) stay display-only via render_code_display


def render_coded_concept(el: _Element | None) -> str:
    """
    Render a clinical coded element as `displayName (System code)`.

    The display half flows through the full `render_code_display` fallback
    chain. The code half is the element's own `@code`, qualified by the
    human-readable system name resolved from `@codeSystem` (the OID).

        - code + known system -> "E. coli (SNOMED CT 112283007)"
        - code + unknown system -> "E. coli (112283007)"
        - no human display, only a code -> "SNOMED CT 112283007"
        - nullFlavor / missing code -> display-only (no empty parens)

    Args:
        el: A clinical coded element (<code>, <value xsi:type="CD">, …), or None.

    Returns:
        The rendered concept string, or "".
    """

    if el is None:
        return ""

    display = render_code_display(el)
    code = el.get("code")
    if not code:
        return display

    system = CODE_SYSTEM_DISPLAY_NAMES.get(el.get("codeSystem") or "")
    qualified = f"{system} {code}" if system else code
    if display and display != code:
        return f"{display} ({qualified})"
    return qualified


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
# coded values defer to render_code_display so a CD result resolves through the
# same originalText/translation fallback as every other coded field, and renders
# display-only (no "(code)" suffix)--matching what pre-refined narratives show


def _render_bound(bound: _Element) -> str:
    """
    Render one IVL low/high bound to a string.

    A bound may be a PQ (value + unit, as in an IVL_PQ reference range) or a
    bare timestamp (as in an IVL_TS effective time). A `@unit` marks the PQ
    case and keeps the unit on the value; otherwise the value is humanized as
    a TS.

    Args:
        bound: The `<low>` or `<high>` element.

    Returns:
        The rendered bound, or "".
    """

    value = bound.get("value")
    if not value:
        return ""
    unit = bound.get("unit")
    return f"{value} {unit}" if unit else format_ts(value)


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

    # coded value (CD)--declared via xsi:type, or monomorphic with @code. a CD
    # value is a clinical concept, so it surfaces code + system via the concept
    # renderer (admin/status codes never reach here; they use kind "coded")
    if xsi_type == "CD" or (xsi_type is None and el.get("code")):
        return render_coded_concept(el)

    # physical quantity (PQ)--declared via xsi:type, or monomorphic
    # (doseQuantity and friends are PQ by the model)
    if xsi_type == "PQ" or (xsi_type is None and el.get("unit") is not None):
        val, unit = el.get("value"), el.get("unit")
        return f"{val} {unit}".strip() if val else ""

    # simple text (ST)
    if xsi_type == "ST":
        return _normalize(el.text)

    # interval (IVL_TS panel/effective time, or IVL_PQ reference range)--low/high
    # children, each rendered per its own type so a PQ bound keeps its unit and a
    # TS bound is humanized; equal bounds collapse to a single value: an EHR
    # renders a low==high panel time as one timestamp, not "X to X" (confirmed
    # against real Epic Results narrative)
    low, high = el.find("hl7:low", HL7_NS), el.find("hl7:high", HL7_NS)
    if low is not None or high is not None:
        lo = _render_bound(low) if low is not None else ""
        hi = _render_bound(high) if high is not None else ""
        if lo and hi:
            return lo if lo == hi else f"{lo} to {hi}"
        return lo or hi or ""

    # periodic interval (PIVL_TS)--frequency
    period = el.find("hl7:period", HL7_NS)
    if period is not None:
        return f"every {period.get('value')} {period.get('unit')}".strip()

    # bare timestamp / value, or text
    return format_ts(el.get("value")) or _normalize(el.text)


# NOTE:
# LAYER 1 — SHARED PRIMITIVE: field extractor + the field-spec record
# =============================================================================
# FieldSpec is a data record (NamedTuple), not a behaviour-bearing class:
# "data record yes, extractor class hierarchy no." `kind` tells the extractor
# how to stringify whatever the xpath lands on:
#   "attr"    -> xpath ends at an attribute; lxml returns the string directly
#   "coded"   -> a <code>-like element rendered display-ONLY (admin/status
#                vocabularies); hand it to render_code_display
#   "interp"  -> an <interpretationCode> rendered display-ONLY, with the HL7
#                ObservationInterpretation flag map as a fallback for a bare
#                @code; hand it to render_interpretation
#   "concept" -> a CLINICAL coded element rendered "display (System code)";
#                hand it to render_coded_concept
#   "typed"   -> a polymorphic value element; hand it to render_typed_value
#                (decides PQ/CD/ST/IVL/PIVL; CD values render as concepts)
#   "text"    -> xpath ends at an element; take its text content


class FieldSpec(NamedTuple):
    """
    One field to read off an anchor element: header, relative xpath, kind.
    """

    label: str  # becomes the column header
    xpath: str  # RELATIVE to the anchor element passed to extract_fields
    kind: Literal["attr", "coded", "interp", "concept", "typed", "text"]


def extract_fields(anchor: _Element, field_map: list[FieldSpec]) -> dict[str, str]:
    """
    Read a flat list of fields off ONE anchor element.

    No joining happens here — every xpath is relative to `anchor`. This is
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
        # HL7_XSI_NS (not HL7_NS) so a field-map xpath may discriminate on
        # @xsi:type--e.g. splitting a medication's two effectiveTimes into
        # the IVL_TS duration and the PIVL_TS frequency
        results = anchor.xpath(spec.xpath, namespaces=HL7_XSI_NS)
        if not isinstance(results, list) or not results:
            row[spec.label] = ""
            continue

        first = results[0]
        if spec.kind == "attr":
            row[spec.label] = str(first)
        elif spec.kind == "coded":
            row[spec.label] = (
                render_code_display(first) if isinstance(first, _Element) else ""
            )
        elif spec.kind == "interp":
            row[spec.label] = (
                render_interpretation(first) if isinstance(first, _Element) else ""
            )
        elif spec.kind == "concept":
            row[spec.label] = (
                render_coded_concept(first) if isinstance(first, _Element) else ""
            )
        elif spec.kind == "typed":
            row[spec.label] = (
                render_typed_value(first) if isinstance(first, _Element) else ""
            )
        elif spec.kind == "text":
            row[spec.label] = (
                _normalize(first.text) if isinstance(first, _Element) else ""
            )
        else:
            row[spec.label] = ""
    return row


# NOTE:
# LAYER 1 — SHARED PRIMITIVE: per-organizer block assembler
# =============================================================================
# emits the section <text> as one self-contained block per grouping entry:
# * a context table (panel/concern + specimen, rendered once) plus a
#   detail table whose rows carry minted xs:IDs. it is the only place that
#   MUTATES surviving entries--it relinks each row to the entry it represents,
#   so the entry↔narrative round-trip survives the narrative swap. namespace-
#   aware element helpers keep the output NarrativeBlock.xsd-valid
# * the block-level "machine-derived" marker goes HERE, on the whole <text>;
#   not smeared across individual fields
# * this is the seam that later grows into <author> participation provenance
#   we won't be implementing this until we have more user driven feedback
#   **but** we can still develop the provenance content as comments

_RECONSTRUCTION_MARKER: str = (
    " Narrative reconstructed by the eCR Refiner from surviving clinical "
    "entries: machine-derived, not clinician-attested. "
)

# prepended to a negated substanceAdministration's leading cell so the row reads
# as the negative it is (a not-administered / "no known" statement) rather than
# as an administered product
_NEGATED_PREFIX: str = "Not administered: "


def _strip_entry_references(section: _Element) -> None:
    """
    Clear the entry references that the swapped-in narrative will strand.

    Replacing the section narrative deletes the `xs:ID`s these references
    point at, so every `#id` under an entry is about to dangle. Two kinds
    live there and they are handled differently:

      - a row-level `<text><reference/>`: the observation/act's link to
        its narrative row. Removed wholesale; the assembler re-adds one
        canonical `<text><reference>` per surviving row (see
        `_relink_source`).
      - a coding-level `<originalText><reference/>`: the sender's own
        `originalText`-by-reference (CDA permits `originalText` by value
        **or** by reference). Blanking it would leave an empty `<originalText/>`
        and destroy the sender's coding provenance in the **shipped**
        structured data. Instead the referenced narrative label is
        resolved and inlined as `originalText` text--a lossless,
        conformant by-reference -> by-value conversion that also lets
        `render_code_display` read the label on any later pass.

    Runs while the **original** narrative is still in place (the caller swaps
    in the reconstruction afterward), so the `#id`s still resolve.
    """

    narrative_index = _index_narrative_ids(section)

    refs = section.xpath(".//hl7:entry//hl7:reference", namespaces=HL7_NS)
    if not isinstance(refs, list):
        return

    for ref in refs:
        if not isinstance(ref, _Element):
            continue

        parent = ref.getparent()
        if parent is not None and etree.QName(parent).localname == "originalText":
            _inline_original_text(parent, ref, narrative_index)
        else:
            remove_element(ref)


def _index_narrative_ids(section: _Element) -> dict[str, str]:
    """
    Map every `@ID` in the section narrative to its collapsed text.

    Scoped to the section's own <text>; returns {} when there is none.
    A local twin of `section.utils._index_narrative_display_ids` — the
    section layer sits ABOVE narrative and imports from it, so narrative
    cannot import back without a cycle.
    """

    text = section.find("hl7:text", HL7_NS)
    if text is None:
        return {}

    index: dict[str, str] = {}
    for element in text.iter():
        node_id = element.get("ID")
        if node_id:
            index[node_id] = str(element.xpath("normalize-space(.)"))
    return index


def _inline_original_text(
    original_text: _Element,
    reference: _Element,
    narrative_index: dict[str, str],
) -> None:
    """
    Replace an `originalText`-by-reference with the resolved label inline.

    Resolves the reference's `#id` against the section narrative and sets
    it as `original_text.text`, then removes the now-redundant <reference>.
    When the id does not resolve (a dangling pointer), only the reference
    is removed — there is nothing to inline, and leaving it would strand a
    broken `#id`.
    """

    value = reference.get("value")
    resolved = (
        narrative_index.get(value[1:]) if value and value.startswith("#") else None
    )
    remove_element(reference)
    if resolved:
        original_text.text = resolved


def _mark_entries_derived(section: _Element) -> None:
    """
    Set entry/@typeCode="DRIV" on every entry in a reconstructed section.

    Reconstruction rebuilds the section narrative FROM these entries, so the
    entry↔narrative relationship is "derived from" (DRIV), not the schema
    default COMP. eICR Vol 2 "Narrative Text" guidance: DRIV tells the receiver
    the narrative's source is the structured entries and the two are clinically
    equivalent. Idempotent; only touched on the reconstruction path, never on a
    retained author-attested narrative.
    """

    for entry in section.findall("hl7:entry", HL7_NS):
        entry.set("typeCode", "DRIV")


def _relink_source(source: _Element, row_id: str) -> None:
    """
    Point a surviving entry at the reconstructed row that represents it.

    Ensures `source` has a <text> child holding a single
    <reference value="#row_id"/>. When the <text> must be created it is
    placed after the last of templateId/id/code — the elements that precede
    <text> in the CDA R2 clinical-statement sequence — so it lands validly
    whether the source carries a <code> (observation) or not
    (substanceAdministration).
    """

    text_element = source.find("hl7:text", HL7_NS)
    if text_element is None:
        text_element = _make_element("text")
        preceding = source.xpath(
            "hl7:templateId | hl7:id | hl7:code", namespaces=HL7_NS
        )
        anchor = preceding[-1] if isinstance(preceding, list) and preceding else None
        if isinstance(anchor, _Element):
            anchor.addnext(text_element)
        else:
            source.insert(0, text_element)
    _sub_element(text_element, "reference", value=f"#{row_id}")


def _append_table(parent: _Element, columns: list[str]) -> _Element:
    """
    Append a bordered <table> with a header row; return its <tbody>.
    """

    table = _sub_element(parent, "table", border="1")
    thead = _sub_element(table, "thead")
    header_row = _sub_element(thead, "tr")
    for col in columns:
        _sub_element(header_row, "th").text = col
    return _sub_element(table, "tbody")


def render_section_text(
    blocks: list[Block],
    *,
    loinc: str,
    augmentation_timestamp: str,
) -> _Element:
    """
    Assemble a section's reconstructed <text> from its blocks.

    Each block renders as an optional one-row context table followed by a
    detail table whose rows carry document-unique xs:IDs. Every detail row's
    source entry is relinked to its row, so the entry↔narrative round-trip
    holds after the caller swaps in this <text>.

    Args:
        blocks: One self-contained block per grouping entry.
        loinc: The section's LOINC code, used in the row ID namespace.
        augmentation_timestamp: The run's HL7 V3 time value; its digits
            stamp the row IDs to the same run as the provenance footnote.

    Returns:
        A detached, namespace-qualified <text>.
    """

    text = _make_element("text")
    text.append(etree.Comment(_RECONSTRUCTION_MARKER))

    digits = run_id_digits(augmentation_timestamp)
    row_seq = 0

    for block in blocks:
        if block.context:
            context_body = _append_table(text, list(block.context))
            context_row = _sub_element(context_body, "tr")
            for label in block.context:
                _sub_element(context_row, "td").text = block.context[label] or ""

        detail_body = _append_table(text, block.columns)
        for row in block.rows:
            row_seq += 1
            row_id = f"{REFINER_ID_PREFIX}{loinc}-{digits}-row{row_seq}"
            tr = _sub_element(detail_body, "tr", ID=row_id)
            for index, col in enumerate(block.columns):
                value = row.values.get(col, "") or ""
                # a negated row is marked in its leading (concept) cell, so the
                # negative reads at the front of the row instead of the product
                # rendering as if it were administered
                if row.negated and index == 0:
                    value = f"{_NEGATED_PREFIX}{value}" if value else _NEGATED_PREFIX
                _sub_element(tr, "td").text = value
            _relink_source(row.source, row_id)

    return text


# NOTE:
# LAYER 2 — DATA: field maps (the part refiner_narrative.xlsx pins down)
# =============================================================================
# each map is "given THIS anchor element, here are its fields." None of them
# mention joins or xsi:type. clinical concepts use kind "concept" (display +
# system + code); HL7 admin/status vocabularies use "coded" (display-only).
# both point at the ELEMENT so they resolve through render_code_display's
# displayName/originalText/translation fallback--real EHR data rarely puts the
# label on @displayName. In the future template-aware engine these become
# keyed by templateId and fold in unchanged

# context anchor: <organizer> (the panel). Performer answers "which lab ran
# this?"--the performing organization. CDA allows performer on the organizer OR
# on the child observations, so we reach for the first one anywhere under the
# panel rather than assume a level (scoped to performer so it never picks up an
# author's organization)
_PERFORMING_ORG_NAME = (
    ".//hl7:performer/hl7:assignedEntity/hl7:representedOrganization/hl7:name"
)

# - Laboratory Result Status (…4.418, CONF:4527-443/444) is a MAY component of the
# Trigger Code Result Organizer carrying the status of the WHOLE battery (<- OBR-25)
# - it is organizer-scoped context, not a result: it is matched on @root only,
# because the organizer cites it as extension 2018-06-11 while its own template
# definition requires 2018-09-01 (CONF:3378-373) and the published schematron
# inherits the contradiction
# - **not** to be confused with Laboratory Observation Result Status (…4.419), which
# is per-observation and hangs off an entryRelationship inside the result
_LAB_RESULT_STATUS_VALUE = (
    f"hl7:component/hl7:observation[hl7:templateId[@root='{LABORATORY_RESULT_STATUS_ID}']]"
    "/hl7:value"
)

PANEL_FIELDS: list[FieldSpec] = [
    FieldSpec("Panel", "hl7:code", "concept"),
    FieldSpec("Date(s)", "hl7:effectiveTime", "typed"),
    FieldSpec("Performer", _PERFORMING_ORG_NAME, "text"),
    FieldSpec("Result Status", _LAB_RESULT_STATUS_VALUE, "coded"),
]

# context anchor: <procedure> (the specimen, a sibling of the observations)
SPECIMEN_FIELDS: list[FieldSpec] = [
    FieldSpec(
        "Specimen",
        "hl7:participant/hl7:participantRole/hl7:playingEntity/hl7:code",
        "concept",
    ),
    FieldSpec("Target Site", "hl7:targetSiteCode", "concept"),
]

# detail anchor: <observation> (the result row's OWN fields); interpretation is
# the observation's own flag (a direct child--never the reference range's nested
# interpretationCode)--reference range is the observationRange value (IVL_PQ), a
# distinct column so a reader sees the result against its normal range
RESULT_FIELDS: list[FieldSpec] = [
    FieldSpec("Test", "hl7:code", "concept"),
    FieldSpec("Outcome", "hl7:value", "typed"),  # PQ, CD, ST — renderer decides
    FieldSpec("Interpretation", "hl7:interpretationCode", "interp"),  # HL7 flag
    FieldSpec(
        "Reference Range",
        "hl7:referenceRange/hl7:observationRange/hl7:value",
        "typed",  # IVL_PQ — bounds render with units
    ),
    FieldSpec("Date(s)", "hl7:effectiveTime", "typed"),  # flat @value or IVL
]

# context anchor: <act> (the Problem Concern Act)
CONCERN_FIELDS: list[FieldSpec] = [
    FieldSpec("Concern Status", "hl7:statusCode/@code", "attr"),
    FieldSpec("Date(s)", "hl7:effectiveTime", "typed"),  # noted date (low)
]

# detail anchor: <observation> (the Problem Observation)
# - Problem Type is a LOINC code from the Problem Type value set (75322-8 "Complaint",
# 75323-6 "Condition", ...)--a row-type LABEL, not the clinical concept--so it is left
# display-only; the Problem itself (hl7:value) is the concept that surfaces code + system
PROBLEM_FIELDS: list[FieldSpec] = [
    FieldSpec("Problem Type", "hl7:code", "coded"),
    FieldSpec("Problem", "hl7:value", "concept"),  # CD by the IG
    FieldSpec("Date(s)", "hl7:effectiveTime", "typed"),  # onset (low) / resolved (high)
]

# Immunizations and Medications share the <substanceAdministration> anchor
# (FLAT — no context join) and the same product-code location. that code is the
# fickle field: senders may nullFlavor the primary CVX/RxNorm code and carry the
# real code in a <translation>, so it flows through the concept resolver which
# falls back through translation @displayName then @code
_MANUFACTURED_MATERIAL_CODE = (
    "hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:code"
)

IMMUNIZATION_FIELDS: list[FieldSpec] = [
    FieldSpec("Immunization", _MANUFACTURED_MATERIAL_CODE, "concept"),
    FieldSpec("Date", "hl7:effectiveTime", "typed"),
    FieldSpec("Status", "hl7:statusCode/@code", "attr"),
]

# Medication Activity carries TWO effectiveTimes (CONF:1098-7513/7514): an
# IVL_TS for the administration window and a PIVL_TS for the dosing frequency
# ("every 12 h"). extract_fields takes results[0], so a single
# "hl7:effectiveTime" spec would render the window and silently drop the
# frequency — the render_typed_value PIVL_TS branch was unreachable for
# medications. split them by @xsi:type so each lands in its own column
MEDICATION_FIELDS: list[FieldSpec] = [
    FieldSpec("Medication", _MANUFACTURED_MATERIAL_CODE, "concept"),
    FieldSpec("Dose", "hl7:doseQuantity", "typed"),  # monomorphic PQ
    FieldSpec("Duration", "hl7:effectiveTime[not(@xsi:type='PIVL_TS')]", "typed"),
    FieldSpec("Frequency", "hl7:effectiveTime[@xsi:type='PIVL_TS']", "typed"),
    FieldSpec("Route", "hl7:routeCode", "concept"),
]


# NOTE:
# LAYER 3 — PER-SECTION JOINS (the part kept as code)
# =============================================================================


def reconstruct_results(section: _Element) -> list[Block]:
    """
    Reconstruct the Results section as one block per panel.

    JOIN section: each organizer is a self-contained block. Its context is
    the PANEL (its own fields) merged with the SPECIMEN reached SIDEWAYS to a
    sibling procedure; its detail rows are the child result observations.
    Context is rendered once per block — never repeated down the result rows.

    Args:
        section: The post-prune, post-enrich Results <section>.

    Returns:
        One Block per organizer that has surviving result observations.
    """

    blocks: list[Block] = []

    for organizer in section.findall("hl7:entry/hl7:organizer", HL7_NS):
        context = extract_fields(organizer, PANEL_FIELDS)

        procedure = organizer.find("hl7:component/hl7:procedure", HL7_NS)
        context |= (
            extract_fields(procedure, SPECIMEN_FIELDS)
            if procedure is not None
            else {spec.label: "" for spec in SPECIMEN_FIELDS}
        )

        # an organizer/component may hold a Laboratory Result Status (...4.418),
        # which IS an <observation> and which the shared-context prune carve-out
        # deliberately keeps alive. unfiltered it renders as a result row
        # reading "Lab order result status"; it belongs in the block context
        # (PANEL_FIELDS), not the table
        #
        # this **excludes** the known non-result template rather than **requiring**
        # the Result Observation V3 one, and the direction is deliberate. requiring
        # ...4.2 would blank the whole table for any sender that omits the
        # templateId — turning the DRIV assertion ("narrative is clinically
        # equivalent to the structured entries") into a lie, which is a far
        # worse outcome than one spurious row. the prune guard in
        # entry_match_rules is inclusive for the mirror-image reason: there,
        # "no result templateId" means **retain** as context, so erring toward the
        # template keeps more. here it would show less
        result_observations = cast(
            list[_Element],
            organizer.xpath(
                "hl7:component/hl7:observation"
                f"[not(hl7:templateId[@root='{LABORATORY_RESULT_STATUS_ID}'])]",
                namespaces=HL7_NS,
            ),
        )
        rows = [
            DetailRow(source=obs, values=extract_fields(obs, RESULT_FIELDS))
            for obs in result_observations
        ]
        if rows:
            blocks.append(
                Block(
                    context=context,
                    columns=[spec.label for spec in RESULT_FIELDS],
                    rows=rows,
                )
            )

    return blocks


def reconstruct_problems(section: _Element) -> list[Block]:
    """
    Reconstruct the Problems section as one block per concern.

    JOIN section, mirroring Results one level down: each Problem Concern Act
    is a self-contained block whose context is the concern (status + noted
    date) and whose detail rows are the Problem Observations reached DOWN
    through entryRelationship. Context renders once per block, not per row.

    Args:
        section: The post-prune, post-enrich Problems <section>.

    Returns:
        One Block per concern act that has surviving problem observations.
    """

    blocks: list[Block] = []

    for act in section.findall("hl7:entry/hl7:act", HL7_NS):
        context = extract_fields(act, CONCERN_FIELDS)

        # only the Problem Observation is a problem row. a Problem Concern Act
        # also permits entryRelationship[@typeCode='REFR'] carrying a Priority
        # Preference (...22.4.143), itself an <observation>; unfiltered it renders
        # as a phantom problem row. the Problem Observation SHALL sit under
        # typeCode='SUBJ' (CONF:1198-9035), so require it
        #
        # - this requires the expected discriminator, the opposite of the Results
        # row filter's exclude-the-known-noise stance--and deliberately.
        # - there the discriminator is a templateId senders frequently omit, so
        # requiring it would blank the table (a DRIV lie)
        # - here it is a positional SHALL conformant senders reliably emit,
        # so requiring it drops the noise without that risk
        rows = [
            DetailRow(source=obs, values=extract_fields(obs, PROBLEM_FIELDS))
            for obs in act.findall(
                "hl7:entryRelationship[@typeCode='SUBJ']/hl7:observation", HL7_NS
            )
        ]
        if rows:
            blocks.append(
                Block(
                    context=context,
                    columns=[spec.label for spec in PROBLEM_FIELDS],
                    rows=rows,
                )
            )

    return blocks


def _reconstruct_flat(
    section: _Element,
    *,
    anchor_xpath: str,
    fields: list[FieldSpec],
) -> list[Block]:
    """
    Reconstruct a FLAT section as a single context-free table.

    The row IS the anchor entry; there is nothing to reach up or sideways
    for. Every anchor becomes one row in a single block with empty context
    (the assembler renders no context table for it). This is the shape both
    substanceAdministration sections (Immunizations, Medications) take.

    Args:
        section: The post-prune, post-enrich <section>.
        anchor_xpath: Row anchor, relative to the section.
        fields: The field map read off each anchor.

    Returns:
        A single Block, or [] when no anchor survived.
    """

    rows = [
        DetailRow(
            source=anchor,
            values=extract_fields(anchor, fields),
            negated=anchor.get("negationInd") == "true",
        )
        for anchor in section.findall(anchor_xpath, HL7_NS)
    ]
    if not rows:
        return []

    return [Block(context={}, columns=[spec.label for spec in fields], rows=rows)]


def reconstruct_immunizations(section: _Element) -> list[Block]:
    """
    Reconstruct the Immunizations section: one row per vaccine.

    Args:
        section: The post-prune, post-enrich Immunizations <section>.

    Returns:
        A single flat Block, or [] when no substanceAdministration survived.
    """

    return _reconstruct_flat(
        section,
        anchor_xpath="hl7:entry/hl7:substanceAdministration",
        fields=IMMUNIZATION_FIELDS,
    )


def reconstruct_medications(section: _Element) -> list[Block]:
    """
    Reconstruct the Medications Administered section: one row per medication.

    Args:
        section: The post-prune, post-enrich Medications <section>.

    Returns:
        A single flat Block, or [] when no substanceAdministration survived.
    """

    return _reconstruct_flat(
        section,
        anchor_xpath="hl7:entry/hl7:substanceAdministration",
        fields=MEDICATION_FIELDS,
    )


# NOTE:
# DISPATCH + PUBLIC ENTRY
# =============================================================================
# convention over container: a flat LOINC -> function dict relates the
# per-section reconstructors. Adding a section is one field map + one
# function + one entry here, touching no Layer 1 primitive

SECTION_RECONSTRUCTORS: dict[str, SectionReconstructor] = {
    ReconstructableSection.RESULTS.value: reconstruct_results,
    ReconstructableSection.PROBLEM.value: reconstruct_problems,
    ReconstructableSection.IMMUNIZATIONS.value: reconstruct_immunizations,
    ReconstructableSection.MEDICATIONS_ADMINISTERED.value: reconstruct_medications,
}


def reconstruct_narrative(
    section: _Element,
    *,
    augmentation_timestamp: str,
) -> _Element | None:
    """
    Reconstruct a section's narrative <text> from its surviving entries.

    Dispatches on the section's LOINC code. Returns a detached, namespace-
    qualified <text> ready to replace the section's existing narrative, or
    None when the section has no registered reconstructor or nothing
    survived to reconstruct — in which case the caller falls back to the
    removal notice rather than leaving a stale narrative.

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
        A detached <text>, or None.
    """

    loinc_codes = section.xpath("hl7:code/@code", namespaces=HL7_NS)
    loinc = (
        str(loinc_codes[0]) if isinstance(loinc_codes, list) and loinc_codes else None
    )

    reconstruct = SECTION_RECONSTRUCTORS.get(loinc) if loinc else None
    if reconstruct is None or loinc is None:
        return None

    blocks = reconstruct(section)
    if not any(block.rows for block in blocks):
        return None

    _strip_entry_references(section)
    _mark_entries_derived(section)
    return render_section_text(
        blocks, loinc=loinc, augmentation_timestamp=augmentation_timestamp
    )
