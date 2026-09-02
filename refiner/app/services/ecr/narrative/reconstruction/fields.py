from collections.abc import Callable
from typing import Literal, NamedTuple

from lxml.etree import _Element

from ...model import HL7_XSI_NS
from ...specification.template_oids import LABORATORY_RESULT_STATUS_ID
from .renderers import (
    _normalize,
    render_code_display,
    render_coded_concept,
    render_interpretation,
    render_performer,
    render_performer_org,
    render_typed_value,
)

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
# THE GENERIC FALLBACK'S FIELD MAP
# =============================================================================
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
