import re

from lxml.etree import _Element

from ...model import HL7_NS, HL7_XSI_NS
from ...specification.constants import (
    CODE_SYSTEM_DISPLAY_NAMES,
    OBSERVATION_INTERPRETATION_DISPLAY,
)

# NOTE:
# STRINGIFY ONE CDA ELEMENT FOR DISPLAY
# =============================================================================
# * layer 1: closed-set, section-agnostic mechanical work, written once. every
# function here takes an element (or None) and returns a string; none of them
# know what section they serve or what a table looks like. this module
# depends on nothing else in the package


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
# SHARED PRIMITIVE: arbitrary-statement concept resolver
# =============================================================================
# the generic fallback renders statements it cannot identify by template, so
# it needs a way to ask "what concept names this thing?" without knowing what
# kind of statement it is

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
