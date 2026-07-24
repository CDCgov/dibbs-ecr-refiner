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
    `reconstruction.py` from the surviving entries.

- **`identifiers.py`** — the `xs:ID` scheme shared by the footnote and the
  reconstructed rows (`ecr-refiner-{loinc}-{timestamp}`), plus the helper that
  compacts reconstruction references. Keeping it separate lets `footnote.py`
  and `reconstruction.py` mint run-stamped IDs without depending on each other.

- **`reconstruction.py`** — the third narrative disposition: rebuild a
  section's `<text>` from the entries that **survived** refinement, so the
  narrative reflects what the document still contains rather than the stale
  story the source EHR authored against the full entry set. See below.

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

When a section is configured `narrative="reconstruct"`, `reconstruction.py`
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
  (panel / concern) above the detail rows.
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

On house style: the reconstruction stays vendor-neutral — it does not encode
one EHR's stylesheet quirks (see
`docs/decisions/0011_2026-06-24_narrative-reconstruction-real-data-blocks-and-linkage.md`).
But "convention-aligned" leans toward the shape a PHA is used to reading, which
in practice means Epic (the long-run-consistent plurality of what flows through
AIMS). Taking inspiration from how Epic renders a section is fine where the
choice is otherwise free; hard-coding its house style is not.

See `docs/decisions/0010_2026-06-05_narrative-reconstruction.md` and
`0011_...` for the full design.
