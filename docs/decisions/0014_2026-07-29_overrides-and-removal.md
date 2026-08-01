# 14. overrides-and-removal

Date: 2026-07-29

## Status

Proposed

## Context and Problem Statement

Refinement today is **retention-by-inclusion**. A jurisdiction's configuration
describes what it _wants_ in the output--a set of codes drawn from TES
conditions plus custom codes--and both matching engines
(`entry_matching.process`, `generic_matching.process`) keep the entries whose
codes are in that want-set and prune everything else. A code that is not in the
want-set already exerts zero pull on the output; it simply never causes an entry
to be retained.

We want to add the ability to describe what a jurisdiction _does not_ want. From
talking it through, there are two distinct needs, and they are **not** the same
mechanism:

1. **De-selection (the "overrides" case).** A jurisdiction is looking at the
   codes a TES condition (or a code set) contributes and decides it does not
   want one of them to participate in refinement. This is a statement about the
   _want-set_: "this code should stop pulling entries into the output." It is
   purely subtractive against the positive set.

2. **Suppression (the "removal" case).** A jurisdiction has codes it never wants
   to appear in the output, _no matter what_--even if some other rule would
   otherwise retain the entry that carries them, and even in sections that
   refinement does not touch at all. This is an active removal that overrides
   inclusion.

> [!NOTE]
> **Terminology.** "Activate/deactivate" is already a first-class
> **configuration lifecycle** in this codebase (`draft → active → inactive`,
> with `s3_url` set/nulled and events emitted--see `activate_configuration_db`
> / `_deactivate_configuration_db` in
> `refiner/app/db/configurations/activations/db.py`). To avoid collision, this ADR calls
> the code-level opt-out **de-selection**, never "deactivation." A user
> _de-selects_ a code; they _deactivate_ a configuration.

The core realization driving this ADR is that these two needs map onto two
completely different seams in the pipeline, and conflating them would produce a
worse design for both:

- De-selection never needs to touch XML traversal. Because refinement only
  retains what is in the want-set, removing a code from the want-set is
  sufficient to stop it retaining anything. The cleanest place to do this is
  **before** the want-set is ever materialized--at the point where `active.json`
  is projected from the configuration.

- Suppression **cannot** live inside the section-processing engines, because of
  a structural fact in `refine_eicr`: most sections never reach those engines.
  A "no matter what" guarantee has to run across the whole document,
  independent of each section's `(include, action, narrative)` instructions.

This ADR sketches both mechanisms, identifies the seams and the new objects, and
prototypes the interfaces so that whoever picks up the implementation has a clear
map of where things plug in.

## Decision Drivers

- **Semantic honesty.** De-selection is subtractive on the want-set; suppression
  is an override on the output. The design should reflect that they are
  different, not force them through one path.
- **Reuse over reinvention--but only when a second consumer exists.** The
  section-aware pruner in `entry_matching.py` already encodes the hard part--
  entry-level vs. container-level vs. whole-entry pruning, driven by IG
  `EntryMatchRule`s. Suppression should reuse that knowledge, but we extract
  shared abstractions only when we actually have two consumers (see
  _Implementation sequencing_), not speculatively.
- **Auditability / visibility.** Users must be able to _see_ which codes they
  have de-selected (and re-select them), and reviewers must be able to tell a
  suppression removal apart from ordinary refinement pruning. This codebase is
  heavy on provenance (match comments, section footnotes,
  `SectionProvenanceRecord`) and the new features should not break that norm.
- **Keep the hot path clean.** The matching-time payload (`code_system_sets`) is
  read on every refinement. De-selection should not add per-match runtime work
  or new fields to that structure.
- **Predictable precedence.** When a code is both wanted and suppressed,
  behavior must be unambiguous and require no reconciliation logic.
- **Minimize CDA breakage risk.** Any removal must leave the document
  schema-valid; we cannot delete a leaf code element and leave a parent that
  `SHALL` contain it.

## Considered Options

### Feature A--De-selection

#### A1. Anti-join at projection time (RECOMMENDED)

Store the set of de-selected codes as first-class configuration state in the DB,
and apply the anti-join in `convert_config_to_storage_payload`
(`refiner/app/services/configurations.py:196`)--the single point where condition codes
and custom codes are collected into `coding_by_code_system` and handed to
`CodeSystemSets.from_dict`. De-selected codes are filtered out **before**
`code_system_sets` is built, so they never enter `active.json`.

**Pros**

- Downstream is completely untouched. Both matching engines, the plan builder,
  and the lambda read the same `code_system_sets` they always have--it just no
  longer contains the de-selected codes.
- Zero matching-time cost and no new field on `ProcessedConfiguration` /
  `CodeSystemSets`.
- The DB remains the expressive source of truth: the UI can render "de-selected"
  state, users can re-select, and the choice is auditable. `active.json` stays a
  clean projection.

**Cons**

- The projection loses the distinction ("this code came from TES but was turned
  off")--but that distinction lives in the DB where it belongs, so this is
  acceptable.
- Requires a new table + read path (mirrors the `custom_codes` work in #1528).

#### A2. Subtract at `ProcessedConfiguration.from_dict` runtime

Keep the full `code_system_sets` in `active.json` plus a separate `de_selected`
set, and subtract on read in `terminology.py`.

**Pros**: preserves the "was in TES, turned off" intent inside the payload.
**Cons**: adds a field to the hot-path object and a per-refinement subtraction;
puts policy in the executor rather than the projection. Rejected as
unnecessary--the DB already preserves intent.

#### A3. Filter inside the matching engines

Pass the de-selected set to the engines and skip matches on those codes.

**Cons**: this is exactly the reinvention we want to avoid--de-selection has no
reason to touch XML at all, since a code absent from the want-set already
retains nothing. Rejected.

### Feature B--Suppression

#### B1. Cross-cutting pre-pass that reuses IG rules in subtractive mode (RECOMMENDED)

Add a suppression pass, `suppress_eicr`, that runs in `refine_for_condition`
(`refiner/app/services/pipeline.py:219`) **before** `refine_eicr`--at the
plan-building seam around `pipeline.py:298`, just ahead of the `refine_eicr` call
at `pipeline.py:304`. This is the right home because the pipeline calls
`refine_for_condition` once per reported condition--though note the seam is
configuration-wide today (it holds the whole `ProcessedConfiguration` and no
`condition_id`), so genuinely per-`(configuration, condition)` scoping is not
free; see the scoping note under _Prototyping--Feature B_. The pass walks every
section in the `structuredBody` regardless of section instructions. For each
section:

- If the section has `entry_match_rules` in its `SectionSpecification`, reuse
  those same rules to locate code-bearing elements, but invert the decision:
  prune the entry/container where a code matches the **suppression set**, using
  the rule's own strategy (`prune_container_xpath`, `preserve_whole_entry`,
  guards). The "surgical vs. whole-entry" decision is already encoded in the
  rules--we get it for free.
- If the section has no rules, fall back to entry-level removal of any entry
  carrying a suppressed code (the inverse of `generic_matching`'s context
  filter).

**Pros**

- Universal coverage: because it runs before `refine_eicr` and ignores section
  instructions, it also cleans `action="retain"` sections, `NARRATIVE_ONLY`
  sections, and `SECTION_PROCESSING_SKIP` sections--the ones refinement never
  visits.
- Correct precedence for free: removing suppressed codes first means the
  subsequent refinement pass cannot re-introduce them (it only retains what is
  present). Suppression beats inclusion with no reconciliation logic.
- Reuses the IG rule metadata and pruning strategies instead of duplicating them.

**Cons**

- The container-prune decision is _inverted_ relative to positive refinement
  (drop matched containers, keep the rest), so it is the same rule metadata
  driving new keep/drop logic--a bounded amount of new code, not a free reuse
  of `_prune_at_container_level`.
- Two traversals of refinable sections (suppress, then refine). Cheap, and the
  clarity is worth it.

#### B2. Parallel generic scanner (whole-entry only)

A standalone pass that searches the whole document generically and removes any
entry containing a suppressed code, without consulting IG rules.

**Pros**: simplest to write; one uniform behavior.
**Cons**: crude--cannot surgically prune a suppressed sub-observation out of an
otherwise-wanted panel; either over-removes (whole entry) or reinvents the
container logic. Loses the section-aware precision we already have.

#### B3. Hook suppression into the matching engines only

Thread the suppression set into `process_section` and subtract there.

**Cons**: fails the core requirement. `refine_eicr` only calls `process_section`
for `action="refine"` sections (branch 3); `retain`, narrative-only, and skip
sections bypass it entirely (`refiner/app/services/ecr/refine.py:484-542`). A code
suppressed "no matter what" would survive in every section refinement does not
touch. Rejected--this is the decisive argument for a separate pass.

## Decision Outcome

> [!IMPORTANT]
> Direction not yet finalized--this document captures the recommended shape
> from the spike so the team can react before implementation. The two
> reframings below are the load-bearing conclusions.

Recommended direction:

- **Feature A (De-selection): option A1.** De-selected codes are stored in the
  DB as first-class config state and anti-joined out during projection in
  `convert_config_to_storage_payload`. Nothing downstream changes.
- **Feature B (Suppression): option B1.** A `suppress_eicr` pre-pass runs before
  `refine_eicr` across all sections, reusing IG `EntryMatchRule`s in subtractive
  mode where they exist and falling back to entry-level removal where they do
  not.

Resolved design decisions (from spike discussion):

- **Suppression scope: configuration + condition, per jurisdiction.** Not
  jurisdiction-wide. A suppression entry belongs to a `(configuration,
  condition)` pair. The per-condition `refine_for_condition` seam is where this
  _would_ apply, but that seam is not per-condition for free today--it holds a
  config-wide payload and no `condition_id`. Making the deny-set honor the
  condition axis is a real decision, spelled out under _Prototyping--Feature B_.
- **Granularity: code + code system** for both features. Shaping the deny-set as
  a `CodeSystemSets` reuses OID-scoped `find_match`, so "code X in SNOMED" is
  distinguished from "code X in a local system" and we avoid over-removal.
- **Provenance is minimal and content-free.** Suppression emits a single generic
  per-section footnote line ("Data in this section was masked")--no code, count,
  or domain--because the codes are suppressed precisely for their sensitivity.
  Nothing goes in the `trace.json` sidecar for now, and de-selection gets no
  document provenance at all (the app configuration is the record). See
  _Prototyping--Feature B → Provenance (decided)_.

Two reframings that should survive into implementation:

1. **Coverage vs. strategy are different axes.** Suppression's _coverage_ is
   universal (every section, ignoring instructions); its _pruning strategy_ is
   rule-driven where rules exist. Collapsing these into "generic search
   everywhere" is what leads to a crude scanner.
2. **Suppression must be its own pass because most sections never reach the
   matching engines.** This is the structural reason B1 beats B3, and it should
   be stated as an invariant wherever the pass is documented.

> [!NOTE]
> **Scope: eICR only; the RR is unaffected.** De-selection edits
> `code_system_sets`, not the `included_condition_rsg_codes` the RR pass
> (`refine_rr`) filters on--so a de-selected clinical code cannot change which
> conditions the RR reports. Suppression is an eICR-only pre-pass. Neither
> feature touches RR refinement; if a future need arises to suppress content from
> the RR, it is a separate design.

## Appendix

### Design rationale--how these decisions took shape

Recording the reasoning path, not just the endpoints, so a later reader can see
_why_ the design looks the way it does--and why some tempting alternatives were
passed over.

1. **"A way to say what we don't want" turned out to be two needs, not one.**
   The starting ask was singular. The first useful move was noticing that
   "de-select a code a condition contributes" and "never emit this code, ever"
   behave differently: one edits the _want-set_, the other overrides the
   _output_. Forcing them down one path would have compromised both.

2. **De-selection falls out of retention-by-inclusion.** Because refinement only
   ever _retains what is in the want-set_, removing a code from that set is
   already sufficient--no XML logic required. That reframed de-selection as a
   _projection_ concern (strip the code before `active.json` is built) rather
   than an engine concern, which is the whole reason A1 beats A3 and nothing
   downstream changes.

3. **The suppression pass location was decided by a fact in the code, not a
   preference.** The initial instinct was "a pre-processing step inside section
   processing." Reading `refine_eicr` overturned that: `retain`, narrative-only,
   and system-skip sections never reach the matching engines at all. A "no matter
   what" guarantee therefore _cannot_ live in the engines--it has to be a pass
   over the whole document. That single structural fact is the load-bearing
   reason for B1 over B3, and it is why the "no overlap with the engines" claim
   is safe.

4. **"Search everywhere" split into two axes.** Once suppression was a
   whole-document pass, the temptation was a generic scanner. Separating
   _coverage_ (universal--every section) from _pruning strategy_ (rule-driven
   where IG rules exist) avoided a crude whole-entry-only scanner and let
   suppression reuse the surgical container logic the positive path already
   encodes.

5. **Reuse only what a second consumer proves.** Rather than abstract refinement
   into a kit of primitives up front, we extract only the piece both paths
   certainly need--the finder--and let _writing_ suppression reveal the true
   shape of anything else. The enrichment seam (see the finder prototype) is the
   payoff: we would not have discovered that enrichment was entangled in the
   finder until a second consumer needed a _non-mutating_ find. That is the YAGNI
   argument made concrete rather than asserted, and it is why the finder is the
   only extraction ticket 1 commits to.

6. **Provenance was shaped by _why_ suppression exists.** Because codes get
   suppressed precisely for their sensitivity, detailed provenance would re-leak
   the very information the removal was meant to hide. That constraint--not a
   convenience call--drove the minimal, content-free footnote line, and
   clarified that de-selection needs no refinement-time trace at all (its codes
   are already gone; the app configuration is the record).

### Implementation sequencing (YAGNI-first)

Feature B shares real logic with positive refinement, which raises the question
of whether to abstract refinement into composable pieces first. The discipline
we landed on: **extract shared abstractions only when a second consumer actually
exists**, not speculatively.

What is actually shared vs. divergent between refine and suppress:

- **Shared, already code-set-agnostic--the _finder_.** `_find_matching_entries`
  (`refiner/app/services/ecr/section/entry_matching.py:248`) / `_try_match_entry`
  (`entry_matching.py:281`)
  already take `code_system_sets` as a parameter and do not care whether those
  codes are "wanted" or "denied." This is the one piece both workflows clearly
  want, and it is the only obviously-correct extraction.
- **Divergent--the _pruner_.** Positive keeps matched; suppression drops
  matched. Same structural vocabulary, inverted decision.
  `_prune_at_container_level` bakes the "keep matched" polarity in.
- **Positive-only**--enrichment, match comments, narrative reconstruction.

> [!IMPORTANT]
> Snapshots protect us from _regressing the positive path_; they cannot tell us
> an abstraction is the right shape for suppression. We only learn that by
> writing suppression. So do not abstract the pruner before the second consumer
> exists.

Recommended ticket sequence:

0. **Snapshot coverage check (cheap insurance).** Confirm the scenario snapshots
   (`refiner/tests/integration/scenarios/snapshots/…`) exercise each pruning branch--
   container-level (Results/Vitals), whole-entry preservation
   (meds/immunizations), and the generic path--so the finder extraction is not
   unguarded on a branch.
1. **Pure, snapshot-identical refactor.** Extract
   `find_entry_matches(section, code_system_sets, rules) -> list[EntryMatch]`
   (and the section-iteration helper) into a shared home with a polarity-neutral
   name. No behavior change; golden `expected_eICR.xml` + `expected_trace.json`
   are the guardrail. Small and reviewable.
2. **Feature B.** Build `suppress_eicr` on the extracted finder + a _new_
   inverted pruner + its own provenance, with new suppression snapshots. This is
   where the true shape of the shared prune vocabulary is discovered.
3. **(Optional) Unify** the two prune paths only if ticket 2 surfaces genuine
   duplication. Rule of three: with two concrete consumers, the abstraction
   writes itself instead of being guessed.

Feature A ships on its own track--it touches no XML and has no dependency on any
of this.

### Prototyping--Feature A (De-selection)

#### Storage (mirror `custom_codes`)

`custom_codes` (schema.sql:263) is the pattern to copy: a per-configuration table
keyed by `(configuration_id, system_id, code)`.

```sql
-- deselected_codes: codes the jurisdiction has turned OFF for a configuration.
-- a row means "this (system_id, code) should NOT enter the want-set for this
-- configuration, even though a linked condition/code set contributes it."
CREATE TABLE public.deselected_codes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    configuration_id uuid NOT NULL,
    system_id uuid NOT NULL,
    code text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);
-- one de-selection per (config, system, code); idempotent toggles.
-- SCOPE UNDER DISCUSSION: this sketch is config-scoped, but de-selection may be
-- (configuration, condition)-scoped like suppressed_codes--see the "Feature A
-- design question" note below. If so, add condition_id here and to this UNIQUE.
ALTER TABLE ONLY public.deselected_codes
    ADD CONSTRAINT deselected_codes_configuration_id_system_id_code_key
    UNIQUE (configuration_id, system_id, code);
```

`DbConfiguration` (`refiner/app/db/configurations/model.py:105`) gains a
`deselected_codes: list[DbDeselectedCode]` field alongside `custom_codes`,
loaded in the same row-mapping path. The new table also needs a schema migration.

> [!NOTE]
> **Reseed persistence--resolve before wiring these tables up.** `seed_db.py`
> clears a set of tables with `TRUNCATE ... RESTART IDENTITY CASCADE`
> (`refiner/scripts/seeding/seed_db.py:23-34`--the table list and the `TRUNCATE`
> statement), and `configurations` is in that set. Because
> `custom_codes` carries an FK to `configurations` (`refiner/schema.sql:820`),
> `TRUNCATE ... CASCADE` on `configurations` **also truncates `custom_codes`**--
> Postgres cascades a truncate to every table that references a truncated one,
> regardless of the FK's `ON DELETE` action (and `custom_codes`'s FK has none). So
> `custom_codes` does **not** survive a reseed today; being absent from the
> _explicit_ truncation list does not protect it. `deselected_codes` and
> `suppressed_codes` mirror `custom_codes` with the same `configuration_id` FK, so
> they inherit exactly this behavior--there is no "sit outside the truncation
> set" escape while they reference `configurations`. The real question is upstream:
> is `seed_db.py` ever run against a database holding live jurisdiction configs? If
> so, per-configuration user state (custom codes included, _today_) is already at
> risk, and that is a broader issue to settle before adding more per-config user
> tables. If reseed only ever runs against a fresh database, the concern is moot.
> Decide which is true before relying on any of these tables persisting.

#### The projection seam (the one place that changes)

`convert_config_to_storage_payload` builds `coding_by_code_system` from custom
codes (`configurations.py:222`) and condition codes (`configurations.py:248`),
then calls `CodeSystemSets.from_dict`. The anti-join sits right before that call:

```python
# build the set of (system_key, code) pairs the jurisdiction turned off.
# keyed by system so we never remove the same digits under a different system.
deselected: set[tuple[CodeSystemKey, str]] = {
    (code_systems[dc.system_id].key, dc.code)
    for dc in configuration.deselected_codes
}

# anti-join: drop de-selected codes before the want-set is materialized.
# after this point nothing downstream can tell a code was ever de-selected--
# that intent stays in the DB, which is where the UI reads it from.
coding_by_code_system = {
    system_key: [c for c in codings if (system_key, c["code"]) not in deselected]
    for system_key, codings in coding_by_code_system.items()
}

code_system_sets = CodeSystemSets.from_dict(
    coding_by_code_system=coding_by_code_system,
    oid_to_system_map=OID_TO_SYSTEM_KEY_MAP,
)
```

> [!NOTE]
> Everything downstream of this function--`ProcessedConfiguration.from_dict`,
> both matching engines, the lambda--is unchanged. That is the whole appeal of
> A1: the seam is one function.

#### Feature A note--de-selection, custom codes, and origin in the payload

The anti-join filters `coding_by_code_system`, which holds **both**
condition-contributed codes and custom codes (both are appended in
`convert_config_to_storage_payload`--custom at `configurations.py:222`,
condition at `:248`). The merged dict does not record where a code came from--
each entry is a bare `Coding(code, display, system_oid)`--so a de-selection
keyed on `(system, code)` matches any code with those digits in that system,
regardless of origin.

This origin-blindness is **intentional, not a gap.** These payload objects
(`active.json` / `CodeSystemSets`) exist to carry only what `refine_for_condition`
needs to refine; origin is not one of those things, so we deliberately do not
thread it through. What keeps the origin-free shape _mostly_ safe is a
duplicate-prevention check plus a planned unified management surface--but the
check is advisory, so this is not safe purely by construction and deserves the
team's eyes:

- **A duplicate-prevention check exists, but it is advisory.**
  `validate_custom_code` (`refiner/app/api/v1/configurations/custom_codes.py:627`) rejects
  a desired custom code that collides with an existing code. It aggregates across
  **all** included conditions (`custom_codes.py:673-674`) into a flat,
  **system-agnostic** `set[str]` of bare code strings, plus existing custom
  codes--so it is actually _broader_ than the ADR's `(system, code)` anti-join.
  BUT it is a standalone `/validate` endpoint (a frontend pre-check). The
  server-side
  write paths do **not** re-run it: `add_custom_code` (`custom_codes.py:77`)
  validates only fields / lock / draft / system, and the CSV upload's
  `_check_row_response_for_duplicates` (`custom_codes.py:274`) checks
  custom-vs-custom and within-batch only--neither compares against condition/TES
  codes. So a custom code duplicating a TES code _can_ still reach the payload via
  those paths.
- **One management surface (planned).** Custom-code add/remove and code
  selection/de-selection are intended to live in the _same_ place, so there is no
  "two surfaces stepping on each other" arbitration problem; a user turns a code
  off in one view whether it originated from TES or was added by hand.

> [!NOTE]
> **Flag for the team--this is not safe purely by construction.** Because the
> payload is deliberately origin-free, correct de-selection leans on the advisory
> duplicate check (which the normal UI flow honors) and the unified surface,
> rather than on the projection distinguishing origins. In the common path that is
> fine. The residual risk is that the check is _not_ enforced on the write paths,
> so a custom code duplicating a TES code can slip in--after which a de-selection
> of that `(system, code)` would strip the custom code as collateral. If the team
> wants a hard guarantee, the options are (a) enforce the duplicate check on
> `add_custom_code` / CSV confirm, or (b) scope the anti-join to condition-origin
> codes (filter before custom codes merge, or tag by origin). Prefer (a)--it
> keeps the payload origin-free--but this should be a deliberate call, not an
> assumption.

#### Feature A design question--carry code system through, flatten on demand

A granularity tension surfaced while reconciling the duplicate check with the
anti-join: the two operate at **different resolutions.** `validate_custom_code`
compares bare code strings (`set[str]`, system-agnostic--`custom_codes.py:671`),
while the A1 anti-join keys on `(system_key, code)`. A system-agnostic comparison
is coarser than the code+system granularity this ADR chose everywhere else (see
_Decision Outcome -> Granularity_): it can flag or strip "code X" across all
systems when the jurisdiction only meant "code X in SNOMED."

Proposal to weigh: let the **intermediate** models--the ones between the DB rows
and the projected payload--carry the code system alongside each code, so any
anti-join or duplicate check performed on them is **faithful**, scoped to
`(system, code)` rather than bare digits. That richer object then exposes a method
to produce a flat `set[str]` **on demand** for hot-path consumers that genuinely
want a bare-code lookup. The end-state object that lands in S3 and that the webapp
reads stays the same clean, minimal, fast shape it is today--it is simply
_derived_ from the system-aware model rather than being the only representation.

This keeps two properties that currently pull against each other:

- **Fidelity** where correctness matters--the anti-join and the duplicate check
  both become system-scoped, matching the granularity the ADR already committed
  to.
- **Leanness** where speed matters--the flat set is generated when needed, and
  the persisted/served payload does not grow (consistent with the origin-free,
  "only what refinement needs" principle above).

> [!NOTE]
> **Open for the team--please react.** Three things to settle:
>
> 1. **Where the system-aware model lives** and which object the flat set is
>    projected from, in `convert_config_to_storage_payload`'s flow.
> 2. **Whether `validate_custom_code` should move to `(system, code)` granularity**
>    to match the anti-join. Today it is deliberately broader (bare string), which
>    _over_-blocks safely but is inconsistent with the chosen granularity--a
>    jurisdiction cannot add "code X in a local system" if "code X" exists in
>    SNOMED, even though those are different codes.
> 3. **The scope key for de-selection.** De-selection is conceptually **per
>    configuration, per condition, per jurisdiction** (the same scope as
>    suppression; jurisdiction is implied by the configuration). The current
>    `deselected_codes` sketch is keyed only by `(configuration_id, system_id,
code)`--if de-selection is truly condition-scoped, that table needs a
>    `condition_id` the way `suppressed_codes` does, and the anti-join must load
>    the de-selected set **per condition** at the `refine_for_condition` seam
>    rather than once per configuration.

### Prototyping--Feature B (Suppression)

#### Storage (per-config, condition-scoped)

Scope is configuration + condition. Mirror `custom_codes` but add a condition
association so the deny-set can be narrowed to the condition being refined.

> [!IMPORTANT]
> **Per-condition scoping is not free at the current seam--decide this before
> building.** The DB table is keyed `(configuration_id, condition_id, ...)`, but
> the runtime the pass plugs into is configuration-wide.
> `convert_config_to_storage_payload` flattens _all_ `included_conditions` into
> one `coding_by_code_system` and emits **one `active.json` per configuration**
> (`refiner/app/services/configurations.py:248`), and `refine_for_condition` is
> handed that whole payload with no `condition_id`. There are two ways to make
> the deny-set actually honor the condition axis, neither cost-free:
>
> 1. **Structure the payload per condition.** Have `ProcessedConfiguration` /
>    `active.json` carry the deny-set keyed by condition, and select the right
>    subset inside `refine_for_condition`. Keeps the lambda's S3-only resolution
>    model, but grows the payload past the "only what refinement needs"
>    principle.
> 2. **Thread a `condition_id` into `refine_for_condition` and load from the
>    DB.** Smallest payload, but the lambda resolves configs from S3, not the DB,
>    so this path does not exist there today.
>
> The prototype below carries a single `suppressed_codes: CodeSystemSets` on
> `ProcessedConfiguration`--effectively **option 1 collapsed to config-wide**.
> That is correct as a "never emit, no matter what" deny-set, but it does not yet
> distinguish conditions. The identical tension applies to Feature A's projection
> anti-join (same flattening seam)--see _Feature A design question_ and open
> question 3.

```sql
-- suppressed_codes: codes that must NEVER appear in the output for a given
-- (configuration, condition), regardless of section instructions.
CREATE TABLE public.suppressed_codes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    configuration_id uuid NOT NULL,
    condition_id uuid NOT NULL,
    system_id uuid NOT NULL,
    code text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);
ALTER TABLE ONLY public.suppressed_codes
    ADD CONSTRAINT suppressed_codes_config_condition_system_code_key
    UNIQUE (configuration_id, condition_id, system_id, code);
```

#### New objects

```python
# app/services/terminology.py--carried on ProcessedConfiguration
@dataclass(frozen=True)
class ProcessedConfiguration:
    codes: set[str]
    code_system_sets: CodeSystemSets
    section_processing: list[dict]
    included_condition_rsg_codes: set[str]
    suppressed_codes: CodeSystemSets  # NEW: code+system-shaped deny-set
```

Shaping the deny-set as a `CodeSystemSets` (not a flat `set[str]`) buys the same
OID-scoped `find_match` the positive path uses.

```python
# app/services/ecr/model.py--a sibling of EICRRefinementPlan
@dataclass(frozen=True)
class SuppressionPlan:
    suppressed_codes: CodeSystemSets
    specification: EICRSpecification  # reused to fetch per-section match rules
```

No `augmentation_timestamp` is needed here: suppression does not mint its own
footnote. It reports masked sections back to `refine_eicr`, which stamps
`content_masked` onto the section's existing provenance record--and that
footnote already carries the run's timestamp.

#### The pipeline seam

```python
# app/services/pipeline.py, inside refine_for_condition (~line 298)

eicr_plan = create_eicr_refinement_plan(...)

# NEW: suppression runs FIRST, across all sections, ignoring section
# instructions. removing suppressed codes before refinement means the
# refinement pass--which only RETAINS what is present--can never
# re-introduce them. precedence (suppress > include) falls out of ordering.
# reuse the spec create_eicr_refinement_plan already loaded (no re-detect).
suppression_plan = create_suppression_plan(
    processed_configuration, eicr_plan.specification
)
masked_section_codes = suppress_eicr(eicr_root=eicr_root, plan=suppression_plan)

# masked_section_codes flows into refine_eicr so each section's footnote can
# carry the generic "data in this section was masked" line--see the
# `content_masked` end-to-end wiring under Provenance.
refine_eicr(
    eicr_root=eicr_root,
    plan=eicr_plan,
    masked_section_codes=masked_section_codes,
)
```

#### The container-prune inversion (the one genuinely new bit of logic)

In positive refinement, `_prune_at_container_level`
(`refiner/app/services/ecr/section/entry_matching.py:458`) **keeps** matched containers
and removes the rest. Suppression wants the opposite: **drop** matched
containers, keep the rest. Same rule metadata (`prune_container_xpath`,
`preserve_whole_entry`, `prune_container_guard_xpath`), inverted keep/drop:

| Rule metadata               | Positive (refine)                  | Subtractive (suppress)                 |
| --------------------------- | ---------------------------------- | -------------------------------------- |
| `preserve_whole_entry=True` | matched entry kept intact          | matched entry **removed** intact       |
| `prune_container_xpath` set | keep matched containers, drop rest | **drop** matched containers, keep rest |
| default                     | keep matched entry, drop unmatched | **drop** matched entry                 |

> [!NOTE]
> **`prune_container_guard_xpath` is unnecessary in subtractive mode.** In
> positive refinement the guard exists to _protect_ shared, non-matching context
> (e.g. the Results Specimen Collection Procedure) from being pruned as
> collateral. Suppression only ever removes a container that _itself_ carries a
> suppressed code, so shared context is safe by construction--there is nothing
> to guard against. If a jurisdiction genuinely suppresses the code on a shared
> container, removing it is the correct, requested behavior.

#### Prototype--the subtractive pruner

The prototype below is the rule-driven core (option B1). It reuses two ticket-1
extractions from the shared `section.matching` module--`find_entry_matches` (the
code-set-agnostic finder) and `container_has_matched_descendant` (a shared
predicate)--and adds only the inverted keep/drop decision. `EntryMatch` is reused
verbatim: the finder
does not care whether the codes it was handed are "wanted" or "denied," so a hit
against the deny-set is the same shape as a hit against the want-set.

```python
# app/services/ecr/suppress.py (PROTOTYPE)
"""
Subtractive refinement--remove suppressed ("deny-list") codes from an eICR.

Runs as a PRE-PASS before `refine_eicr`, across every section regardless of its
configured (include, action, narrative). See option B1 above for why the three
load-bearing properties hold--universal coverage, precedence-for-free from
ordering, and the coverage-vs-strategy split--rather than restating them here.
"""

from collections import defaultdict
from typing import Literal, cast

from lxml.etree import _Element

from app.services.format import remove_element
from app.services.terminology import CodeSystemSets

from .model import (
    HL7_NS,
    EntryMatchRule,
    NamespaceMap,
    SectionSpecification,
    SuppressionPlan,
)
# NOTE: get_all_sections + get_section_loinc_code are NEW helpers to add--neither
# exists yet. Today the `section` package exports get_section_loinc_codes(
# structured_body) -> list[str] (codes, not elements) and get_section_by_code(...).
# suppress_eicr needs to iterate section *elements* and read each one's LOINC code,
# so add (a) a section-element iterator and (b) a single-section code accessor--
# both trivial, mirroring the get_section_loinc_codes xpath in section/traversal.py.
from .section import get_all_sections, get_section_loinc_code

# `find_entry_matches`, `container_has_matched_descendant`, and `EntryMatch` are
# the ticket-1 extractions, relocated to the shared `section.matching` module and
# reused verbatim by both positive refinement and suppression.
from .section.matching import (
    EntryMatch,
    container_has_matched_descendant,
    find_entry_matches,
)

# which structural unit a matched entry's rules tell us to remove
type PruneStrategy = Literal["whole_entry", "container", "entry"]


def suppress_eicr(eicr_root: _Element, plan: SuppressionPlan) -> set[str]:
    """
    Remove every suppressed code from the document, section by section.

    Returns the LOINC codes of the sections content was removed from so the
    caller (`refine_eicr`) can stamp `content_masked` on each section's
    provenance record and render the generic "data in this section was masked"
    footnote line. Nothing about *what* was removed leaves this function.
    """

    structured_body = eicr_root.find(".//hl7:structuredBody", HL7_NS)
    if structured_body is None:
        # a document with no structured body has nothing to suppress; the
        # refinement pass will raise on it if it matters
        return set()

    masked: set[str] = set()
    for section in get_all_sections(structured_body):
        loinc_code = get_section_loinc_code(section)
        if suppress_section(
            section=section,
            suppressed_codes=plan.suppressed_codes,
            specification=plan.specification.sections.get(loinc_code),
            namespaces=HL7_NS,
        ):
            masked.add(loinc_code)

    return masked


def suppress_section(
    section: _Element,
    suppressed_codes: CodeSystemSets,
    specification: SectionSpecification | None,
    namespaces: NamespaceMap,
) -> bool:
    """
    Remove suppressed codes from a single section. Returns whether anything was
    removed (drives the section's `content_masked` flag).

    Dispatches on the same axis as `process_section`: rule-driven when the
    section has IG entry match rules, generic entry-level removal otherwise.

    If removal empties a refinable section of its <entry> children, we set
    nullFlavor="NI" here--the same guard the matching engines apply--because
    this pass runs BEFORE refine_eicr and covers sections (retain,
    narrative-only, system-skip) that never reach those engines. Nothing
    downstream would otherwise satisfy the CDA "SHALL contain at least one
    entry" rule for a section we just emptied.
    """

    if specification is not None and specification.has_match_rules:
        removed = _suppress_by_rules(
            section, suppressed_codes, specification.entry_match_rules, namespaces
        )
    else:
        removed = _suppress_generic(section, suppressed_codes, namespaces)

    # a section suppression emptied must still satisfy CDA cardinality. the
    # matching engines do this for `action=refine` sections; we must do it for
    # everything else, since suppression is the only pass that touches them.
    if removed and section.find("hl7:entry", namespaces) is None:
        section.attrib["nullFlavor"] = "NI"

    return removed


def _suppress_by_rules(
    section: _Element,
    suppressed_codes: CodeSystemSets,
    match_rules: list[EntryMatchRule],
    namespaces: NamespaceMap,
) -> bool:
    """
    Locate entries carrying a suppressed code via the shared finder, then remove
    them using each matched rule's own strategy--inverted from positive
    refinement (drop what matched rather than keep it).
    """

    # the finder is code-set agnostic: hand it the deny-set and it returns the
    # entries/elements that carry a suppressed code, using the section's rules.
    hits = find_entry_matches(section, suppressed_codes, match_rules)
    if not hits:
        return False

    hits_by_entry: dict[int, list[EntryMatch]] = defaultdict(list)
    for hit in hits:
        hits_by_entry[id(hit.entry)].append(hit)

    matched_code_element_ids = {id(hit.matched_code_element) for hit in hits}

    removed = False
    for entry_hits in hits_by_entry.values():
        entry = entry_hits[0].entry
        strategy, prune_xpath = _resolve_strategy(entry_hits)

        match strategy:
            case "whole_entry":
                # atomic unit (medications, immunizations, procedures): a denied
                # code cannot be excised without breaking clinical meaning or CDA
                # cardinality, so the entry is removed whole.
                remove_element(entry)
                removed = True
            case "container" if prune_xpath is not None:
                # surgical: drop only the containers (Results / Vital Signs
                # sub-observations) that carry a denied code; siblings survive.
                removed |= _drop_matched_containers(
                    entry, prune_xpath, matched_code_element_ids, namespaces
                )
            case _:
                # default: the denied code defines the entry; drop the entry.
                remove_element(entry)
                removed = True

    return removed


def _resolve_strategy(
    entry_hits: list[EntryMatch],
) -> tuple[PruneStrategy, str | None]:
    """
    Pick the removal strategy for one entry from the rules that matched it.

    Precedence mirrors positive refinement's `_prune_at_container_level`
    (whole-entry preservation wins over container pruning), but the resulting
    action is inverted--the strategy names the unit to *remove*, not keep. The
    returned xpath is populated only for the "container" strategy.
    """

    if any(hit.rule.preserve_whole_entry for hit in entry_hits):
        return "whole_entry", None

    if prune_xpath := next(
        (
            hit.rule.prune_container_xpath
            for hit in entry_hits
            if hit.rule.prune_container_xpath
        ),
        None,
    ):
        return "container", prune_xpath

    return "entry", None


def _drop_matched_containers(
    entry: _Element,
    prune_xpath: str,
    matched_code_element_ids: set[int],
    namespaces: NamespaceMap,
) -> bool:
    """
    Remove the containers under `entry` that carry a suppressed code, keeping the
    rest. If that empties the entry of its containers, remove the now-hollow
    entry too.

    This is the exact inverse of the positive path: there we keep the container
    with a matched descendant and drop the others; here we drop the container
    with a matched descendant. No guard xpath is needed--a container we never
    touch is, by definition, one with no suppressed code in it.
    """

    containers = cast(list[_Element], entry.xpath(prune_xpath, namespaces=namespaces))

    removed = False
    for container in containers:
        if container_has_matched_descendant(container, matched_code_element_ids):
            remove_element(container)
            removed = True

    # only an entry we actually emptied is removed; an entry that still holds
    # sibling containers keeps its surviving clinical content
    if removed and not entry.xpath(prune_xpath, namespaces=namespaces):
        remove_element(entry)

    return removed


def _suppress_generic(
    section: _Element,
    suppressed_codes: CodeSystemSets,
    namespaces: NamespaceMap,
) -> bool:
    """
    Fallback for sections without IG entry match rules: remove any <entry> that
    carries a suppressed code anywhere within it. Entry-level only--there is no
    rule metadata to justify finer-grained pruning, and whole-entry removal is
    the CDA-safe primitive.
    """

    removed = False
    for entry in section.findall("hl7:entry", namespaces):
        coded = cast(
            list[_Element],
            entry.xpath(".//*[@code]", namespaces=namespaces),
        )
        if any(
            suppressed_codes.has_match(code, el.get("codeSystem"))
            for el in coded
            if (code := (el.get("code") or "").strip())
        ):
            remove_element(entry)
            removed = True

    return removed
```

> [!CAUTION]
> **CDA cardinality.** The safe removal primitive is "remove the entry or
> container that the suppressed code _defines_," never "delete the code element
> in place." An `observation` `SHALL` carry a `value`; deleting a leaf `<code>`
> and leaving its parent produces a schema-invalid entry. `preserve_whole_entry`
> and the container xpaths already point at removable structural units--reuse
> them and do not invent finer-grained deletion.

> [!CAUTION]
> **Emptied sections need `nullFlavor`.** Today `nullFlavor="NI"` is set on an
> emptied section _only inside the matching engines_, to satisfy the schematron
> "SHALL contain at least one entry" for refinable sections. Suppression runs as
> a pre-pass over **all** sections, and `retain` / narrative-only /
> `SECTION_PROCESSING_SKIP` sections never reach those engines (`refine_eicr`
> branch 2a for narrative-only and branch 2b for `retain` leave their entries
> untouched). So if suppression removes the last
> `<entry>` from a retained refinable section, nothing downstream sets
> `nullFlavor` and the document is schema-invalid. `suppress_section` closes this
> by applying `nullFlavor="NI"` itself whenever it empties a section--see the
> prototype above and the coverage row in _Test scenarios_.

#### Prototype--the shared finder (ticket 1 extraction)

Ticket 1 lifts the finder out of `entry_matching` into a polarity-neutral home so
both positive refinement and `suppress_eicr` share one traversal + rule-precedence
implementation. The move is mostly mechanical--`_find_matching_entries`,
`_try_match_entry`, `EntryMatch`, and `_container_has_matched_descendant` relocate
and lose their leading underscores--with **one real seam** the second consumer
exposes: displayName enrichment.

> [!IMPORTANT]
> **Enrichment must leave the finder, but it cannot simply be dropped.** Today
> `_try_match_entry` calls `_enrich_display_name(el, coding)` _inline_ the moment
> it matches, mutating the element mid-find. A finder shared with suppression must
> not mutate (we are about to _delete_ those elements), so enrichment moves to the
> caller. The tempting shortcut--"delete the inline call, let STEP 4's
> `enrich_surviving_entries` cover it"--is **not snapshot-safe**: STEP 4 resolves
> the display via each element's own `@codeSystem`, while the inline call uses the
> _rule's_ `code_system_oid`, which is often `None` (broad) or a semantic OID that
> disagrees with the element's literal `@codeSystem`. When they diverge, STEP 4
> misses an element inline enrichment would have labeled.
>
> The lossless fix: the finder is pure and _returns_ the matches; `EntryMatch`
> already carries `matched_coding` (the Coding found via the rule's OID), so the
> positive caller reproduces the old inline behavior exactly by enriching from
> that carried coding. Snapshot-identical, and enrichment is now honestly a
> caller concern.

```python
# app/services/ecr/section/matching.py (PROTOTYPE--ticket 1 extraction)
"""
Polarity-neutral entry matching.

`find_entry_matches` locates the <entry> elements in a section whose codes are
present in a given CodeSystemSets, using the section's IG EntryMatchRules. It is
deliberately agnostic about WHY the caller wants those matches:

  - positive refinement hands it the want-set and KEEPS what it returns;
  - suppression hands it the deny-set and REMOVES what it returns.

The finder makes no keep/drop decision and--unlike the pre-extraction code--no
longer mutates the elements it finds. displayName enrichment is a caller concern:
each EntryMatch carries `matched_coding`, so a caller that wants enrichment reads
it off the match rather than relying on a side effect during the search.
"""

from dataclasses import dataclass
from typing import cast

from lxml.etree import _Element

from app.services.terminology import CodeSystemSets, Coding

from ..model import HL7_XSI_NS, EntryMatchRule, NamespaceMap
from .utils import SDTC_NAMESPACE

# the finder always evaluates against the xsi-extended namespace map: Results
# rules filter on @xsi:type='CD' to tell coded values from physical quantities.
_MATCH_NAMESPACES = HL7_XSI_NS


@dataclass
class EntryMatch:
    """
    One code match inside an <entry>: the entry, the specific code-bearing
    element that matched, the Coding it matched (carrying the display for
    caller-side enrichment), and the rule that claimed it (carrying the prune
    strategy). Unchanged by the extraction--only its home moves.
    """

    entry: _Element
    matched_code_element: _Element
    matched_coding: Coding
    rule: EntryMatchRule


def find_entry_matches(
    section: _Element,
    code_system_sets: CodeSystemSets,
    match_rules: list[EntryMatchRule],
) -> list[EntryMatch]:
    """
    Return every EntryMatch in `section` whose code is present in
    `code_system_sets`, evaluating `match_rules` with structural precedence.

    Pure: it reads the tree and returns matches; it does not prune, enrich, or
    otherwise mutate. Callers decide what the matches mean.

    (Body is `_find_matching_entries` verbatim: iterate <entry> children, call
    `_try_match_entry` on each, flatten the results.)
    """

    matches: list[EntryMatch] = []
    for entry in section.findall("hl7:entry", _MATCH_NAMESPACES):
        matches.extend(_try_match_entry(entry, code_system_sets, match_rules))
    return matches


def _try_match_entry(
    entry: _Element,
    code_system_sets: CodeSystemSets,
    match_rules: list[EntryMatchRule],
) -> list[EntryMatch]:
    """
    Evaluate rules against one entry with structural precedence (a rule that
    finds candidates claims the entry; later rules are not tried).

    Same body as the pre-extraction version EXCEPT (1) the two inline
    `_enrich_display_name(...)` calls are removed--the finder no longer mutates--
    and (2) the `namespaces` parameter is dropped in favor of the module-level
    `_MATCH_NAMESPACES` constant. The matched Coding is still recorded on each
    EntryMatch so a caller can enrich from it.
    """

    entry_matches: list[EntryMatch] = []
    for rule in match_rules:
        code_elements = cast(
            list[_Element],
            entry.xpath(rule.code_xpath, namespaces=_MATCH_NAMESPACES),
        )
        candidates_found = any((el.get("code") or "").strip() for el in code_elements)

        for code_el in code_elements:
            if not (code_val := (code_el.get("code") or "").strip()):
                continue
            if rule.require_value_set_attr and not code_el.get(
                f"{{{SDTC_NAMESPACE}}}valueSet"
            ):
                continue
            if coding := code_system_sets.find_match(code_val, rule.code_system_oid):
                # NOTE: pre-extraction this line was preceded by
                # `_enrich_display_name(code_el, coding)`. That mutation now lives
                # at the positive call site, driven by `matched_coding` below.
                entry_matches.append(
                    EntryMatch(entry, code_el, coding, rule)
                )

        # ... translation_xpath fallback: same shape, same removal of the inline
        #     `_enrich_display_name` call ...

        if candidates_found:
            break

    return entry_matches


def container_has_matched_descendant(
    container: _Element,
    matched_element_ids: set[int],
) -> bool:
    """
    True if `container` (or any descendant) is one of the matched code elements.
    Moved verbatim from entry_matching; shared by the positive container pruner
    and the subtractive one.
    """

    if id(container) in matched_element_ids:
        return True
    return any(id(d) in matched_element_ids for d in container.iter())
```

The two call sites then differ only in what they do with the returned matches:

```python
# positive path--app/services/ecr/section/entry_matching.py, STEP 2 → 3
matches = find_entry_matches(section, code_system_sets, rules)

# reproduce the old inline enrichment losslessly from the carried coding, so the
# rule-OID-derived display is preserved even where STEP 4 would miss it.
for match in matches:
    _enrich_display_name(match.matched_code_element, match.matched_coding)

if not matches:
    ...  # unchanged no-match handling
_prune_section_by_matches(section, matches, namespaces)   # KEEP matched
enrich_surviving_entries(section, code_system_sets, namespaces)  # STEP 4, unchanged


# subtractive path--app/services/ecr/suppress.py
matches = find_entry_matches(section, suppressed_codes, rules)
# no enrichment: these entries are on their way out.
... # invert the prune decision (see the subtractive pruner prototype)
```

> [!NOTE]
> Scope discipline (per _Implementation sequencing_): ticket 1 extracts **only**
> the finder + `container_has_matched_descendant` + `EntryMatch`, plus the
> enrichment lift-out that the extraction forces. It does **not** touch the
> pruners, enrichment internals, comment injection, or narrative handling. The
> golden `expected_eICR.xml` snapshots are the guardrail proving the positive
> path is byte-identical before Feature B is written.

#### Why this isn't a new (or duplicate) matcher

A reader arriving at `find_entry_matches` may reasonably ask whether this is a
fourth copy of code-matching logic. It is not. The relationship: there are
exactly **two** match-finders in the service today, sitting on **one** shared
primitive:

- **`CodeSystemSets.find_match` / `has_match`**--the low-level lookup ("is this
  code, optionally in this system, in my set?"). This is the real shared atom;
  every finder sits on top of it, and always has.
- **`entry_matching._find_matching_entries`**--rule-driven, system-scoped,
  returns rich `EntryMatch`es. **`find_entry_matches` _is_ this function,
  relocated.** It is not a new matcher--the extraction is a move, so the
  "overlap" with the entry path is total and intentional (one implementation,
  one home), not a second copy.
- **`generic_matching._find_condition_relevant_elements`**--the unscoped
  fallback used by sections without IG rules.

The entry finder and the generic finder overlap in _purpose_ but not in
_contract_:

|           | entry finder (extracted)             | generic finder                           |
| --------- | ------------------------------------ | ---------------------------------------- |
| code set  | `CodeSystemSets` (OID-scoped)        | flat `set[str]`                          |
| driven by | IG `EntryMatchRule`s                 | unscoped `.//` xpath sweep               |
| returns   | `EntryMatch` (carries coding + rule) | raw `list[_Element]`                     |
| dedup     | structural precedence                | its own `_deduplicate_clinical_elements` |

We deliberately do **not** unify those two:

- They are different contracts. Reusing the generic finder for suppression would
  **downgrade** it off the code+system granularity we chose--which is exactly
  why `_suppress_generic` calls `CodeSystemSets.has_match(code, @codeSystem)`
  directly rather than borrowing it.
- The generic path is slated to **shrink** as sections migrate to
  `entry_match_rules` (see the `codes_to_check` note on `EICRRefinementPlan`).
  Unifying toward code that is meant to be deleted is the opposite of the YAGNI
  stance in _Implementation sequencing_.

So: one shared lookup primitive (already there), one finder extracted to be
shared (a move, not a copy), and one intentionally-separate fallback. No new
duplication is introduced.

#### Provenance (decided)

The motivation for suppressing a code "no matter what" is usually that it is
sensitive or stigmatizing (e.g. behavioral health, substance use, reproductive
or HIV status). Any provenance that names the suppressed code--or even its
domain/system or a count--would re-disclose the very thing the suppression
removed. So suppression provenance is deliberately **minimal and content-free**:

- **No per-entry comments.** A removed entry has no anchor, and an orphan
  "removed by suppression" comment sitting next to a surviving entry's "matched"
  comment is contradictory at a glance. Suppression does not use the per-entry
  comment path at all.
- **One generic per-section footnote line.** When suppression removes anything
  from a section, the section's existing provenance footnote (rendered by
  `append_section_provenance_footnote`) gains a single line to the effect of
  _"Data in this section was masked."_ No code, no count, **no domain/system**--
  just the bare fact that content was removed here.
- **Nothing in the trace, for now.** The `trace.json` sidecar is deliberately
  _not_ extended with suppression detail. No consumer is asking for it. If an
  itemized, jurisdiction-facing audit is ever needed, the sidecar is the place
  for it (it does not ship inside the eICR), but that is out of scope for this
  work.
- **De-selection has no document provenance at all.** It is a want-set edit made
  in the app; the configuration is the record. We do not echo de-selected codes
  into the output (they could be a handful or thousands, and the user can see
  them in the app).

> [!NOTE]
> The per-section line reveals _which_ section had content masked, but nothing
> about _what_. That granularity is an accepted, deliberate tradeoff--the fact
> that a section was refined is already implied by the document being a refined
> eICR; the sensitive detail (code, domain, count) is what we withhold.

##### End-to-end wiring: `content_masked`

`suppress_eicr` runs as a pre-pass, but the footnote is rendered later inside
`refine_eicr`. So the masked fact travels from the pass, through the plan's
existing per-section provenance record, to the writer. Four small touchpoints,
each riding machinery that already exists.

**1. The record gains one flag** (`refiner/app/services/ecr/model.py`,
`SectionProvenanceRecord`):

```python
@dataclass(frozen=True)
class SectionProvenanceRecord:
    ...
    outcome: SectionOutcome = SectionOutcome.REFINED_WITH_MATCHES
    content_masked: bool = False  # NEW: suppression removed content from this section
```

Defaulting to `False` keeps every existing construction site
(`_build_section_provenance`) unchanged--only the finalize step sets it.

**2. The pipeline runs suppression first and threads the result** into
`refine_eicr` (`refiner/app/services/pipeline.py`, `refine_for_condition`). This
is the same seam shown under _The pipeline seam_ above--the only addition for
provenance is that `suppress_eicr`'s return value (`masked_section_codes`) is
passed into `refine_eicr`:

```python
masked_section_codes = suppress_eicr(
    eicr_root, create_suppression_plan(processed_configuration, eicr_plan.specification)
)
refine_eicr(
    eicr_root=eicr_root,
    plan=eicr_plan,
    masked_section_codes=masked_section_codes,
)
```

**3. `refine_eicr` stamps the flag where it already finalizes the record**
(`refiner/app/services/ecr/refine.py`, the tail of the section loop at ~549). The
signature gains one defaulted parameter so existing callers keep working:

```python
def refine_eicr(
    eicr_root: _Element,
    plan: EICRRefinementPlan,
    masked_section_codes: set[str] | None = None,
) -> None:
    ...
    masked = masked_section_codes or set()

    for section_code, section_rules in plan.section_instructions.items():
        ...
        # (all four existing branches set `outcome`, unchanged)

        if provenance is not None:
            # the record was already going to be finalized here with the runtime
            # outcome; we add the masked flag in the same replace() so there is
            # still exactly one finalize point per section.
            finalized = dataclasses.replace(
                provenance,
                outcome=outcome,
                content_masked=section_code in masked,
            )
            append_section_provenance_footnote(
                section=section,
                provenance=finalized,
                augmentation_timestamp=plan.augmentation_timestamp,
            )
```

Because `plan.section_instructions` is keyed by the same present-section LOINC
codes that `suppress_eicr` reports, the `in` check needs no translation. A
section that suppression emptied _and_ the jurisdiction configured for wholesale
removal still gets a footnote (branch 1 already appends one)--the flag is
harmless there, since the section is a stub regardless.

**4. The writer renders one generic line when the flag is set**
(`refiner/app/services/ecr/narrative/footnote.py`, after the provenance table at ~159):

```python
    # ... existing single-row provenance table ...
    _add_provenance_cell(row, PROVENANCE_OUTCOME_NOTES.get(provenance.outcome, ...))

    # a single generic notice--no code, count, or domain. present only when
    # something was actually removed, absent otherwise.
    if provenance.content_masked:
        masked_paragraph = _sub_element(footnote, "paragraph")
        masked_content = _sub_element(masked_paragraph, "content", styleCode="Italics")
        masked_content.text = MASKED_NOTICE  # constants.py: "Data in this section was masked."
```

Rendering it as a sibling paragraph (not a new table column) keeps the notice
out of every unmasked section entirely--an unmasked section's footnote is
byte-identical to today's, so the existing provenance snapshots do not churn.
Only sections that actually lost content carry the line.

### Test scenarios--suppression (ticket 2 checklist)

The container inversion is the risky part, and "new suppression snapshots" is too
vague to build against. These are the cases ticket 2 must cover; each is also a
`content_masked` assertion. Fixtures build on the existing
`all_sections_covid_influenza` pair.

| #   | Scenario                                                                           | Expectation                                                                                                                |
| --- | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| 1   | Suppress a code in a **Results** panel (container rule)                            | that sub-observation's container removed; sibling observations + guarded Specimen Collection Procedure survive; entry kept |
| 2   | Suppress a code in a **Medications** entry (`preserve_whole_entry`)                | whole entry removed; no partial excision                                                                                   |
| 3   | Suppress the **only** matching code in a default-strategy section                  | whole entry removed                                                                                                        |
| 4   | Suppress a code present in a **`retain`** section and a **narrative-only** section | both removed even though refinement never processes them (coverage proof)                                                  |
| 5   | Suppress a code that is **also in the want-set**                                   | code absent from output; refinement did not re-introduce it (precedence)                                                   |
| 6   | Suppress that removes the **last container**, emptying the entry                   | entry removed too (not left hollow)                                                                                        |
| 7   | Suppress that removes the **last entry** of a **retained refinable** section       | section carries `nullFlavor="NI"`; document still schema-valid (ties to the emptied-section caution)                       |
| 8   | Suppress a code on a **guarded shared-context** container (e.g. code `17636008`)   | that container removed--the guard does not protect it in subtractive mode                                                 |
| 9   | Suppress with an **empty deny-set**                                                | document byte-identical to the no-suppression run; `content_masked` false everywhere                                       |
| 10  | Section with a suppressed code **and** a wanted code in different entries          | only the suppressed entry removed; the wanted entry survives to refinement                                                 |

Ticket 1's guardrail is the inverse: the existing golden `expected_eICR.xml`
snapshots must be **unchanged** after the finder extraction (scenario 9's
"byte-identical" is the same property applied to the refactor).

### Open questions to resolve before building

1. **Feature A de-selection vs. custom codes** (full detail in the _Feature A
   note_ above). Because the payload is origin-free and the duplicate check is
   advisory, a custom/TES duplicate can reach the payload, where a de-selection
   would strip it as collateral. Decide: (a) enforce the duplicate check on the
   write paths (`add_custom_code` + CSV confirm) or (b) scope the anti-join to
   condition-origin codes. Recommended: (a).
2. **De-selection vs. suppression overlap.** A code could in principle be both
   de-selected (removed from want-set) and suppressed (removed from output).
   These are independent and compose cleanly--de-selection stops retention,
   suppression removes anything present--but the UI should probably not offer
   both toggles on the same code in a way that reads as contradictory.
3. **De-selection granularity & scope** (see the _Feature A design question_
   above). Two coupled decisions: (a) whether the intermediate models carry code
   system so the anti-join and the duplicate check are faithful `(system, code)`
   rather than bare strings, with a flat set derived on demand for the hot path;
   and (b) whether de-selection is `(configuration, condition)`-scoped--needing a
   `condition_id` on `deselected_codes` and a per-condition load at the
   `refine_for_condition` seam--rather than config-wide as the current sketch
   assumes.

### Key references

- `convert_config_to_storage_payload`--Feature A seam:
  `refiner/app/services/configurations.py:196`
- `refine_eicr` branch logic (why suppression can't live in the engines):
  `refiner/app/services/ecr/refine.py:470-555`
- `_find_matching_entries` (`entry_matching.py:248`) / `_try_match_entry`
  (`entry_matching.py:281`)--the finder to extract:
  `refiner/app/services/ecr/section/entry_matching.py`
- `_prune_at_container_level` (the strategy to invert):
  `refiner/app/services/ecr/section/entry_matching.py:458`
- `process_section` dispatcher (rules-vs-generic split to mirror):
  `refiner/app/services/ecr/section/__init__.py:21`
- `custom_codes` table (storage pattern): `refiner/schema.sql:263`
- `activate_configuration_db` / `_deactivate_configuration_db` (the lifecycle
  the "de-selection" name avoids colliding with):
  `refiner/app/db/configurations/activations/db.py`
- `refine_for_condition` (Feature B pass placement): `refiner/app/services/pipeline.py:219`

**Be sure to read the information about this in [CONTRIBUTING](https://github.com/CDCgov/dibbs-ecr-refiner/blob/main/CONTRIBUTING.md##Request-for-comment)**
