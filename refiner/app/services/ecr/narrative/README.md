# Section narrative writers

This package owns every transformation the refiner makes to a CDA
`<section>`'s human-readable narrative `<text>` element. A section's `<text>`
is what a reviewer sees when they open a refined eICR in a CDA stylesheet; the
machine-readable `<entry>` elements are handled elsewhere (the matching
engines). These writers decide what story the `<text>` tells about what the
refiner did.

## Why this is its own module

Everything that touches a section's `<text>` lives here so the narrative
behavior — and the CDA R2 validity rules it has to respect — can be reasoned
about in one place. The matching engines (`entry_matching`, `generic_matching`)
and the orchestrator (`refine.py`) call into this package; they never build
narrative elements directly.

## Layout

- **`elements.py`** — the shared low-level primitives. `_make_element` /
  `_sub_element` emit namespace-qualified elements (every node written into
  `<text>` must carry the `urn:hl7-org:v3` namespace or it fails
  `NarrativeBlock.xsd`). `_ensure_text_element` places a `<text>` in the
  correct CDA R2 `xs:sequence` slot. `remove_all_comments` scrubs stale source
  comments. Every other module here builds on these.

- **`footnote.py`** — the per-section provenance footnote. Refinement attaches
  an unanchored `<footnote>` to every section (refined, retained, removed, or
  narrative-stripped) carrying a one-row table: what the jurisdiction
  configured vs. what the refiner actually did. The footnote's `xs:ID` encodes
  the augmentation run's timestamp so a consumer can structurally tie every
  footnote to the document's augmentation header.

- **`writers.py`** — the narrative-body writers that replace or stub a
  section's `<text>`:
  - `replace_narrative_with_removal_notice` — strip the narrative to a notice
    while keeping clinical entries for machine processing.
  - `restore_narrative` — put back a saved `<text>` deep copy (the generic
    matching path clears `<text>` during processing to avoid false matches,
    then restores it).
  - `create_minimal_section` — reduce a section to a `nullFlavor="NI"` stub
    with a status message (no match found, or configured for removal).
  - `replace_narrative_with_reconstruction` — swap in a `<text>` rebuilt by
    `reconstruction/` from the surviving entries.

- **`identifiers.py`** — the `xs:ID` scheme shared by the footnote and the
  reconstructed rows (`ecr-refiner-{loinc}-{timestamp}`), plus the helper that
  compacts reconstruction references. Keeping it separate lets `footnote.py`
  and `reconstruction/` mint run-stamped IDs without depending on each other.

- **`reconstruction/`** — the third narrative disposition: rebuild a
  section's `<text>` from the entries that **survived** refinement, so the
  narrative reflects what the document still contains rather than the stale
  story the source EHR authored against the full entry set. A package, split
  along its layering — see below.

## Invariants

- **Namespace everything.** All emitted elements go through
  `_make_element` / `_sub_element`. A bare (unprefixed) element silently fails
  `NarrativeBlock.xsd` validation.
- **Respect the `xs:sequence`.** A `<text>` must sit after `<title>` (or
  `<code>`) in `StrucDoc.Section`. Insertion always goes through the placement
  helpers rather than a bare `append`.
- **These functions mutate the section in place.** Consistent with the rest of
  the `ecr` service; the pipeline owns parse/serialize.

## Narrative reconstruction

The package is split along the layering, one module per layer, and the
dependencies run one way (`renderers` <- `fields` <- `sections` -> `blocks`):

| module | holds | depends on |
|---|---|---|
| `renderers.py` | stringify ONE element: CDA data types, code-display fallback chains, timestamps, units, intervals | nothing in the package |
| `fields.py` | `FieldSpec`/`FieldSource`, the extractor, and every per-statement field map | `renderers` |
| `blocks.py` | `Block`/`DetailRow`, the table assembler, minted row IDs, and the entry mutations (`DRIV`, relinking) | nothing in the package |
| `sections.py` | the per-section joins and the generic fallback | `blocks`, `fields`, `renderers` |
| `__init__.py` | `SECTION_RECONSTRUCTORS`, `reconstruct_narrative`, and the package's public surface (`__all__`) | all of the above |

Adding a section stays "one field map + one join function + one dict entry" —
no Layer 1 primitive is touched.


When a section is configured `narrative="reconstruct"`, `reconstruction/`
rebuilds its `<text>` from the surviving `<entry>` elements instead of
retaining the source narrative. The guiding question is a content one: **can
this table be reproduced from just the `<entry>`s?** If a column cannot be
sourced from a surviving entry, it does not belong in the reconstruction — the
narrative must stay clinically equivalent to the structured data it is derived
from (the entries are stamped `typeCode="DRIV"` to assert exactly that).

Three layers, drawn at the honest DRY seam:

1. **Shared primitives** — the typed-value renderer (closed CDA data-type set:
   CD / PQ / ST / IVL / PIVL), the code-display fallback chain
   (`@displayName` → `<originalText>` → `<translation>` → bare `@code`, because
   real EHR data rarely puts the label on `@displayName`), the clinical
   concept renderer (`display (System code)`), the performer renderer
   (person-then-organization), and the block/table assembler. Section-agnostic,
   written once.
2. **Field maps** (data) — per-statement `(label, relative-xpath, kind)` lists.
   This is the layer the source spreadsheet (`.scratch/refiner-narrative.xlsx`)
   pins down: which attributes go in the table and why. The sheet is the
   correctness floor; a map may carry more than the sheet (e.g. Status and
   Performer on every Plan of Treatment table) as long as every column is
   reproducible from the entries.
3. **Per-section joins** (code) — the structural quirks: the row anchor plus
   the ancestor/sibling context a row reaches for.

Sections relate by convention, not container: a flat `LOINC → function`
dispatch dict. Adding a section is "one field map + one function + one dict
entry."

Reconstructable sections (`policy.ReconstructableSection`):

- **Results** (30954-2) and **Problems** (11450-4) — JOIN sections: one
  self-contained block per organizer / concern act, with a context table
  (panel / concern) above the detail rows. `StrucDoc.Td` permits no nested
  `<table>`, so the two are siblings in the markup; containment is carried by
  the detail table's `<caption>` (which names the parent panel) and an
  `xallIndent` `styleCode` marking it subordinate.
- **Immunizations** (11369-6) and **Medications Administered** (29549-3) —
  FLAT sections: a single table, one row per `substanceAdministration`.
- **Plan of Treatment** (18776-5) — the HETEROGENEOUS section: five unlike
  clinical statements (planned observation, procedure, act, medication,
  immunization) share one `<section>`. It emits one **captioned** table per
  entry kind rather than collapsing unlike patterns into a shared grid;
  `substanceAdministration` is split into medication vs immunization by
  templateId, mirroring how the section's match rules discriminate.

Reconstruction is the one narrative writer that MUTATES surviving entries: it
strips the now-dangling source references, relinks each entry to its minted
row, and stamps `typeCode="DRIV"`. It only runs on the refine path — a retained
section never reconstructs, and when nothing survived (or a section has no
registered reconstructor) it falls back to retaining the original narrative.

### The fallback when there is nothing to rebuild from

`reconstruct` falls back to **keep-on-match**, not to keeping the original.
When nothing in the section matched, every entry is pruned and the narrative
is replaced with the removal notice.

The reasoning is what the retained narrative would actually have contained.
Nothing matched, so all the entries are gone — and the source narrative still
describes every one of them, in full clinical prose. Keeping it ships exactly
the content the jurisdiction's configuration said should not be here, with the
structured entries stripped so a receiver cannot even process it. Choosing
`reconstruct` grants the refiner broad licence to rewrite the section;
keep-on-match is much closer to the spirit of that grant than handing back the
unrefined original.

One case still retains: **no registered reconstructor**, meaning
`narrative="reconstruct"` on a section outside `ReconstructableSection`. The
policy layer normally coerces that to `retain`, so it is a defensive branch.
It says so in the section footnote, including that the retained narrative may
describe entries the refinement removed.

### Entries the section reconstructor cannot cover

A per-section reconstructor knows one shape. `reconstruct_results` anchors on
`entry/organizer`, `reconstruct_problems` on `entry/act`. An entry arranged
differently — a Problem Observation under a non-`SUBJ` entryRelationship, a
Result Observation sitting directly under `<entry>` with no organizer — still
matches, still survives pruning, and produces no row.

Doing that silently is the problem, and the **partial** case is the dangerous
one: the section reports a clean `reconstructed`, every surviving entry is
stamped `typeCode="DRIV"` — the document asserting its narrative is derived
from and clinically equivalent to those entries — and one of them is missing
from the narrative entirely.

So reconstruction always ends with a sweep. Whatever the section's own
reconstructor did not represent goes into a captioned reduced-form block
(`_generic_block`): the concept, when it happened, its status. `Item` comes
from `render_entry_concept`, which searches the places a clinical statement
puts its identifying concept (`code`, `value`, then the substanceAdministration
`manufacturedMaterial/code`) — it is a renderer rather than a `FieldSpec`
because a field wanting three alternatives wants its own function.

`reconstruct_narrative` returns `ReconstructedNarrative(text,
reduced_entry_count)`. A non-zero count becomes
`SectionOutcome.REFINED_NARRATIVE_RECONSTRUCTED_REDUCED`, so a reviewer
looking at a thin table finds out why from the provenance footnote instead of
guessing. This is measured, not theoretical: across the five committed fixture
eICRs the sweep fires zero times, but both shapes above are constructible and
are pinned by tests.

Making the fallback *configurable* is still not built. It needs design work
(the narrative dropdown encodes one axis; a fallback is a second) and user
feedback we do not have. The default above is the one to argue from.

On house style: the reconstruction stays vendor-neutral — it does not encode
one EHR's stylesheet quirks ([see here](/docs/decisions/0011_2026-06-24_narrative-reconstruction-real-data-blocks-and-linkage.md)).
But "convention-aligned" leans toward the shape a PHA is used to reading, which
in practice means Epic (the long-run-consistent plurality of what flows through
AIMS). Taking inspiration from how Epic renders a section is fine where the
choice is otherwise free; hard-coding its house style is not.

See `docs/decisions/0010_2026-06-05_narrative-reconstruction.md` and
`0011_...` for the full design.
