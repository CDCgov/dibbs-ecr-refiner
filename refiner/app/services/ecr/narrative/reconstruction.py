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
    IMMUNIZATION_ACTIVITY_V3,
    LABORATORY_RESULT_STATUS_ID,
    PLANNED_IMMUNIZATION_ACTIVITY,
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

    Tries, in order: the text of an <originalText> child (ignoring any
    <reference> it wraps), the @displayName attribute, the @displayName of
    the first <translation>, the bare @code, and finally the @code of the
    first <translation>. Returns "" when none resolve.

    `originalText` is preferred over `@displayName` because it is what the
    sender showed its own clinicians: a lab that codes AST as LOINC 1920-8
    writes `displayName="Aspartate aminotransferase [Enzymatic activity/
    volume] in Serum or Plasma"` and `<originalText>AST</originalText>`. Both
    are correct; only one is what a PHA scanning a results table recognizes,
    and the formal name is the one they can least afford to read twenty
    times. The code and system are rendered alongside by
    `render_coded_concept`, so nothing verifiable is lost by leading with the
    plainer label.

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

    original_text = el.find("hl7:originalText", HL7_NS)
    if original_text is not None:
        # normalize-space gathers descendant text (skipping the <reference>
        # child, which has none) and collapses whitespace in one step
        if text := str(original_text.xpath("normalize-space(.)")):
            return text

    if display := _normalize(el.get("displayName")):
        return display

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
# LAYER 1 — SHARED PRIMITIVE: performer renderer
# =============================================================================
# "who is/was responsible for this act" arrives in two shapes under the same
# <performer>: a person (<assignedPerson><name> with given/family **children**) or
# an organization (<representedOrganization><name> with simple text). a field
# map cannot express that with a plain xpath--kind "text" reads .text and
# returns "" for the structured person name--so the choice lives here. person
# wins when both are present: a planned act's intended performer is the
# clinician, and the organization is the coarser answer


def _render_name(name: _Element) -> str:
    """
    Render an HL7 `EN` name element to a display string.

    A person name carries its parts as CHILDREN (`<given>`, `<family>`,
    `<suffix>`, ...); they are joined with single spaces in document order,
    so a name carrying parts this function does not enumerate still renders.
    Joining explicitly (rather than taking the element's string-value) is
    what keeps a compactly serialized `<name><given>Jane</given><family>Doe
    </family></name>` from rendering as "JaneDoe". An organization name is
    simple text and falls through to its own content.

    A `qualifier="CL"` part is dropped: that is HL7's "call me" name, an
    additional nickname alongside the legal given name rather than a part
    of it.

    Args:
        name: The `<name>` element.

    Returns:
        The rendered name, or "".
    """

    parts = [
        part
        for child in name
        if isinstance(child.tag, str)
        and child.get("qualifier") != "CL"
        and (part := _normalize(child.text))
    ]
    return " ".join(parts) if parts else _normalize(name.text)


def render_performer(el: _Element | None) -> str:
    """
    Render a `<performer>` to the responsible party's display name.

    Prefers the assigned person's name and falls back to the represented
    organization's: a planned act's intended performer is the clinician,
    and the organization is the coarser answer to the same question.

    Args:
        el: A `<performer>` element, or None.

    Returns:
        The performer's display name, or "".
    """

    return _render_performer_preferring(
        el,
        "hl7:assignedEntity/hl7:assignedPerson/hl7:name",
        "hl7:assignedEntity/hl7:representedOrganization/hl7:name",
    )


def render_performer_org(el: _Element | None) -> str:
    """
    Render a `<performer>` to the represented ORGANIZATION's display name.

    The mirror of `render_performer`: same element, opposite preference.
    For a resulted lab the question a PHA asks is "which laboratory ran
    this?", and the answer is the organization -- the individual who
    verified the battery is noise on a results table, and naming them
    discloses a clinician the receiver did not need. The person is still
    the fallback so a performer that carries only a name renders something.

    Args:
        el: A `<performer>` element, or None.

    Returns:
        The performing organization's display name, or "".
    """

    return _render_performer_preferring(
        el,
        "hl7:assignedEntity/hl7:representedOrganization/hl7:name",
        "hl7:assignedEntity/hl7:assignedPerson/hl7:name",
    )


def _render_performer_preferring(el: _Element | None, *xpaths: str) -> str:
    """
    Render the first `<performer>` name found at `xpaths`, in order.
    """

    if el is None:
        return ""

    for xpath in xpaths:
        name = el.find(xpath, HL7_NS)
        if name is not None and (rendered := _render_name(name)):
            return rendered

    return ""


# NOTE:
# LAYER 1 — SHARED PRIMITIVE: clinical coded-concept renderer
# =============================================================================
# clinical-terminology concepts (LOINC panels, SNOMED findings, RxNorm/CVX
# products) surface their authoritative half--code + system--alongside the
# editable displayName, so a reader of the stylesheet-rendered HTML who never
# opens the structured entries still gets a verifiable concept identifier;
# the system name is resolved from the codeSystem OID, **not** the unreliable
# codeSystemName attribute -- except as a LAST resort, when the OID is a
# proprietary one we cannot name and the alternative is showing a bare
# integer. HL7 admin/status vocabularies (statusCode, interpretationCode)
# stay display-only via render_code_display


def render_coded_concept(el: _Element | None) -> str:
    """
    Render a clinical coded element as `displayName (System code)`.

    The display half flows through the full `render_code_display` fallback
    chain. The code half is the element's own `@code`, qualified by the
    human-readable system name resolved from `@codeSystem` (the OID), or --
    when that OID is not one we can name -- by the sender's own
    `@codeSystemName`.

        - code + known system -> "E. coli (SNOMED CT 112283007)"
        - code + unknown OID, named by sender -> "16 (Epic.Result.Type 16)"
        - code + unknown system -> "E. coli (112283007)"
        - no human display, only a code -> "SNOMED CT 112283007"
        - nullFlavor / missing code -> display-only (no empty parens)

    Preferring the OID keeps the naming consistent across senders who spell
    the same system differently ("SNOMED-CT" vs "SNOMED CT"); reaching for
    `@codeSystemName` only after that lookup fails costs nothing on codes we
    recognize and is the difference between "16" and "Epic.Result.Type 16"
    on the proprietary results rows PHAs have reported as unreadable.

    Args:
        el: A clinical coded element (<code>, <value xsi:type="CD">, ...), or None.

    Returns:
        The rendered concept string, or "".
    """

    if el is None:
        return ""

    display = render_code_display(el)
    code = el.get("code")
    if not code:
        return display

    system = CODE_SYSTEM_DISPLAY_NAMES.get(el.get("codeSystem") or "") or _normalize(
        el.get("codeSystemName")
    )
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


def _render_unit(unit: str | None) -> str:
    """
    Render a UCUM unit for display, unwrapping a pure annotation.

    UCUM writes a unit that is really just a name for what is being counted
    as a curly-brace annotation on the dimensionless unit: 60 tablets is
    `value="60" unit="{tbl}"`. The braces are UCUM syntax, not part of the
    label, and showing them to a reviewer reading a medication table is
    noise. A unit that only wraps an annotation is unwrapped; anything else
    (including a real unit that merely carries a trailing annotation, like
    `mg{total}`) is left exactly as the sender wrote it.

    Args:
        unit: The `@unit` attribute value, or None.

    Returns:
        The display unit, or "".
    """

    if not unit:
        return ""
    stripped = unit.strip()
    if (
        stripped.startswith("{")
        and stripped.endswith("}")
        and "}" not in stripped[1:-1]
    ):
        return stripped[1:-1]
    return stripped


def _render_bound(bound: _Element) -> str:
    """
    Render one IVL low/high bound to a string.

    A bound may be a PQ (value + unit, as in an IVL_PQ reference range) or a
    bare timestamp (as in an IVL_TS effective time). A `@unit` marks the PQ
    case and keeps the unit on the value; otherwise the value is humanized as
    a TS.

    A nullFlavored bound may still carry its number one level down, in a
    `<translation>` whose `<originalText>` holds the unit:

        <low nullFlavor="OTH">
          <translation nullFlavor="OTH" value="49">
            <originalText>IU/L</originalText>
          </translation>
        </low>

    That is how Epic ships lab reference ranges whose units are not UCUM-
    codable, and reading only the bound's own `@value` renders the whole
    range blank. The translation is consulted ONLY when the bound itself has
    no `@value`, so a conformant bound is never second-guessed.

    Args:
        bound: The `<low>` or `<high>` element.

    Returns:
        The rendered bound, or "".
    """

    source = bound
    value = bound.get("value")
    if not value:
        translation = bound.find("hl7:translation[@value]", HL7_NS)
        if translation is None:
            return ""
        source, value = translation, translation.get("value")

    if unit := _render_unit(source.get("unit")):
        return f"{value} {unit}"
    # a translation carries its unit as originalText, not @unit
    if unit := _first_xpath_str(source, "hl7:originalText/text()"):
        return f"{value} {unit}"
    return format_ts(value or "")


def _is_quantity_bound(bound: _Element | None) -> bool:
    """
    Return True if a bound carries a measurement rather than a timestamp.
    """

    if bound is None:
        return False
    # a translation-carried bound is the Epic reference-range shape, whose unit
    # rides in <originalText> rather than on @unit
    return bool(bound.get("unit")) or (
        bound.find("hl7:translation[@value]", HL7_NS) is not None
    )


def _render_open_interval(el: _Element, low: _Element | None, rendered: str) -> str:
    """
    Render a one-sided interval, naming the side that is open.

    A one-sided interval collapsed to its bare bound is the one date shape the
    refiner cannot render honestly by accident: "2026-08-03" reads as "this
    happened on that date" whether the source said "started then, no end
    recorded" (`<low>` alone) or "ended then" (`<high>` alone). Those are
    different clinical facts, and on Problems the first is the difference
    between an active condition and a one-off note.

    The wording splits on what is being bounded, because "onward" is
    meaningless on a lab reference range:

        time,     low  -> "2026-08-03 onward"
        time,     high -> "until 2026-08-10"
        quantity, low  -> "≥ 0 mg/dL"
        quantity, high -> "≤ 1.2 mg/dL"

    An HL7 V3 IVL bound is inclusive unless it says otherwise, so the
    inclusive symbols are the default and `@inclusive="false"` earns the
    strict ones. Nothing here asserts more than the source did: an open high
    bound says the end was not recorded, NOT that the interval is ongoing --
    which is why the wording is "onward" and never "to present".

    Args:
        el: The interval element, consulted for @xsi:type.
        low: The `<low>` element when it is the side that rendered, else None.
        rendered: The already-rendered bound string.

    Returns:
        The rendered one-sided interval.
    """

    high = None if low is not None else el.find("hl7:high", HL7_NS)
    bound = low if low is not None else high

    xsi_type = el.get(f"{{{_XSI}}}type")
    if xsi_type == "IVL_PQ":
        quantity = True
    elif xsi_type == "IVL_TS":
        quantity = False
    else:
        quantity = _is_quantity_bound(bound)

    if not quantity:
        return f"{rendered} onward" if low is not None else f"until {rendered}"

    inclusive = (bound.get("inclusive") if bound is not None else None) != "false"
    if low is not None:
        return f"{'≥' if inclusive else '>'} {rendered}"
    return f"{'≤' if inclusive else '<'} {rendered}"


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
        return f"{val} {_render_unit(unit)}".strip() if val else ""

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
        # exactly one side resolved (the other absent, or nullFlavored with
        # nothing to read): name the open side rather than emit a bare value
        # that reads as a point in time
        if lo:
            return _render_open_interval(el, low, lo)
        if hi:
            return _render_open_interval(el, None, hi)
        return ""

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
#   "perf"    -> a <performer>; hand it to render_performer (person, else org)
#   "perf_org" -> a <performer> rendered as the represented ORGANIZATION,
#                falling back to the person; hand it to render_performer_org
#   "text"    -> xpath ends at an element; take its text content

type FieldKind = Literal[
    "attr", "coded", "interp", "concept", "typed", "perf", "perf_org", "text"
]


class FieldSource(NamedTuple):
    """
    One place to look for a field's value: a relative xpath and how to read it.
    """

    xpath: str  # RELATIVE to the anchor element passed to extract_fields
    kind: FieldKind


class FieldSpec(NamedTuple):
    """
    One field to read off an anchor element: header, xpath, kind, fallback.

    `fallback` names a **second** location to try when the primary one renders
    nothing. It carries its own `kind` because the two locations are rarely
    the same shape -- a battery's result status is a coded `<value>` on an
    IG template that most senders omit, while the answer a reader actually
    wants is sitting on the organizer's own `statusCode/@code`. Keeping the
    alternative in the field map (rather than branching in a join function)
    keeps "where does this column come from" answerable by reading data.

    It is deliberately ONE alternative, not a chain: every case real data has
    produced is "the conformant location, else the one senders actually
    populate." A third would be a sign the field wants its own renderer.
    """

    label: str  # becomes the column header
    xpath: str  # RELATIVE to the anchor element passed to extract_fields
    kind: FieldKind
    fallback: FieldSource | None = None


# each kind's renderer, keyed by the kind name. every one of them takes an
# element and returns a string, so the extractor never branches on kind--it
# looks the renderer up. "attr" is absent because its xpath lands on an
# attribute (a string), not an element, and is handled before the lookup
_FIELD_RENDERERS: dict[FieldKind, Callable[[_Element], str]] = {
    "coded": render_code_display,
    "interp": render_interpretation,
    "concept": render_coded_concept,
    "typed": render_typed_value,
    "perf": render_performer,
    "perf_org": render_performer_org,
    "text": lambda el: _normalize(el.text),
}


def _read_source(anchor: _Element, source: FieldSource) -> str:
    """
    Read ONE field source off an anchor and stringify it per its kind.

    Args:
        anchor: The element the source's xpath is evaluated against.
        source: The xpath + kind to read.

    Returns:
        The rendered value, or "" when the xpath finds nothing.
    """

    # HL7_XSI_NS (not HL7_NS) so a field-map xpath may discriminate on
    # @xsi:type--e.g. splitting a medication's two effectiveTimes into
    # the IVL_TS duration and the PIVL_TS frequency
    results = anchor.xpath(source.xpath, namespaces=HL7_XSI_NS)
    if not isinstance(results, list) or not results:
        return ""

    first = results[0]
    if source.kind == "attr":
        return str(first)

    render = _FIELD_RENDERERS.get(source.kind)
    if render is None or not isinstance(first, _Element):
        return ""
    return render(first)


def extract_fields(anchor: _Element, field_map: list[FieldSpec]) -> dict[str, str]:
    """
    Read a flat list of fields off ONE anchor element.

    No joining happens here — every xpath is relative to `anchor`. This is
    reused at every structural level by the join functions (organizer,
    procedure, observation all flow through this same call).

    A spec carrying a `fallback` tries it only when the primary source
    rendered nothing, so a column backed by an optional IG template can
    still fill from wherever conformant senders actually put the answer.

    Args:
        anchor: The element each field xpath is evaluated against.
        field_map: The fields to read.

    Returns:
        A label -> value mapping; missing fields render as "".
    """

    row: dict[str, str] = {}
    for spec in field_map:
        value = _read_source(anchor, FieldSource(spec.xpath, spec.kind))
        if not value and spec.fallback is not None:
            value = _read_source(anchor, spec.fallback)
        row[spec.label] = value
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
# this?"--CDA allows performer on the organizer OR on the child observations,
# so we reach for the first one anywhere under the panel rather than assume a
# level (scoped to performer so it never picks up an author's organization).
# kind "perf_org" resolves it to the represented ORGANIZATION: the question is
# which laboratory, not which technologist verified the battery
_PANEL_PERFORMER = ".//hl7:performer"

# - Laboratory Result Status (...4.418, CONF:4527-443/444) is a MAY component of the
# Trigger Code Result Organizer carrying the status of the WHOLE battery (<- OBR-25)
# - it is organizer-scoped context, not a result: it is matched on @root only,
# because the organizer cites it as extension 2018-06-11 while its own template
# definition requires 2018-09-01 (CONF:3378-373) and the published schematron
# inherits the contradiction
# - **not** to be confused with Laboratory Observation Result Status (...4.419), which
# is per-observation and hangs off an entryRelationship inside the result
_LAB_RESULT_STATUS_VALUE = (
    f"hl7:component/hl7:observation[hl7:templateId[@root='{LABORATORY_RESULT_STATUS_ID}']]"
    "/hl7:value"
)

PANEL_FIELDS: list[FieldSpec] = [
    FieldSpec("Panel name", "hl7:code", "concept"),
    FieldSpec("Date(s)", "hl7:effectiveTime", "typed"),
    FieldSpec("Performer", _PANEL_PERFORMER, "perf_org"),
    # the IG template is a MAY that senders almost never emit, so the column
    # read empty on every real document reviewed -- while the answer a PHA
    # wanted ("completed") sat on the organizer's own statusCode, a SHALL
    # that is always present. prefer the specific template, fall back to the
    # one that is actually populated
    FieldSpec(
        "Result Status",
        _LAB_RESULT_STATUS_VALUE,
        "coded",
        fallback=FieldSource("hl7:statusCode/@code", "attr"),
    ),
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
    FieldSpec("Result value", "hl7:value", "typed"),  # PQ, CD, ST — renderer decides
    FieldSpec("Interpretation", "hl7:interpretationCode", "interp"),  # HL7 flag
    # the sender's own <text> ("49 - 135 IU/L") is the last resort: it is an
    # unparsed string rather than rendered bounds, so it reads differently
    # from every other cell -- but a range the sender spelled out is strictly
    # better than a blank cell when the structured bounds render nothing
    FieldSpec(
        "Reference Range",
        "hl7:referenceRange/hl7:observationRange/hl7:value",
        "typed",  # IVL_PQ — bounds render with units
        fallback=FieldSource(
            "hl7:referenceRange/hl7:observationRange/hl7:text", "text"
        ),
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
# a PIVL_TS is only a FREQUENCY if it actually carries a <period>. senders
# ship `<effectiveTime xsi:type="PIVL_TS" operator="A" value="..."/>` -- a
# periodic interval with no period, just a timestamp wearing the wrong type --
# and splitting on @xsi:type alone filed that date under "Frequency" while
# leaving the administration date blank. discriminate on the period, so each
# column can only ever hold the kind of thing its header promises
_FREQUENCY = "hl7:effectiveTime[@xsi:type='PIVL_TS'][hl7:period]"
_ADMINISTRATION_TIME = "hl7:effectiveTime[not(@xsi:type='PIVL_TS' and hl7:period)]"

# the SUPPLIED quantity ("60 tablets"), which is a different question from the
# dose ("500 mg") -- it hangs off the Medication Supply Order/Dispense that the
# Medication Activity relates to, not off the administration itself
_SUPPLY_QUANTITY = "hl7:entryRelationship/hl7:supply/hl7:quantity"

MEDICATION_FIELDS: list[FieldSpec] = [
    FieldSpec("Medication", _MANUFACTURED_MATERIAL_CODE, "concept"),
    FieldSpec("Dose", "hl7:doseQuantity", "typed"),  # monomorphic PQ
    FieldSpec("Quantity", _SUPPLY_QUANTITY, "typed"),  # monomorphic PQ
    # the low bound alone, NOT the rendered interval. an administration is
    # given at a time, not over a window: senders that stamp a high bound put
    # it minutes after the low (the end of the infusion, the moment the nurse
    # closed the record), and rendering "19:00:00 to 19:27:00" reads as a
    # duration that carries no clinical meaning. the source narratives this
    # replaces label the column "date". falls back to the whole element for
    # senders who write a flat <effectiveTime value=""/> with no bounds
    FieldSpec(
        "Date administered",
        f"{_ADMINISTRATION_TIME}/hl7:low",
        "typed",
        fallback=FieldSource(_ADMINISTRATION_TIME, "typed"),
    ),
    FieldSpec("Frequency", _FREQUENCY, "typed"),
    FieldSpec("Route", "hl7:routeCode", "concept"),
    # "completed" vs "aborted" is the difference between a drug that was given
    # and one that was stopped, refused or cancelled -- statusCode is SHALL on
    # Medication Activity, so this column costs nothing and is always present
    FieldSpec("Status", "hl7:statusCode/@code", "attr"),
]

# plan of treatment is the first heterogeneous section: five unrelated clinical
# statements share one <section>, so it needs five field maps rather than one.
# each is a planned-mood mirror of a statement the refiner already renders
# somewhere else, which is why they repeat rather than share--a planned
# medication is not a Medications Administered row with a different label:
# it carries no administration window, and its Date is the date the
# medication is planned **for**
#
# performer is on every map. It is the one field the source spreadsheet
# deliberately left out ("you could add performer if present but I did not add
# to each as it complicates the structure"); for a **plan**, "who is expected to do
# this" is exactly the question a reviewer asks, so the complication is worth
# absorbing here (see render_performer) rather than pushing onto the reader.
# status likewise goes on every map: statusCode is SHALL on all five templates,
# and "active" vs "aborted" is the difference between a plan and a plan that
# was called off
_STATUS = FieldSpec("Status", "hl7:statusCode/@code", "attr")
_PERFORMER = FieldSpec("Performer", "hl7:performer", "perf")

PLANNED_OBSERVATION_FIELDS: list[FieldSpec] = [
    FieldSpec("Planned Observation", "hl7:code", "concept"),
    FieldSpec("Date", "hl7:effectiveTime", "typed"),
    _STATUS,
    _PERFORMER,
]

PLANNED_PROCEDURE_FIELDS: list[FieldSpec] = [
    FieldSpec("Planned Procedure", "hl7:code", "concept"),
    FieldSpec("Date", "hl7:effectiveTime", "typed"),
    FieldSpec("Target Site", "hl7:targetSiteCode", "concept"),
    FieldSpec("Method", "hl7:methodCode", "concept"),
    _STATUS,
    _PERFORMER,
]

PLANNED_ACT_FIELDS: list[FieldSpec] = [
    FieldSpec("Planned Activity", "hl7:code", "concept"),
    FieldSpec("Date", "hl7:effectiveTime", "typed"),
    _STATUS,
    _PERFORMER,
]

# unlike MEDICATION_FIELDS this does NOT split effectiveTime into an
# administration window and a dosing frequency. a Medications Administered row
# describes a course that ran; a planned medication carries the single date the
# medication is planned for (the spreadsheet's "Planned medication date",
# xsi:type="IVL_TS"). the PIVL_TS split earns its keep there and would only add
# a perpetually empty column here
PLANNED_MEDICATION_FIELDS: list[FieldSpec] = [
    FieldSpec("Planned Medication", _MANUFACTURED_MATERIAL_CODE, "concept"),
    FieldSpec("Date", "hl7:effectiveTime", "typed"),
    FieldSpec("Dose", "hl7:doseQuantity", "typed"),  # monomorphic PQ
    FieldSpec("Route", "hl7:routeCode", "concept"),
    _STATUS,
    _PERFORMER,
]

# lot and manufacturer are unique to the immunization map: they are how a PHA
# ties a planned vaccine to a supply. repeatNumber is in the spreadsheet but
# annotated "typically don't get this", so it stays out until real data shows
# otherwise
PLANNED_IMMUNIZATION_FIELDS: list[FieldSpec] = [
    FieldSpec("Planned Immunization", _MANUFACTURED_MATERIAL_CODE, "concept"),
    FieldSpec("Date", "hl7:effectiveTime", "typed"),
    FieldSpec("Dose", "hl7:doseQuantity", "typed"),
    FieldSpec("Route", "hl7:routeCode", "concept"),
    FieldSpec(
        "Lot",
        "hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial"
        "/hl7:lotNumberText",
        "text",
    ),
    FieldSpec(
        "Manufacturer",
        "hl7:consumable/hl7:manufacturedProduct/hl7:manufacturerOrganization/hl7:name",
        "text",
    ),
    _STATUS,
    _PERFORMER,
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
        # the DISPLAY half only: the context table one row up already carries
        # the qualified concept, and repeating "(LOINC 105066-5)" in the
        # caption directly above it is noise
        panel_name = render_code_display(organizer.find("hl7:code", HL7_NS))

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
                    # names the battery these rows belong to. a panel that
                    # resolved to nothing gets the generic caption rather than
                    # a dangling "Tests in panel: "
                    caption=(
                        f"Tests in panel: {panel_name}"
                        if panel_name
                        else "Tests in panel"
                    ),
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
# PLAN OF TREATMENT — the heterogeneous section
# =============================================================================
# every other reconstructable section is **one** kind of thing repeated. plan of
# treatment is five: planned observations, procedures, acts, medications and
# immunizations sit as siblings under a single <section>. that is why it emits
# one **captioned** block per entry kind instead of one block per grouping entry:
# the kinds do not share columns, and "unlike patterns are never collapsed into
# a shared grid" cuts the other way here--without a caption the reader gets a
# run of unlabelled tables
#
# the split is by ELEMENT NAME, except for substanceAdministration, which is
# both the medication and the immunization shape and can only be told apart by
# templateId. that mirrors how the matching rules for this section already
# discriminate (see specification/entry_match_rules.py, rules 2-5), so the two
# halves of the pipeline agree on what an entry **is**

# a substanceAdministration bearing either immunization template is a vaccine;
# the Planned variant (22.4.120) is IG-recommended for this section and the
# event-mood one (22.4.52) is the discouraged-but-permitted fallback the
# matching rules also accept
_IMMUNIZATION_TEMPLATES: tuple[str, ...] = (
    PLANNED_IMMUNIZATION_ACTIVITY,
    IMMUNIZATION_ACTIVITY_V3,
)


def _is_planned_immunization(anchor: _Element) -> bool:
    """
    Return True if a `<substanceAdministration>` is a vaccine, not a drug.
    """

    return any(
        template.get("root") in _IMMUNIZATION_TEMPLATES
        for template in anchor.findall("hl7:templateId", HL7_NS)
    )


def _entry_kind_block(
    anchors: list[_Element],
    *,
    fields: list[FieldSpec],
    caption: str,
) -> Block:
    """
    Build the captioned block for one Plan of Treatment entry kind.

    The caller skips empty kinds before calling, so this always builds a
    block (one row per anchor).
    """

    return Block(
        context={},
        columns=[spec.label for spec in fields],
        rows=[
            DetailRow(
                source=anchor,
                values=extract_fields(anchor, fields),
                negated=anchor.get("negationInd") == "true",
            )
            for anchor in anchors
        ],
        caption=caption,
    )


def reconstruct_plan_of_treatment(section: _Element) -> list[Block]:
    """
    Reconstruct the Plan of Treatment section as one block per entry kind.

    HETEROGENEOUS section: entries are grouped by the clinical statement
    they are, each kind rendering as its own captioned table with its own
    columns. Blocks come out in the spreadsheet's order (observation,
    procedure, act, medication, immunization) rather than document order,
    so like sits with like.

    Args:
        section: The post-prune, post-enrich Plan of Treatment <section>.

    Returns:
        One Block per entry kind that has surviving entries.
    """

    # a substanceAdministration carrying **neither** immunization template is read
    # as a medication rather than dropped: its field map is the generic
    # substanceAdministration shape, and an entry that survived pruning with no
    # narrative row would make the section's typeCode="DRIV" a lie
    immunizations: list[_Element] = []
    medications: list[_Element] = []
    for anchor in section.findall("hl7:entry/hl7:substanceAdministration", HL7_NS):
        target = immunizations if _is_planned_immunization(anchor) else medications
        target.append(anchor)

    # (anchors, field map, caption) per entry kind, in spreadsheet order. the
    # grouping is by element name, except substanceAdministration — one element
    # serving two kinds — which was split by templateId above
    kinds: list[tuple[list[_Element], list[FieldSpec], str]] = [
        (
            section.findall("hl7:entry/hl7:observation", HL7_NS),
            PLANNED_OBSERVATION_FIELDS,
            "Planned Observations",
        ),
        (
            section.findall("hl7:entry/hl7:procedure", HL7_NS),
            PLANNED_PROCEDURE_FIELDS,
            "Planned Procedures",
        ),
        (
            section.findall("hl7:entry/hl7:act", HL7_NS),
            PLANNED_ACT_FIELDS,
            "Planned Activities",
        ),
        (medications, PLANNED_MEDICATION_FIELDS, "Planned Medications"),
        (immunizations, PLANNED_IMMUNIZATION_FIELDS, "Planned Immunizations"),
    ]

    # a kind with no surviving entries contributes no table
    return [
        _entry_kind_block(anchors, fields=fields, caption=caption)
        for anchors, fields, caption in kinds
        if anchors
    ]


# NOTE:
# LAYER 3 — THE GENERIC FALLBACK
# =============================================================================
# a per-section reconstructor knows one shape. It anchors on the arrangement
# the IG describes -- Results on `entry/organizer`, Problems on `entry/act` --
# and an entry arranged differently produces no row, even though it matched
# and survived pruning. That is not hypothetical: a Problem Observation under a
# non-SUBJ entryRelationship, or a Result Observation sitting directly under
# `<entry>` with no organizer, both match, both survive, and both render
# nothing.
#
# Silently is the problem. The section still reports "reconstructed", every
# surviving entry is still stamped typeCode="DRIV" -- the document asserting
# its narrative is derived from and clinically equivalent to those entries --
# and one of them is missing from the narrative entirely. The assertion
# becomes false and nothing says so.
#
# So the fallback is not a separate path taken when reconstruction "fails". It
# runs after every reconstruction, over whatever entries the section's own
# reconstructor did not represent, and renders them in reduced form: the
# concept, when it happened, its status. Enough for a reviewer to see that
# something is there and what it is. The block is captioned, and the section's
# provenance footnote reports that it happened, so a narrative that looks thin
# says why rather than leaving the reader to wonder.

_GENERIC_CAPTION: str = (
    "Additional entries — shown in reduced form; "
    "full reconstruction unavailable for this structure"
)

# where a clinical statement carries the concept that names it, in the order
# worth trying. `code` covers observations, acts and procedures; `value` covers
# an assertion-coded observation whose meaning is in the value; the
# manufacturedMaterial path covers substanceAdministration, which carries no
# code of its own. This is a renderer rather than a FieldSpec fallback chain
# because FieldSpec deliberately allows exactly ONE alternative -- a field
# wanting three is a field that wants its own function
_GENERIC_CONCEPT_XPATHS: tuple[str, ...] = (
    "hl7:code",
    "hl7:value",
    "hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:code",
)


def render_entry_concept(statement: _Element) -> str:
    """
    Render the concept that identifies an arbitrary clinical statement.

    Tries the locations a CDA clinical statement puts its identifying concept,
    in order, and returns the first that resolves to anything. Used only by the
    generic fallback, which by definition does not know what kind of statement
    it is looking at.

    Args:
        statement: The clinical statement element (the child of `<entry>`).

    Returns:
        The rendered concept, or "" when none of the locations resolve.
    """

    for xpath in _GENERIC_CONCEPT_XPATHS:
        element = statement.find(xpath, HL7_NS)
        if element is not None and (rendered := render_coded_concept(element)):
            return rendered
    return ""


# the concept column is deliberately NOT a FieldSpec: it comes from
# render_entry_concept's location search, not from a single xpath, and a spec
# with an empty xpath would be a lie in the field-map data
_GENERIC_ITEM_COLUMN: str = "Item"

GENERIC_FIELDS: list[FieldSpec] = [
    FieldSpec("Date", "hl7:effectiveTime", "typed"),
    FieldSpec("Status", "hl7:statusCode/@code", "attr"),
]

_GENERIC_COLUMNS: list[str] = [
    _GENERIC_ITEM_COLUMN,
    *(spec.label for spec in GENERIC_FIELDS),
]


def _entry_statement(entry: _Element) -> _Element | None:
    """
    Return the clinical statement an `<entry>` wraps, or None if it wraps none.
    """

    return next((child for child in entry if isinstance(child.tag, str)), None)


def _unrepresented_statements(section: _Element, blocks: list[Block]) -> list[_Element]:
    """
    Return the clinical statements no reconstructed row already covers.

    Identity is compared by tree path rather than by object: lxml builds
    element proxies on demand, so two lookups of the same node can hand back
    different Python objects and `id()`/`is` are not dependable across them.
    `getpath` is derived from the node's position, so it is stable.

    An entry counts as represented when a row's source is the entry's own
    statement OR anything beneath it -- the join sections anchor their rows on
    child observations, not on the entry.

    Args:
        section: The post-prune section.
        blocks: The blocks the section's own reconstructor produced.

    Returns:
        One statement element per unrepresented entry, in document order.
    """

    tree = section.getroottree()
    represented = {tree.getpath(row.source) for block in blocks for row in block.rows}

    unrepresented: list[_Element] = []
    for entry in section.findall("hl7:entry", HL7_NS):
        statement = _entry_statement(entry)
        if statement is None:
            continue
        prefix = tree.getpath(entry) + "/"
        if any(path.startswith(prefix) for path in represented):
            continue
        unrepresented.append(statement)
    return unrepresented


def _generic_block(statements: list[_Element]) -> Block:
    """
    Build the captioned reduced-form block for unrepresented statements.
    """

    rows = [
        DetailRow(
            source=statement,
            values={_GENERIC_ITEM_COLUMN: render_entry_concept(statement)}
            | extract_fields(statement, GENERIC_FIELDS),
            negated=statement.get("negationInd") == "true",
        )
        for statement in statements
    ]
    return Block(
        context={},
        columns=_GENERIC_COLUMNS,
        rows=rows,
        caption=_GENERIC_CAPTION,
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
    ReconstructableSection.PLAN_OF_TREATMENT.value: reconstruct_plan_of_treatment,
}

type NarrativeReconstructionFallback = Literal[
    "no_matching_entries", "reconstruction_unavailable"
]


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
) -> ReconstructedNarrative | NarrativeReconstructionFallback:
    """
    Reconstruct a section's narrative <text> from its surviving entries.

    Dispatches on the section's LOINC code, then sweeps up whatever the
    dispatched reconstructor did not cover into a captioned reduced-form
    block (see LAYER 3 above), so every surviving entry is represented.

    Returns a `ReconstructedNarrative` carrying the detached, namespace-
    qualified <text> and how many entries needed the reduced form, or a
    fallback literal when the section has no registered reconstructor or
    nothing survived to reconstruct at all.

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
        A `ReconstructedNarrative`, or a fallback literal.
    """

    loinc_codes = section.xpath("hl7:code/@code", namespaces=HL7_NS)
    loinc = (
        str(loinc_codes[0]) if isinstance(loinc_codes, list) and loinc_codes else None
    )

    reconstruct = SECTION_RECONSTRUCTORS.get(loinc) if loinc else None
    if reconstruct is None or loinc is None:
        return "reconstruction_unavailable"

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

    if not any(block.rows for block in blocks):
        return "no_matching_entries"

    _strip_row_references(section)
    _mark_entries_derived(section)
    return ReconstructedNarrative(
        text=render_section_text(
            blocks, loinc=loinc, augmentation_timestamp=augmentation_timestamp
        ),
        reduced_entry_count=len(reduced),
    )
