from collections.abc import Callable
from typing import NamedTuple

from lxml import etree
from lxml.etree import _Element

from app.services.format import remove_element

from ...model import HL7_NS
from ..elements import _make_element, _sub_element
from ..identifiers import REFINER_ID_PREFIX, run_id_digits

# NOTE:
# ASSEMBLE BLOCKS INTO A SECTION'S NARRATIVE AND RELINK THE ENTRIES
# =============================================================================
# * layer 1's other half: the table builder. `Block` and `DetailRow` are the
# currency between a section reconstructor (which decides what the rows **are**)
# and this module (which decides what they **look** like and mints their ids)
# * this is also the only place that **mutates** surviving entries--stripping the
# narrative references the swap is about to strand, relinking each entry to the
# row representing it, and stamping `typeCode="DRIV"`. it knows nothing about
# field maps or renderers


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

    `caption` names the detail table. Two kinds of section set it:

      - a **heterogeneous** section (Plan of Treatment), where consecutive
        tables carry different columns and a reader would otherwise have no
        way to tell a planned procedure from a planned act;
      - a **join** section whose context names the thing the rows belong to,
        where the caption restates that name over the detail table. The
        markup cannot nest the two tables (StrucDoc.Td forbids it), so
        naming the parent in the child's caption is what carries the
        containment a reviewer could not otherwise see.

    It stays empty for a flat section whose blocks are all the same kind of
    thing -- the section title already says what they are.
    """

    context: dict[str, str]
    columns: list[str]
    rows: list[DetailRow]
    caption: str = ""


# a section reconstructor takes a post-prune section and returns one
# self-contained Block per grouping entry
type SectionReconstructor = Callable[[_Element], list[Block]]


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


def _negated_prefix(source: _Element) -> str:
    """
    Return the negation prefix appropriate to an anchor's moodCode.

    Prepended to a negated substanceAdministration's leading cell so the
    row reads as the negative it is rather than as a product. The wording
    follows moodCode: negating an EVN statement says the act did **not**
    happen ("No Known Medications", a refused vaccine); negating a planned
    one says it is NOT going to be done--a contraindication or a
    cancelled order, not a missing administration.

    Absent `@moodCode` is treated as EVN: it is the CDA default for the
    clinical statements the flat reconstructors anchor on.
    """

    mood = source.get("moodCode") or "EVN"
    return "Not administered: " if mood == "EVN" else "Not planned: "


def _inline_original_text_references(section: _Element) -> None:
    """
    Convert every `originalText`-by-reference under an entry to by-value.

    CDA permits `originalText` by value **or** by reference, and senders who
    choose the latter park the human label in the narrative:

        <originalText><reference value="#problem13name"/></originalText>

    Two things need it inlined. The narrative is about to be replaced, which
    deletes the `xs:ID` the `#id` points at -- blanking the reference would
    leave an empty `<originalText/>` and destroy the sender's coding
    provenance in the **shipped** structured data. And `render_code_display`
    prefers `originalText` over `@displayName` precisely because it is the
    plain-English label a reviewer recognizes; read before inlining, it finds
    an empty element and falls through to the formal terminology name.

    So this runs BEFORE the field extractor, not after: the conversion is
    lossless and conformant either way, and doing it first is what makes the
    label reach the rendered table. Requires the **original** narrative to
    still be in place, which it is -- the caller swaps in the reconstruction
    afterward.

    Args:
        section: The section whose entries should be inlined.
    """

    narrative_index = _index_narrative_ids(section)

    refs = section.xpath(
        ".//hl7:entry//hl7:originalText/hl7:reference", namespaces=HL7_NS
    )
    if not isinstance(refs, list):
        return

    for ref in refs:
        if not isinstance(ref, _Element):
            continue
        parent = ref.getparent()
        if parent is not None:
            _inline_original_text(parent, ref, narrative_index)


def _strip_row_references(section: _Element) -> None:
    """
    Remove the row-level narrative references the swap is about to strand.

    A row-level `<text><reference/>` is the observation/act's link to its
    narrative row. Replacing the narrative deletes the `xs:ID` it points at,
    so each is removed wholesale and the assembler re-adds one canonical
    `<text><reference>` per surviving row (see `_relink_source`).

    Coding-level `originalText` references are NOT touched here --
    `_inline_original_text_references` has already converted them to
    by-value. This half is destructive, so it runs only once the caller has
    committed to swapping the narrative; the inlining half is lossless and
    runs earlier.

    Args:
        section: The section whose entries should be unlinked.
    """

    refs = section.xpath(".//hl7:entry//hl7:reference", namespaces=HL7_NS)
    if not isinstance(refs, list):
        return

    for ref in refs:
        if not isinstance(ref, _Element):
            continue
        parent = ref.getparent()
        if parent is not None and etree.QName(parent).localname == "originalText":
            continue
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


# StrucDoc.Td permits no nested <table>, so a detail table cannot literally sit
# inside its context table -- the two are siblings in the markup no matter what,
# and a reviewer reading a Results section saw a panel table and a test table as
# two peers rather than a battery and its members. what IS available is
# @styleCode, which StrucDoc types as NMTOKENS and CDA R2 leaves open to
# "x"-prefixed local extensions. "xallIndent" is the token Epic itself emits for
# exactly this (it appears in the source narratives these reconstructions
# replace), so a PHA stylesheet that renders one vendor's indent renders ours
_SUBORDINATE_TABLE_STYLE: str = "xallIndent"


def _append_table(
    parent: _Element,
    columns: list[str],
    caption: str = "",
    *,
    style_code: str = "",
) -> _Element:
    """
    Append a bordered <table> with a header row; return its <tbody>.

    A non-empty `caption` is emitted as the table's <caption>, which
    StrucDoc.Table requires FIRST — before <thead> — so it is written
    before anything else is appended. A non-empty `style_code` marks the
    table as subordinate to the one above it.
    """

    table = _sub_element(parent, "table", border="1")
    if style_code:
        table.set("styleCode", style_code)
    if caption:
        _sub_element(table, "caption").text = caption
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

        # a block WITH context is a grouping entry and its members, so its
        # detail table is subordinate; a flat block's table stands alone
        detail_body = _append_table(
            text,
            block.columns,
            block.caption,
            style_code=_SUBORDINATE_TABLE_STYLE if block.context else "",
        )
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
                    prefix = _negated_prefix(row.source)
                    value = f"{prefix}{value}" if value else prefix
                _sub_element(tr, "td").text = value
            _relink_source(row.source, row_id)

    return text
