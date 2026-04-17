# eCR Refinement and Augmentation Flow

## What this does

The `ecr` service and its orchestration layer `pipeline.py` (located a level above the `ecr` service) take an eICR/RR document pair (`XMLFiles`), remove clinical content that isn't relevant to a specific jurisdiction and condition, and stamp the output with provenance metadata so downstream consumers know the document was transformed, by what tool, when, and what happened to each section along the way.

## Architecture

The system is organized into three layers:

**`pipeline.py`** — Orchestration. Owns the parse/serialize boundary. Takes `XMLFiles` (raw XML strings) from callers, parses them into lxml element trees, sequences the transformation steps, and serializes the results back to strings. Neither the webapp (`testing.py`) nor the lambda (`lambda_function.py`) ever touch `lxml` directly — they interact entirely through the pipeline's public API.

**`refine.py`** — Content filtering and per-section provenance. Receives parsed element trees and mutates them in place according to a refinement plan. For eICRs, this means walking each section, removing entries that don't match the jurisdiction's configured codes, and attaching a per-section provenance footnote that records what the refiner did. For RRs, this means removing condition observations that aren't reportable to the jurisdiction or scoped to the refined eICR. Does not parse or serialize.

**`augment.py`** — Document-level provenance stamping. Receives parsed element trees (after refinement) and mutates them in place to add document-level augmentation metadata per the draft eICR Data Augmentation IG (Version 2). This includes a new document ID, timestamp, authoring device information, and a `relatedDocument` block that traces back to the original. Does not parse or serialize.

## Data flow

```
XMLFiles (strings)
  │
  ├─ pipeline parses both documents
  │
  ├─ eICR: plan → refine → augment
  ├─ RR:   plan → refine → augment
  │
  ├─ pipeline serializes both documents
  │
  └─ RefinementResult (strings)
```

The pipeline creates an `AugmentationContext` for each document before any work begins. Both contexts share the same timestamp, and the same timestamp is also stamped onto each per-section provenance footnote ID — so the eICR header, the RR header, and every footnote in the refined eICR can be correlated structurally without parsing dates.

## What augmentation adds to the eICR

All of this is per the eICR Data Augmentation Header template (`urn:hl7ii:2.16.840.1.113883.10.20.15.2.1.3:2025-11-01`):

- **`templateId`** — signals the document conforms to the augmentation header template
- **`id`** — new UUID with `assigningAuthorityName="ecr-refinement"`
- **`effectiveTime`** — timestamp of the augmentation operation (with timezone)
- **`setId`** — new UUID (replaces original, or inserted if absent)
- **`versionNumber`** — reset to 1
- **`author`** — identifies the refiner tool via `functionCode` (from the Data Augmentation Tool value set) and `assignedAuthoringDevice/softwareName`
- **`relatedDocument`** — `typeCode="XFRM"` with a `parentDocument` block containing the original document's ID, setId, and versionNumber. If the input was already augmented by another tool, the prior ID chain is carried forward cumulatively.

## What augmentation adds to the RR

The augmentation IG doesn't define RR-specific templates, so the RR gets the same treatment as the eICR minus the augmentation `templateId` (which would be a conformance error since that template is eICR-specific). If the original RR didn't have `setId` or `versionNumber` (common — RRs are one-shot response documents), those are skipped rather than fabricated.

## Per-section provenance footnotes

Refinement attaches an unanchored `<footnote>` to every section in the refined eICR, regardless of whether the section was refined, retained, removed, or had its narrative stripped. The footnote carries a small table summarizing how the refiner treated the section:

- **what the jurisdiction configured** — included or not, action (refine or retain), narrative handling, configuration version
- **where the configuration came from** — explicitly configured by the jurisdiction, held by a system rule, or unconfigured (fell back to retain)
- **what the refiner actually did** — refined with matches, refined with the narrative removed, retained as-is, removed by configuration, or refined-but-no-matches-found

The "what was configured" and "what actually happened" columns usually agree, but they can diverge. The most common divergence is the no-match case: a jurisdiction configures a section for refinement, the matching step finds nothing in the section that matches the configured codes, and the refiner stubs the section rather than preserving an orphaned narrative. The footnote makes that decision visible — a reviewer sees "Action: refine, Outcome: Refined; no matches found" in the same row and doesn't have to wonder why a refine-configured section came out empty.

The footnote ID is built from the section's LOINC code and the augmentation timestamp (`ecr-refinement-{loinc}-{timestamp}`), so every footnote in a refinement run is structurally tied to the augmentation author's `<time>` value. A consumer can verify document integrity by checking that all footnote IDs in a document carry the same timestamp the augmentation header advertises.

The user-facing labels for the configuration source and the runtime outcome live in `section/constants.py` as small dicts keyed by enum values. Editing the copy is one file change with no code touches.

## Supporting modules

**`model.py`** — Shared data structures and namespace constants. Defines `HL7_NS`, `HL7_NAMESPACE`, and `HL7_XSI_NS` used by all `ecr` service modules. Also contains the plan dataclasses (`EICRRefinementPlan`, `RRRefinementPlan`), the provenance dataclasses, the section run result that the matching engines return, and the enums (`SectionSource`, `SectionOutcome`) that drive the provenance footnote.

**`specification/`** — Static IG knowledge as a small package. Section LOINC codes, C-CDA template IDs, IG-verified entry match rules, and per-version trigger code overlays drawn from the eICR IG volumes. This is the source of truth for "what does the eICR specification say about this version." `loader.detect_eicr_version` reads a document and returns the version; `loader.load_spec` assembles a fully resolved specification.

**`section/`** — The mechanics of applying refinement to a section, also a package. The `process_section` dispatcher picks between the IG-driven section-aware engine (`entry_matching`) and the unscoped fallback engine (`generic_matching`) based on whether the section's specification declares entry match rules. The narrative writers (`narrative`) handle every kind of `<text>` element the refiner produces — refined clinical tables, removal notices, minimal stubs, and the per-section provenance footnotes.

**`reportability.py`** — RR document traversal. Extracts reportable conditions grouped by jurisdiction from the RR11 Coded Information Organizer.

## Key design decisions

**Mutate in place.** Every XML transformation function receives an `_Element` and mutates it. This is consistent with how lxml works naturally, avoids unnecessary tree copies, and means the pipeline can chain multiple transformations (refine then augment) on the same tree with a single parse and a single serialize.

**Pipeline owns parse/serialize.** The `ecr` service functions never parse raw XML strings and never serialize trees to strings. This keeps them focused on tree transformations and means the pipeline can compose them freely without intermediate serialization round-trips.

**Callers are insulated.** `testing.py` and `lambda_function.py` pass `XMLFiles` into the pipeline and get strings back. They don't know about `lxml`, element trees, or augmentation contexts. The pipeline's public API didn't change when augmentation was added, and it didn't change when per-section provenance was added.

**Engines report facts; the orchestrator interprets them.** The matching engines return a small `SectionRunResult` describing what they did (matches found or not, what happened to the narrative). `refine.py` maps that structural result to a user-facing `SectionOutcome` for the provenance footnote. This split keeps the matching code focused on structural concerns and puts policy decisions (like "stub the section when nothing matches") in one place where they can be audited and changed without touching the engines.

**Namespace standardization.** All modules use `hl7:` as the XPath prefix for `urn:hl7-org:v3`. The namespace map is defined once in `model.py` and imported everywhere. The CDA literature uses both `hl7:` and `cda:` interchangeably (per Keith Boone's _The CDA Book_, §4.2); having one convention across the codebase prevents silent bugs from mismatched prefix/map pairs.

## Future work

**Entry-level author participations.** The augmentation IG defines an Entry Author Participation template for stamping individual entries with what the tool did to them (retained, removed, nulled). This would give downstream consumers per-entry provenance to complement the per-section provenance footnotes. It's more invasive than header-level augmentation because it needs to happen during section processing, not after.

**Three-way narrative configuration.** The `narrative` setting on a section configuration is currently a bool (retain or remove). A planned third value, `refine`, will reconstruct the narrative from the surviving entries after refinement. The `SectionOutcome.REFINED_NARRATIVE_RECONSTRUCTED` enum value and its label are already in place; the work is in the matching engines and the configuration UI.

> [!IMPORTANT]
> **March 2026 spec update.** The IG is removing `functionCode` from the header-level author and adding a value set binding to `softwareName` instead. The code has comments marking where this change applies. When adopted, the header author's `functionCode` block gets removed and `softwareName` gains `@code` and `@codeSystem` attributes from the Data Augmentation Tool value set.
