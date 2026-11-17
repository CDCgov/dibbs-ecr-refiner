# Refinement snapshot generator

These snapshots help us test that moving shared eCR specification code into
`dibbs-ecr` leaves Refiner's output unchanged. We run the same fixtures with the
same settings and compare the XML byte for byte.

From the repository root, using the project's `refiner/.venv`:

```bash
just server generate-snapshots
```

Install dependencies first with `just server install-dev` if needed.
Alternatively, from `refiner/` with the project's Python dependencies installed:

```bash
python -m scripts.snapshot_generator.generate_snapshots
```

The command writes XML to `tests/fixtures/expected/`. Rerunning it overwrites
expected XML. If a fixture has been deleted, its expected output files remain in place so the parity check can
report them.

Run the parity suite from `refiner/`:

```bash
python -m pytest tests/parity/
```

The tests run the cases once in memory and compare the complete output inventory
and raw bytes. The tests fail if files are missing, extra files are present, or
the generated XML differs from the expected output. Failures
identify the affected output paths and show an
`expected`/`actual` diff of formatted XML copies. Each diff is limited to 80 lines
and 8,000 characters, with a notice when truncated. Invalid XML falls back to a
raw text diff. If formatting hides the difference, such as a trailing newline,
the test reports that the raw bytes differ even though the displayed XML is
identical.

During `dibbs-ecr` extraction, keep the recorded XML and fixed inputs unchanged. Investigate
differences rather than regenerating the baseline to accept them.

## Fixed inputs and coverage

`tests/fixtures/manifest.py` identifies every loose eICR/RR pair, exact ZIP member,
and standalone section fragment. Missing or unlisted fixtures and archive members
fail validation.

`tests/fixtures/parity/cases.json` records the scenarios, contexts, fixed
augmentation time **20260101000000+0000**, and terminology provenance
**TES 3.0.0**. Five configuration files under
`tests/fixtures/parity/configurations/` were copied verbatim from the original
baseline. Replay does not query TES, rebuild configurations from the specification,
or derive canonical URLs from directory names.

The baseline contains **72 XML files**:

- **21 pair scenarios** produce 42 eICR/RR outputs. All 10 original loose/archive
  pairs retain their reportable jurisdiction and condition-grouper contexts.
- **30 section scenarios** produce 30 fragment outputs. All 10 fragments run
  under specifications **1.1**, **3.1**, and **3.1.1**.

All configured pair sections use `include: true`, `action: refine`, and
`narrative: reconstruct`. Each pair uses the canonical URL and jurisdiction
recorded in `cases.json`, along with configuration version **1**. Before refining
the pair, the runner checks that the reportable conditions found in its RR match the
expected conditions for each jurisdiction in `cases.json`. It then uses the
production code to read the source document information needed for augmentation,
but sets the augmentation timestamp to the fixed value in `cases.json` so it
stays the same on every run.

Each section fragment is processed by the same `process_section` function used
by Refiner. Its LOINC code, matching codes, and display names come from
`cases.json`, so every run uses the same inputs. The runner reconstructs the
narrative for each fragment using specification versions **1.1**, **3.1**, and
**3.1.1**. Any code-system lists or display names left out of `cases.json` are
treated as empty.

## Expected outputs

`tests/fixtures/expected/` contains XML only. Pair outputs use the fixture's
top-level source directory, manifest name, and catalog scenario name. Scenario
names identify the jurisdiction and condition, without a narrative-mode suffix:

```text
expected/eicr_v3_1_1/all_sections_sddh_nonsense_problems_zip/
  SDDH_covid_19/
    eICR.xml
    RR.xml
```

Fragment outputs use
`expected/sections/<fixture-name>/<version>/section.xml`.
Input mappings and configuration references live in the fixed catalog; there
are no generated `case.json` files.

XML is compared exactly as emitted, including whitespace, augmented headers,
document IDs, set IDs, and RR references. Formatting is
used only to display a failed comparison. Git attributes and pre-commit whitespace
exclusions preserve these recorded bytes.

## CI

The standalone `Refinement parity` workflow runs on pull requests that modify
`refiner/packages/dibbs-ecr/**`. Its job is named `run-refinement-parity`.
