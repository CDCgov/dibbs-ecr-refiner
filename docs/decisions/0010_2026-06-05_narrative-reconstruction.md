# 10. narrative reconstruction

Date: 2026-06-05

## Status

Proposed

## Context and Problem Statement

The refiner prunes a section's `<entry>` content down to the clinical data
relevant to a jurisdiction's configured condition. When a section's action is
`refine`, the surviving entries remain, but the human-readable narrative
(`<text>`) is unchanged: it was authored by the source EHR against the _full_
entry set, so it can describe clinical facts that pruning has since removed.
Today the `refine` path can only `retain` that stale narrative or `remove` it
entirely. We want a third option--reconstruct a narrative that reflects only
what survived--starting with the four sections mapped in
`refiner_narrative.xlsx`: Results, Problems, Medications, Immunizations.

> [!NOTE]
> The `refiner_narrative.xlsx` is a document that Tim at APHL put together when evaluating a previous attempt at narrative reconstruction that did not pass the CDA R2 XSD validation. Therefore, we disconnected that as a section processing instruction until we could dedicate the time required to do this narrative reconstruction correctly.

The decision this ADR records is **not** "should we reconstruct." It is "how
should the per-section extraction knowledge be represented," because that
representation choice is what either lays groundwork for the planned
template-aware matching engine or paints us into a corner. A secondary
constraint: do this without refactoring the matching engine, which is not yet
ready to be replaced.

Two facts about CDA shape this problem and are worth stating up front, because
the wrong mental model leads to the wrong architecture:

1. **An `<entry>` is a containment wrapper, not a clinical assertion.** In the
   CDA R2 clinical-statement model, meaning is carried by the statements --
   `observation`, `substanceAdministration`, `act`, `organizer`--wired
   together by `entryRelationship` / `component`. The `<entry>` itself has a
   `typeCode` and no clinical content. We match on entries because they are a
   structurally convenient unit for breaking up a `<section>`, not because they
   are the unit a consumer reads.

2. **A "row" a consumer reads is a projection, not a partition.** It frequently
   reaches _up_ to an ancestor and _sideways_ to a sibling. A single Results
   row pulls its panel code from the enclosing `organizer`, its specimen from a
   sibling `procedure`, and its test/value/date from the `observation` itself.
   The row inherits ancestor context and borrows sibling context; you cannot
   cut it out as a clean subtree.

These two facts mean the row is the _clinically_ meaningful unit but the tree
is what must be carried through pruning (so shared context survives) and emitted
(so output stays Schematron-valid--a bare Problem Observation or lone result
`observation` is not a valid section entry on its own). Decision granularity and
emission granularity differ.

## Decision Drivers

- Land the feature for the four target sections with CDA-correct output.
- DRY-enough: share the genuinely shared mechanical work; do not force-share
  divergent structural work.
- YAGNI: do not formalize an abstraction on too-thin evidence. We have four
  sections, half of them structurally flat--a poor base for generalizing.
- Functional design: data records and free functions; avoid class hierarchies
  and over-abstraction.
- Foundation: maximize reuse into the future template-aware matching engine
  _without_ pre-building it.
- No matching-engine refactor now.
- Provenance honesty: a reconstructed narrative is machine-derived, not
  clinician-attested, and must be marked as such.

A note on the seam, which is a sub-decision driven by the same drivers.
Reconstruction must read the **post-prune, post-enrich** section. Capturing a
row during the match loop is too early for two reasons: container-pruned
sections (Results, Vital Signs) have not yet had non-matching panels removed,
so a match-time row would include content about to be deleted; and stashing
lxml element references to re-read later runs into proxy `id()` instability
across `.iter()` reaccess. The correct seam is the surviving-entry walk that
`_inject_entry_match_comments` already performs--a sibling of comment
injection, extracting string values immediately rather than threading element
handles through matching.

## Considered Options

### Option A--Four hardcoded extractor functions

Each section gets a function that walks the tree with inline XPath and returns
rows to a shared table renderer. The xlsx stays as documentation.

- Pro: maximally functional, zero abstraction, YAGNI-pure.
- Pro: easy to read each function in isolation.
- Con: lays no foundation. The extraction knowledge lives in imperative code,
  not inspectable data, so the future template engine re-derives all of it.
- Con: cannot actually stay pure--the typed-value rendering (ST/CD/PQ/IVL_TS/
  PIVL_TS) is needed by every function, so A is really "A plus a shared value
  renderer" by the second function anyway.

### Option B--One uniform declarative map + one generic engine

Every section becomes data: a row anchor plus a field list, interpreted by a
single `reconstruct(section, field_map)`.

- Pro: maximally DRY. The maps are exactly the inspectable template-foundation
  we want.
- Con: over-DRY. To cover all four sections, the map must express "relative to
  the row," "relative to the ancestor organizer," "relative to a sibling
  procedure reached by _this_ path," xsi:type discrimination, and repetition.
  That is four orthogonal concepts in the data--a small query language.
  Reading the map back becomes harder than reading a function.
- Con: the join vocabulary would be designed against four examples (two of them
  flat, with no join at all), which is the weakest possible evidence base.

### Option C--Declarative field maps (data) + thin per-section joins (code)

The fields _within a single clinical statement_ are data (label ->
relative-xpath -> kind). The _projection_--what counts as a row, and what
context to reach up/sideways for--is a short per-section function that
delegates field extraction and value rendering to shared helpers.

- Pro: draws the DRY line at the honest seam. Shared, closed-set mechanical
  work is written once; open-ended structural work stays explicit and readable.
- Pro: the field maps are the foundation down payment. Keyed by `template_id`
  (already accumulating on `EntryMatchRule`), they migrate into the
  template-aware engine's declared field/code locations unchanged.
- Pro: each per-section join is the written specification of that template's
  context-preservation rule. Results' "prune to matched sibling observations"
  and Medications' "preserve the whole graph" are the two ends of the single
  context axis that `preserve_whole_entry` / `prune_container_xpath` will
  eventually collapse into. The join code is not throwaway--it is the
  research that tells the template-aware engine what its context rule must say.
- Con: slightly more moving parts than A (maps + functions vs functions alone).
- Con: requires discipline to keep the join in code and resist letting it drift
  into the data (which would silently rebuild B).

### Option D--Build the template-driven model now

Start the template-aware engine early: a registry where templates declare code
locations, field locations, context rules, and CONF citations; reconstruction
reads from it.

- Pro: one model to rule both matching and reconstruction.
- Con: premature. The model would be designed with only reconstruction's
  requirements visible and matching's requirements absent, then need
  reconciliation when matching finally adopts it. Foundation built blind to
  half its consumers is built wrong.

## Decision Outcome

Based on the above **Option C** seems like the best path forward at this point.

Absent the foundation driver, A would be the YAGNI pick. _With_ the foundation
driver, C dominates A because C is essentially "A, but lift the flat fields
into data"--low marginal cost, and it is the exact down payment A discards. C
beats B because the four sections do not fit one format cleanly: half are flat
reads and half are joins, so forcing a uniform map pushes join-and-
discrimination logic into a DSL that reads worse than code. C avoids D's
premature-model trap by deferring the unified model until matching's
requirements are also on the table.

The architecture is three layers:

1. **Shared primitives (written once).** A typed-value renderer
   (`element -> display string`, branching over the closed CDA data-type set),
   a field extractor driven by a field map, and a CDA narrative-`<table>`
   builder. These know nothing about any section. The typed-value renderer is
   the highest-leverage primitive: it is grounded in the CDA R2 abstract data
   types, every section uses it, and it is the same logic the displayName
   enrichment performs by hand today--the piece most likely to be reused by
   matching when the template-aware engine lands.

2. **Field maps (data).** Per-statement lists of `(label, relative-xpath,
kind)`, keyed by `template_id`. No joins, no xsi:type--just reads against
   one anchor element. This is the part `refiner_narrative.xlsx` already pins
   down and the part that folds into the template-aware engine unchanged.

3. **Per-section joins (code).** Short functions owning the structural quirks:
   the row anchor and the ancestor/sibling context joins. Two of the four are
   one-liners (Medications, Immunizations: row == the `substanceAdministration`,
   no join); two are short folds (Problems: two-level; Results: three-level
   with a sibling reach).

Sections relate by **convention, not container**: a flat `LOINC -> function`
dispatch dict, not a registry object or a base class. Adding a section later is
"one field map + one function + one dict entry," and it should touch no Layer 1
primitive. That is the extensibility test.

The provenance marker lives at the **block level**--one machine-derived
annotation on the reconstructed `<text>`, not a flag smeared across fields.
This is the seam that later grows into structured `<author>` participation
metadata, consistent with the existing per-entry comment prototype.

**What we explicitly defer:** join-as-data (B's move), the registry / unified
template model (the template-aware engine), template-keyed _matching_ (matching
keeps running untouched), and the CONF-carrying template objects. These wait
until the harder sections (Social History, Plan of Treatment) are surveyed and
matching's needs are visible. When the join's shape reveals itself across more
sections, the field maps locked in now slot into that future model unchanged.

### How the toy demonstrated this

A runnable toy reconstructs Results and Medications
from a tiny eICR fragment. It made the abstract argument concrete:

<details>
  <summary>
    📝 Expand to view Python example
  </summary>

```python
from typing import NamedTuple

from lxml import etree
from lxml.etree import _Element

# NOTE:
# NAMESPACES
# =============================================================================

HL7 = "urn:hl7-org:v3"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
NS = {"hl7": HL7, "xsi": XSI}


# NOTE:
# LAYER 1 -- SHARED PRIMITIVE: typed-value renderer
# =============================================================================
# this is the highest-leverage primitive; CDA data types are a CLOSED set,
# so all the "render a value element to a string" branching lives HERE, in
# one place. The field maps below never mention xsi:type--they just say
# "this field is a typed value" and hand the element to this function
#
# note the two flavours of polymorphism it absorbs:
#   -- <value xsi:type="PQ"/> is polymorphic: the type rides on xsi:type
#   -- <doseQuantity value= unit=/> is monomorphic: it is PQ by the CDA model,
#      with no xsi:type at all. We handle both without the field map caring


def render_typed_value(el: _Element | None) -> str:
    if el is None:
        return ""

    xsi_type = el.get(f"{{{XSI}}}type")

    # coded value (CD)--e.g. a coded lab result, a coded problem
    if xsi_type == "CD" or (xsi_type is None and el.get("code")):
        disp, code = el.get("displayName"), el.get("code")
        if disp and code:
            return f"{disp} ({code})"
        return disp or code or ""

    # physical quantity (PQ)--declared via xsi:type, **or** monomorphic
    # elements that are PQ by the model (doseQuantity, etc)
    if xsi_type == "PQ" or (xsi_type is None and el.get("unit") is not None):
        val, unit = el.get("value"), el.get("unit")
        return f"{val} {unit}".strip() if val else ""

    # simple text (ST)
    if xsi_type == "ST":
        return (el.text or "").strip()

    # interval of time (IVL_TS)--low/high children
    low, high = el.find("hl7:low", NS), el.find("hl7:high", NS)
    if low is not None or high is not None:
        lo = low.get("value") if low is not None else None
        hi = high.get("value") if high is not None else None
        if lo and hi:
            return f"{lo} to {hi}"
        return lo or hi or ""

    # periodic interval (PIVL_TS)--frequency
    period = el.find("hl7:period", NS)
    if period is not None:
        return f"every {period.get('value')} {period.get('unit')}".strip()

    # bare timestamp / value, or text
    return el.get("value") or (el.text or "").strip()


# NOTE:
# LAYER 1 -- SHARED PRIMITIVE: field extractor + the field-spec record
# =============================================================================
# FieldSpec is a record (NamedTuple), **note** a behaviour-bearing class; this is
# the "data record yes, extractor class hierarchy no" line. it carries no
# logic--it is a typed tuple the extractor interprets
#
# `kind` tells the extractor how to stringify whatever the xpath lands on:
#   "attr"  -> xpath ends at an attribute; lxml returns the string directly
#   "typed" -> xpath ends at an element; hand it to render_typed_value
#   "text"  -> xpath ends at an element; take its text content


class FieldSpec(NamedTuple):
    label: str  # becomes the column header
    xpath: str  # **relative** to the anchor element passed to extract_fields
    kind: str  # "attr" | "typed" | "text"


def extract_fields(
    anchor: _Element, field_map: list[FieldSpec]
) -> dict[str, str]:
    """
    Read a flat list of fields off ONE anchor element. No joining here--
    every xpath is relative to `anchor`. This is reused at every structural
    level by the join functions (organizer, procedure, observation all flow
    through this same call).
    """

    row: dict[str, str] = {}
    for spec in field_map:
        results = anchor.xpath(spec.xpath, namespaces=NS)
        if not results:
            row[spec.label] = ""
            continue

        first = results[0]
        if spec.kind == "attr":
            row[spec.label] = str(first)
        elif spec.kind == "typed":
            row[spec.label] = render_typed_value(first)
        elif spec.kind == "text":
            row[spec.label] = (first.text or "").strip()
        else:
            row[spec.label] = ""
    return row


# NOTE:
# LAYER 1 -- SHARED PRIMITIVE: CDA narrative table builder
# =============================================================================
# builds a CDA narrative block <text><table>...</table></text>; both sections
# (and the existing clinical-data table writer) want this same machinery, so
# it lives once here. the block-level "machine-derived" marker goes **here**,
# on the whole block--not smeared across individual fields. this is the seam
# that later grows into the <author> participation provenance


def build_table(columns: list[str], rows: list[dict[str, str]]) -> _Element:
    text = etree.Element(f"{{{HL7}}}text")
    text.append(
        etree.Comment(
            " Narrative reconstructed by eCR Refiner from surviving clinical "
            "entries: machine-derived, not clinician-attested. "
            "(XML comments cannot contain a double dash, so this marker "
            "avoids one.) "
        )
    )

    table = etree.SubElement(text, f"{{{HL7}}}table", border="1")

    thead = etree.SubElement(table, f"{{{HL7}}}thead")
    htr = etree.SubElement(thead, f"{{{HL7}}}tr")
    for col in columns:
        th = etree.SubElement(htr, f"{{{HL7}}}th")
        th.text = col

    tbody = etree.SubElement(table, f"{{{HL7}}}tbody")
    for row in rows:
        tr = etree.SubElement(tbody, f"{{{HL7}}}tr")
        for col in columns:
            td = etree.SubElement(tr, f"{{{HL7}}}td")
            td.text = row.get(col, "") or ""

    return text


# NOTE:
# LAYER 2 -- DATA: field maps (the part the xlsx already pins down)
# =============================================================================
# each map is "given **this** anchor element, here are its fields." in the real
# thing these would be keyed by templateId so they slot into the future
# template engine unchanged. Note none of them mention joins or xsi:type

# anchor: <substanceAdministration>
MEDICATION_FIELDS: list[FieldSpec] = [
    FieldSpec(
        "Medication",
        "hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:code/@displayName",
        "attr",
    ),
    FieldSpec(
        "Code",
        "hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:code/@code",
        "attr",
    ),
    FieldSpec("Status", "hl7:statusCode/@code", "attr"),
    FieldSpec("Period", "hl7:effectiveTime", "typed"),  # IVL_TS low/high
    FieldSpec("Dose", "hl7:doseQuantity", "typed"),  # monomorphic PQ
    FieldSpec("Route", "hl7:routeCode/@displayName", "attr"),
]

# anchor: <organizer>  (the panel context, reached UP to from each result row)
PANEL_FIELDS: list[FieldSpec] = [
    FieldSpec("Panel", "hl7:code/@displayName", "attr"),
]

# anchor: <procedure>  (the specimen context, reached SIDEWAYS via a sibling)
SPECIMEN_FIELDS: list[FieldSpec] = [
    FieldSpec(
        "Specimen",
        "hl7:participant/hl7:participantRole/hl7:playingEntity/hl7:code/@displayName",
        "attr",
    ),
]

# anchor: <observation>  (the result row's OWN fields)
RESULT_FIELDS: list[FieldSpec] = [
    FieldSpec("Test", "hl7:code/@displayName", "attr"),
    FieldSpec("Result", "hl7:value", "typed"),  # PQ or CD -- renderer decides
    FieldSpec("Interpretation", "hl7:interpretationCode/@code", "attr"),
    FieldSpec("Date", "hl7:effectiveTime/@value", "attr"),
]


# NOTE:
# LAYER 3 -- PER-SECTION JOINS (the part we keep as code)
# =============================================================================


def reconstruct_medications(
    section: _Element,
) -> tuple[list[str], list[dict[str, str]]]:
    """
    FLAT section: row == the substanceAdministration. No join. The whole
    function is "find the row anchors, extract each one's fields." This is
    why a join FORMAT would be overkill for half our sections -- there is
    nothing to join.
    """

    columns = [f.label for f in MEDICATION_FIELDS]
    rows = [
        extract_fields(sbadm, MEDICATION_FIELDS)
        for sbadm in section.xpath(
            "hl7:entry/hl7:substanceAdministration", namespaces=NS
        )
    ]
    return columns, rows


def reconstruct_results(
    section: _Element,
) -> tuple[list[str], list[dict[str, str]]]:
    """
    JOIN section: row == each result observation, but a complete row needs
    context from two other structural levels:
      -- the PANEL, reached UP to the enclosing organizer
      -- the SPECIMEN, reached SIDEWAYS to a sibling procedure
    Each level flows through the SAME extract_fields primitive against its
    own field map. The merge at the bottom IS the join -- that one line is
    exactly the thing we are choosing not to express as data yet.
    """

    columns = ["Panel", "Specimen"] + [f.label for f in RESULT_FIELDS]
    rows: list[dict[str, str]] = []

    for organizer in section.xpath("hl7:entry/hl7:organizer", namespaces=NS):
        panel = extract_fields(organizer, PANEL_FIELDS)  # reach UP

        procedure = organizer.find("hl7:component/hl7:procedure", NS)
        specimen = (
            extract_fields(procedure, SPECIMEN_FIELDS)  # reach SIDEWAYS
            if procedure is not None
            else {"Specimen": ""}
        )

        for obs in organizer.xpath(
            "hl7:component/hl7:observation", namespaces=NS
        ):
            result = extract_fields(obs, RESULT_FIELDS)  # the row's own fields
            rows.append({**panel, **specimen, **result})  # <-- THE JOIN

    return columns, rows


# NOTE:
# DISPATCH -- LOINC -> reconstruction function
# =============================================================================
# convention over container: a flat dict relates the per-section functions,
# rather than a registry object or a base class. Adding a section later is
# "write one field map + one function + one dict entry"

SECTION_RECONSTRUCTORS = {
    "30954-2": reconstruct_results,  # Results
    "10160-0": reconstruct_medications,  # Medications
}


def main() -> None:
    root = etree.fromstring(TOY_EICR.encode())

    for section in root.xpath("//hl7:section", namespaces=NS):
        loinc_codes = section.xpath("hl7:code/@code", namespaces=NS)
        loinc = loinc_codes[0] if loinc_codes else None

        reconstruct = SECTION_RECONSTRUCTORS.get(loinc)
        if reconstruct is None:
            continue

        columns, rows = reconstruct(section)
        text_block = build_table(columns, rows)

        print(f"\n=== Section {loinc} -> reconstructed narrative ===")
        print(etree.tostring(text_block, pretty_print=True).decode())


# NOTE:
# TOY DATA -- a tiny eICR fragment (post-prune, i.e. "what survived")
# =============================================================================

TOY_EICR = """\
<ClinicalDocument xmlns="urn:hl7-org:v3"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xmlns:sdtc="urn:hl7-org:sdtc">
 <component><structuredBody>

  <component>
   <section>
    <code code="30954-2" codeSystem="2.16.840.1.113883.6.1" displayName="Results"/>
    <title>Results</title>
    <text>...original clinician-attested narrative would be here...</text>
    <entry>
     <organizer classCode="BATTERY" moodCode="EVN">
      <code code="58410-2" codeSystem="2.16.840.1.113883.6.1" displayName="CBC panel"/>
      <component>
       <procedure classCode="PROC" moodCode="EVN">
        <participant typeCode="SBJ">
         <participantRole>
          <playingEntity>
           <code code="119297000" codeSystem="2.16.840.1.113883.6.96" displayName="Blood specimen"/>
          </playingEntity>
         </participantRole>
        </participant>
       </procedure>
      </component>
      <component>
       <observation classCode="OBS" moodCode="EVN">
        <code code="718-7" codeSystem="2.16.840.1.113883.6.1" displayName="Hemoglobin"/>
        <effectiveTime value="20240115"/>
        <value xsi:type="PQ" value="9.2" unit="g/dL"/>
        <interpretationCode code="L" codeSystem="2.16.840.1.113883.5.83"/>
       </observation>
      </component>
      <component>
       <observation classCode="OBS" moodCode="EVN">
        <code code="600-7" codeSystem="2.16.840.1.113883.6.1" displayName="Bacteria identified"/>
        <effectiveTime value="20240115"/>
        <value xsi:type="CD" code="112283007" codeSystem="2.16.840.1.113883.6.96" displayName="Escherichia coli"/>
       </observation>
      </component>
     </organizer>
    </entry>
   </section>
  </component>

  <component>
   <section>
    <code code="10160-0" codeSystem="2.16.840.1.113883.6.1" displayName="Medications"/>
    <title>Medications</title>
    <text>...original clinician-attested narrative would be here...</text>
    <entry>
     <substanceAdministration classCode="SBADM" moodCode="EVN">
      <statusCode code="completed"/>
      <effectiveTime xsi:type="IVL_TS">
       <low value="20240115"/>
       <high value="20240122"/>
      </effectiveTime>
      <routeCode code="C38288" codeSystem="2.16.840.1.113883.3.26.1.1" displayName="Oral"/>
      <doseQuantity value="1" unit="tablet"/>
      <consumable>
       <manufacturedProduct>
        <manufacturedMaterial>
         <code code="197361" codeSystem="2.16.840.1.113883.6.88" displayName="Amoxicillin 500 MG Oral Tablet"/>
        </manufacturedMaterial>
       </manufacturedProduct>
      </consumable>
     </substanceAdministration>
    </entry>
   </section>
  </component>

 </structuredBody></component>
</ClinicalDocument>
"""


if __name__ == "__main__":
    main()
```

</details>

- **The B-vs-C contrast is visible in code.** `reconstruct_medications` has no
  join to express (one `extract_fields` call); `reconstruct_results` reaches up
  to the organizer for the panel and sideways to the sibling procedure for the
  specimen, then merges. A join _format_ would be machinery serving nothing
  half the time.

- **The join is one line.** `{**panel, **specimen, **result}` is the entire
  section-specific structural decision; everything feeding it went through the
  same shared extractor against the same flat field-map shape. That one line is
  precisely what we are choosing not to turn into data yet.

- **The typed-value primitive earns its place.** The same field-map entry
  (`Result -> hl7:value, kind=typed`) rendered "9.2 g/dL" (a PQ) and
  "Escherichia coli (112283007)" (a CD) in two different rows, with the field
  map never mentioning xsi:type. Medications' "20240115 to 20240122" (IVL_TS)
  and "1 tablet" (a monomorphic PQ with no xsi:type) went through the same
  function. All discrimination stayed in one place.

- **Two CDA gotchas surfaced.** XML comment nodes cannot contain a double dash
  (`--`), so the block-level provenance marker must avoid one. And the standalone
  `ns0:` prefixing in the toy output is a serialization artifact of building the
  `<text>` in isolation--once inserted into a tree that declares
  `urn:hl7-org:v3` as the default namespace, the injected elements inherit it
  and serialize unprefixed. Worth confirming empirically when wiring in.

## Appendix

- Field source of truth: `refiner_narrative.xlsx` (Results, Problems,
  Medications Administered, immunizations).
- Spec correction found while sourcing the maps: the Problems sheet lists the
  problem code at `.../observation/value/code/@code`. Per the Problem
  Observation (V3) value constraint and worked examples in the eICR STU 3.1.1
  IG (Vol 2), the code is an attribute directly on the value element --
  `<value xsi:type="CD" code="..." codeSystem="..."/>`--so the correct path
  is `.../observation/value/@code` (and `.../value/@displayName`). Fix in the
  source of truth before any extractor reads it, or it silently yields empty
  cells.
- Open design questions deferred, not closed:
  - Coded-field humanizing: e.g. `interpretationCode/@code` renders as `L`
    rather than "Low" (HL7 ObservationInterpretation, OID
    2.16.840.1.113883.5.83). Several fields are codes that want display
    resolution; this is per-field policy the field map can carry once the
    pattern is clear.
  - Absence policy: a missing field currently renders as `""`. Empty string vs
    a "no information" marker vs dropping an all-empty column is a real choice,
    deferrable until a section needs it.
  - Dangling references: surviving entries may carry
    `entry/.../text/reference value="#..."` pointing into narrative anchors that
    reconstruction replaces. Reconstruction must either drop them or regenerate
    `<content ID>` anchors. Check against what the current `remove` path already
    does so behavior matches.
- Source materials: Keith Boone, _The CDA Book_ (clinical-statement model);
  eICR STU 1.1 IG (Vol 1 & 2); eICR STU 3.1.1 IG (Vol 2); RR STU 1.1 IG (Vol 2).

**Be sure to read the information about this in [CONTRIBUTING](https://github.com/CDCgov/dibbs-ecr-refiner/blob/main/CONTRIBUTING.md##Request-for-comment)**
