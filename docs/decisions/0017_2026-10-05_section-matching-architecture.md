# 17. Section Matching Architecture

Date: 2026-10-05

## Status

Proposed

## Context and Problem Statement

The refiner decides what to keep in each eICR section with two matching
engines in `app/services/ecr/section/`:

- `entry_matching` is rule-driven. Each section has a list of `EntryMatchRule`s
  in `specification/entry_match_rules.py`.
- `generic_matching` is the fallback. It matches any code anywhere and keeps
  whole entries.

Most section behavior is decided by those rules.

### The prompting incident

Issue #1504 asked that a Results organizer's `<procedure>` components, such as
the specimen collection procedure, be kept alongside the results they give
context to. It was fixed, broke again, and was fixed again:

- **#1522** added a guard: "only prune an organizer component that contains a
  Result Observation (`…22.4.2`)". Procedures survived.
- Epic sends proprietary result rows: an `<observation>` with an Epic
  `templateId`, no code, and a bare value like `16`. They lacked the Result
  Observation `templateId`, so the guard kept them as context, and they rendered
  as narrative rows reading "16". PHAs in two jurisdictions reported them as
  unreadable.
- **#1763** flipped the guard to "keep a component **only** if it carries one
  of the IG's two context templates (`…4.415`, `…4.418`)". The "16" rows were
  gone.
- A state jurisdiction then reported specimen procedures missing again. Epic
  sends its specimen collection `<procedure>` with **no** `templateId`, so it no
  longer qualified as context.

Each fix was reasonable and tested against the case in front of it. The guard
is a single XPath expression answering two questions at once ("is this context
to keep?" and "is this noise to drop?"), and it keyed on `templateId`s, the part
vendors are least consistent about. The tests used only IG-conformant shapes,
so neither change failed anything.

# 1504 has since been fixed again: the guard now keys on statement **kind**, so
only `<observation>`s and nested `<organizer>`s are prunable. A hand-authored
fixture now pins every component kind seen in a Results organizer, in both
directions.

### A review of the matching code

Prompted by this, a review of the matching code found that the incident
reflects a broader pattern.

**Each rule answers three questions at once**, all encoded as XPath strings:

1. **What kind of statement is this?** It's never asked directly. A `templateId`
   predicate inside the rule's `code_xpath` stands in for it.
2. **Where can a condition code live in it?** That's `code_xpath`,
   `translation_xpath` and the code-system bucket.
3. **Given a match, what else survives?** That's `prune_container_xpath`, the
   guard and `preserve_whole_entry`.

**Coverage gaps.** These are places the IG (or a rule's own comment) puts a
condition code that no rule searches:

- a trigger code on the Results organizer's own `code` (CONF:4527-438/466/467).
  The IG's own STU 3.1.1 sample loses every Results entry when only the
  organizer's trigger code is configured.
- coded Result values whose `xsi:type` isn't literally `CD`, and codes in
  `value/translation`
- the exposure agent in Social History
  (`participant/participantRole/playingEntity/code`)
- Indications in Encounters, Procedures and Medications

**Rule precedence.** When a section has several rules, the first group whose
XPath finds _any_ code claims the entry, and later rules are never tried. This
only has an effect in Plan of Treatment (8 groups) and Procedures (3 groups);
every other section's rules form one group. In those two sections it silently
drops real matches:

- a planned procedure whose Indication is the configured condition
- an act whose trigger code is configured, but which nests another procedure
- a planned act that nests a planned observation

**Copy-paste as the way rules get extended.** The Problem-shaped rule pair is
duplicated across five sections, and the medication rule across four. A fix has
to be made in every copy, and nothing checks that the copies stay equal.

**Routing and robustness:**

- The engine choice depends on the detected eICR version. A section absent from
  that version's manifest silently goes to the generic engine, which keeps
  whole entries. Vital Signs in a document detected as 1.1 keeps entire
  organizers.
- The generic engine raises on a configured code found outside any `<entry>`,
  which fails refinement for the whole condition.

**Docs drift.** The Matching Engine Guide and several docstrings describe
behavior from earlier PRs.

**Tests skew toward IG shapes.** The integration scenarios all run against one
synthetic document. The unit fixtures are mostly IG-conformant. The existing
reachability test proves every rule _can_ fire, not that a code at a given
location is _retained_.

**What isn't a problem.** The layering above the engines is sound:
`pipeline → refine → process_section → engine`. Engines report facts
(`SectionRunResult`), `refine.py` names the outcome, and `policy.py` normalizes
configuration at the edge. The table-driven approach is also the right pattern.
The problem is the table's vocabulary, not that the table exists.

**Question:** how do we change matching so that fixing one behavior stops
silently breaking another?

## Decision Drivers

- **Regressions must be caught by tests, not by PHAs.** A behavior change
  should show up as a named, failing test row.
- **Real sender shapes over IG shapes.** Vendor output routinely departs from
  the IG; correctness for real documents is what matters.
- **No production data in the repository.** Production-derived documents, even
  "de-identified" ones, are not committed without written clearance from APHL.
  Scrubbing in practice misses provider NPIs, phone numbers and addresses.
  Fixtures must be synthetic.
- **Small, reviewable changes.** Prefer steps that can each be verified and
  shipped on their own over a migration window with two engines.
- **Healthy codebase.** Prefer less code that's easier to reason about. Don't
  build abstractions before a concrete consumer needs them.
- **Keep the working parts.** The orchestration layering and the configuration
  boundary stay as they are.

## Considered Options

### 1. Harden in place ("A+")

Keep the rule-driven engine and fix it incrementally, behind a new test net:

- **Section-fixture "outcome matrix".** Each row is a synthetic CDA section,
  the configured codes by bucket, and the expected kept and dropped elements,
  including which siblings and children survive. Tests call `process_section`
  directly, so no configuration, jurisdiction, reportability or database is
  involved; just codes and matching. Rows that record known-wrong behavior are
  marked `xfail(strict=True)`, so a fix flips them loudly.
- **Remove rule precedence**, since it only blocks matches.
- **Fill the coverage gaps** in today's rule vocabulary, one matrix row at a
  time.
- **Rule factories** in place of the copy-pasted rules.
- **Express the Results context exemptions as a named list** compiled into the
  guard, so the knob that broke twice becomes reviewable data.

**Pros:**

- delivers every fix without a second engine or a migration window
- each step is local and pinned by matrix rows
- the precedence problem goes away with a small change

**Cons:**

- the "what survives" decision stays mostly XPath
- there's no record of _how_ each statement was recognized, and none shared
  with narrative reconstruction

### 2. Recognize, extract, decide, apply

Classify each entry's statements into explicit kinds first, then work from
those kinds:

- **Recognize:** use `templateId`s where present, fall back to structure (element
  name, mood, parent and relationship), and otherwise mark the statement
  "unknown".
- **Extract:** each `(section, kind)` declares every location where a condition
  code may live.
- **Decide:** retention is a table keyed by `(parent kind, relationship, kind)`.
- **Apply:** mutate the lxml tree once, at the end.

This would migrate one section at a time.

**Pros:**

- a named, testable vocabulary for what to keep and drop
- unknown statements are handled explicitly
- recognition evidence becomes data, not comments
- narrative reconstruction could share it
- the generic engine falls out as a degenerate case

**Cons:**

- real work per section, and two engines during migration
- recognizer coverage becomes the main risk
- its decide semantics have known traps:
  - an "unknown means drop" default repeats #1763's mistake
  - keeping a statement has to keep its children, or units, statuses and
    susceptibility results inside matched results would be lost
- can only be validated against hand-authored shapes (see Decision Drivers)

### 3. Typed domain model (e.g. pydantic) of CDA entries

Parse entries into validated models.

**Pros:**

- strong typing and editor support
- a familiar tool

**Cons:**

- reject-on-invalid is the wrong default when rejecting means dropping clinical
  data, and lenient validation keeps the cost while losing most of the benefit
- the model can't be the serialization source, because CDA is far larger than
  anything we'd model, so lxml handles are still needed
- pulls toward modeling everything

### 4. Classify statements with the published IG schematron

**Pros:**

- authoritative

**Cons:**

- schematron checks conformance; it can't classify non-conformant input, which
  is the hard case
- slow
- useful at most as a test oracle

## Decision Outcome

**Option 1, hardening in place.** Option 2 is recorded as the direction to
revisit, not scheduled.

Option 1 meets the drivers directly:

- The outcome matrix makes regressions fail as named rows, written in real
  sender shapes with synthetic data.
- Every step is small and verifiable on its own.
- The layering stays as it is.

Option 2's main stated benefit, removing precedence, turns out to be a small
change in Option 1. Its remaining value, a named decide vocabulary and
recognition shared with narrative reconstruction, doesn't yet have a consumer
that justifies a migration.

### Sequence

1. **#1504.** Done: the Results guard keys on statement kind, and a vendor-shaped
   fixture pins it in both directions.
2. **Outcome matrix and docs.**
   - Build the section-fixture matrix, recording current behavior, with
     known-wrong rows marked `xfail`.
   - Bring the Matching Engine Guide and the docstrings up to date.
   - Exit: every rule-driven section has rows for each IG code location and
     each known gap.
3. **Remove rule precedence.** Gated on the nested-match question below.
   - Exit: the precedence rows flip, and the scenario snapshots are unchanged
     or their diffs are signed off.
4. **Coverage and routing fixes** in today's rules, each one flipping its rows:
   - the organizer trigger code
   - coded values beyond `CD`, and `value/translation`
   - the Social History exposure agent
   - the generic engine's out-of-entry raise
   - consistent code normalization
   - version routing
5. **Structure without behavior change.**
   - Rule factories for the duplicated rules, and the named Results exemption
     list.
   - Exit: the matrix is unchanged, and the rule file is measurably shorter.

### When to revisit Option 2

Any of these:

- a "what survives" regression recurs after the matrix exists
- narrative reconstruction needs to share statement recognition with matching
- the coverage fixes start needing per-shape exceptions the rule vocabulary
  can't express cleanly

If revisited:

- unknown statements default to _kept as context_, with named noise dropped
  explicitly
- keeping a statement keeps its subtree
- code locations are declared per section, not globally

### Open questions

- **Nested matches.** Should a match on a nested statement keep its parent
  entry? An existing scenario test ("Roll-up #5") asserts that a Reaction
  Observation match does **not** keep a Procedures entry. Does that principle
  extend to Indications (Plan of Treatment, Encounters, Procedures,
  Medications) and to nested trigger statements? This gates step 3.
- **Organizer trigger code.** When the Results organizer's own trigger code
  matches, keep the whole panel or only the matched components? This gates the
  organizer fix in step 4.
- **Version routing.** Keep gating a section's rules on the detected version's
  manifest, or apply them whenever the section is present? This gates the
  routing fix in step 4.
- **Out of scope:** custom codes saved under the "Other" code system can't
  match in the seven sections whose rules are scoped to specific code systems
  (Problems, Past Medical History, Admission and Discharge Diagnosis,
  Encounters, Results, Vital Signs). That's a code-management question, to be
  decided separately.

## Appendix (OPTIONAL)

- Issues and PRs: #1504, #1522, #1763
- Matching engine: `refiner/app/services/ecr/section/`
- Rules and guard: `refiner/app/services/ecr/specification/entry_match_rules.py`
- How rules are evaluated:
  `refiner/app/services/ecr/DIBBs-eCR-Refiner-Matching-Engine-Guide.md`
- Pipeline overview: `refiner/app/services/ecr/README.md`
- Section-level fixtures: `refiner/tests/fixtures/sections/`
- CDA background: `refiner/DIBBs-eCR-and-CDA-for-Engineers.md`

**Be sure to read the information about this in [CONTRIBUTING](https://github.com/CDCgov/dibbs-ecr-refiner/blob/main/CONTRIBUTING.md##Request-for-comment)**
