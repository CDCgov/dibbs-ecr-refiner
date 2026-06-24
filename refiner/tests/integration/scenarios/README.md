# Scenarios suite

Pinned `(fixture, configuration)` refinement scenarios. Each scenario builds a configuration through the live API, refines a committed eICR/RR pair against it, validates the refined documents against CDA R2 XSD and schematron, then compares the result against committed snapshots.

The suite catches regressions in entry-matching, identifier derivation, section-level pruning, and CDA conformance as the codebase evolves. Like the unit tests, scenarios exercise the full production refinement pipeline (the same path lambda runs). Unlike them, each scenario authors its configuration through the running app — `create configuration → customize → activate → read the activation payload back from localstack` — so the suite uses the exact serialization production uses, with a single authoring path and no committed configuration JSON to drift. Configurations are therefore _not_ static files: the suite needs the integration infrastructure (docker compose, localstack) up, the same as the rest of `tests/integration/`.

## Running

```bash
pytest tests/integration/scenarios/
```

To see a specific scenario's expected output:

```bash
cat tests/integration/scenarios/snapshots/all_sections_covid_influenza/covid_baseline/expected_trace.json
```

For a high-level summary intended for stakeholder review, see [REPORT.md](./REPORT.md).

## When refinement behavior legitimately changes

Snapshots fail loudly when output differs. To regenerate:

```bash
pytest tests/integration/scenarios/test_all_sections_covid_influenza.py --update-snapshots
```

Validation runs before the snapshot write, so invalid refined documents fail the test before any stale snapshot gets overwritten. The test passes and prints the snapshot directory for each updated scenario. Always inspect the resulting diff before committing — many regressions arrive as "unexpectedly different output" rather than "test failure." The `expected_trace.json` should change in obvious, explicable ways for any intentional refactor; opaque XML diffs are the cue to look closer.

A snapshot change should ride with the change that caused it. If you alter a scenario's recipe (codes, section processing, associated conditions), regenerate that scenario's snapshot in the same PR as the recipe change, and keep unrelated scenarios out of the diff. A migration or refactor that legitimately shifts only the augmented document identifiers (for example, a jurisdiction-label change) should produce an identifier-only diff across the affected snapshots — confirm that before committing.

## Regenerating the stakeholder report

`REPORT.md` is an auto-generated summary of the suite intended for stakeholder review. It pulls from the committed snapshots and the roll-up coverage table inside `build_report.py`. Regenerate it whenever you update snapshots or change scenario coverage:

```bash
pytest tests/integration/scenarios/ --update-snapshots
python tests/integration/scenarios/build_report.py
```

Commit both the regenerated snapshots and the regenerated `REPORT.md` together. A follow-up PR will add a CI step that runs `build_report.py` and fails with `git diff --exit-code` if the committed `REPORT.md` is out of date; until that lands, the discipline is on the developer.

To update the coverage tables shown in the report, edit the data lists at the top of `build_report.py` and re-run the script: `ROLLUP_COVERAGE` for Tim's numbered Roll-up issues (e.g. after adding a scenario that closes a gap, or after a stakeholder shares additional concerns), and `CAPABILITY_COVERAGE` for product capabilities the suite pins that aren't Roll-up issues (e.g. narrative reconstruction). A scenario listed in either gets a back-reference in its detail section.

## How configurations are built

A scenario does not point at a committed configuration file. It carries a _recipe_ — a `Scenario` dataclass in `conftest.py` naming the condition to configure for plus the customizations layered on top of the default configuration:

- `custom_codes` — added one per entry via the custom-code endpoint.
- `section_overrides` — per-section processing changes (`include` / `narrative` / `action`) applied via the section-processing endpoint.
- `associated_conditions` — additional code sets associated with the configuration.

The `build_scenario_configuration` fixture interprets the recipe against the running app: it creates a draft configuration for the condition, applies the customizations, activates it (which writes `active.json` to localstack exactly as production does), then reads that payload back as a `ProcessedConfiguration`. The augmented document identifiers are seeded by the jurisdiction the config was activated under (the integration test user's jurisdiction, `SDDH`), _not_ by the RR's reportable-to jurisdiction — that lets the suite reuse arbitrary test data without standing up matching fake jurisdictions.

## Authoring a new configuration

1. Add a `Scenario(...)` entry to `SCENARIOS` in `conftest.py`, giving it a unique `name`, the `condition_name` to configure for, the condition grouper's `canonical_url`, a fresh `configuration_version`, and whatever `custom_codes` / `section_overrides` / `associated_conditions` the scenario exercises.
2. The parametrized snapshot test picks the entry up automatically. (Explicit-assertion tests reference scenarios by name via `SCENARIOS_BY_NAME` when they need one)
3. Generate the expected outputs:

```bash
pytest tests/integration/scenarios/test_all_sections_covid_influenza.py \
  -k <scenario_name> --update-snapshots
```

1. Inspect the snapshots; commit them.
2. Run `python tests/integration/scenarios/build_report.py` to regenerate `REPORT.md`.
3. Commit `REPORT.md` alongside the new snapshots and the `conftest.py` change.

There is no `awslocal s3 cp` step and no committed `active.json` — authoring is entirely in code via the recipe. If the condition's `display_name` doesn't resolve against the seeded TES data, `get_condition_id` fails diagnostically; query the `conditions` table to find the exact name.

## Adding a new fixture

1. Commit the eICR and RR XML to `tests/fixtures/ecr_paris/<fixture_dir>/` named `eICR.xml` and `RR.xml`.
2. Add at least one `Scenario` for it via the workflow above (the `fixture_dir` field points the loader at the new directory).
3. If the new fixture warrants its own file, add `tests/integration/scenarios/test_<fixture_dir>.py`, modeled on `test_all_sections_covid_influenza.py`; otherwise add scenarios to the existing list.
4. Generate snapshots, regenerate the report, commit everything together.

## Why three assertion artifacts per scenario

Three artifacts give three independent failure modes:

- `expected_trace.json` is the Tim-readable headline. It catches top-line regressions (outcome changed, size reduction shifted, identifier derivation changed) with a one-line diff. Read this first when CI goes red.
- `expected_eICR.xml` is the structural truth. It catches section-level changes the trace cannot see — different entries retained, footnote text changes, narrative handling.
- `expected_RR.xml` does the same for the refined RR.

The trace JSON and the XML are correlated but not redundant: a change to provenance footnote rendering would touch the XML without touching the trace, and a change to size-reduction calculation would touch the trace without touching the XML.

In addition to the snapshot comparison, every refined document is validated for well-formedness, CDA R2 XSD conformance, and schematron conformance before snapshot operations run. Warnings are tolerated; errors and fatal severity fail the test.

## Snapshot scenarios vs explicit assertions

The suite contains two kinds of tests, and they cover different ground:

- **Parametrized snapshot scenarios** in `test_all_sections_covid_influenza.py` assert that the refined output matches a committed expected file. They catch every kind of regression but a failure reads as "the output changed" rather than "this specific behavior broke."
- **Explicit assertions** in `test_explicit_assertions.py` pick out specific named behaviors worth pinning deliberately. Each test builds its configuration through the same recipe path (keyed by scenario name), asserts preconditions on the fixture and configuration to guard against silent drift, and asserts a specific structural property. The function name describes the behavior being pinned. When a fixture or configuration change makes the test no longer exercise its named concern, the precondition assertions fail diagnostically rather than the test passing for the wrong reason.

Both kinds build configurations through `build_scenario_configuration`; the difference is what they assert on the result, not how they obtain it.

Add to `test_explicit_assertions.py` when a snapshot's coverage of a specific concern is implicit and the concern is named externally.

## Behaviors pinned by the current suite

The suite was designed to catch regressions in entry-matching behavior, especially the kinds of issues surfaced during early testing.

- **OID-relaxed matching for Immunizations.** The `all_sections_covid_influenza` fixture has Immunization codes tagged with the RxNorm OID where the code values themselves are CVX. The `covid_with_custom_codes` scenario adds one such CVX code (`2563008`) as a custom code; the snapshot pins whether the matcher accepts the cross-OID match.
- **Custom codes in nested entryRelationship/value.** Custom code `10628911000119103` lives in the fixture's Problem List `entryRelationship/observation/value`. `covid_with_custom_codes` adds it; the snapshot pins whether matching reaches into that nested location.
- **Custom codes in substanceAdministration.** `covid_with_substance_admin_custom_code` adds a custom code targeting the `substanceAdministration/consumable` of a Medications entry that's outside the COVID grouper. The snapshot pins that the entry survives — Medications Administered goes from 1 to 2 entries, History of Medication Use from 1 to 2.
- **Procedure entryRelationship-only matches don't justify retention.** Nausea (SNOMED `422587007`) is a configured matching code under the COVID grouper, and the fixture's three procedure entries (Colonic polypectomy, ECMO, Ventilator care) all carry Nausea in their `entryRelationship`. Even so, `covid_baseline` shows the Procedures section stubbed at 0 entries — the matcher correctly requires a match at an entry-level location, not anywhere inside the entry. The explicit assertion `test_covid_baseline_does_not_retain_procedures_via_entry_relationship_only_match` in `test_explicit_assertions.py` pins this directly with precondition guards.
- **Procedures retained via custom procedure codes.** `covid_with_custom_codes` adds ECMO (SNOMED `233573008`) and `covid_with_procedure_only_code` adds Ventilator care (SNOMED `385857005`) as custom codes. Both snapshots show the matching procedure surviving whole.
- **Vital sign sub-component pruning.** `covid_with_custom_codes` adds Heart Rate (LOINC `8867-4`) as a single custom code; combined with body temperature (LOINC `8310-5`, a COVID condition-grouper member matched from the baseline configuration), the snapshot pins panel pruning at the two-of-nine cardinality. `covid_with_multi_vital_sign_codes` adds three more (`8867-4`, `8480-6`, `9279-1`) and pins the four-of-nine case. The surviving sub-components are the configured-and-present codes, not only the custom additions.
- **Adding unrelated code sets does not remove relevant data.** `covid_plus_unrelated_condition` associates Agricultural Chemicals (Fertilizer) Poisoning (the condition Tim cited) with the COVID configuration. Its size reduction matches `covid_baseline`, confirming that adding orthogonal codes neither adds matches nor removes COVID-relevant content. A regression would manifest as the size reduction climbing above the baseline's. The explicit assertion `test_adding_unrelated_condition_codes_does_not_change_refinement` pins this as a direct equality on size reduction and retained clinical entries.
- **Section processing variations.** `covid_with_section_overrides` exercises the section-processing dimensions: excluding sections (`include=False`), refining a section while dropping its narrative (`narrative="remove"`), and forcing `retain`, across both narrative-only and entry-based sections. The snapshot pins the resulting dispositions in the refined output.
- **No-match section stubbing.** Several sections of the fixture have no codes that match the COVID grouper (Procedures under baseline, Immunizations under baseline, etc.). `covid_baseline` pins the "stub the section when nothing matches" policy.
- **CDA conformance through refinement.** Every refined eICR and RR is validated against CDA R2 XSD and schematron on every test run. Refactors that produce malformed output (e.g. a regression in removed-narrative handling that breaks schema) fail loudly here rather than at downstream consumers.

> [!NOTE]
> Issues #1, #2, #4, #5, and #6 are additionally backed by named explicit
> assertions in `test_explicit_assertions.py`, which fail with a behavior-level
> message rather than an opaque snapshot diff

## Known coverage gaps

No remaining gaps from the original roll-up sheet. Forward-looking work to consider:

- **Additional fixtures.** Currently only the COVID/Influenza fixture is exercised. Adding Mpox, Chlamydia, Pertussis, or other condition mixes would catch grouper-specific regressions.
- **Additional jurisdictions.** All scenarios activate under the `SDDH` jurisdiction. Multi-jurisdiction coverage would surface any jurisdiction-dependent behavior in the augmentation seed — though note configs are authored by the integration test user, whose jurisdiction is fixed, so this would need additional seeded users.
- **Build cost.** Each scenario now does a full create → activate → fetch cycle, and the two comparison-based explicit tests do two. If the suite grows large enough that this dominates, a session-scoped cache of built configurations keyed by scenario name is the natural lever.

## Cross-suite imports (tech debt)

This suite imports `normalize_xml` from `tests/unit/conftest.py`, and the parent integration `conftest.py` contributes the validation helpers (`validate_xml_string`, `validate_xml_string_xsd`, `xsd_schema`, `validate_refined_xml`, `assert_schematron_valid`, `assert_xsd_valid`) — the fixtures by inheritance (this suite is a subdirectory of `tests/integration/`), and the plain helper functions by explicit import from `..conftest`. The `normalize_xml` import across to the unit suite remains architecturally awkward.

A future cleanup ticket should lift the shared helpers to a `tests/_helpers/` module that unit, integration, and scenarios all import from. The functions themselves don't need to change; only their location.
