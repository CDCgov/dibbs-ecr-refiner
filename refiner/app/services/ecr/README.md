# eCR Refinement and Augmentation Flow

## What this does

The `ecr` service as well as it's orchestration layer `pipeline.py` (located a level above the `ecr` service) takes an eICR/RR document pair (`XMLFiles`), removes clinical content that isn't relevant to a specific jurisdiction and condition, and stamps the output with provenance metadata so downstream consumers know the document was transformed, by what tool, and when.

## Architecture

The system is organized into three layers:

**`pipeline.py`** — Orchestration. Owns the parse/serialize boundary. Takes `XMLFiles` (raw XML strings) from callers, parses them into lxml element trees, sequences the transformation steps, and serializes the results back to strings. Neither the webapp (`testing.py`) nor the lambda (`lambda_function.py`) ever touch `lxml` directly — they interact entirely through the pipeline's public API.

**`refine.py`** — Content filtering. Receives parsed element trees and mutates them in place according to a refinement plan. For eICRs, this means walking each section and removing entries that don't match the jurisdiction's configured codes. For RRs, this means removing condition observations that aren't reportable to the jurisdiction or scoped to the refined eICR. Does not parse or serialize.

**`augment.py`** — Provenance stamping. Receives parsed element trees (after refinement) and mutates them in place to add document-level augmentation metadata per the draft eICR Data Augmentation IG (Version 2). This includes a new document ID, timestamp, authoring device information, and a `relatedDocument` block that traces back to the original. Does not parse or serialize.

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

The pipeline creates an `AugmentationContext` for each document before any work begins. Both contexts share the same timestamp so the eICR and RR outputs can be correlated in logs.

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

## Supporting modules

**`model.py`** — Shared data structures and namespace constants. Defines `HL7_NS`, `HL7_NAMESPACE`, and `HL7_XSI_NS` used by all ecr service modules. Also contains the plan dataclasses (`EICRRefinementPlan`, `RRRefinementPlan`), section specifications, and other frozen models.

**`specification.py`** — Static IG knowledge. Section LOINC codes, template IDs, trigger codes, entry match rules, and version detection logic drawn from the eICR IG volumes. This is the source of truth for "what does the eICR specification say about this version."

**`process_eicr.py`** — Entry-level XML manipulation for eICR sections. Called by `refine_eicr` to process individual sections — matching entries against codes, pruning non-matching content, rebuilding narrative text.

**`reportablility.py`** — RR document traversal. Extracts reportable conditions grouped by jurisdiction from the RR11 Coded Information Organizer.

## Key design decisions

**Mutate in place.** Every XML transformation function receives an `_Element` and mutates it. This is consistent with how lxml works naturally, avoids unnecessary tree copies, and means the pipeline can chain multiple transformations (refine then augment) on the same tree with a single parse and a single serialize.

**Pipeline owns parse/serialize.** The ecr service functions never parse raw XML strings and never serialize trees to strings. This keeps them focused on tree transformations and means the pipeline can compose them freely without intermediate serialization round-trips.

**Callers are insulated.** `testing.py` and `lambda_function.py` pass `XMLFiles` into the pipeline and get strings back. They don't know about `lxml`, element trees, or augmentation contexts. The pipeline's public API didn't change when augmentation was added.

**Namespace standardization.** All modules use `hl7:` as the XPath prefix for `urn:hl7-org:v3`. The namespace map is defined once in `model.py` and imported everywhere. Both `hl7:` and `cda:` are conventional (per Keith Boone's CDA Book, §4.2), but having one convention across the codebase prevents silent bugs from mismatched prefix/map pairs.

## Future work

**Entry-level author participations.** The augmentation IG defines an Entry Author Participation template for stamping individual entries with what the tool did to them (retained, removed, nulled). This would give downstream consumers per-entry provenance. It's more invasive than header-level augmentation because it needs to happen during section processing, not after.

> [!IMPORTANT]
> **March 2026 spec update.** The IG is removing `functionCode` from the header-level author and adding a value set binding to `softwareName` instead. The code has comments marking where this change applies. When adopted, the header author's `functionCode` block gets removed and `softwareName` gains `@code` and `@codeSystem` attributes from the Data Augmentation Tool value set.
