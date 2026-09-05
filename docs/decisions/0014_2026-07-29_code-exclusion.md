# 14. code-exclusion

Date: 2026-07-29

## Status

Proposed

> [!NOTE]
> **This ADR was split.** It originally covered two features under the title
> _overrides-and-removal_. Review established that they are independent
> decisions on different tracks with different risk, so the second feature now
> lives in [ADR 0015](0015_2026-08-05_overrides.md). This document covers
> **exclusion** only. The shared framing that produced both is in _Context_
> below; 0015 refers back to it rather than restating it.

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

1. **Exclusion.** A jurisdiction is looking at the codes a TES condition (or a
   code set) contributes and decides it does not want one of them to participate
   in refinement. This is a statement about the _want-set_: "this code should
   stop pulling entries into the output." It is purely subtractive against the
   positive set. **This ADR.**

2. **Overrides.** A jurisdiction has codes it never wants to appear in the
   output, _no matter what_--even if some other rule would otherwise retain the
   entry that carries them, and even in sections that refinement does not touch
   at all. This is an active removal that overrides inclusion. **See
   [ADR 0015](0015_2026-08-05_overrides.md).**

> [!NOTE]
> **Terminology.** This ADR uses the names the application uses, per review
> feedback on the original draft:
>
> | Application feature | What it does                           | This codebase          |
> | ------------------- | -------------------------------------- | ---------------------- |
> | **Exclusion**       | turn off a code a code set contributes | `exclusion` (ADR 0014) |
> | **Overrides**       | never emit this code, ever             | `overrides` (ADR 0015) |
>
> The first draft called exclusion "the overrides case," which collides with the
> product's use of "overrides" for the _other_ feature. Naming in code should
> track the feature name so a reader does not have to translate.
>
> Note also that "activate/deactivate" is already a first-class **configuration
> lifecycle** in this codebase (`draft → active → inactive`--see
> `activate_configuration_db` in `refiner/app/db/configurations/activations/db.py`).
> A user _excludes_ a code; they _deactivate_ a configuration.

The core realization driving the split is that these two needs map onto two
completely different seams in the pipeline:

- Exclusion never needs to touch XML traversal. Because refinement only retains
  what is in the want-set, removing a code from the want-set is sufficient to
  stop it retaining anything. The cleanest place to do this is **before** the
  want-set is ever materialized--at the point where `active.json` is projected
  from the configuration.

- Overrides **cannot** live inside the section-processing engines, because most
  sections never reach them. That argument is developed in ADR 0015.

## Decision Drivers

- **Semantic honesty.** Exclusion is subtractive on the want-set. The design
  should reflect that, not force it through the same path as overrides.
- **Auditability / visibility.** Users must be able to _see_ which codes they
  have excluded, and re-include them.
- **Keep the hot path clean.** The matching-time payload (`code_system_sets`) is
  read on every refinement. Exclusion should not add per-match runtime work or
  new fields to that structure.
- **Origin safety.** An exclusion of a TES-contributed code must not
  collaterally strip a custom code a user added by hand.

## Considered Options

### A1. Anti-join at projection time (RECOMMENDED)

Store excluded codes as first-class configuration state in the DB, and apply the
anti-join in `convert_config_to_storage_payload`
(`refiner/app/services/configurations.py:197`)--the single point where condition
codes and custom codes are collected into `coding_by_code_system` and handed to
`CodeSystemSets.from_dict`. Excluded codes are filtered out **before**
`code_system_sets` is built, so they never enter `active.json`.

**Pros**

- Downstream is completely untouched. Both matching engines, the plan builder,
  and the lambda read the same `code_system_sets` they always have--it just no
  longer contains the excluded codes.
- Zero matching-time cost and no new field on `ProcessedConfiguration` /
  `CodeSystemSets`.
- The DB remains the expressive source of truth: the UI can render "excluded"
  state, users can re-include, and the choice is auditable. `active.json` stays a
  clean projection.
- **No backfill.** The full condition code set remains the default; an absent
  row means "included."

**Cons**

- The projection loses the distinction ("this code came from TES but was turned
  off")--but that distinction lives in the DB where it belongs.
- Requires a new table + read path (mirrors the `custom_codes` work in #1528).

### A2. Subtract at `ProcessedConfiguration.from_dict` runtime

Keep the full `code_system_sets` in `active.json` plus a separate `excluded`
set, and subtract on read in `terminology.py`.

**Cons**: adds a field to the hot-path object and a per-refinement subtraction;
puts policy in the executor rather than the projection. It also buys nothing--
the intent it would preserve inside the payload is already preserved in the DB.
Rejected.

### A3. Filter inside the matching engines

Pass the excluded set to the engines and skip matches on those codes.

**Cons**: exclusion has no reason to touch XML at all, since a code absent from
the want-set already retains nothing. Rejected.

## Decision Outcome

**Option A1.** Excluded codes are stored in the DB as first-class config state
and anti-joined out during projection. Nothing downstream changes.

Resolved design decisions:

- **Scope: `(configuration, condition)`.** An exclusion belongs to a
  configuration/condition pair, not to a jurisdiction and not to a configuration
  as a whole.
- **Granularity: code + code system.** Guaranteed by construction--see _Storage_.
- **The anti-join runs inside the per-condition loop**, not over the merged
  payload dict. This is what makes it both condition-scoped and origin-scoped.
  See _The projection seam_.
- **No document provenance.** Exclusion is a want-set edit made in the app; the
  configuration is the record. We do not echo excluded codes into the output
  (they could be a handful or thousands, and the user can see them in the app).

> [!NOTE]
> **Scope: eICR only; the RR is unaffected.** Exclusion edits `code_system_sets`,
> not the `included_condition_rsg_codes` the RR pass (`refine_rr`) filters on--so
> an excluded clinical code cannot change which conditions the RR reports.

## Appendix

### Storage

Implemented in `configurations_conditions_code_exclusions` (see PR #1633):

```sql
CREATE TABLE configurations_conditions_code_exclusions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    configuration_id UUID NOT NULL,
    condition_id UUID NOT NULL,
    code_id UUID NOT NULL REFERENCES codes(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- ON DELETE CASCADE is required: removing a condition from a configuration
    -- deletes the configurations_conditions row, and deleting a configuration
    -- cascades to it. Without this, either path raises a ForeignKeyViolation
    -- once the user has excluded any code from that condition.
    FOREIGN KEY (configuration_id, condition_id)
        REFERENCES configurations_conditions(configuration_id, condition_id)
        ON DELETE CASCADE,

    UNIQUE (configuration_id, condition_id, code_id)
);
```

Two properties fall out of this shape, and both retire questions the first draft
had left open:

- **Granularity is `(system, code)` by construction.** `codes` carries
  `UNIQUE (system_id, code)` (`refiner/schema.sql:414`), so a `code_id` _is_ a
  system-scoped code. The first draft proposed teaching the intermediate models
  to carry a code system so the anti-join could be faithful; the normalized
  `codes` table introduced in ADR 0009 already is that model. No new work.
- **Only condition-origin codes are addressable.** Rows reference `codes` via
  `conditions_codes`; custom codes live in their own table with no `code_id`. An
  exclusion therefore _cannot name_ a custom code.

### The projection seam (the one place that changes)

`convert_config_to_storage_payload` appends custom codes and condition codes in
**separate loops** (`configurations.py:223` and `:249`). The anti-join goes
inside the **condition** loop:

```python
excluded_codes = await get_code_exclusions_db(
    configuration_id=configuration.id, db=db
)

for condition in conditions:
    # exclusions are scoped to (configuration, condition), so they are applied
    # here rather than to the merged dict below: this loop is the last point
    # where a code's originating condition is still known, and it is the only
    # loop custom codes never pass through -- so an exclusion can never strip a
    # hand-added custom code that happens to share a (system, code) pair.
    excluded_for_condition = excluded_codes.get(condition.id, set())

    for key, code_list in code_system_map.items():
        ...
        coding_by_code_system[system_metadata.key].extend([
            asdict(Coding(code=c.code, display=c.display, system_oid=system_metadata.oid))
            for c in code_list
            if (key, c.code) not in excluded_for_condition
        ])
```

Placement is the whole design:

- **Condition-scoping is free here.** The payload flattens every included
  condition into one want-set, but the flattening happens _after_ this loop, so
  `condition.id` is still in hand. (The first draft treated this flattening as a
  blocker for both features. It is not a problem for exclusion at all, and ADR
  0015 explains why it is not one for overrides either.)
- **Origin-scoping is free here.** Filtering the _merged_ dict--as the first
  draft's sketch did--would strip any code with matching `(system, code)`,
  including custom codes. Filtering inside the condition loop cannot.

`get_code_exclusions_db` resolves `code_id` to `(system key, code)` because the
projection reads condition codes from the `conditions` JSONB columns, which carry
no code ID. The `UNIQUE (system_id, code)` constraint makes that resolution
lossless. Migrating the projection to read from `conditions_codes` directly
(retiring the `TODO` at `app/services/terminology.py:31`) would let the anti-join
key on `code_id` and remove the bridge; that is a worthwhile follow-up, not a
prerequisite.

### Behavior worth knowing about

#### Shared codes: the want-set is a union

Exclusions are per `(configuration, condition)`, but `active.json` holds one
flattened want-set. So excluding code X from condition A while condition B still
contributes X leaves X in the want-set.

This is not an edge case. In the seeded database, **51.9% of codes appear in more
than one condition** (72,588 unique to one condition vs. 78,324 shared; the most
widely shared codes appear in ~146 conditions each). For any multi-condition
configuration, "I excluded this code and it is still in my output" is the
expected experience unless the user excludes it from every code set that
contributes it.

The engine behavior is the honest reading of condition-scoped storage, and it
matches the management UI, which lists one row per `(condition, code)`. What it
needs is a UI affordance--surfacing that a code is contributed by _N_ code sets--
rather than a different projection. **Open: see _Open questions_.**

#### Duplicate codes collapse, last-wins

`CodeSystemSets.from_dict` builds `{code: Coding}` per system
(`app/services/terminology.py:213`), so two codings with the same code in the
same system collapse to one, last-wins, **including the display**. Custom codes
are appended before condition codes, so today the condition's display wins.

Consequence: if a custom code duplicates a condition code on `(system, code)`,
excluding the condition's contribution leaves the custom code--the code stays in
the want-set and its display changes to the custom one. That is correct (the user
added it deliberately), but it presents as a failed exclusion. Pinned by
`test_exclusion_never_strips_a_matching_custom_code`.

This makes custom-code duplicate-prevention **independent of this ADR**. The
first draft proposed enforcing `validate_custom_code` on the write paths as a
prerequisite; with the anti-join inside the condition loop, it no longer is.

### Test coverage

Unit (`tests/unit/test_service_terminology.py::TestCodeExclusions`) — projection
behavior with the DB read mocked:

| Scenario                                    | Expectation                                            |
| ------------------------------------------- | ------------------------------------------------------ |
| Excluded code                               | absent from the want-set                               |
| Code shared by two included conditions      | survives when excluded from only one (union semantics) |
| Same digits in two systems                  | only the named system's code is dropped                |
| Custom code colliding with an excluded code | survives; display becomes the custom one               |
| No exclusions                               | want-set identical to baseline                         |
| Exclusion naming an unincluded condition    | ignored                                                |

Integration (`tests/integration/test_code_exclusions.py`) — real SQL against the
real table, which also checks that the `conditions` JSONB columns and the
normalized `codes` tables still agree:

| Scenario                          | Expectation                                            |
| --------------------------------- | ------------------------------------------------------ |
| Exclude one real condition code   | dropped from the payload; every sibling code untouched |
| `get_code_exclusions_db` grouping | returns `{condition_id: {(system_key, code)}}`         |

### Open questions

1. **Shared-code UX.** Given 51.9% of codes are contributed by more than one
   condition, does the management UI need to surface "this code is also in _N_
   other code sets," and should it offer an exclude-from-all action? The engine
   behavior (union) is settled; this is a product decision about the surface.
2. **Write path ownership.** The read path and the projection are covered. The
   toggle endpoint and UI live with the manage-codes work (#1633).
