# Scenarios suite

Pinned `(fixture, configuration)` refinement scenarios. Each scenario refines a committed eICR/RR pair against a committed configuration JSON, validates the refined documents against CDA R2 XSD and schematron, then compares the result against committed snapshots.

The suite catches regressions in entry-matching, identifier derivation, section-level pruning, and CDA conformance as the codebase evolves. Unlike the unit tests, scenarios exercise the full production refinement pipeline (the same path lambda runs); unlike the integration tests, they need no infrastructure--fixtures and configs are static files on disk.

## Running

```bash
pytest tests/scenarios/
```

To see a specific scenario's expected output:

```bash
cat tests/scenarios/snapshots/all_sections_COVID_INFLUENZA/covid_baseline/expected_trace.json
```

For a high-level summary intended for stakeholder review, see [REPORT.md](./REPORT.md).

## When refinement behavior legitimately changes

Snapshots fail loudly when output differs. To regenerate:

```bash
pytest tests/scenarios/test_all_sections_covid_influenza.py --update-snapshots
```

Validation runs before the snapshot write, so invalid refined documents fail the test before any stale snapshot gets overwritten. The test passes and prints the snapshot directory for each updated scenario. Always inspect the resulting diff before committing -- many regressions arrive as "unexpectedly different output" rather than "test failure." The `expected_trace.json` should change in obvious, explicable ways for any intentional refactor; opaque XML diffs are the cue to look closer.

## Regenerating the stakeholder report

`REPORT.md` is an auto-generated summary of the suite intended for stakeholder review. It pulls from the committed snapshots and the roll-up coverage table inside `authoring/build_report.py`. Regenerate it whenever you update snapshots or change scenario coverage:

```bash
pytest tests/scenarios/ --update-snapshots
python tests/scenarios/authoring/build_report.py
```

Commit both the regenerated snapshots and the regenerated `REPORT.md` together. A follow-up PR will add a CI step that runs `build_report.py` and fails with `git diff --exit-code` if the committed `REPORT.md` is out of date; until that lands, the discipline is on the developer.

To update the roll-up coverage matrix shown in the report (e.g. after adding a scenario that closes a gap, or after Tim or another stakeholder shares additional concerns), edit the `ROLLUP_COVERAGE` list at the top of `authoring/build_report.py` and re-run the script.

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
5. Run `python tests/scenarios/authoring/build_report.py` to regenerate `REPORT.md`.
6. Commit `REPORT.md` alongside the new snapshots and the test file change.

## Adding a new fixture

1. Commit the eICR and RR XML to `tests/fixtures/<fixture_dir>/` named `eICR.xml` and `RR.xml`.
2. Author at least one configuration for it via the workflow above.
3. Add a new test file `tests/scenarios/test_<fixture_dir>.py`, modeled on `test_all_sections_covid_influenza.py`.
4. Generate snapshots, regenerate the report, commit everything together.

## Directory layout

```
tests/
├── fixtures/
│   └── <fixture_dir>/
│       ├── eICR.xml
│       ├── RR.xml
│       └── configurations/
│           └── <config_name>.json
└── scenarios/
    ├── README.md                       Explains the scenarios suite
    ├── REPORT.md                       Human-readable stakeholder report
    ├── harness.py                      Production refinement wrapper (fixed timestamp)
    ├── conftest.py                     --update-snapshots flag, composed validation fixture
    ├── test_scenario_wiring.py         Harness composition + determinism (no snapshots)
    ├── test_<fixture>.py               One file per fixture, parametrized snapshot scenarios
    ├── test_explicit_assertions.py     Named assertions for specific behaviors (no snapshots)
    ├── authoring/
    │   └── build_report.py             Regenerates REPORT.md from snapshots + coverage table
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
- `expected_eICR.xml` is the structural truth. It catches section-level changes the trace cannot see -- different entries retained, footnote text changes, narrative handling.
- `expected_RR.xml` does the same for the refined RR.

The trace JSON and the XML are correlated but not redundant: a change to provenance footnote rendering would touch the XML without touching the trace, and a change to size-reduction calculation would touch the trace without touching the XML.

In addition to the snapshot comparison, every refined document is validated for well-formedness, CDA R2 XSD conformance, and schematron conformance before snapshot operations run. Warnings are tolerated; errors and fatal severity fail the test.

## Snapshot scenarios vs explicit assertions

The suite contains two kinds of tests, and they cover different ground:

- **Parametrized snapshot scenarios** in `test_<fixture>.py` assert that the refined output matches a committed expected file. They catch every kind of regression but a failure reads as "the output changed" rather than "this specific behavior broke."
- **Explicit assertions** in `test_explicit_assertions.py` pick out specific named behaviors worth pinning deliberately. Each test runs its own refinement, asserts preconditions on the fixture and configuration to guard against silent drift, and asserts a specific structural property. The function name describes the behavior being pinned. When a fixture or configuration change makes the test no longer exercise its named concern, the precondition assertions fail diagnostically rather than the test passing for the wrong reason.

Add to `test_explicit_assertions.py` when a snapshot's coverage of a specific concern is implicit and the concern is named externally.

## Behaviors pinned by the current suite

The suite was designed to catch regressions in entry-matching behavior, especially the kinds of issues surfaced during early testing.

- **OID-relaxed matching for Immunizations.** The `all_sections_COVID_INFLUENZA` fixture has Immunization codes tagged with the RxNorm OID where the code values themselves are CVX. The `covid_with_custom_codes` scenario adds one such CVX code (`2563008`) as a custom code; the snapshot pins whether the matcher accepts the cross-OID match.
- **Custom codes in nested entryRelationship/value.** Custom code `10628911000119103` lives in the fixture's Problem List `entryRelationship/observation/value`. `covid_with_custom_codes` adds it; the snapshot pins whether matching reaches into that nested location.
- **Custom codes in substanceAdministration.** `covid_with_substance_admin_custom_code` adds a custom code targeting the `substanceAdministration/consumable` of a Medications entry that's outside the COVID grouper. The snapshot pins that the entry survives -- Medications Administered goes from 1 to 2 entries, History of Medication Use from 1 to 2.
- **Procedure entryRelationship-only matches don't justify retention.** Nausea (SNOMED `422587007`) is a configured matching code under the COVID grouper, and the fixture's three procedure entries (Colonic polypectomy, ECMO, Ventilator care) all carry Nausea in their `entryRelationship`. Even so, `covid_baseline` shows the Procedures section stubbed at 0 entries -- the matcher correctly requires a match at an entry-level location, not anywhere inside the entry. The explicit assertion `test_covid_baseline_does_not_retain_procedures_via_entry_relationship_only_match` in `test_explicit_assertions.py` pins this directly with precondition guards.
- **Procedures retained via custom procedure codes.** `covid_with_custom_codes` adds ECMO (SNOMED `233573008`) and `covid_with_procedure_only_code` adds Ventilator care (SNOMED `385857005`) as custom codes. Both snapshots show the matching procedure surviving whole.
- **Vital sign sub-component pruning.** `covid_with_custom_codes` adds Heart Rate (LOINC `8867-4`) as a single custom code; the snapshot pins panel pruning at the one-of-nine cardinality. `covid_with_multi_vital_sign_codes` adds three (`8867-4`, `8480-6`, `9279-1`) and pins the three-of-nine case.
- **Adding unrelated code sets does not remove relevant data.** `covid_plus_unrelated_condition` adds Fertilizer Poisoning (the exact condition Tim cited) to the COVID configuration. The snapshot's size reduction matches `covid_baseline` (52%), confirming that adding orthogonal codes neither adds matches nor removes COVID-relevant content. A regression would manifest as the size reduction climbing above the baseline's.
- **Section action variations.** `covid_with_section_overrides` snapshots the three section actions (`refine`, `retain`, `remove`) and narrative on/off across multiple sections, including narrative-only sections (Chief Complaint, HPI, Reason for Visit, Review of Systems) and section removal (Vital Signs).
- **No-match section stubbing.** Several sections of the fixture have no codes that match the COVID grouper (Procedures under baseline, Immunizations under baseline, etc.). `covid_baseline` pins the "stub the section when nothing matches" policy.
- **CDA conformance through refinement.** Every refined eICR and RR is validated against CDA R2 XSD and schematron on every test run. Refactors that produce malformed output (e.g. a regression in removed-narrative handling that breaks schema) fail loudly here rather than at downstream consumers.

## Known coverage gaps

No remaining gaps from the original roll-up sheet. Forward-looking work to consider:

- **Additional fixtures.** Currently only the COVID/Influenza fixture is exercised. Adding Mpox, Chlamydia, Pertussis, or other condition mixes would catch grouper-specific regressions.
- **Additional jurisdictions.** All scenarios use the `SDDH` jurisdiction label. Multi-jurisdiction coverage would surface any jurisdiction-dependent behavior in the augmentation seed.
- **Performance pinning.** If the suite grows large enough that schematron compile time becomes meaningful, the integration conftest's per-call XSLT compile is the natural place to add caching.

## Cross-suite imports (tech debt)

This suite currently imports `normalize_xml` from `tests/unit/conftest.py` and the validation helpers (`validate_xml_string`, `validate_xml_string_xsd`, `xsd_schema`, `validate_refined_xml`, `assert_schematron_valid`, `assert_xsd_valid`) from `tests/integration/conftest.py`. Both are functional but architecturally awkward -- scenarios shouldn't depend on the implementation details of unit or integration conftests.

A future cleanup ticket should lift these to a shared `tests/_helpers/` module that unit, integration, and scenarios all import from. The functions themselves don't need to change; only their location.
