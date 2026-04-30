# DIBBs eCR Refiner Augmentation Guide

This document explains how the eCR Refiner's augmentation service works, why it makes the decisions it does, and how to reason about its outputs. It complements the inline docstrings in [`augment.py`](./augment.py) — the docstrings explain individual functions; this document explains the design as a whole.

If you're modifying `augment.py`, read this first.

## What augmentation does

The augmentation service is the second half of the Refiner's transformation pipeline. The first half (`refine.py`) removes clinical content from an eICR/RR pair that isn't relevant to a specific (jurisdiction, condition) combination. The second half stamps the resulting documents with provenance metadata so downstream consumers--primarily public health agencies (PHAs) — know:

- That the document was transformed
- By what tool
- When
- From what original
- For what jurisdiction
- For what reportable condition

The augmentation service is responsible for that document-level metadata. It does not touch clinical content; that's `refine.py`'s job. The two halves run sequentially in the pipeline on the same parsed XML tree.

The service implements the eICR Data Augmentation Header template (`urn:hl7ii:2.16.840.1.113883.10.20.15.2.1.3:2025-11-01`) and the RR Data Augmentation Header template (`urn:hl7ii:2.16.840.1.113883.10.20.15.2.1.4:2026-04-01`) per the eICR Data Augmentation IG (Version 4 draft).

> [!IMPORTANT]
> We will eventually add in the `<entry>` level augmentation but once we've had a chance to understand the impacts on PHAs and other downstream processes.

## What the augmentation service produces

For each refined document, the augmentation service stamps:

- **`templateId`** — identifying the document as an augmentation header (eICR or RR variant)
- **`id`** — a new deterministic UUID with `assigningAuthorityName="ecr-refiner"`
- **`effectiveTime`** — timestamp of the augmentation operation (with timezone)
- **`setId`** — a new deterministic UUID with `assigningAuthorityName="ecr-refiner"`
- **`versionNumber`** — inherited from the source eICR (not reset to 1)
- **`author`** — a new author element identifying the Refiner via coded `softwareName` attributes
- **`relatedDocument`** — one or more sibling blocks describing the original document and any prior augmentations

The original `<id>`, `<effectiveTime>`, `<setId>`, and `<versionNumber>` are replaced. The original `<author>` is preserved (we append, not replace). Any prior `<relatedDocument>` elements are preserved verbatim and our new one is added as a sibling.

> [!TIP]
> One thing to keep in mind is that the `effectiveTime` for both the augmented eICR and RR will be the same. This is one way that the eCR Refiner can explicitly connect the two documents as a pair.

## How the seed strings work

Every augmented identifier is derived deterministically via UUIDv5. The seed string for every Refiner-derived UUID has the shape:

```
{jurisdiction_id}|{condition_grouper_name}|{prefix:}{source}
```

with the namespace UUID `cdcd1bb5-ecdc-4cdc-8cdc-d1bb5ecdc0dc` (pinned in `REFINER_DETERMINISTIC_NS`).

Each field plays a specific role.

### `jurisdiction_id` (outermost scope)

The jurisdiction code from the RR (e.g., `lac`, `nyc`, `ca`, `ny`). A single eICR/RR pair can be reportable to up to four jurisdictions simultaneously — the local and state context where the encounter happened, plus the local and state context where the patient lives. Each jurisdiction independently configures the Refiner. Each gets its own refined output, and the jurisdiction id makes those outputs distinguishable at the wire level.

### `condition_grouper_name` (inner scope within a jurisdiction)

The name of the condition grouper used to produce this refinement (e.g., "COVID-19", "Influenza"). Each jurisdiction may have multiple conditions configured for the same input pair. The grouper name narrows the scope of an output within a jurisdiction. Our test file demonstrates this since both COVID-19 and Influenza are reportable and if both are configured there will be condition scoped output that requires uniqueness in its ids.

The grouper name is the right discriminator because activated configurations are immutable in the Refiner and are versioned. Once a configuration is active under its version for a condition its grouper name is stable for the lifetime of any augmented document derived under it.

### `prefix:` (field role within an identifier scope)

For document `id` derivations, this is empty. For `setId` derivations, it's `eicr-setid:` or `rr-setid:`.

The prefixes exist because the augmented eICR setId and the augmented RR setId both seed from the same source (the original eICR's setId — see "Why both setIds seed from the eICR's setId" below). Without a discriminator, the same source value would produce identical UUIDs in both slots. The prefix keeps the two derivations distinct within a (jurisdiction, condition) scope.

### `source` (the original identifier)

The original eICR's `id/@root`, the original eICR's `setId/@root`, or the original RR's `id/@root`, depending on which augmented identifier is being derived.

## Working examples

### Single jurisdiction, single condition

A patient's eICR is reportable to one jurisdiction (`lac`) for one condition ("COVID-19").

| Augmented field        | Seed string                                   | UUID source |
| ---------------------- | --------------------------------------------- | ----------- |
| Augmented eICR `id`    | `lac\|COVID-19\|<eicr id root>`               | UUIDv5      |
| Augmented eICR `setId` | `lac\|COVID-19\|eicr-setid:<eicr setid root>` | UUIDv5      |
| Augmented RR `id`      | `lac\|COVID-19\|<rr id root>`                 | UUIDv5      |
| Augmented RR `setId`   | `lac\|COVID-19\|rr-setid:<eicr setid root>`   | UUIDv5      |

Note that all four augmented identifiers come from a single namespace UUID and four distinct seed strings. A PHA holding the namespace UUID and the four input identifiers (or just the eICR's `id` and `setId`, plus the jurisdiction id and grouper name) can independently recompute every augmented identifier.

The four UUIDs are guaranteed distinct: the eICR `id` and RR `id` seed from different source values; the eICR `setId` and RR `setId` seed from the same source value but with different prefixes; the document ids and setIds are distinguished by whether the prefix appears at all.

### Multiple jurisdictions, multiple conditions

A patient lives in Los Angeles County (`lac` / `ca`) and has an encounter in New York City (`nyc` / `ny`). The eICR is reportable for both COVID-19 and Influenza in all four jurisdictions.

That single eICR/RR pair, run through the Refiner, produces:

| Jurisdiction | Condition | Augmented quad                       |
| ------------ | --------- | ------------------------------------ |
| lac          | COVID-19  | (id_a, setid_a, rr_id_a, rr_setid_a) |
| lac          | INFLUENZA | (id_b, setid_b, rr_id_b, rr_setid_b) |
| ca           | COVID-19  | (id_c, setid_c, rr_id_c, rr_setid_c) |
| ca           | INFLUENZA | (id_d, setid_d, rr_id_d, rr_setid_d) |
| nyc          | COVID-19  | (id_e, setid_e, rr_id_e, rr_setid_e) |
| nyc          | INFLUENZA | (id_f, setid_f, rr_id_f, rr_setid_f) |
| ny           | COVID-19  | (id_g, setid_g, rr_id_g, rr_setid_g) |
| ny           | INFLUENZA | (id_h, setid_h, rr_id_h, rr_setid_h) |

Eight augmented document quads, all from one input pair. Every UUID across this matrix is distinct because every seed string is distinct (different jurisdictions, different conditions, or both).

For example, the augmented eICR id for lac/COVID-19 has the seed string `lac|COVID-19|<eicr id root>`, while the augmented eICR id for nyc/COVID-19 has the seed string `nyc|COVID-19|<eicr id root>`. Same source value, different jurisdictions, different UUIDs.

### Multiple versions of the same case

The patient's eICR is updated by the EHR. Version 1 was reportable for COVID19 to lac; version 2 corrects a typo and is also reportable. Two separate runs through the Refiner produce:

| Source eICR                       | Augmented eICR id             | Augmented eICR setId                     | Augmented version |
| --------------------------------- | ----------------------------- | ---------------------------------------- | ----------------- |
| v1 (id=`A`, setId=`Z`, version=1) | uuid5(ns, `lac\|COVID-19\|A`) | uuid5(ns, `lac\|COVID-19\|eicr-setid:Z`) | 1                 |
| v2 (id=`B`, setId=`Z`, version=2) | uuid5(ns, `lac\|COVID-19\|B`) | uuid5(ns, `lac\|COVID-19\|eicr-setid:Z`) | 2                 |

The augmented `id`s differ (different source eICR ids). The augmented `setId`s are the **same** (both seed from `Z`, the original eICR's setId, which is stable across versions of the same conceptual document by CDA design). The augmented `versionNumber`s differ (inherited from each source eICR's version).

A PHA querying by augmented setId gets both augmented documents back, ordered by inherited versionNumber — exactly the case-grouping semantics PHAs already use for non-augmented eICRs.

## The wire-protocol contract

The seed strings are part of the Refiner's wire-protocol contract. Once augmented documents have been produced in production, the following values cannot change without breaking idempotency:

- The namespace UUID `REFINER_DETERMINISTIC_NS`
- The seed prefix labels `eicr-setid` and `rr-setid`
- The field separator `|`
- The field ordering `{jurisdiction_id}|{condition_grouper_name}|{prefix:}{source}`
- The composition of the source value (currently `id/@root` or `setId/@root` only — see "Open questions" below)

Changing any of these would mean re-running the Refiner on the same input produces _different_ augmented identifiers than it did historically. Any downstream consumer that captured the old identifiers would observe duplicates or unresolvable references.

When a change to the contract is genuinely necessary (e.g., to address a collision risk), it should be:

1. Discussed and documented in this file before implementation
2. Coordinated with downstream consumers
3. Treated as a versioning event — historical augmented documents derived under the old contract are not reproducible from new code

## Why the operational invariants matter

Several of the design choices in `augment.py` rest on operational invariants that are worth naming explicitly. If any of these stop being true, the design needs to be revisited.

### Invariant 1: eICR/RR pairs are processed together

The Refiner never processes an eICR without its paired RR, or vice versa. The pair-aware `AugmentationContext` carries identifiers for both halves, both halves share an `effectiveTime`, both inherit a `versionNumber` from the eICR. If a path ever opened where the RR was processed independently, the design would need to grow a fallback for "RR without paired eICR" identity derivation.

### Invariant 2: Activated configurations are immutable

Once a jurisdiction activates a configuration for a condition, neither the jurisdiction code nor the grouper name can change. This is what makes them safe to use as wire-protocol seed values. If editing of activated configurations becomes possible, the seed contract becomes vulnerable—a renamed grouper would orphan all augmented documents derived under the old name.

> [!NOTE]
> Since names come from versioned condition grouper names in the TES and since our configurations are explicitly tied to a specific versioned condition grouper in our `conditions` table, and since we also provide ways in the document, specifically in the narrative `<text>` inside a `<footnote>` to understand the configuration version used to produce the refined document, this feels like a safe way to proceed. If names change during a set, this would change the `setId`, which wouldn't be good. This might be worth further discussions.

### Invariant 3: The eICR has setId and versionNumber

eICR STU 3.1.1 requires both. The augmentation IG v4 also requires both on inputs. The `create_augmentation_context_for_pair` factory raises `ValueError` if either is missing. If 1.1-era eICRs (which made these optional) ever need to be processed, this precondition needs to relax.

### Invariant 4: The RR may not have setId or versionNumber

RCKMS does not consistently populate setId or versionNumber on RRs. The augmentation service handles this by:

- Inheriting the augmented RR's own setId and versionNumber from the eICR-side context (so the augmented RR is always fully populated)
- Faithfully omitting setId and versionNumber from the augmented RR's `relatedDocument/parentDocument` block when the original RR lacked them

The omission is a deliberate violation of v4 CONF:5573-77 / CONF:5573-78 cardinality. The principle is "don't invent identity for documents we didn't author." See "Open IG questions" below.

## Why both setIds seed from the eICR's setId

The augmented RR's setId could in principle seed from the original RR's setId. We chose to seed it from the original eICR's setId instead, with a different prefix. Two reasons:

**Pair recoverability.** A PHA holding the original eICR's setId can derive the augmented RR's setId without seeing the RR. This supports pair lookup without an external join—the PHA computes `uuid5(ns, "lac|COVID19|rr-setid:<eicr setid>")` and queries directly.

**RRs commonly lack setId.** If we seeded the augmented RR's setId from the original RR's setId, every RR-without-setId would force us into a synthesis or rejection path. Seeding from the eICR's setId sidesteps that--the eICR is required to have one (per Invariant 3), so the seed source is always present.

The cost is one seed prefix label (`rr-setid:`) and one piece of asymmetric documentation. The benefit is a useful operational property and a simpler error model.

## What augmentation does _not_ do

A few things worth being explicit about, since they're easy to assume:

- **No clinical content changes.** Augmentation only touches header metadata. The structuredBody and section content are `refine.py`'s responsibility.
- **No entry-level provenance.** The IG defines an entry-level Author Participation template for stamping individual entries with what happened to them. The Refiner doesn't currently use it. Per-section provenance footnotes (in `refine.py`) cover this need at the section level for now.
- **No per-condition configuration version in the seed.** If a jurisdiction reactivates a configuration with different rules under the same grouper name, augmented documents derived before and after the reactivation will share identifiers. This is acceptable because activated configurations are immutable (Invariant 2) — reactivation requires deactivating the old configuration first. If config-version-in-seed becomes necessary, it would be added as a new field after `condition_grouper_name`.
- **No ID synthesis for missing original identifiers.** If the original RR lacks setId or versionNumber, the augmented RR's `parentDocument` block faithfully omits the corresponding child element. We do not synthesize substitutes for documents we did not author.

---

## Open IG questions

These are unresolved with the IG authors as of the v4 draft. They are flagged as `IG QUESTION (v4-followup)` in the code where they intersect with implementation choices.

**Cardinality violation in `parentDocument` for RRs without setId/version.** v4 CONF:5573-77 / 5573-78 require both. We omit them rather than synthesize. We propose v4 explicitly allow omission when the original document lacked the field.

**Determinism algorithm.** v4 Vol 1 Appendix A says "deterministic content-based GUIDs" without specifying the algorithm. We use UUIDv5 (RFC 4122 §4.3) with a Refiner-pinned namespace. We propose this as a concrete recommendation.

**Composite identity for `id+extension` and `setId+extension`.** The current seed strings use `@root` only. Real-world Epic eICRs use both `@root` and `@extension` together. We propose seeds incorporate `@extension` when present (e.g., `{root}^{extension}`).

**Vol 1 / Vol 2 inconsistencies.** Vol 1 §2.1.2.1 says the augmented document's `setId/@assigningAuthorityName` should be from the Data Augmentation Document Source value set; Vol 2 Figure 1 shows it without that attribute. We've implemented per Vol 1. Editorial fix needed; we use `assigningAuthorityName="ecr-refiner"`.

**`setId` sharing across the augmented eICR/RR pair.** Currently produces distinct setIds via the `eicr-setid` / `rr-setid` prefix discriminator. We anticipate proposing the augmented eICR and RR could share a single setId since the Refiner is the custodian of both. If accepted, the `rr-setid:` prefix becomes unused.

**Display name drift.** Vol 2 Table 2 lists the Refiner's print name as `eCR Refiner`; Vol 2 Figure 3 (an RR augmentation example) shows `eCR Refinement`. We use `eCR Refiner` and in per Table 2 (the value set definition). Editorial fix needed.
