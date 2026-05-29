# Scenarios suite

Pinned `(fixture, configuration)` refinement scenarios. Each scenario refines a committed eICR/RR pair against a committed configuration JSON and compares the result against committed snapshots.

The suite catches regressions in entry-matching, identifier derivation, and section-level pruning as the codebase evolves. Unlike the unit tests, scenarios exercise the full production refinement pipeline (the same path lambda runs); unlike the integration tests, they need no infrastructure; fixtures and configs are static files on disk.

## Running

```bash
pytest tests/scenarios/
```

To see a specific scenario's expected output:

```bash
cat tests/scenarios/snapshots/all_sections_COVID_FLU/covid_baseline/expected_trace.json
```

## When refinement behavior legitimately changes

Snapshots fail loudly when output differs. To regenerate:

```bash
pytest tests/scenarios/test_all_sections_covid_flu.py --update-snapshots
```

The test passes and prints the snapshot directory for each updated scenario. Always inspect the resulting diff before committing--many regressions arrive as "unexpectedly different output" rather than "test failure." The `expected_trace.json` should change in obvious, explicable ways for any intentional refactor; opaque XML diffs are the cue to look closer.

## Authoring a new configuration

Configurations are committed as the production activation-format JSON that lambda reads from S3. We don't generate these from a script; rather, we use the local app to author them and pull the result out of localstack. This keeps the suite using the same serialization production uses, with no parallel authoring path to drift.

1. Start the local stack: `docker compose up -d`.
2. In the webapp, create a configuration with the desired conditions / custom codes / section processing rules, then activate it.
3. Pull the activation JSON from localstack:

```bash
docker compose exec localstack awslocal s3 cp \
  s3://local-config-bucket/configurations/<jurisdiction>/<canonical_url_uuid>/<version>/active.json \
  - > <descriptive_name>.json
```

1. Move the JSON to `tests/fixtures/<fixture_dir>/configurations/<descriptive_name>.json`.
2. Add a `Scenario(...)` entry to the relevant test file referencing it.
3. Run `pytest tests/scenarios/test_<fixture>.py --update-snapshots` to generate the expected outputs.
4. Inspect the snapshots; commit them.

## Adding a new fixture

1. Commit the eICR and RR XML to `tests/fixtures/<fixture_dir>/` named `eICR.xml` and `RR.xml`.
2. Author at least one configuration for it via the workflow above.
3. Add a new test file `tests/scenarios/test_<fixture_dir>.py`, modeled on `test_all_sections_covid_flu.py`.
4. Generate and commit snapshots.

## Directory layout

```bash
tests/
    ├── fixtures/
    │   └── <fixture_dir>/
    │       ├── eICR.xml
    │       ├── RR.xml
    │       └── configurations/
    │           └── <config_name>.json
    └── scenarios/
        ├── harness.py            production refinement wrapper (fixed timestamp)
        ├── conftest.py           registers --update-snapshots
        ├── test_smoke.py         harness composition + determinism (no snapshots)
        ├── test_<fixture>.py     one file per fixture
        └── snapshots/
            └── <fixture_dir>/
                └── <scenario>/
                    ├── expected_trace.json
                    ├── expected_eICR.xml
                    └── expected_RR.xml
```

## Why three assertion artifacts per scenario

Three artifacts give three independent failure modes:

- `expected_trace.json` is the Tim-readable headline. It catches top-line regressions (outcome changed, size reduction shifted, identifier derivation changed) with a one-line diff. Read this first when CI goes red.
- `expected_eICR.xml` is the structural truth. It catches section-level changes the trace cannot see — different entries retained, footnote text changes, narrative handling.
- `expected_RR.xml` does the same for the refined RR.
  The trace JSON and the XML are correlated but not redundant: a change to provenance footnote rendering would touch the XML without touching the trace, and a change to size-reduction calculation would touch the trace without touching the XML.

In addition to the snapshot comparison, every refined document is validated for well-formedness, CDA R2 XSD conformance, and schematron conformance before snapshot operations run. Warnings are tolerated; errors and fatal severity fail the test.

## Behaviors pinned by the current suite

The suite was designed to catch regressions in entry-matching behavior, especially the kinds of issues surfaced during early testing.

- **OID-relaxed matching for Immunizations.** The `all_sections_COVID_FLU` fixture has Immunization codes tagged with the RxNorm OID where the code values themselves are CVX. The `covid_with_custom_codes` scenario adds one such CVX code as a custom code; the snapshot pins whether the matcher accepts the cross-OID match.
- **Custom codes in nested locations.** Custom code `10628911000119103` lives in the fixture's Problem List `entryRelationship/observation/value`. `covid_with_custom_codes` adds it; the snapshot pins whether matching reaches into that nested location.
- **Procedure retention via unrelated `entryRelationship` codes.** The Colonic polypectomy procedure in the fixture has a Nausea code in its `entryRelationship`. `covid_baseline` snapshots whether that triggers retention of an otherwise-unrelated procedure.
- **Adding procedures as custom codes.** `covid_with_custom_codes` adds `233573008` (ECMO) — a procedure not in the COVID grouper — and snapshots whether the procedure entry is preserved whole.
- **Vital sign sub-component pruning.** `covid_with_custom_codes` adds `8867-4` (Heart Rate) to test whether one matching sub-component preserves just that component or the whole panel.
- **Section action variations.** `covid_with_section_overrides` snapshots the three section actions (`refine`, `retain`, `remove`) and narrative on/off across multiple sections, including narrative-only sections (Chief Complaint, HPI, Reason for Visit, Review of Systems) and section removal (Vital Signs).
- **No-match section stubbing.** Several sections of the fixture have no codes that match the COVID grouper (Immunizations, Vital Signs under baseline, etc.). `covid_baseline` pins the "stub the section when nothing matches" policy.
- **CDA conformance through refinement.** Every refined eICR and RR is validated against CDA R2 XSD and schematron on every test run. Refactors that produce malformed output (e.g. a regression in removed-narrative handling that breaks schema) fail loudly here rather than at downstream consumers.
