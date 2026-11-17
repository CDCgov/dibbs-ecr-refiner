# eCR Refiner -- Narrative Reconstruction Guide

Narrative reconstruction rebuilds a section's `<text>` from the `<entry>` elements that survived refinement, so the human-readable narrative describes what the document still contains rather than what the source EHR sent. Part 1 is the map: where the code lives, when it runs, what it touches, and how the calls chain. Part 2 is how to add a section. Design rationale is in [`narrative/README.md`](narrative/README.md) and ADRs [0010](/docs/decisions/0010_2026-06-05_narrative-reconstruction.md) and [0011](/docs/decisions/0011_2026-06-24_narrative-reconstruction-real-data-blocks-and-linkage.md).

## Where it lives

```
app/services/
├── pipeline.py                     calls refine_eicr
└── ecr/
    ├── policy.py                   ReconstructableSection, normalize_section_processing
    ├── refine.py                   refine_eicr (BRANCH 3), _interpret_run_result
    ├── section/
    │   ├── __init__.py             process_section: picks the matching engine
    │   ├── entry_matching.py       STEP 6: narrative disposition when matches were found
    │   ├── generic_matching.py     STEP 5: the same branch for the generic engine
    │   └── utils.py                resolve_no_match_section: when nothing matched
    └── narrative/
        ├── writers.py              replace_narrative_with_reconstruction
        └── reconstruction/
            ├── __init__.py         SECTION_RECONSTRUCTORS, reconstruct_narrative
            ├── sections.py         per-section joins + the reduced-form sweep
            ├── fields.py           FieldSpec maps + extract_fields
            ├── renderers.py        one element → one string
            └── blocks.py           Block/DetailRow, render_section_text, entry mutations
```

Two files outside `services/` are involved:

- `api/v1/configurations/sections.py` rejects invalid configurations on save.
- `api/validation/file_validation.py` calls `compact_reconstruction_references`. Pretty-printing the webapp's output for display breaks up the minted `<text><reference/></text>` pointers, and this collapses them again. Lambda output is never pretty-printed, so it needs no compaction.

## When it's in scope

Reconstruction runs only after every one of these gates passes, in this order:

| gate                                                  | enforced by                                                                                              | on failure                                                                                                     |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `narrative="reconstruct"` requires `action="refine"`  | API returns 400 on save; `normalize_section_processing` coerces to `retain` on clone and migration paths | never stored                                                                                                   |
| section is a `ReconstructableSection`                 | same two places (rule 5)                                                                                 | never stored                                                                                                   |
| `include=True`, not narrative-only, `action="refine"` | `refine_eicr` BRANCH 3                                                                                   | BRANCH 1, 2a or 2b handles it; reconstruction is never reached                                                 |
| a reconstructor is registered for the section's LOINC | `reconstruct_narrative` returns `None`                                                                   | matches found: original narrative retained (`reconstruct_unavailable`); no matches: removal notice (`removed`) |

The last gate is defensive; the first two should make it unreachable.

Five sections are reconstructable today: Results `30954-2`, Problems `11450-4`, Immunizations `11369-6`, Medications Administered `29549-3` and Plan of Treatment `18776-5`. All five have IG match rules in every supported eICR version, so in practice they always go through `entry_matching`; the generic engine's identical branch is only a fallback.

## What it touches

**It reads** the section _after_ pruning (STEP 3) and enrichment (STEP 4), so it sees only surviving entries, with their `@displayName`s already filled in -- that is why the tables show labels instead of bare codes.

**It writes** two things:

- the section's `<text>`, replaced wholesale.
- the surviving entries -- the only narrative writer that mutates them. It:
  - inlines `originalText` references
  - strips references into the old narrative
  - relinks each entry to its minted row (`#ecr-refiner-<loinc>-<ts>-rowN`)
  - stamps `typeCode="DRIV"`

**It does not** decide which entries survive (the matching engines do), write the provenance footnote (`refine_eicr` adds it afterwards, from the outcome), or touch the document header (`augment.py`).

One content rule governs every column: _can this be reproduced from just the surviving `<entry>`s?_ If not, it doesn't belong. `DRIV` asserts the narrative is derived from the entries, so anything else would make it false.

## How the calls chain

```
refine_eicr                                            refine.py
└─ process_section(narrative="reconstruct")            section/__init__.py
   └─ entry_matching.process                           section/entry_matching.py
      ├─ STEP 2  _find_matching_entries
      │    └─ nothing matched → resolve_no_match_section      section/utils.py
      │         prunes every entry, sets nullFlavor="NI", then calls ↓ over zero entries
      ├─ STEP 3  prune · STEP 4  enrich · STEP 5  match comments
      └─ STEP 6  reconstruct_narrative(section, augmentation_timestamp)
         │                                             reconstruction/__init__.py
         ├─ look up section/code/@code in SECTION_RECONSTRUCTORS
         ├─ _inline_original_text_references           blocks.py
         ├─ reconstruct_<section>(section) → list[Block]   sections.py
         │    └─ extract_fields(anchor, FIELD_MAP)     fields.py
         │         └─ _FIELD_RENDERERS[kind](element)  renderers.py
         ├─ _unrepresented_statements → _generic_block sections.py
         ├─ _strip_row_references · _mark_entries_derived   blocks.py
         └─ render_section_text(blocks, …)             blocks.py
              └─ for each row: mint an ID, write the <tr>, _relink_source
         → ReconstructedNarrative(text, reduced_entry_count)
      replace_narrative_with_reconstruction            writers.py
      → SectionRunResult(narrative_disposition=…)
_interpret_run_result → SectionOutcome → provenance footnote
```

Each layer hands the next a narrower kind of data; respect that seam when adding to it:

| layer                 | signature                                    | owns                                                                                                                                        |
| --------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| renderer              | `_Element → str`                             | CDA data types and display fallback chains; knows nothing about sections                                                                    |
| `extract_fields`      | `(anchor, list[FieldSpec]) → dict[str, str]` | reading a field map off one anchor; every xpath is relative to that anchor, with no joins                                                   |
| section reconstructor | `section → list[Block]`                      | structure: what anchors a row, and what context a row reaches up or sideways for. Pure: `DetailRow.source` keeps the entry handle for later |
| `render_section_text` | `list[Block] → <text>`                       | building the markup and relinking entries; the only place either happens                                                                    |

The reduced-form sweep (`_unrepresented_statements`) gives every surviving entry a row, including shapes the section reconstructor doesn't recognise; those land in a captioned generic block and are counted. The engine reports what it did, and `refine.py` names the result:

| `narrative_disposition`   | when                                                                                              | `SectionOutcome`                                    |
| ------------------------- | ------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `reconstructed`           | the section reconstructor covered every surviving entry                                           | `REFINED_NARRATIVE_RECONSTRUCTED`                   |
| `reconstructed_reduced`   | the sweep caught at least one entry                                                               | `REFINED_NARRATIVE_RECONSTRUCTED_REDUCED`           |
| `reconstructed_empty`     | nothing matched; the `<text>` is a `<paragraph>`, since CDA R2 can't express a table with no rows | `REFINED_NARRATIVE_RECONSTRUCTED_EMPTY`             |
| `reconstruct_unavailable` | no reconstructor is registered (defensive)                                                        | `REFINED_RECONSTRUCT_UNAVAILABLE_FALLBACK_RETAINED` |

---

# Adding a section

Going from a section that refines to one that also reconstructs is mostly reading -- the match rules, the sample data, the IG. The code at the end is usually small.

## The strategy

1. **Start from the match rules.** A section's `EntryMatchRule`s (`specification/entry_match_rules.py`) are the most precise statement of what can survive refinement. `code_xpath` names the clinical statement that identifies a row; `preserve_whole_entry` and `prune_container_guard_xpath` decide what surrounding context is still in the entry when reconstruction runs. Every shape the rules can keep needs an anchor in the reconstructor, or it falls into the sweep and the outcome reads `reconstructed_reduced`.
2. **Survey the sample data.** List the entry shapes in the committed fixtures (`tests/fixtures/ecr_pairs/`, `eicr_v1_1/`, `eicr_v3_1_1/`) -- root element, templateId, and what sits under `entryRelationship` or `component`. Write one synthetic fixture per shape in `tests/fixtures/sections/`, copying structure and templateIds but inventing every value. Production-derived documents never go in the repo.
3. **Grade each element against the IG.** Use Volume 2 of the eICR IG (STU 1.1 and STU 3.1.1), where every template's constraints carry a CONF number you can cite in a comment. The schematron in `tests/validation/` encodes the same SHALLs.
   - **SHALL** -- safe to build a column on; a conformant sender always populates it.
   - **SHOULD / MAY** -- fine as a column, but expect it missing. Give it a `FieldSpec.fallback` when conformant senders have a second place for the answer, and make sure an empty cell still reads correctly.
   - **Not in the IG** -- one sender's habit. Build for it only when real data shows it, and say so in a comment.
4. **Let the shape choose the join.** A new section is almost always one of three shapes:
   - **flat** -- the row _is_ the entry (`_reconstruct_flat`; Immunizations, Medications Administered).
   - **join** -- one block per grouping entry, with the group's own fields as a context table above the detail rows (Results: organizer → observations; Problems: concern act → observations).
   - **heterogeneous** -- unlike statements share the section, so each kind gets its own captioned table (Plan of Treatment).
5. **Copy the closest finished section, then check what each field _means_.** Two sections built from the same template can carry different clinical meaning in the same element. Write a new field map whenever a label would become wrong, even if every xpath is identical.
6. **Validate.** Unit-test the field map and join against the synthetic fixtures. Three tests loop over every `ReconstructableSection` and cover the new one automatically: `test_every_reconstructable_section_has_a_reconstructor`, `test_every_reconstructable_section_has_entry_match_rules` and `test_every_reconstructable_section_reconstructs_empty_on_no_match`. Finish with an integration scenario in `tests/integration/scenarios/`, which validates every refined document against CDA R2 XSD and schematron and fails on any error.

The code is usually three pieces: a field map in `fields.py`, a join function in `sections.py` (or a call to an existing helper), and an entry in both `ReconstructableSection` and `SECTION_RECONSTRUCTORS`.

## This worked

- **Treat APHL's field list as the floor, not the ceiling.** APHL gave us a spreadsheet listing the bare minimum fields each section has to display for reconstruction to count as working. Plan of Treatment shipped more (Status and Performer on every table) because each passes the content rule above.
- **Borrow content, not style, from familiar output.** Most public health reviewers are used to Epic's narratives, so where a choice is otherwise free, matching what Epic puts in a table lowers friction. Copying its markup or stylesheet quirks breaks for every other sender.
- **Extract a helper on the second identical section, not the first.** `_reconstruct_flat` appeared once Immunizations and Medications Administered turned out to share a shape; earlier would have been a guess.
- **Fix display problems upstream.** When senders parked labels in the narrative behind `originalText/reference`, the fix went into enrichment (STEP 4), not reconstruction -- the shipped entries improved too, and reconstruction got the labels for free.
- **Route every display through the shared renderers.** Real data rarely puts the label on `@displayName`; `render_code_display`'s fallback chain already handles `originalText`, `translation` and bare codes. A field map should pick a `kind`, not invent its own fallback.

## This didn't

- **Designing context columns before checking what survives pruning.** Results' Specimen cells came out empty because STEP 3 pruned the specimen procedure before STEP 6 could read it. The fix belonged in the match rules (`prune_container_guard_xpath`), not the reconstructor.
- **Reshaping source data to tidy the table.** Some EHRs send one organizer per lab test, so Results shows many small panel tables. Merging or splitting organizers would make the output look better, but it would also mean the refiner rewrites clinical structure at will; any fix there is presentational only.
- **Putting unlike statements in one grid.** A planned procedure and a planned medication don't share columns. One captioned table per kind reads clearly; a shared grid full of empty cells does not.
- **Shapes the schema can't express.** CDA R2 allows no `<table>` inside a `<td>` and no table without a row, so containment is carried by `<caption>` plus `styleCode="xallIndent"`, and an empty reconstruction is a `<paragraph>`. Both were found by validating, so validate any new markup shape early.
- **Previewing without enrichment.** An offline preview that skips STEP 4 shows bare codes the real pipeline would have labelled. Judge output from the pipeline or the scenario suite.

## Which section next

APHL's field list covers only the five sections already reconstructed. We don't know whether an update for the remaining sections is coming, so plan to go without one: the IG, the content rule, and the closest finished section are the guide.

Ranked by how closely each remaining section resembles a finished one, using the shapes in the committed fixtures:

| section                                               | entry shape                                                  | closest finished section                                   | what changes                                    |
| ----------------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------- | ----------------------------------------------- |
| **Medications** `10160-0`                             | `substanceAdministration` (22.4.16) directly under `<entry>` | Medications Administered -- same template, same match rule | the field map only                              |
| Admission Medications `42346-7`                       | `act` (22.4.36) → `substanceAdministration`                  | Medications Administered                                   | the anchor is one level deeper                  |
| Past Medical History `11348-0`                        | Problem Observation (22.4.4) directly under `<entry>`        | Problems, detail rows only                                 | flat instead of a join                          |
| Admission / Discharge Diagnosis `46241-6` / `11535-2` | `act` (22.4.34 / 22.4.33) → Problem Observation              | Problems -- same join                                      | the context fields; these acts are not concerns |
| Vital Signs `8716-3`                                  | `organizer` (22.4.26) → observations                         | Results -- same join                                       | no specimen                                     |

**Medications is the recommended next section**, and a good illustration of step 5. It uses the same Medication Activity template as Medications Administered, but it is a medication _list_: per CONF:1098-7508 its `effectiveTime` interval is the duration of therapy, not the moment of an administration. The fixtures show exactly that -- an `IVL_TS` with `low="20120318"` beside a `PIVL_TS` frequency. Reusing `reconstruct_medications` as-is would label the start of therapy "Date administered", so the work is a new field map passed to `_reconstruct_flat`, plus the registry entries.

Furthest away are Encounters and Procedures (nested or heterogeneous statements), Pregnancy, and Social History, whose rules are deliberately broad because its structure varies so much between senders. Sections handled by `generic_matching` are not candidates until they gain IG match rules -- reconstruction depends on knowing a section's structure, and `test_every_reconstructable_section_has_entry_match_rules` enforces it.
