# 11. narrative reconstruction: real-data shape, per-organizer blocks, and entry linkage

Date: 2026-06-24

## Status

Proposed

Extends [10. narrative reconstruction](0010_2026-06-05_narrative-reconstruction.md).
That RFC chose the three-layer architecture (shared primitives + field-map data

- per-section join code) and shipped it for Results. It closed with three
  **deferred** questions in its appendix: coded-field display resolution, absence
  policy, and dangling references. This RFC resolves the first and third against
  real EHR data, and records the structural decisions needed to extend
  reconstruction to Problems, Medications, and Immunizations.

## Context and Problem Statement

RFC 0010 was sourced from `refiner_narrative.xlsx` and synthetic fixtures.
Before extending to three more sections we surveyed real EHR output (an Epic
Results section, `results.xml`, kept out of the repo) plus the pre-refined
narrative tables in `tests/fixtures/eicr_v1_1` and `eicr_v3_1_1`. Three findings
overturn assumptions the synthetic fixtures let us hold:

1. **Display names are usually not on `@displayName`.** In the Epic data the
   organizer and observation `<code>` elements carry **no** `displayName`
   attribute; the human label lives in `code/originalText` ("Stool Pathogens,
   NAAT, Parasite") and/or `code/translation/@displayName`. The xlsx paths
   (`.../code/@displayName`) and the current Layer-2 maps would render **blank**
   cells against this document. `originalText` also frequently contains a child
   `<reference value="#..."/>`, so the label is `originalText`'s `.text`, not its
   full string content, and values need whitespace normalization
   ("Not\n Detected").

2. **The pre-refined narrative is a per-panel block of several tables, not a
   flat grid.** Each Epic panel renders as a `<list>` item with a caption and up
   to four sub-tables (components / specimen / provider / performing org).
   Specimen is its own context block reached via the organizer's sibling
   `procedure` (`targetSiteCode` etc.), confirming the xlsx's three field-groups
   (Organizer / Procedure(specimen) / Observation) are the real structure.

3. **Replacing `<text>` dangles existing entry→narrative references.** The
   synthetic fixtures carry no `reference` links, so today's "replace the whole
   `<text>`" looks clean. Real Epic observations carry
   `text/reference/@value` and `code/originalText/reference/@value` pointing at
   narrative IDs. Reconstruction deletes those IDs and leaves the references
   dangling — a latent correctness bug the fixtures hide.

Meditech and Cerner samples were too malformed to design against; Epic is the
reference EHR for this work. The non-Epic robustness of the display resolver is
flagged but not validated here (see Deferred).

## Decision Drivers

- Carry RFC 0010's drivers forward unchanged: CDA-correct output, DRY-at-the-
  honest-seam, YAGNI-but-foundation, functional design, no matching-engine
  refactor, block-level provenance honesty.
- **Vendor neutrality.** Reconstruction must not encode one EHR's house style;
  it reflects surviving entries in a straightforward, convention-aligned shape.
- **Scale to heterogeneous sections.** The next sections after these four (Plan
  of Treatment, Social History) mix entry patterns. The representation must not
  require reconciling unlike patterns into one grid.
- **Linkage integrity.** A consumer must be able to tie each narrative row to
  the entry it came from, and reconstruction must not leave dangling references.

## Decisions

### D1 — Output shape: one self-contained block per grouping entry; never collapse unlike patterns

Each top-level grouping entry emits its **own self-contained block** inside the
section `<text>`:

- **Join sections** (Results: `entry/organizer`; Problems: `entry/act`) — a
  block per group: the group's context (panel/concern + specimen/target site)
  plus a detail table of its child observations.
- **Flat sections** (Medications, Immunizations: `entry/substanceAdministration`)
  — a single table, one row per entry. A homogeneous list is _not_ the
  collapsing we avoid; it shares one pattern.

The rule we are buying: **do not flatten a group's context+detail into
repeated-context rows, and do not force heterogeneous patterns into one grid.**
This supersedes the flat single-table currently emitted for Results (where panel
and specimen would repeat down every result row). It is what makes Plan of
Treatment tractable later: each planned-act pattern renders its own block by its
own field map, with nothing to reconcile.

### D2 — Synthesize from entries; do not preserve-and-prune the native narrative

We considered keeping the EHR's native `<text>` and pruning the rows whose
entries were removed, driven by the entry↔narrative links (maximum fidelity, no
display re-derivation). Rejected for v1:

- Reconstruction exists _because_ the source narrative is the stale story the
  EHR authored against the full entry set (RFC 0010); preserving it reintroduces
  exactly that distrust.
- The linkage it depends on is clean only in Epic.
- It requires surgically editing vendor-specific nested narrative HTML.

We synthesize a clean block per surviving group instead. A **hybrid** (prefer
native-prune when linkage is complete and well-formed, fall back to synthesize)
is a possible v2, deferred to avoid two code paths now.

### D3 — Code-display resolver as a mandatory Layer-1 primitive

Add `render_code_display(code_el) -> str` next to `render_typed_value`, with the
fallback chain learned from real data:

```
@displayName  →  originalText/text()  →  translation/@displayName  →  @code  →  ""
```

It strips a child `<reference>` from `originalText` (takes `.text`) and
normalizes whitespace. `render_typed_value`'s CD branch routes through it, and
its output becomes **display-only** — the trailing "(code)" suffix is dropped to
match every pre-refined narrative, which shows names, not codes. (Codes appear
only in the trigger-code machinery columns we do not reconstruct.) This closes
RFC 0010's deferred "coded-field humanizing" question and is the single change
most responsible for reconstruction working on real vendor output rather than
just fixtures.

### D4 — Generate our own row IDs and relink wholesale; accept that reconstruction now mutates entries

Closing RFC 0010's deferred "dangling references" question. On reconstruction:

1. **Strip** every now-dangling narrative `reference` off the surviving entries
   (wholesale, not hunted one by one — dodges the "did we catch them all?"
   footgun). Keep `originalText`'s text; remove only the `<reference>` child.
2. **Mint** deterministic, document-unique row IDs, namespaced like the existing
   footnote (`ecr-refiner-<loinc>-<run>-<n>`) and derived from the **same
   deterministic augmentation timestamp the footnote uses** (tests inject a fixed
   stamp) so snapshots stay stable and IDs cannot collide with untouched EHR IDs
   elsewhere in the document.
3. **Relink** one canonical reference per surviving observation at the **row
   level** (`<text><reference value="#rowId"/>`); we do not reproduce Epic's
   name-cell-granular linking.

We generate rather than preserve the EHR's IDs because original IDs are often
absent (so a generation path is needed regardless), and a single uniform path
beats a reuse-or-mint branch that must also interpret an EHR's multiple,
conflicting references. The honest tradeoff: generating means rewriting every
surviving entry's reference, so it is _more_ entry mutation, not less — the win
is uniformity and control. This **breaks `reconstruct_narrative`'s purity**: it
now mutates the entries it reads. Accepted — the pipeline mutates trees in place
anyway — but the function contract and the "does not mutate section" test change
to reflect it. Centralize the mutation in one assembler (D5) so per-section code
stays a pure projection.

### D5 — Keep the layering; evolve the contract to carry blocks + source handles

RFC 0010's three layers stand. The contract between Layer 3 and the renderer
changes so linkage and grouping have a home, and so mutation stays in one place:

- A `SectionReconstructor` returns `list[Block]` (one per grouping entry; flat
  sections return a single block), where a `Block` carries group context plus
  detail rows, and **each detail row retains a handle to its source element** so
  the assembler can relink it:

  ```python
  class DetailRow(NamedTuple):
      source: _Element            # the observation / substanceAdministration
      values: dict[str, str]      # column -> rendered value

  class Block(NamedTuple):
      context: dict[str, str]     # group-level fields (panel, concern, specimen)
      columns: list[str]          # detail-table headers
      rows: list[DetailRow]
  ```

- Per-section functions stay **pure projections**: walk the tree, call
  `extract_fields` against the field maps, return `Block`s. They hold element
  handles but never mutate.
- A single `render_section_text(blocks, *, loinc, run_id) -> _Element` does all
  rendering, ID minting, and relinking — the only place that mutates entries. It
  emits the block-level provenance marker once, then one rendered block per
  group (context lines/sub-table + detail `<table>` with minted row IDs).

The dispatch stays a flat `LOINC -> function` dict; adding a section remains "one
field map (or two) + one function + one dict entry," now plus a `Block` return
instead of `(columns, rows)`.

## Per-section composition

| Section       | Category | Group anchor → detail anchor                  | Context fields                           | Detail columns                                                     |
| ------------- | -------- | --------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------ |
| Results       | join     | `entry/organizer` → `component/observation`   | Panel · Date(s) · Specimen · Target Site | Test · Outcome · Interpretation · Date(s) _(+ Ref Range, stretch)_ |
| Problems      | join     | `entry/act` → `entryRelationship/observation` | Concern · Concern Status · Date(s)       | Problem Type · Problem · Date(s)                                   |
| Medications   | flat     | `entry/substanceAdministration`               | —                                        | Medication · Dose · Duration · Route                               |
| Immunizations | flat     | `entry/substanceAdministration`               | —                                        | Immunization · Date · Status                                       |

Notes carried from the survey: dates render via `typed` on the `effectiveTime`
_element_ (handles flat `@value`, IVL `low/high`, and PIVL uniformly), not `attr`
on `@value`; Problems collapses the xlsx's separate active/resolved dates into one
interval "Date(s)" cell to match convention; Medications/Immunizations drop the
xlsx fields absent from the narrative convention (status on meds; lot/manufacturer/
dose/route on immunizations — often `nullFlavor` anyway). Coded fields (Panel,
Test, Specimen, Medication, Immunization, Problem) all flow through
`render_code_display`.

## Implementation plan

1. **Layer 1 — `render_code_display`** + route `render_typed_value`'s CD branch
   through it and make it display-only. Update the affected unit tests
   (`test_render_cd_*`, `test_result_fields_use_typed_interpretation`).
2. **Layer 1/3 — block contract + assembler.** Add `DetailRow`/`Block`,
   `render_section_text` (rendering + minting + relinking), and the
   strip-dangling-references helper. Unit-test the assembler against a synthetic
   section: block grouping, minted-ID format/determinism, reference relink, and
   no-dangling invariant.
3. **Migrate Results** onto the block contract + the convention column changes
   (Outcome naming, code-display resolver, keep specimen + target site, add panel
   date). This is the regression canary — it churns the existing
   `covid_results_reconstruction` snapshot, which we re-baseline deliberately.
4. **Problems** (join), then **Medications** (flat), then **Immunizations**
   (flat): field map(s) + thin function + dispatch entry + unit tests. Uncomment
   the `ReconstructableSection` members and update the `test_service_policy.py`
   guard as each lands.
5. **Integration.** Parametrize the existing XSD/Schematron validity helper
   across all four LOINCs (do not copy it); assert the no-dangling-reference
   invariant on a document that _has_ references (the Epic shape, as a sanitized
   fixture); add snapshot scenarios beside `covid_results_reconstruction`.

## Deferred (not closed)

- **Hybrid preserve-and-prune** (D2) — revisit when a fidelity gap is felt and
  linkage reliability is better understood.
- **Non-Epic display-resolver robustness** — the `originalText`/`translation`
  fallback order is validated only against Epic; confirm when usable
  multi-vendor data exists.
- **Absence policy** (open since RFC 0010) — empty string vs a "no information"
  marker vs dropping an all-empty column.
- **Specimen cardinality** — treated as one-per-organizer context; revisit if
  multi-specimen panels appear.
- **Plan of Treatment / Social History** — the heterogeneous sections D1 is
  designed to absorb; surveyed separately before they are added.
- **`action="retain" + narrative="reconstruct"`** — still documented-invalid but
  unguarded; UI guard vs server coercion vs 422 unresolved.

## Post-review refinements (expert IG review, 2026-06-25)

Three items from an IG/CDA-Book expert review, all on the reconstruction path:

- **`entry/@typeCode="DRIV"`.** Reconstruction stamps every `<entry>` in a
  reconstructed section with `typeCode="DRIV"` ("narrative is derived from the
  entries"), overriding the schema default `COMP` carried over from the source.
  Retained author-attested narratives are untouched. (eICR Vol 2 "Narrative
  Text"; Boone, CDA Body chapter. Descriptive prose, no CONF#.)
- **Human-readable timestamps.** A shared `format_ts` renders HL7 TS values to
  `YYYY-MM-DD[ HH:MM[:SS]][ ±HH:MM]`, preserving source precision and presenting
  the offset as given (no timezone conversion). Consumed by `render_typed_value`
  so every section's date cells humanize; structured entry `@value`s are left
  raw. (eICR Vol 2 human-readable intent; Boone, narrative block.)
- **Mixed-content reference whitespace.** The minted `<text><reference/></text>`
  pointers must not carry surrounding whitespace (Boone, ch. 6). Pretty-printing
  the document indents them; `compact_reconstruction_references` (a post-format
  pass scoped to `#ecr-refiner-` ids, since the in-tree form is already compact
  and only the global pretty-print reintroduces whitespace) restores the compact
  form. Author-attested references are left untouched. (Note: the scenario
  snapshots re-pretty-print via `normalize_xml`, so they show the indented form;
  the raw product is compact, asserted in `test_explicit_assertions.py`.)
- **Surface code + system for clinical concepts.** HTML-only readers see the
  least reliable half (the locally-editable `displayName`) and have no path to
  the authoritative code. A new `"concept"` field kind renders clinical coded
  concepts as `displayName (System code)` via `render_coded_concept`; the system
  name comes from a vendored OID→name map (`CODE_SYSTEM_DISPLAY_NAMES` in
  `specification/constants.py`, e.g. "SNOMED CT", "RxNorm", "NCI Thesaurus"),
  resolved from the codeSystem OID rather than the unreliable codeSystemName.
  HL7 admin/status vocabularies (statusCode, interpretationCode, Problem Type)
  stay display-only (`"coded"` kind). `nullFlavor`/missing code → display-only,
  no empty parens. The narrative map is deliberately distinct from
  `CODE_SYSTEM_LABELS` (the terser match-comment labels) — different audience.

## Appendix

- Field source of truth: `refiner_narrative.xlsx` (Results, Problems, Medications
  Administered, immunizations), read as a directional guide and corrected against
  real data where it diverges (display-name location; Problems `value/@code` vs
  `value/code/@code`, per RFC 0010's appendix).
- Real-data reference: an Epic Results section (`results.xml`, intentionally not
  committed) and the pre-refined narrative tables under
  `tests/fixtures/eicr_v1_1` and `eicr_v3_1_1`.
- Tool identity is `ecr-refiner` / `eCR Refiner` throughout.

**Be sure to read the information about this in [CONTRIBUTING](https://github.com/CDCgov/dibbs-ecr-refiner/blob/main/CONTRIBUTING.md##Request-for-comment)**
