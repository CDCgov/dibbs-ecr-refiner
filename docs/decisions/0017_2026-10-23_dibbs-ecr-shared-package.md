# 17. A shared `dibbs-ecr` package for eCR specification knowledge

Date: 2026-10-23

## Status

Proposed

<!-- draft: add an entry to `docs/decisions/decisions.json` when filed -->

## Context and Problem Statement

Three DIBBs products read and write eICR and RR CDA documents: the Refiner, Difference in
Docs (DiD, `CDCgov/dibbs-ecr-diff`) and text-to-code (TTC, `CDCgov/dibbs-text-to-code`).
Each carries its own copy of the same specification knowledge.

References in this ADR are to Refiner `main` @ `8cb55264`, `dibbs-ecr-diff` @ `b8b2b0b` and
`dibbs-text-to-code` @ `5e3e1f7`.

- **The HL7 namespace and code-system OIDs** are defined three times:
  `services/ecr/model.py` here, `core/constants.py` in DiD,
  `augmentation/services/eicr_utils.py` and `shared_models/__init__.py` in TTC.
- **The Data Augmentation IG writer** exists three times. DiD's `core/augment.py` (1,008
  lines) is a fork of `services/ecr/augment.py` (1,131 lines): of 22 shared function names, 16
  are code-identical once namespace spelling and docstrings are normalized; the 6 that differ
  are tool identity and ID derivation. TTC's `eicr_augmenter.py` (406 lines) is an
  independent reimplementation.
- **The template catalog** exists only here: `services/ecr/specification/` holds a generated
  templateId catalog (`template_oids.py`), the section catalog, the per-version trigger-code
  overlays and version detection. DiD has none of it, and its whole-document comparison is
  the main reason its change detection fails on real documents.

DiD is moving to section-based comparison (a separate ADR in that repository). That work
needs this repository's section catalog, version map, and RR parsing. DiD stays a separate
repository and product: the Refiner is not required for DiD, and a jurisdiction can use either
without the other.

The question this ADR answers: **how do the products share eCR specification knowledge
without copying it again?**

An earlier proposal, closed without landing, ran DiD as a second Lambda handler in this
repository. Its case rested on sharing this repository's per-condition configuration.
Condition configuration is out of scope for DiD's MVP, which removes that reason; what
remains is code sharing, which this ADR provides.

## Decision Drivers

- One copy of each piece of eCR specification knowledge.
- No package registry and no publishing process to run.
- The Refiner's runtime behaviour does not change, and a check proves it rather than asserts it.
- Generated code keeps its provenance: generator, pinned source, and a way to prove the output
  matches.
- A product can adopt a new version when it is ready, not when another product releases.
- Reversible: moving the package to its own repository later must be cheap.

## Considered Options

### A. Where the code lives and how products install it

#### A1. A package directory in this repository, installed by git tag (RECOMMENDED)

`refiner/packages/dibbs-ecr/` with its own `pyproject.toml`. Other repositories install it from
a pinned tag; the Refiner installs it from the local path.

It sits under `refiner/`, not at the repository root, because that is where the Python
tooling already looks. The local `server` container mounts only `./refiner`; ruff,
pytest and pre-commit are configured there. A root-level `packages/` would be invisible to
the dev stack and need its own lint and test wiring.

- Pro: no registry; a tag is the release. The pin is exact and recorded in each consumer's lock
  file.
- Pro: ordinary imports, so tests, type checking and editors work everywhere.
- Pro: lives next to the most CDA-literate code in the portfolio -- the generated catalog, the
  version map, both eICR XSLT stylesheets, the Schematron bundles, the augmentation guide the
  IG cites.
- Con: releases are tagged in the Refiner repository; a `dibbs-ecr-v*` tag namespace keeps
  them apart from Refiner releases. Refiner releases are bare `MAJOR.MINOR.PATCH`, which
  `build-release-candidate.yml` enforces, so the two cannot collide.
- Con: the template-aware model that follows is developed against DiD first, so its fastest
  changes are made here for a consumer elsewhere. A tag per iteration would make the release
  mechanism the bottleneck; consumers pin a branch while iterating (see Versioning).
- Con: a consumer's image build needs `git` and access to GitHub. DiD's image is built by
  GitHub Actions, so access is not a problem.

#### A2. A seventh repository, installed by git tag

- Pro: the cleanest boundary and an independent release cadence.
- Con: one more repository, CI and remote to keep up, for a small team.
- Con: separates the package from the code and reference material it was extracted from.
- Moving from A1 to A2 later changes only the git URL in each consumer.

#### A3. Publish to a registry (PyPI or AWS CodeArtifact)

- Pro: the conventional mechanism.
- Con: a publishing process to own. GitHub Packages does not host Python packages, so it would
  mean PyPI or CodeArtifact.

#### A4. Copy from this repository's Lambda image in a multi-stage build

- Pro: no packaging at all for the image.
- Con: exists only inside Docker; `pytest`, type checking and editors cannot see it, so
  development needs a second mechanism.
- Con: copies an internal directory layout, not an interface. `services/ecr` imports
  `app.core` and `app.services.terminology`, so it does not stand alone.
- Con: no dependency metadata; `lxml` versions can drift between products.

#### A5. Submodule, subtree, or copy with a CI drift check

- Con: submodules have a poor story with `uv`; copies are how the current drift happened.

### B. What enters first

#### B1. Specification types and the catalog only

Namespaces, OIDs, the generated template catalog, the section catalog without match rules,
version detection, trigger overlays, and the RR types and parser. Behaviour-free moves.

- Pro: proves the install mechanism on code that rarely changes.
- Pro: it is what DiD's section-based work needs first.
- Con: every consumer reads the same code the same way, so the release cannot show that the
  package serves two products with different needs. Augmentation is the first module where
  they differ.

#### B2. Everything reusable

- Con: no consumer is asking for most of it; it would grow a package nobody owns.

#### B3. B1 plus augmentation (RECOMMENDED)

- Pro: deletes DiD's fork in the first release.
- Pro: the first release is tested by two products that use it differently. The Refiner and
  DiD both stamp documents through the same writer, each with its own tool identity and
  ID derivation (see "How augmentation is parameterised"). If both still produce the same
  output, that is the evidence the package works.
- Con: the largest move with the most behaviour, and the per-tool parameters need designing.
  The byte-level parity baseline (on both sides) is what makes it safe to include now.

### C. Name

`dibbs-ecr` (import `dibbs_ecr`), chosen over `ecrtools`, `phcr`, a `dibbs.*` namespace
package, and format-split `ecr-cda` / `ecr-fhir`. It matches the repository names, is
unambiguous, and keeps the format out of the top-level name so FHIR eCR tooling can join as a
subpackage. A bare `ecr` was rejected: it collides with `app.services.ecr` here and with AWS
Elastic Container Registry everywhere in these repositories.

## Decision Outcome

Proposed: **A1 + B3 + `dibbs-ecr`**.

### What may enter: specification, not policy

- **Specification** -- anything deterministic from the IGs or CDA R2: templates and their
  structure, OIDs, vocabulary, version differences, the augmentation IG's header and author
  shapes. May enter when one DIBBs product needs it.
- **Policy** -- a tool's choice: the Refiner's pruning and precedence rules, DiD's verdicts
  and tiers, each tool's `setId` derivation. Never enters.
- A generated module enters together with its generator, its pinned source and a regeneration
  test.
- Anything used by only one product is marked unstable until a second adopts it.

### Layout

```
refiner/packages/dibbs-ecr/
  pyproject.toml                    # depends on lxml only; requires-python >=3.14
  README.md
  src/dibbs_ecr/
    cda/          HL7 namespaces; generic CDA R2 helpers (II root+extension, XML utilities)
    vocab/        code-system OIDs
    eicr/         template_oids.py (generated), section catalog, versions, detection, loader
    rr/           RR types and parsing, reportable conditions by jurisdiction
    augment/      Data Augmentation IG writer, parameterised by tool
  scripts/oid_catalog/              # not shipped in the installed package
    README.md                       # download + sha256 + marker steps to reproduce the source
    generate_template_oids.py
    sources/                        # gitignored; local conversion of the licensed IG
  tests/
    test_template_oids_regenerates.py   # skipped without a local conversion
```

`fhir/` arrives when a FHIR consumer does, behind an optional extra so CDA consumers don't
install it.

Names follow ADR 0016: `display_name` for human-readable labels.

### What moves in the first release, and what stays

| Refiner module                                                                                                                                      | Moves             | Notes                                                                                                                                                                                                     |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `model.py`: `HL7_NAMESPACE`, `HL7_NS`, `HL7_XSI_NS`, `EicrVersion`, `TriggerCode`, `EICRSpecification`                                              | yes               | reference nothing in `app.*`                                                                                                                                                                              |
| `model.py`: `SectionSpecification`                                                                                                                  | **splits**        | the shared part keeps `loinc_code`, `display_name`, `template_id`, `trigger_codes`; `entry_match_rules` stays here                                                                                        |
| `model.py`: `ReportableCondition`, `JurisdictionReportableConditions`, `ProcessedRR`                                                                | yes               | with `reportability.py`                                                                                                                                                                                   |
| `model.py`: `EntryMatchRule`, `SectionInstructions`, `SectionProvenanceRecord`, `SectionOutcome`, `SectionSource`, the refinement plans and results | no                | refinement policy and run state                                                                                                                                                                           |
| `specification/template_oids.py`, `constants.py`, `versions.py`                                                                                     | yes               |                                                                                                                                                                                                           |
| `specification/catalog.py`                                                                                                                          | splits            | the catalog moves without rules                                                                                                                                                                           |
| `specification/loader.py`                                                                                                                           | splits            | version detection and the rule-free spec move; the Refiner attaches its rules                                                                                                                             |
| `specification/entry_match_rules.py`                                                                                                                | no                | refinement policy                                                                                                                                                                                         |
| `reportability.py`                                                                                                                                  | yes               | its one `app.*` import, `core.exceptions`, is replaced by a package exception; nothing in `app/` catches `StructureValidationError` by name, but `tests/unit/test_service_reportability.py` asserts on it |
| `augment.py`                                                                                                                                        | **splits**        | the IG writer moves; the Refiner's tool identity, deterministic namespace and ID/`setId` derivation stay here and are passed in                                                                           |
| `narrative/`, `section/`, `refine.py`, `policy.py`                                                                                                  | no                | refinement                                                                                                                                                                                                |

Since #1908, `model.py`'s only Refiner imports are `NarrativeAction` and `SectionAction`
(`app.core.models.configurations`) and, under `TYPE_CHECKING`, `CodeSystemSets`. All three
are used only by types that stay. The split is a move, not an untangling.

### Why DiD takes the RR now

DiD already reads every RR: the Lambda loads it for each manifest entry
(`did_lambda/lambda_function.py:191`), and `condition_codes_from_rr`
(`telemetry_helpers.py:57`) extracts every condition code it finds. That is a third copy of
RR knowledge, and it does not filter on reportability status or jurisdiction.

`get_reportable_conditions_by_jurisdiction` gives DiD the same list the Refiner starts
from: jurisdictions paired with the SNOMED codes they mark "reportable", de-duplicated.
Logging that list on every comparison lets failures be grouped by condition and
jurisdiction. That answers a question DiD currently can't: do particular conditions need
their own comparison rules? This is telemetry, not policy, so it meets the admission rule.

### How augmentation is parameterised

The IG writer is specification; who is stamping and how they mint IDs is policy. 16 of the
22 shared functions are already identical. The 6 that differ are exactly the
tool-specific parts:

- **Tool identity:** the author `code` and `displayName` (`REFINER_TOOL_CODE`,
  `REFINER_TOOL_DISPLAY` here; DiD's own values there).
- **ID derivation:** document `id` and `setId` for the eICR and the RR. The Refiner seeds a
  UUIDv5 from its own namespace plus the refinement scope (`_derive_augmented_eicr_id` and
  siblings). DiD derives from the original eICR's `root`. Each product's scheme is its
  policy, per the admission rule.

Both are passed as one immutable value object, built by the product and handed to
`augment_eicr` / `augment_rr`:

```python
@dataclass(frozen=True, slots=True)
class AugmentingTool:
    code: str
    display_name: str
    derive_ids: Callable[[OriginalIdentity, Scope], AugmentedIds]
```

- Not an environment variable: a library that reads the environment hides an input. A
  product may read its own environment to _build_ the `AugmentingTool` it passes.
- The exact field set is drafted against both forks before the move, so the package's
  first public signature isn't shaped by the Refiner alone.
- The Refiner's `ecr-refiner` constants, `REFINER_DETERMINISTIC_NS` and its seed prefixes
  stay in `app/services/ecr/`.

### How the Refiner re-attaches match rules

A Refiner-side lookup keyed by LOINC -- `entry_match_rules_for(loinc_code)` over the dict
`catalog.py` already builds implicitly -- not a wrapper around the shared
`SectionSpecification`. A wrapper section type would force a wrapper `EICRSpecification` as
well, duplicating the shared shape to carry one field.

- Rules are version-invariant: `loader.py` copies `catalog_entry.entry_match_rules` onto
  every version's section unchanged, so LOINC alone is a sufficient key. If a rule ever
  becomes version-specific, the key becomes `(version, loinc_code)`.
- The change is contained: `entry_match_rules` is read in `section/__init__.py`,
  `section/entry_matching.py`, `narrative/reconstruction/sections.py`, `terminology.py`
  and the loader.

### Generated code and provenance

`template_oids.py` stays generated and marked "do not edit". Its generator moves with it; its
source does not.

**No IG text is committed -- not the PDF, not the `.docx`, not a markdown conversion.** HL7's
licence allows products that "implement, but do not directly incorporate" the IG, and
copying "for internal purposes only". The generated `template_oids.py` is the committed
record. It carries only template names and identifiers, which an implementation has to
contain anyway.

- The README walks through reproducing the source locally:
  1. Get a free HL7 licence and download the eICR STU 3.1.1 Vol 2 PDF from HL7's standards
     page (product brief 436).
  2. Check the PDF against the sha256 recorded in the README.
  3. Convert it:

     ```sh
     uvx --python 3.14 --from 'marker-pdf==1.10.2' marker_single <ig>.pdf --output_dir=sources/
     ```

  4. Run the generator against `sources/`.
- `sources/` is in `.gitignore`, so a local conversion can't be committed by accident.
- HL7's public `CDA-phcaserpt` repository has no PDFs. Its 3.1.1 zip
  (`CDA-phcaserpt-3.1.1/input/20241007_CDAR2_IG_PHCASERPT_R2_STU3.1.1.zip`) contains the
  `.docx` volumes and a `_readme.txt` that still lists PDFs. The README points at the
  licensed download, not the zip.

> [!NOTE]
> `marker` is not a dependency of anything in the package but required if you wanted to re-create the `*.md` version of the eICR IG.

- The conversion is not reproducible byte for byte. `marker` uses ML models, and two
  conversions of the same PDF that are in use today differ textually. They still produce
  the same 113 OIDs. Regeneration is therefore checked on output, not input: the
  regeneration test compares the generated module with the committed `template_oids.py`.
  - It runs only when a local conversion is present, and is skipped otherwise, including
    in CI.
  - Anyone touching the generator or the catalog runs it locally.
- Regenerating today's file from today's input reproduces the committed file (verified
  2026-10-23; the only difference is one blank line, which the existing script's
  `ruff check --fix` removes).
- The generator covers eICR 3.1.1 only. The 1.1 overlays in `versions.py` are hand-written;
  the README says so.

### Versioning

- Releases are git tags `dibbs-ecr-vMAJOR.MINOR.PATCH` on this repository.
- Semver against the public import surface: removing or renaming anything importable is
  major; additions are minor.
- Unstable modules are excluded from that promise until a second product adopts them.
- While a consumer iterates on unreleased package changes, it pins a branch or commit (`rev`)
  or points a local `[tool.uv.sources]` path at a checkout; it pins a tag once the change
  is merged and released. Tags mark what was released, not every iteration.

### How the Refiner uses it

Installed from the local path, explicitly, at every install site. It cannot ride along in
`requirements.txt`: pip resolves a relative path in a requirements file against the current
directory, not the file's (verified 2026-10-26: `./pkg` in `sub/req.txt` installs from
`sub/`, fails from elsewhere), and the Dockerfiles copy `requirements.txt` away from the
package.

| Install site                                            | Today                                                                   | Change                                                                                 |
| ------------------------------------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `Dockerfile.app`, `Dockerfile.ops`                      | `pip install -r requirements.txt`                                       | add `pip install ./refiner/packages/dibbs-ecr`; build context is already the repo root |
| `Dockerfile.lambda`                                     | `pip install -r app/lambda/requirements.txt`                            | same                                                                                   |
| `docker-compose.override.yml` `server`                  | mounts `./refiner:/app`; command runs `pip install -r requirements.txt` | add `-e packages/dibbs-ecr` to the command; the mount already covers it                |
| `docker-compose.yml` `lambda`                           | mounts selected `app/*` directories                                     | mount the package and install it editable, or the container silently runs a stale copy |
| `.github/workflows/tests.yml` (4 jobs), `typecheck.yml` | `pip install -r ...`                                                    | add the package                                                                        |
| `just server` `_venv`                                   | `python3 -m venv .venv`                                                 | install the package editable                                                           |

- Refiner code imports `dibbs_ecr`, never a relative path into the package.
- CI runs the package's tests and fails if anything under `src/dibbs_ecr/` imports `app`.
- mypy runs on `app/**` only, so the package gets its own ruff and mypy run.
- The Python floor is 3.14, following the containers. Every runtime already runs 3.14:
  - the Refiner's three Dockerfiles and all its CI workflows
  - DiD's Lambda image and `.python-version` (3.14.6)
  - TTC's three Lambda images (`requires-python = "==3.14.*"`)

  The lagging pieces are declarations:
  - the Refiner's ruff `target-version = "py313"` (root and `refiner/pyproject.toml`)
  - DiD's `requires-python = ">=3.12"`, from which ruff infers `py312`

  The package declares `requires-python = ">=3.14"` and targets `py314`, and its CI runs
  3.14 only. The floor also enforces upgrades: uv refuses to resolve the package for a
  consumer whose `requires-python` allows an older Python. DiD therefore raises its floor
  when it adopts the package, and the Refiner raises its ruff target to match.

### Proving the Refiner is unchanged

The first-release moves are behaviour-free, so refined output must be byte-identical. That
includes the augmented header, since the Refiner passes its own `AugmentingTool` and gets
its own IDs back. That is checked, not argued:

- Before the first move, refine every document under `tests/fixtures/` (`ecr_pairs`,
  `eicr_v1_1`, `eicr_v3_1_1`, `sections`) on `main` and record the output.
- After each ticket, refine the same inputs and diff byte for byte. Any difference blocks
  the ticket.
- The scenario snapshots in `tests/integration/scenarios/snapshots/` are not enough on their
  own: they cover one pair and need the database.
- The Lambda installs dependencies by a different path, so once the moves land, rebuild its
  image and run the eval harness (`tests/localstack/eval.py`) against the same baseline.
- DiD's side follows the same rule. Before it swaps its `core/augment.py` fork for
  `dibbs_ecr.augment`, it records its augmented output over its own fixtures. After the
  swap, the output must be byte-identical. The release is done when both products' parity
  checks pass against one tag.

### How other products use it

- `uv` workspaces (DiD, TTC):
  `dibbs-ecr = { git = "https://github.com/CDCgov/dibbs-ecr-refiner", subdirectory = "refiner/packages/dibbs-ecr", tag = "dibbs-ecr-v0.1.0" }`
- `pip`: `dibbs-ecr @ git+https://github.com/CDCgov/dibbs-ecr-refiner@dibbs-ecr-v0.1.0#subdirectory=refiner/packages/dibbs-ecr`
- An image build stage that installs it needs `git`.
- Moving the package to its own repository later (option A2) changes only this URL, provided
  consumers import `dibbs_ecr` and never a path into it.

## Consequences

- `services/ecr/model.py` and `specification/` shrink to the Refiner's own types and rules,
  importing the rest from `dibbs_ecr`. `reportability.py` moves. `augment.py` shrinks to the
  Refiner's `AugmentingTool`.
- The Refiner gains `refiner/packages/` and a second tag namespace.
- Every Refiner image, the dev stack, the local venv and CI install one more local package --
  six install sites, listed above. Missing one fails loudly in images and CI, but silently
  in the `lambda` dev container.
- Each first-release ticket carries a byte-level parity diff against a recorded baseline.
- On adopting the first release:
  - DiD deletes its namespace and OID constants, its augmentation fork and
    `condition_codes_from_rr`, and raises `requires-python` to `>=3.14`.
  - TTC can delete its constants. Its independent augmenter can follow later, as separate
    work.
- Changes to shared specification code land in one place and one review, whichever product
  needs them.
- The template-aware model the Refiner deferred in ADR 0010 (Option D) has a home. It gets its
  own ADR.

## Open Questions

None. Resolved 2026-10-26:
- augmentation is in the first release (B3)
- the RR enters, for DiD's telemetry
- the Python floor is 3.14
- no IG text is committed. The README documents the download and conversion, and the
  generated `template_oids.py` is the record.

## Links

- ADR 0010 (narrative reconstruction; defers the template-aware model)
- ADR 0016 (naming conventions)
- The closed DiD-lambda proposal (branches `1968fc43` / `e24eb58f`), option A2
- `services/ecr/README.md`, `DIBBs-eCR-Refiner-Augmentation-Guide.md`
- eICR STU 3.1.1 IG Vol 2; eCR Data Augmentation IG v5

## Appendix

### Suggested Implementation Tickets

Ordered so that the parity baseline and every install site exist before any code moves.

#### `test: record a refinement parity baseline`

Refine every document under `tests/fixtures/` on `main`, record the output, and add a check
that diffs a branch's output against it byte for byte. Every following refactor ticket runs
it.

#### `chore: add refiner/packages/dibbs-ecr skeleton`

`pyproject.toml` (`requires-python = ">=3.14"`, ruff `py314`), empty `src/dibbs_ecr/`, a
test that the package imports, its own ruff and mypy run. No code moves. Raise the Refiner's
ruff `target-version` to `py314` in the same ticket. Any new `UP` findings are fixed
separately, so the parity baseline isn't mixed with lint churn.

#### `chore: install dibbs-ecr at every install site`

`Dockerfile.app`, `Dockerfile.lambda`, `Dockerfile.ops`; the `server` command in
`docker-compose.override.yml`; a mount plus editable install for `lambda` in
`docker-compose.yml`; `tests.yml` and `typecheck.yml`; `just server` `_venv`. Lands before
any move, so a moved import never meets an environment without the package.

#### `ci: forbid app imports in dibbs_ecr`

#### `refactor: split spec types out of services/ecr/model.py`

Move the namespace constants, `EicrVersion`, `TriggerCode` and `EICRSpecification` into
`dibbs_ecr`; re-export from `model.py` temporarily so nothing else changes.

#### `refactor: split SectionSpecification and the section catalog`

Shared catalog without rules in `dibbs_ecr.eicr`; the Refiner keeps `entry_match_rules.py`
and adds `entry_match_rules_for(loinc_code)`, reading it in place of
`SectionSpecification.entry_match_rules`.

#### `refactor: move template_oids with its generator`

`git mv` the generated file and `generate_template_oids.py`. Rewrite the README as the
reproduction steps: licensed download, sha256, `marker` conversion into a gitignored
`sources/`, then generate. Fold `generate_template_oids.sh` into it, since the script's
markdown path is going away. `git rm` the IG markdown and `marker`'s `_page_0_Picture_1.jpeg`.
Add the regeneration test, skipped when there's no local conversion.

#### `refactor: move versions, detection and the loader`

#### `refactor: move reportability`

Move the RR types and `reportability.py`; replace the `core.exceptions` import with a package
exception and update `tests/unit/test_service_reportability.py`.

#### `design: AugmentingTool against both forks`

Diff the 6 differing functions in `services/ecr/augment.py` and DiD's `core/augment.py`, and
draft `AugmentingTool` and the `augment_*` signatures before any code moves.

#### `refactor: move augmentation behind AugmentingTool`

Move the IG writer into `dibbs_ecr.augment`. The Refiner keeps its identity constants,
`REFINER_DETERMINISTIC_NS` and ID derivation, and passes them as its `AugmentingTool`.
Parity baseline must match byte for byte.

#### `chore: remove re-exports from services/ecr/model.py`

Once all imports point at `dibbs_ecr`.

#### `test: verify the Lambda against the baseline`

Rebuild the Lambda image and run the eval harness against the parity baseline.

#### `release: tag dibbs-ecr-v0.1.0`

#### DiD (tracked in `dibbs-ecr-diff`): adopt `dibbs-ecr-v0.1.0`

Record augmented-output parity over DiD's fixtures first. Then:
- swap the fork for `dibbs_ecr.augment`
- replace `condition_codes_from_rr` with `get_reportable_conditions_by_jurisdiction` and log
  its result
- raise `requires-python` to `>=3.14`

Parity must match. A pass here and on the Refiner's baseline is the sign the package works.
