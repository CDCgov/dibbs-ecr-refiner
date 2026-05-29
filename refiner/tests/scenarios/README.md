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

## Why three artifacts per scenario

The trio gives three independent failure modes:

- `expected_trace.json` is the human-readable headline. It catches top-line regressions (outcome changed, size reduction shifted, identifier derivation changed) with a one-line diff. Read this first when CI goes red.
- `expected_eICR.xml` is the structural truth. It catches section-level changes the trace cannot see; different entries retained, footnote text changes, narrative handling.
- `expected_RR.xml` does the same for the refined RR.

The trace JSON and the XML are correlated but not redundant: a change to provenance footnote rendering would touch the XML without touching the trace, and a change to size-reduction calculation would touch the trace without touching the XML.
