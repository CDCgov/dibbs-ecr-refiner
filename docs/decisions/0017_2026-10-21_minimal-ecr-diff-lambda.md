# 17. A minimal eCR diff Lambda in the Refiner

Date: 2026-10-21

## Status

Proposed

## Context and Problem Statement

Public health agencies (PHAs) receive several versions of the same eICR for one
encounter. Reviewers can't easily tell what changed between versions, so they
either re-read every version or skip updates that matter.

Difference in Docs (DiD, `CDCgov/dibbs-ecr-diff`) was built to answer "what
changed between this version and the last one?" This ADR proposes rebuilding a
**minimal** version of that capability inside the Refiner repository, as a
second Lambda. It reuses the Refiner's configuration, CDA knowledge and
augmentation code.

References to `dibbs-ecr-diff` below are to commit `314e7e0`.

### What DiD does today

1. **Input.** AIMS writes a `DIDInput/{persistence_id}` manifest
   (`docs/01-Technical-Overview.md:5`). Each entry carries `eicr`, `rr`,
   `setId`, `versionNumber` and `jurisdictions` (`did_lambda/models.py:9-17`),
   and points at a refined pair (`RefinerOutputV2/…`), an original pair
   (`eCRMessageV2/{pid}`, `RRMessageV2/{pid}`) or a remainder RR
   (`e2e/helpers.py:203-225`). The manifest describes only the current version.
2. **Baseline.** For each incoming eICR, DiD looks up the latest earlier version
   of the same `setId` that it marked _actionable_ (DynamoDB, keyed by `setId` +
   `versionNumber`; `did_lambda/dynamodb.py:25-43`).
3. **Detect.** It walks the **whole document** recursively and pairs elements
   between versions using a 12-rank "stable key" ladder (`core/cda/stable_key.py`).
   It never uses the section to scope pairing.
4. **Classify.** Every change is checked against a JSON list of XPath rules
   (`core/configurations/aphl_baseline.json`). The main rule is
   `//hl7:entry/descendant-or-self::*`, so any change under any entry counts.
5. **Report and flag.** It writes a JSON list of changes and stamps augmentation
   `author`s carrying `did-*` function codes into the eICR.

### Problems found

These were found by reading the code and running synthetic probes:

- **Whole-document matching collapses.** When a document has more than six
  sections and some section ids are regenerated between versions, the body fails
  to pair. The whole body is then reported as one deletion plus one addition. The
  change list stops telling you anything.
- **Rules can only see one version.** XPath rules are evaluated against one tree
  at a time (`core/__init__.py:44-63`, `:391-392`). No rule can say "v2 had a
  lab order and v3 now has its result". That kind of criterion is
  inexpressible.
- **Output has no context.** A change row carries a type, a positional xpath, a
  document id and the rule that matched (`core/models.py:33-47`). It has no
  before or after value, no template and no code. DiD computes the section LOINC
  for every change, then leaves it out of the JSON (`core/models.py:44`). The
  positional xpath doesn't resolve in DiD's own augmented output.
- **Status changes are found but not explained.** A probe changing a Result
  Organizer's `statusCode` from `active` to `completed` produced two
  `UPDATED …/statusCode[1]` rows. Both carried the same generic "entry" rule
  name that fires on an author's family-name change.
- **The verdict says almost nothing.** Under the baseline rule, first versions
  are actionable by construction (`did_lambda/lambda_function.py:185`), and almost any
  compared version is too. The verdict is never logged (`did_lambda/telemetry.py:149-175`),
  so a silent evaluation can't measure it either.
- **No trigger-code or RR awareness.** Nothing compares the set of trigger codes
  across versions. The RR is never diffed.
- **No PHA configuration story.** The configuration is a flat file in the
  repository. Custom configuration is deferred to "post-MVP"
  (`docs/Configuration-Spec.md:15`).
- **The actionability criteria were translated, not specified.** The baseline
  rules are an XPath translation of criteria APHL described in conversation, and
  that prose isn't recorded anywhere. `cste.json` is a transcription of the
  XPath column of the CSTE eCR Consensus Criteria Table 1, with at least four
  transcription errors (a wrong path for encounter type, `4.54` instead of `4.23`
  for medications, an OID typo, and rules on header ids the collector
  suppresses). That table is an onboarding **completeness** list, not a list of
  changes that matter (CSTE eCR Consensus Criteria, Feb 2026, pp.7, 9-10).

### What the Refiner already has

- **Per-PHA, per-condition configuration, activated to S3.** Each activation
  writes
  `configurations/{jurisdiction}/{condition-grouper-uuid}/current.json` and
  versioned `active.json` / `metadata.json` (ADR 0003, ADR 0006). There's an ops
  migration path when the payload shape changes (ADR 0012) and a maintenance
  lock (`lambda_function.py:293`).
- **Condition-scoped streams.** Refined output gets one `setId` per
  (jurisdiction, condition grouper) (`services/ecr/augment.py:171-191`) and
  keeps the source `versionNumber` (`augment.py:432-433` for the eICR,
  `:521-522` for the RR). So each refined stream
  is already "this PHA, this condition".
- **CDA knowledge DiD lacks.** A generated template OID catalog
  (`services/ecr/specification/template_oids.py`), entry-match rules
  (`specification/entry_match_rules.py`), a version map
  (`specification/versions.py`) and RR parsing (`services/ecr/reportability.py`).
- **Section processing.** Refinement runs section by section and records what
  it did per section in `SectionOutcome` (`services/ecr/model.py:399`).
- **The augmentation writer.** DiD's `core/augment.py` is a fork of
  `services/ecr/augment.py`.
- **A completion signal.** The Lambda writes
  `{REFINER_COMPLETE_PREFIX}{persistence_id}` listing every refined output file
  (`lambda_function.py:352-370`). It's written for every processed eCR, and its
  `RefinerMetadata` marks each (jurisdiction, RSG code) in the RR as refined or
  skipped.

### The scoping insight

A diff only needs to run on eICR/RR pairs a PHA has **configured** it for. A
PHA-scoped configuration decides what runs; a global "is actionable" verdict
isn't needed. That is the same gating the Refiner already does.

## Decision Drivers

- Only run on pairs a PHA has configured, using the Refiner's existing
  activation flow.
- A PHA can use the diff without refinement, or refinement without the diff.
- Never block or slow refined delivery. A diff failure must not affect the
  Refiner's output or its `RefinerComplete` signal.
- Compare in units an epidemiologist recognises: sections and clinical entries,
  not XML nodes.
- Output a reader can use without opening the source XML.
- Reuse the Refiner's CDA, configuration and augmentation code; don't fork it a
  second time.
- Minimise new infrastructure APHL has to provision and operate.
- Leave room for criteria that span versions (for example order → result)
  without designing them all now.

## Considered Options

### A. Where the diff runs

#### A1. Inside the existing refining Lambda

After refining, load the previous version and diff it in the same invocation.

- Pro: no new function, trigger or queue. All context is already in memory.
- Con: refinement latency now includes a version-store read and a diff.
- Con: a diff failure has to be carefully isolated, or it risks the
  `RefinerComplete` signal AIMS depends on.
- Con: one function's memory and timeout must fit both jobs.

#### A2. A second Lambda handler in this repository, same image (recommended)

Add `app/lambda/diff_function.py` (name to be decided) to the image built by
`Dockerfile.lambda`. Deploy it as a separate function with its own `CMD`,
triggered when a `RefinerComplete` file is written (or by a `DIDInput`-style
manifest; see Open Questions).

- Pro: refinement is unaffected; the diff can fail, retry or be turned off
  independently.
- Pro: shares `services/ecr/specification`, the activation and configuration
  loaders, and the augmentation writer with no copying.
- Pro: one repository, one release cadence, one set of CDA tests.
- Con: AIMS must wire a second function, trigger and queue (APHL deploys both
  images today; `dibbs-ecr-diff/docs/RELEASING.md:3`).
- Con: the image grows slightly, and both functions ship together.

#### A3. Keep `dibbs-ecr-diff` as a separate repository and fix it in place

- Pro: no migration; existing AIMS wiring stays.
- Con: it would need the template catalog, configuration activation, RR parsing
  and section processing the Refiner already has. That means either a second
  copy or a cross-repo dependency.
- Con: the augmentation fork continues to drift.

#### A4. Extract a shared library consumed by both repositories

- Pro: the cleanest long-term boundary.
- Con: premature. The shared surface isn't stable yet, and it adds a publishing
  and versioning burden before the diff has proven its shape. Revisit once A2
  has run in production.

### B. Where versions are recorded

> [!NOTE]
> **Open questions that shape this section.** What follows is how we _think_
> version storage should work and the options considered. Two things are
> unresolved, and either could change the answer:
>
> - **Reference or copy?** The input pairs live in AIMS's bucket
>   (`RefinerOutputV2/`, `eCRMessageV2/`, `RRMessageV2/`), under AIMS's
>   Lifecycle rules. DiD stores references only (`s3Key` is the manifest's
>   input key, `did_lambda/lambda_function.py:246-257`) and reads the baseline
>   back from there (`:209`), so a baseline AIMS has expired is simply gone.
>   The options:
>   - **Copy** the input pair into the version store when the record is
>     written. The store owns its retention; the cost is a second copy of PHI.
>   - **Snapshot** only the watched units as JSON. Small and cheap to compare,
>     but a later configuration can't compare units the snapshot lacks, and a
>     snapshot can't be re-extracted when the catalog code changes.
>   - **Reference only**, if AIMS commits to a retention window longer than the
>     gap between versions.
> - **No baseline before activation.** The index exists only for versions the
>   diff processed with a configuration active. A configuration activated at v2
>   gives v3 no baseline, because v2's refined pair sits under an unknown
>   `persistence_id`. The Refiner could write a record for every refined output
>   whether or not a diff configuration exists, at the cost of coupling it to the
>   diff's storage. The minimal version accepts the gap: the first version after
>   activation is record only.
>
> Whatever the trigger turns out to be (`RefinerComplete` or a `DIDInput`-style
> manifest), the manifest describes one version. The version store, not the
> manifest, answers "where is the previous one". DiD works the same way: its
> DynamoDB table is the only place earlier versions can be found.

The diff needs, per stream: every stored version's S3 keys, its input kind, the
configuration version it was refined under, and a way to find "the previous
one".

#### B1. DynamoDB index + S3 objects

The table is keyed by stream (partition; see "Stream identity" under §1) and
`versionNumber` (sort). It stores S3 keys for the refined pair (when there is
one) and the **original** pair, the input kind, the refiner configuration
version, and the diff output key. Documents stay in S3.

- Pro: queries across streams (for example "all streams for jurisdiction X with
  findings this week") need a secondary index, not an S3 scan.
- Pro: DiD already runs this pattern on AIMS.
- Con: a second store to keep consistent with S3. Documents still need S3
  Lifecycle, so expiry runs on two mechanisms (TTL for rows, Lifecycle for
  objects) that can drift apart.
- Con: new infrastructure for the Refiner, which is S3-only today, configuration
  included: IaC, IAM, and a DynamoDB gateway endpoint for a Lambda in a private
  VPC. DiD's table belongs to DiD.
- Con: deleting a jurisdiction's data needs a secondary index on jurisdiction
  _plus_ the S3 deletion.

#### B2. S3 only (recommended)

`{version-store-prefix}/{jurisdiction}/{condition-grouper-uuid}/{source-setId}/{versionNumber:010d}/`
holds a version record (input kind, S3 keys of the refined and original pairs, refiner
configuration version) and the findings file. Whether the documents are
referenced or copied is open (see the note above).

- Pro: one store, and no new service for APHL to run. This is the decision
  driver on minimising infrastructure.
- Pro: "previous version" is one `ListObjectsV2` on the stream prefix. The
  zero-padded keys list in order, listing has been strongly consistent since
  2020, and streams are short (99% of encounters produce 10 versions or fewer).
  The listing _is_ the "latest" pointer; no atomic one is needed. A summary
  across 2-4 versions is the same listing.
- Pro: duplicate deliveries are handled by `If-None-Match: *` on the version
  record. A second put fails with `412 PreconditionFailed`. The record is the
  commit marker, so it's written **last**: findings first (idempotent
  overwrite), then the record. A crash in between is retried in full; a `412`
  means the version is complete. The condition grouper is the uuid from its
  `canonical_url`, matching the configuration keys, not the space-stripped name
  `RefinerOutputFiles` uses. Bucket and prefix are AIMS's to provision.
- Pro: retention by jurisdiction is a single prefix delete. Retention is open
  (see Open Questions), and this keeps the likeliest answer cheap.
- Con: queries across streams need a scan or Athena. Nothing in the minimal
  version needs them.
- Con: Lifecycle expires objects by age. That is also true of DynamoDB TTL, and
  streams have no close event either way.

Verified against the LocalStack community edition that compose pins
(`localstack/localstack:4`, reporting `4.14.0`, `edition: community`):
`If-None-Match: *` and `If-Match` both return `412` on conflict, and
`ListObjectsV2` returns zero-padded version prefixes in order. So the
`tests/localstack/eval.py` harness can exercise B2 without a paid edition.

**Revisit B1** if findings become a delivery-time signal to AIMS that needs
low-latency lookups across streams, or if a UI needs "latest findings per
stream for jurisdiction X". Both depend on §4.

**Out-of-order arrival affects both options.** "Previous version" means the
highest version already stored below this one. If v3 arrives before v2, v3 is
compared to v1 and v2 is compared to v1, so v3's findings are relative to v1.
Neither store fixes this; it is an ordering problem, not a storage problem.

### C. The rule vehicle

#### C1. XPath rules (DiD today)

- Con: they evaluate against one version at a time, so criteria that span
  versions or entries can't be written (see above).
- Con: they encode _where_ a node is, not _what_ it means. A `statusCode` change
  and an author-name change match the same rule.
- Con: they are easy to get wrong. `cste.json` carries four transcription errors
  that no test caught.
- Con: they can't express the cases where the IG matters. In eICR 3.1.1, the
  lab's preliminary, in-lab and not-verified statuses all map to `active`, and
  final, corrected, amended and appended all map to `completed`
  (Laboratory Observation Result Status `2.16.840.1.113883.10.20.22.4.419`). A
  corrected final result is `completed` → `completed`. Only a rule that knows to
  look at template `4.419` or the value can see it.
- Con: PHAs can't author or review them. CSTE independently lists "correlation
  between data elements" and "evaluation of string or HTML in the narrative"
  as things its own XPath/Schematron tooling can't do (CSTE eCR Consensus
  Criteria, Appendix A, p.24).

#### C2. A catalog of named elements with typed comparisons (recommended)

Code defines, per section, the comparable **units** (entry templates), their
**pairing key**, and the **kinds of difference** that can happen to them. The
configuration only picks from that catalog. XPath stays an implementation
detail inside the catalog, where it's covered by tests against IG examples.

## Decision Outcome

Proposed: **A2 + B2 + C2**, kept to the minimum below.

### 1. Shape of the Lambda

```
RefinerComplete/{persistence_id} written
  → (EventBridge/SQS, wired by AIMS)
  → diff Lambda
      for each (jurisdiction, RSG code) in RefinerMetadata:
        RSG → condition grouper via rsg_cg_mapping.json
        load diff config for (jurisdiction, condition grouper); none → skip
        refined (true)  → use the refined pair
        skipped (false) → use the original pair
        find previous version of this stream; none → record only, stop
        compare section by section (+ patient, encounter, trigger codes)
        write findings to a flat file (see §4)
        record this version (version record in S3, written last)
```

- **One trigger.** The Refiner writes `RefinerComplete` for every eCR it
  processes, not only the refined ones. `RefinerMetadata` lists every
  (jurisdiction, RSG code) in the RR as `true` (refined) or `false` (skipped)
  (`lambda_function.py:944`, `:1058`; `app/lambda/RefinerComplete.md`). That is
  already the signal for whether the diff has refined input, so nothing has to
  run ahead of the Refiner.
- **Refined input when it exists.** There's no reason to diff entries the
  Refiner removes. When the condition isn't refined for that jurisdiction, the
  diff uses the original pair. A PHA can configure one condition for refinement
  and another for the diff.
- Gated by configuration: no diff configuration for a (jurisdiction, condition
  grouper) means nothing runs, exactly like refinement.
- It never rewrites the refined output AIMS already delivered. Its outputs are
  new objects.
- The baseline is the **previous stored version**, not the "last actionable"
  one. Choosing a different baseline (for example the last delivered version) is
  a read-time choice that can come later.

#### Additions to `RefinerComplete`

All three add fields, so nothing AIMS reads today changes:

- **`RefinerInputFiles`**: the original eICR/RR keys, needed on **both**
  branches. The `false` branch has no other way to find the original pair; the
  `true` branch needs it for the source `setId` (below) and because every
  version record keeps the original pair's keys (§B, §6).
- **Refined outputs keyed by (jurisdiction, condition grouper).** Today
  `RefinerOutputFiles` is a flat list of paths built from condition grouper
  names with the spaces stripped (`.../NY/COVID19/refined_eICR.xml`), so the diff
  would have to parse paths to find its stream.
- **The refiner configuration version** per refined entry, so the diff knows
  what produced each refined output (§6).

All of this depends on how AIMS routes the signal; see Open Questions.

#### Stream identity

The refined `setId` is derived per (jurisdiction, condition grouper) from the
source eICR's `setId` (`services/ecr/augment.py:171-191`). The original `setId`
is whatever the sender sent. If a PHA turns refinement on or off partway through
an encounter, consecutive versions arrive as different kinds with different
setIds, and their content isn't comparable. So:

- Every stream is keyed on **(source `setId`, jurisdiction, condition
  grouper)**, whichever input kind arrives. The refined setId is a uuid5 and
  can't be reversed, so for refined input the source setId is read from the
  original eICR (`RefinerInputFiles`), with the refined document's own
  `relatedDocument` (`augment.py:911`) as a fallback.
- The input kind (refined or original) is recorded per stored version.
- When the input kind changes between versions, the diff emits a finding saying
  so rather than diffing across it. This is the same treatment §6 gives a
  refiner configuration change.

DiD keys on `setId` alone, as AIMS supplies it (the refined setId for refined
pairs, the sender's for originals), so its refined and original streams for one
encounter never pair, and nothing reports it.

"Source `setId`" assumes nothing upstream of the Refiner rewrites it. The
augmentation chain is TTC → (RCKMS) → Refiner → DiD, and every augmenter
rewrites `setId`. If text-to-code runs for some versions of an encounter and not
others, the source setId changes mid-stream. The stable identity would then be
the sender's setId: the oldest `relatedDocument/parentDocument/setId` in the
chain. The Refiner carries prior `relatedDocument[@typeCode='XFRM']` blocks
forward verbatim, oldest first (`services/ecr/augment.py:916-933`), but it can
only carry what it receives. See Open Questions.

### 2. Compare section by section

- **Sections are stable units.** Section LOINC plus `templateId` gives a free,
  stable pairing key between versions. Inside a section, entries pair by
  clinical key, and DiD's stable-key ladder can serve as the fallback.
- **Failures stay contained.** A failure to pair one section can't turn the
  whole body into one deletion and one addition.
- **It matches how PHAs read eICRs.** Most PHAs read a section's `<text>`
  narrative, not its entries, so findings grouped by section map directly onto
  what they review.
- **It matches the Refiner.** Configuration, `SectionOutcome` and the
  provenance footnote are all per section already.
- **Cost.** Changes that cross sections aren't paired. The IG binds each entry
  template to its section, so the same entry moving to another section would be
  a sender defect, not a normal case. What does happen is that the same clinical
  fact appears as a _different_ entry in a _different_ section as care
  progresses:
  - a lab order (Planned Observation in Plan of Treatment, 18776-5) becomes a
    Result Observation in Results (30954-2)
  - an admission diagnosis (46241-6) becomes a discharge diagnosis (11535-2)
  - a medication on admission becomes a medication administered

  Each side shows up in its own section as added or removed. Linking them is a
  criterion that spans entries, which is out of scope.

- **Header.** The header isn't a section, but about half of the CSTE consensus
  data elements live there. It becomes **two** pseudo-sections, because the
  user research treats them separately and they change differently: patient
  fields fill in late on emergency encounters, while encounter fields change on
  admission and discharge.
  - **`patient`**: `recordTarget/patientRole` (`id`, `addr`, `telecom`; name,
    gender, birth time, race and ethnicity, `languageCommunication`,
    `guardian`, and the required `sdtc:deceasedInd` / `sdtc:deceasedTime`,
    CONF:4527-404 and -106), plus `participant/associatedEntity` (emergency
    contact, next of kin).
  - **`encounter`**: `componentOf/encompassingEncounter` (`code` for the
    encounter class, `effectiveTime/low` and `/high` where `high` is the
    discharge, `sdtc:dischargeDispositionCode`, `responsibleParty`,
    `location/healthCareFacility`), plus
    `author/assignedAuthor/representedOrganization` (the facility).
  - **Excluded**: `author/time` (changes on every version), `custodian`, `id`,
    `setId`, `versionNumber`, `effectiveTime` and `relatedDocument`.
  - Encounter Activity entries (`<encounter>`) live in the Encounters section
    (46240-8), not the header.

**Sections the Refiner removed.** The diff never sees `SectionOutcome`: it
shares the Refiner's code, not its runtime state, and the outcome only exists in
memory during refinement. It doesn't need it. Under an unchanged refiner
configuration, a section reduced to a stub (`REMOVED_BY_CONFIG`) is a stub in
both versions and compares equal. A refiner configuration change, the only thing
that turns a populated section into a stub or a `REFINED_NO_MATCHES_*` section
between versions, is flagged per §6 rather than diffed across, so it can't show
up as mass removal. A diff configuration that watches a section the refiner
configuration removes can never fire; the activation UI should warn about that
later.

Pairing within a section uses a **clinical key** where one exists, for example
a result's LOINC code plus specimen collection time, or a problem's value code.
Instance ids are a fallback only, because senders regenerate them between
versions.

### 3. Configuration

**One configuration per (jurisdiction, condition grouper), condition-agnostic
for now.** Every new diff configuration starts from the same default. There is
no core/overlay layering: a PHA adds or changes rules, and the configuration
version goes up. Two version numbers are kept apart:

- **Configuration `version`**, per (jurisdiction, condition grouper). It goes up
  whenever a PHA edits its rules.
- **`schema_version`**, global. It goes up only when the JSON shape changes, and
  is migrated per ADR 0012. A new unit or kind of change is a catalog change in
  code and needs no schema bump unless the structure moves.

The condition examples from user research shape the catalog without becoming
overlays. Enterics needs a "result became final" kind, including the corrected
final case. Chlamydia/gonorrhea needs Medications Administered and Plan of
Treatment units to exist, even if they're off by default. Hep B/C needs
Immunizations.

**Keyed by section.** Units belong to sections in the catalog, so a
configuration can't watch a unit in a section that doesn't have one. There are
three scopes:

- **`document`**: things that span sections. Trigger codes can appear in
  Problems, Results, Encounters, Plan of Treatment, Procedures, Medications and
  Immunizations (`get_trigger_code_sections()`).

**RR comparison doesn't fit a per-condition stream.** A stream is one
(jurisdiction, condition grouper). A newly reportable condition or jurisdiction
has no earlier version in its stream, so it is always "record only". A condition
that stops being reportable drops out of `RefinerMetadata`, so its stream is
never visited. Comparing RR conditions needs a record per (source `setId`,
jurisdiction) alongside the per-condition streams. It's out of the minimal
version; see Out of scope and Open Questions.

- **Header pseudo-sections**: `patient` and `encounter` (§2).
- **Body sections**, keyed by LOINC to match `_SECTION_CATALOG`
  (`services/ecr/specification/catalog.py`).

The configuration refers to named catalog entries, never XPaths. An
illustrative sketch; field names are not final:

```json
{
  "schema_version": 1,
  "document": {
    "trigger_codes": ["added", "removed"]
  },
  "sections": {
    "patient": {
      "fields": ["deceased", "name", "birth_date", "address", "race_ethnicity"]
    },
    "encounter": {
      "fields": ["discharge_time", "discharge_disposition", "class", "facility"]
    },
    "30954-2": {
      "units": {
        "result_observation": [
          "added",
          "status_changed",
          "value_changed",
          "interpretation_changed"
        ]
      }
    },
    "11450-4": { "units": { "problem": ["added", "status_changed"] } },
    "10154-3": { "units": { "narrative": ["changed"] } }
  }
}
```

**Narrative-only sections** have no entry match rules (Chief Complaint, Reason
for Visit, History of Present Illness). They get one unit, `narrative`, with one
kind, `changed`: a hash of the normalized `<text>` per version. It says the narrative changed and
nothing about what changed. Utah named chief complaint and reason for visit as
must-know regardless of condition, and these sections have no entries to compare.

What belongs in the default configuration is the main open design question (see
below). The CSTE consensus data elements are a reasonable list of **candidate
units**, because they are the agreed floor of what every PHA needs to be
present. They aren't a list of changes that matter. The CSTE header identity
elements (such as `id`, `setId`, `versionNumber`, `effectiveTime` and the
custodian) change or are irrelevant by definition and are excluded.

#### Storage

- **S3: a separate namespace, the same machinery.** Diff configurations live
  under their own prefix (for example
  `diff-configurations/{jurisdiction}/{condition-grouper-uuid}/`) with the same
  `current.json` pointer, versioned `active.json` / `metadata.json`,
  `schema_version` checks. Two things are refinement-specific today:
  `S3_CONFIGURATION_DIR_PREFIX` in `services/aws/s3_keys.py`, which becomes a
  parameter, and `MAINTENANCE_LOCK_KEY = "configurations/maintenance.lock"`,
  hard-coded in `db/configurations/model.py:20`. The diff gets its own lock under
  its own prefix, so diff maintenance never stalls refinement. The refining
  Lambda never reads diff files, and a PHA can activate, deactivate or roll back
  either kind on its own.
- **One mapping file.** Both Lambdas need `rsg_cg_mapping.json`: the RR is the
  only source of jurisdiction and condition, and a configuration can't be
  looked up without it. Today the file holds only conditions with an active
  refiner configuration (`api/v1/configurations/activation.py:164`). It becomes
  the union of conditions with an active configuration of either kind, and it
  stays where it is (`configurations/{jurisdiction}/rsg_cg_mapping.json`,
  `s3_keys.py:34-44`) so the refining Lambda's read path doesn't move. Each
  Lambda then checks for a `current.json` in its own namespace. The Refiner
  already records "mapped but no active configuration" as skipped.
- **Postgres: separate tables.** For example `diff_configurations`, keyed by
  (jurisdiction, condition `canonical_url`), with its own version and status
  columns mirroring `configurations`. Rules sit in a JSONB column validated by a
  Pydantic model until the catalog settles; normalizing the watch list now would
  mean reshaping tables every time the catalog changes. It keys on
  `canonical_url`, not `conditions.id`, because the id is minted fresh for each
  TES release. A `kind` column on `configurations` was rejected: that table is
  built around code sets and section settings. Separate tables also leave room
  for other ideas about what a diff configuration is.

#### Testing the minimal version

The Lambda sketch doesn't need a diff UI or diff tables. Hand-written diff
`active.json` fixtures are written straight into localstack. The existing
`tests/localstack/eval.py` harness is the model, but it can't be used as-is: it
authors refiner configurations through the running server and database, not
from fixtures (`eval.py:5-17`), and it invokes only the refining Lambda's RIE.
The diff harness reuses its upload and RIE-invocation steps, writes diff
fixtures directly, and still needs the dev stack for any case with refined
input. The version chains are synthetic, built by mutating existing fixtures:

- preliminary → final lab result
- corrected final: `statusCode` stays `completed`, the 4.419 status value
  changes
- discharge time added to the encompassing encounter
- new diagnosis
- `sdtc:deceasedInd` flips
- race or name filled in on an emergency encounter
- a refined → original input-kind switch mid-stream
- regenerated instance ids with no clinical change, which must produce **zero**
  findings. That is the case where DiD's whole-document matching collapsed.

### 4. Output: the main risk

Where change information lands is the **biggest risk in this project**, and
this ADR doesn't decide it. APHL's stated interest is section- or entry-level
`<author>` participations. We have very low confidence that any downstream
system parses them, and the Refiner's users asked for no markup in
`<structuredBody>`. Every option has to answer:

- Who reads it?
- What system parses it?
- What decision does it drive?
- What happens if nothing reads it?

**Interim: a flat file.** The minimal Lambda writes findings to a flat file in
the version store, next to the version record (§B). That isn't the product. It lets the Lambda run and be
measured (DiD's verdict was never logged, which is why the silent evaluation
can't say whether it worked), and it gives the findings model a concrete shape
while the destination is discussed.

**The findings model.** Findings, not an "is actionable" verdict. Each finding
is self-describing:

```json
{
  "source_set_id": "…",
  "jurisdiction": "SDDH",
  "condition_grouper": "07221093-b8a1-4b1d-8678-259277bfba64",
  "version": 3,
  "compared_to_version": 2,
  "input_kind": "refined",
  "refiner_config_version": 7,
  "diff_config_version": 2,
  "sections": [
    {
      "section_loinc": "30954-2",
      "findings": [
        {
          "unit": "result_observation",
          "kind": "status_changed",
          "key": {
            "code": "…",
            "code_system": "2.16.840.1.113883.6.1",
            "display": "…"
          },
          "before": { "status": "active" },
          "after": { "status": "completed" }
        }
      ]
    }
  ]
}
```

- **What every finding carries.** Each finding states its section, unit, kind,
  pairing key with display, and before and after values. Nothing needs the
  source XML to be read.
- **No findings is itself useful.** An empty findings list under this
  configuration is the "nothing new" signal PHAs asked for, for example to avoid
  reopening closed cases. It replaces `is_actionable` without pretending to be a
  global judgement.

**Where findings could land.** Listed for discussion, with no recommendation:

| Option                                                         | Who reads it                     | Pros                                                                | Cons                                                                                                                                                     |
| -------------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Flat file in S3 (interim)                                      | Us; anything AIMS picks up later | No effect on the delivered document; measurable; easy to throw away | No PHA sees it unless something new is built                                                                                                             |
| Document-level `author` + `relatedDocument` (header only)      | Systems that read CDA headers    | Within the IG; header changes are low-risk for parsers              | Says _that_ a diff happened, not _what_ changed                                                                                                          |
| Section-level `<author>`                                       | What APHL is asking for          | Scoped where PHAs read; follows the IG pattern                      | Refiner users asked for no markup in `<structuredBody>`; no known parser reads it; `did-*` function codes sit outside the bound value set (CONF:5573-43) |
| Entry-level `<author>`                                         | Machine readers                  | Most precise                                                        | Highest parser risk; same value-set problem                                                                                                              |
| Narrative in the section's `<text>` (footnote or summary line) | Epidemiologists reading the HTML | Reaches the person who acts; the Refiner already writes footnotes   | Not machine-readable; edits the document PHAs read                                                                                                       |
| Separate summary document (HTML or CDA)                        | Epidemiologists                  | Delivered document untouched                                        | AIMS needs a new delivery path; a second artifact to track                                                                                               |
| Signal to AIMS (metadata or message attribute)                 | AIMS routing                     | Supports "don't reopen closed cases"                                | That is gating, which is out of scope; needs AIMS work                                                                                                   |

### 5. Does the Refiner need to emit author tags for the diff?

**Not for the minimal version.** The diff shares the Refiner's code but not its
runtime state, so anything it needs about the Refiner's decisions has to be
written out. Today the XML is the only thing written out, and it doesn't carry
those decisions reliably:

- The "why this entry was kept" information exists only as XML comments
  (`services/ecr/section/utils.py:249-287`).
- The Refiner strips comments from each section it processes
  (`narrative/elements.py:92`), so that information doesn't survive a hop.

The Refiner should instead write a **machine-readable refinement trace** next
to each refined output. Per section it records: `SectionOutcome`, entries kept
and removed (counts), and for each kept entry the rule and code that matched.
This is the same information as the comments and the footnote, in a form the
diff can read.

- **Within one version**, it explains why an entry is present.
- **Across versions**, it separates "the clinical data changed" from "the
  configuration changed".

The trace applies only to refined input. An original pair has no Refiner
decisions to explain. It isn't needed for the minimal version, because §6 flags
configuration changes from the version numbers alone and removed sections
compare equal (§2); it's the natural next step
once findings need to say _why_ an entry is present.

Section-level and entry-level IG `author`s carrying that same information can
follow later, as a per-deployment setting, when PHAs are ready for markup in
`<structuredBody>`.

### 6. Configuration changes between versions

If a PHA changes either configuration between v2 and v3, the findings mix
clinical change with configuration change: a refiner configuration change alters
what's in the refined documents, and a diff configuration change alters what
counts as a finding. The footnote already
records `config_version` (`narrative/footnote.py:148-149`). The minimal version:

- **Records** both configuration versions (refiner and diff) per stored
  version.
- **Flags** a change in either in the findings rather than silently diffing
  across it.

A change of input kind (refined ↔ original) between versions is flagged the
same way (see "Stream identity" under §1).

Keeping the **original** eICR/RR keys per version leaves room for a later fix:
re-refine the previous original under the current configuration, then diff.
That only works if the original is still there, which is the reference-or-copy
question in §B.

## Out of scope for the minimal version

- Criteria spanning versions or entries (order → result, "hold until a confirmed
  lab arrives"). The storage and finding shapes above leave room for them.
- Summaries across more than two versions.
- Diffing narrative text beyond `narrative` / `changed`, i.e. saying _what_
  changed in a narrative.
- Comparing RR conditions and jurisdictions across versions (§3).
- Gating or suppressing delivery in AIMS. The diff only informs.
- Writing any augmentation markup into delivered documents until §4 is decided.
- The configuration UI. The minimal version is tested with hand-written
  `active.json` fixtures (§3).

## Consequences

- AIMS must route a trigger (`RefinerComplete`, or a `DIDInput`-style manifest)
  to a second function, and provision its queue and a version-store bucket or
  prefix. No DynamoDB.
- `RefinerComplete` gains three additive fields (§1).
- `rsg_cg_mapping.json` widens to cover conditions with an active configuration
  of either kind (§3).
- Postgres gains diff configuration tables, separate from `configurations`.
- `dibbs-ecr-diff` would become a reference implementation. Its stable-key
  ladder (`core/cda/stable_key.py`) and schema-ordered insertion
  (`core/cda/xsd_sequence.py`) are worth porting. Its XPath rule engine,
  whole-document walk and `is_actionable` verdict are not.
- The configuration UI eventually gains a "diff" area per condition. Activation
  writes to a second S3 namespace.
- If built, the refinement trace (§5) is a new output the Refiner commits to.

## Open Questions

1. **Routing through AIMS (for the APHL tech sync).** The diff needs no new
   "should this continue" variable: `RefinerComplete` already carries it (§1).
   The questions for AIMS are:
   - Can AIMS route `RefinerComplete` to a second consumer?
   - Does every eICR go through the Refiner, including jurisdictions that don't
     use it? If not, diff-only jurisdictions never get a `RefinerComplete`.
   - What should happen on the error signal (`RefinerSkip: true`) and in
     maintenance mode (no file is written at all)?
   - AIMS already builds a `DIDInput` manifest for DiD from refiner output and
     originals. Is reusing that contract (adding the condition grouper and
     original keys per entry) less work for AIMS than routing `RefinerComplete`
     to a second consumer?
   - How long does AIMS keep `RefinerOutputV2/`, `eCRMessageV2/` and
     `RRMessageV2/`? This decides reference vs copy (see the note in §B).
   - Which `setId` does AIMS write into each `DIDInput` entry: the one in the
     document it points at (the refiner's per-(jurisdiction, condition grouper)
     setId for a refined pair) or the sender's? DiD's dev uploader reads it from
     the input eICR (`e2e/helpers.py:191-201`), but AIMS's own manifest builder
     isn't in either repository. This decides whether DiD's production streams
     were per condition or per sender document.
   - Is anything upstream of the Refiner rewriting `setId` (text-to-code)? This
     decides whether the stream key is the input's `setId` or the oldest
     `relatedDocument/parentDocument/setId` (see "Stream identity" under §1).
   - Does AIMS deliver versions of the same document in order? Can the queue be
     FIFO-grouped by `setId`? This bounds the out-of-order problem in §B.
   - What does reprocessing do? The silent evaluation has a reprocessed-entries
     query (q14). A re-delivered version is a no-op under `If-None-Match`, but a
     reprocess _after_ a configuration change is ambiguous: keep the first record
     or replace it?
   - What is a `persistence_id`: one per eCR version, and stable across
     reprocessing? The evaluation materials describe it two different ways.
   - How does the second consumer subscribe (S3 event → EventBridge rule, or SNS
     fan-out)? A failing diff must never back up the queue that delivers
     `RefinerComplete`.
2. **Where do findings land?** The main risk; see §4. Who reads them, what
   system parses them, what decision they drive.
3. **What is in the default configuration?** For each section: the unit, the
   pairing key, which differences matter, and which are noise. It needs real
   v1 → v2 eICR pairs to validate against; none have been available so far.
4. **APHL's original actionability criteria in prose.** The baseline XPaths were
   translated from a conversation. We need the source to check the default
   configuration against.
5. **What DiD received in the silent evaluation.** Its manifest accepts refined
   pairs, original pairs and remainder RRs. Which did production send, and in
   what mix? And which DiD build and configuration ran? Neither is stated in the
   evaluation materials.
6. **Retention.** How long may versions be kept, and does a PHA's data-sharing
   agreement require deletion by jurisdiction? This is APHL's decision.
   `documentId` may count as PII (`dibbs-ecr-diff/docs/Storage-Architecture.md:208`).
7. **IG semantics.**
   - The `did-*` function codes sit outside the bound Data Augmentation Tool
     Operation value set (CONF:5573-43). Propose codes to the IG rather than
     invent them.
   - Can one document reference several prior versions in `relatedDocument`,
     for multi-version summaries?
8. **Trigger and RR comparison** has no user-research or CSTE basis yet. It's a
   product judgement and needs PHA validation. RR comparison also needs its own
   record per (source `setId`, jurisdiction), because per-condition streams
   can't see a condition appear or disappear (§3).

## Links

- `CDCgov/dibbs-ecr-diff` @ `314e7e0`: `docs/01-Technical-Overview.md`,
  `docs/Configuration-Spec.md`, `docs/Storage-Architecture.md`,
  `packages/core/src/core/cda/stable_key.py`
- `app/lambda/RefinerComplete.md` (the `RefinerComplete` schema)
- ADR 0003 (activation S3 file structure), ADR 0006 (condition grouper-level
  Lambda), ADR 0012 (updating active configs in S3)
- HL7 CDA R2 IG: Public Health Case Report (eICR) STU 3.1.1. Trigger code
  templates `2.16.840.1.113883.10.20.15.2.3.*`; Laboratory Observation Result
  Status `2.16.840.1.113883.10.20.22.4.419`
- CSTE eCR Consensus Criteria: Completeness Thresholds for Priority Data
  Elements (February 4, 2026), Table 1 and Appendix A
- eCR Data Augmentation IG v5 (`relatedDocument`, author participations,
  CONF:5573-*)
