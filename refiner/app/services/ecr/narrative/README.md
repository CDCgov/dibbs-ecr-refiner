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

## Invariants

- **Namespace everything.** All emitted elements go through
  `_make_element` / `_sub_element`. A bare (unprefixed) element silently fails
  `NarrativeBlock.xsd` validation.
- **Respect the `xs:sequence`.** A `<text>` must sit after `<title>` (or
  `<code>`) in `StrucDoc.Section`. Insertion always goes through the placement
  helpers rather than a bare `append`.
- **These functions mutate the section in place.** Consistent with the rest of
  the `ecr` service; the pipeline owns parse/serialize.

## Planned: narrative reconstruction

A third narrative disposition — reconstruct the `<text>` from the entries that
survived refinement — will land here as a `reconstruction.py` peer of
`writers.py`, built on the same `elements.py` primitives. See
`docs/decisions/0010_2026-06-05_narrative-reconstruction.md` for the design
(typed-value renderer + per-`template_id` field maps + per-section joins).
