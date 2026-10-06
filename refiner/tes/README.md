# TES pipeline

Everything that turns published TES terminology into something the refiner can
seed. This directory owns the FHIR knowledge; nothing downstream needs any.

```
fetch  ──▶  data/source-tes-groupers/   ──▶  normalize  ──▶  data/processed/  ──▶  seeding  ──▶  database
           raw FHIR ValueSet bundles     ▲        flat gzipped CSV
           741 MB, 45 files              │        11 MB, 6 files
                                         │
fetch  ──▶  data/source-ersd/  ──────────┘
           eRSD releases (trigger codes)
           25 MB each, current one read
```

The split matters: **version-specific unpacking happens once per release, here.**
Seeding is a `COPY`. The ops container carries `data/processed/` and never reads a
FHIR resource.

## What this bought

Measured, not estimated. The old seeder was restored from git and run against the
same wiped-and-migrated database, in the same container, over the same raw
bundles, so the two columns are directly comparable.

### Seeding

| | before | after |
|---|---|---|
| `load_static_data.py` / `load_processed_data.py`, clean database | **62.0s** | **13.7s** |

Where the 48 seconds went, largest first:

1. **Parsing left the deploy.** The old seeder read 741 MB of FHIR, classified
   groupers, resolved the reference graph and extracted 2.6 M codes *on every
   seed*. That now happens once per release in `normalize`.
2. **Foreign keys are validated in one pass.** Three per-row FK checks across a
   million junction rows cost 38s; dropping the constraints and re-adding them
   validates the whole table in 0.32s. The old seeder paid this too — it was just
   hidden behind the parsing.
3. **SQL does the plumbing.** The old loader pulled generated ids back into Python
   dicts to build relationships; natural keys now join in the database.

### Deploy sequence (`ops prepare-db`)

| Step | before | after |
|---|---|---|
| `dbmate migrate` | 0.6s | 0.6s |
| verify processed (`--integrity-only`) | — | 1s |
| seed | 62.0s | 13.7s |
| verify database | — | 12.9s |
| regenerate active configs | ~0s | ~0s |
| **total** | **~63s** | **31s** |

Twice as fast *while also* running ~14s of verification that did not previously
exist. The data path alone is roughly 4x faster.

### Footprint

| | before | after |
|---|---|---|
| ops image | 699 MB | **222 MB** |
| docker build context (every image) | 2.7 GB | **130 MB** |
| what seeding reads | 741 MB of JSON, 45 files | **11 MB of CSV, 6 files** |
| git cost per TES release | ~17 MB (raw JSON, delta-compressed) | +8.4 MB (processed, no delta) |

The ops image shrank because it no longer ships the raw bundles; the build context
shrank because there was no `.dockerignore` at all. Note the last row is not a
saving — committed gzip cannot delta-compress, so processed data costs ~8.4 MB per
release *on top of* the raw bundles, which are kept for provenance and
re-derivation.

### What is newly possible

Not a speedup, but the reason the work is worth more than the seconds:

- **A bad seed fails the deploy.** `prepare-db` verifies before reactivation, so a
  broken projection never reaches regenerated `active.json` files.
- **Data PRs are reviewable.** `summary.csv` shows per-condition code changes as a
  handful of diff lines instead of several million lines of JSON.
- **The release table is enforced.** `verify-processed` asserts what each TES
  release's shape is — and caught a wrong claim in its own documentation the first
  time it ran.

## Commands

```sh
just tes fetch              # both sources below
just tes fetch-tes          # TES API -> data/source-tes-groupers  (needs TES_API_KEY)
just tes fetch-ersd         # eRSD API -> data/source-ersd          (needs ERSD_API_KEY)
just tes normalize          # raw bundles -> data/processed
just tes verify             # all three verification layers
just tes release            # fetch, verify bundles, normalize, verify processed
just tes diff               # what changed in data/processed since last commit
```

Both API keys go in `tes/.env`; copy `tes/.env.sample` to start. The fetchers find it
by walking up from their own directory, so it has to live here.

Then `just db seed` (or `just db refresh`) loads `data/processed` into Postgres.

In a deployed environment the ops image is the interface:

```sh
ops prepare-db              # migrate, verify, seed, verify, regenerate active configs
ops verify-db               # just the processed-vs-database checks
ops orphans                 # valueset rows seeding has quarantined, and why
```

## The three stages

### `fetch/` — talk to TES and eRSD

`detect_changes.py` pulls from the TES API into a staging area, validates every
resource with `fhir.resources`, compares hashes against
`data/source-tes-groupers/manifest.json`, syncs only what changed, and rewrites the
manifest. Resources are sharded at 30 MB per file to stay under GitHub's 50 MB
warning, so categories arrive as `<category>_<version>.partNN.json`.

This is the only stage that validates FHIR. The files it writes are
`ValueSet.model_dump()` output, which is why re-parsing them downstream is safe.

`ersd.py` pulls the eICR trigger codes from the eRSD API, not TES, whose copy is a
stale unversioned snapshot (`fetch_api_data.py` drops it). The API serves only the
latest release and has retired v1 and v2, so each release is kept as it arrives:
stored byte-for-byte as `data/source-ersd/ersd_<rctc version>.json`, validated as
FHIR **R4** (the default R5 models reject its `PlanDefinition`), and never deleted.
`manifest.json` there records every release and names the newest as `current`. The
two sources release on different cycles, so each keeps its own manifest and can be
fetched alone.

### `normalize/` — the only place that understands FHIR

Reads the bundles and writes flat tables. Five modules:

| Module | Role |
|---|---|
| `readers.py` | Per-release code readers, selected by a version→era lookup. **The release table in its docstring is the record of what TES changed and when.** |
| `groupers.py` | The single answer to "what kind of grouper is this" and "what are its children" |
| `model.py` | Flat row types, supported code systems, the sets verify asserts against |
| `ersd.py` | Reads trigger codes from the current eRSD release into `is_trigger_code`. Includes `retired` members on purpose: the RCTC groupers still expand them |
| `run.py` | Orchestration and the writers |

Three kinds of ValueSet go in:

- **Condition grouper (CG)** — a manifest. `compose.include[].valueSet` names its
  children by `(url, version)`. Carries its own `expansion.contains` from 4.0.0,
  which nothing reads: a condition's codes come from resolving its children.
- **Reporting specification grouper (RSG)** — one per reportable condition,
  identified by `rs-grouper-<SNOMED>` in its url. Carries codes.
- **Additional context grouper (ACG)** — annotates a condition with a category
  (diagnosis, medication, symptom, …) parsed from its title. Carries codes.

Adding support for a new TES shape means **writing a new reader**, not editing an
existing one. Published bundles never change, so old readers stay correct.

### `verify/` — three layers, different costs and triggers

| Entry point | Asserts | Needs | Where it runs |
|---|---|---|---|
| `verify/validate_tes_valuesets.py` | structural invariants of the raw FHIR | raw bundles | dev, after a fetch |
| `verify/processed.py` | 9 checks: files intact, current, reproducible; data-quality; release table still true | raw + processed | dev, CI on `tes/**` |
| `verify/database.py` | 4 checks: seeded DB is a faithful projection | processed + a connection | anywhere, **including the ops container against production** |

`verify/database.py` also runs as an integration test
(`tests/integration/test_tes_verify.py`), so a CI failure and an ops failure mean
the same thing.

`verify/processed.py --quick` skips the regeneration check (~25s) and keeps the
hash checks (~1s).

`Dockerfile.ops` ships `tes/normalize` and `tes/verify` alongside `data/processed`,
so these run in the ops container. `tes/fetch` is left out deliberately: it needs
the raw bundles and API credentials that container has no business holding.

### In the deploy sequence

`ops prepare-db` runs both verifications as gates. `set -e` is on and each step
exits non-zero on failure, so a bad artifact stops the deploy rather than being
reported into a log nobody reads:

```
migrate
verify processed --integrity-only   ~1s    are the files we are about to load intact?
seed                                ~13s
verify database                     ~13s   is the database what we just loaded?
regenerate-active-configs
```

The pre-flight runs `--integrity-only` because that is the one check needing
nothing but `data/processed` — everything else in `verify/processed.py` reads the
raw bundles, which are not in the image. The database check runs *before*
reactivation so a bad seed is not baked into regenerated `active.json` files.

Total `prepare-db` is ~31s against a million-row database, of which ~14s is
verification. `ops verify-db` runs the same check on its own against any
environment.

## Output contract

```
data/processed/
  conditions.csv.gz    1,596 rows   one per condition grouper per release
  valuesets.csv.gz     2,854 rows   one per leaf grouper per condition per release
  codes.csv.gz        97,264 rows   distinct (system_oid, code, display)
  memberships.csv.gz   2.0 M rows   the junction: condition x code x leaf grouper
  summary.csv          2,854 rows   per-grouper code count, trigger count + content hash
  manifest.json                     counts, output hashes, source hashes
```

Two properties the rest of the pipeline depends on:

**Determinism.** Regenerating the same inputs produces the same content. `gzip` is
written with `mtime=0` and no embedded filename, and the manifest carries no
timestamp, so a changed hash means changed data. That is what makes "regenerate and
diff" a meaningful check.

The manifest records hashes of **decompressed content**, not of the files on disk.
gzip output depends on the zlib build — Python 3.13 links zlib, 3.14 links zlib-ng,
and they emit different bytes for identical input — so a file hash would fail
whenever the interpreter verifying differs from the one that generated. Hashing
content asserts the thing we care about and is portable across interpreters.

One consequence: **run `just tes normalize` rather than invoking it directly.** The
recipe runs inside the server container, which pins the interpreter, so the
committed `.gz` bytes stay stable in git. Regenerating from a local venv on a
different Python will produce a spurious binary diff even when the data is
identical.

**`summary.csv` is the review artifact.** It is committed uncompressed so a data PR
shows what moved:

```diff
-Anotia Reporting Specification Grouper,7.0.0,rsg,2,0,4f2a...
+Anotia Reporting Specification Grouper,7.0.0,rsg,12,3,9c81...
```

The content hash catches a grouper that swapped codes without changing its count —
Rubella went +3/−13 between 6.0.0 and 7.0.0, which a count alone would show as −10.
`trigger_count` does the same job for an eRSD release bump: the grouper's codes
don't change, so it is the only column that moves.

## When a grouper stops existing

This one is worth understanding even if you never touch the SQL, because it
decides which table you should be reading.

Four tables come out of seeding, and it helps to say what each one *means*:

- **`conditions`** — one row per reportable condition, per TES release. "Influenza
  as published in 6.0.0" and "Influenza as published in 7.0.0" are two rows.
- **`valuesets`** — one row per grouper: the buckets TES sorts a condition's codes
  into (diagnosis, medication, symptom, and so on). Each belongs to one condition
  row, so a grouper is also per-release.
- **`codes`** — the vocabulary. Just "this code, in this code system, means this."
- **`conditions_codes_temp`** — the join that carries the actual meaning: *this
  condition gets this code, by way of this grouper.*

Seeding does not treat these the same way, and that asymmetry is the thing to
know. The junction is thrown away and rebuilt from scratch on every run, so it
always reflects exactly what the processed files say. Conditions and valuesets
are updated in place — new rows inserted, changed rows updated.

For a long time nothing ever *removed* one. So when TES stopped publishing a
grouper, or when a bug that had attached a grouper to the wrong condition got
fixed, the membership rows vanished on the next seed (the junction was rebuilt
without them) while the `valuesets` row stayed behind. What is left is a grouper
that belongs to a condition and contributes no codes to it. Nothing about the row
itself says so: it keeps its name, its category, and even its `code_count`,
frozen at whatever it was the day it was written.

The seeder now moves those rows to `orphaned_valuesets` instead of leaving them
(see `_quarantine_stale_valuesets`), so they stop accumulating. They are moved
rather than deleted because the environments where this matters most are ones
nobody can open a database session against, and a row that only ever existed as a
number in a log is a row nobody can examine or put back.

**The rule of thumb this leaves you with:** if the question is *what codes does
this condition have*, start from `conditions_codes_temp` and join outward. If you
start from `valuesets` instead, you are asking a subtly different question — *what
groupers are on file for this condition* — and the answer can include groupers
that contribute nothing.

Most of the app already gets this right by construction: every query in
`app/db/configurations/codes/db.py` enters through the junction and reaches
`valuesets` only to read a grouper's name, so a contributing-nothing row is
unreachable. The one query that read `valuesets` directly,
`get_context_groupers_by_condition_id_db`, now filters on the grouper having at
least one membership. That matters because its rows become the code category
badges on a condition's detail page, and a grouper with no codes should not get a
vote in what those say.

Note that quarantine and that filter cover different things and you want both. A
grouper whose codes all happen to live in code systems the refiner does not
support is *legitimately* declared by the processed files — the quarantine will
never remove it, correctly — and it still contributes no memberships. There are
none in the current data, but the query handles it either way.

## Things that are easy to get wrong

- **A ValueSet is `(canonical_url, version)`, never url alone.** The same url is
  republished every release, and `display_name` is not unique — two distinct RSGs
  can share a title.
- **`compose.include[].concept[]` entries have no `system`.** It lives on the
  enclosing `include` and has to be pushed down. `expansion.contains[]` entries
  carry their own. Neither is a `Coding`.
- **Two version families.** Semver (`7.0.0`) on condition and additional context
  groupers, datetimes (`20260731`) on reporting specification groupers. A release
  is one or the other. Their pairing is implicit — 7.0.0 CGs reference RSG
  20260731 — and both must be inside the seeding window or conditions silently
  lose codes.
- **The junction's grain is a membership, not a code.** A code in eight sibling
  groupers is eight rows. Every aggregate over it must deduplicate.
- **`is_child_rsg` is scoped to (code, the grouper that names itself with it).**
  The same SNOMED legitimately appears as ordinary context in a sibling grouper;
  that membership is not a self-naming one.
- **An RSG does not always list the SNOMED code it names itself with.** The
  membership is emitted anyway — the condition owns that code regardless.
- **A row in `valuesets` is not proof the grouper still contributes codes.** Ask
  the junction, not the table. See "When a grouper stops existing" above.

## Seeding window

Local and CI seed only the two newest releases; production seeds all. The filter is
`DEFAULT_VERSIONS_TO_KEEP` in `ops/seeding/load_processed_data.py`, applied as a
`WHERE` clause — `data/processed/` always holds every release.

When the window slides, anything pinned to the evicted version breaks. Bump
`DEFAULT_TES_VERSION` / `PREV_TES_VERSION` in `tests/integration/conftest.py` and
`LATEST_TES_VERSION` / `PREVIOUS_TES_VERSION` in `client/e2e/constants.ts` together.
