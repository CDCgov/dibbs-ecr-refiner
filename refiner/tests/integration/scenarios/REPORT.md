# eCR Refiner — Scenarios Report

*Auto-generated. To regenerate:*

```
pytest tests/integration/scenarios/ --update-snapshots
python tests/integration/scenarios/build_report.py
```

This report summarizes the behaviors pinned by the scenarios test suite at `tests/integration/scenarios/`. Each scenario refines a committed eICR/RR pair against a committed configuration JSON and asserts in two layers: validation (well-formedness, CDA R2 XSD, schematron) and snapshot comparison against committed expected files.

See the [scenarios README](./README.md) for the full mechanics. This document is the high-level summary intended for stakeholder review.


## Roll-up issue coverage

Mapping of the issues identified during early testing (Roll-up sheet, May 2026) to current suite coverage. Each scenario reference is a link to its detail section below.

| # | Issue | Status | Scenario(s) |
|---|-------|--------|-------------|
| 1 | Adding code sets removes relevant data | **Direct** | [`covid_baseline`](#covid-baseline), [`covid_plus_unrelated_condition`](#covid-plus-unrelated-condition) |
| 2 | Immunization code matching across OID mismatch | **Direct** | [`covid_with_custom_codes`](#covid-with-custom-codes) |
| 3 | Schematron validation of refined output | **Covered by validation** | all scenarios |
| 4 | Custom codes in nested locations (entryRelationship/value, substanceAdministration) | **Direct** | [`covid_with_custom_codes`](#covid-with-custom-codes), [`covid_with_substance_admin_custom_code`](#covid-with-substance-admin-custom-code) |
| 5 | Procedures retained via unrelated entryRelationship codes | **Direct** | [`covid_baseline`](#covid-baseline), [`covid_with_custom_codes`](#covid-with-custom-codes), [`covid_with_procedure_only_code`](#covid-with-procedure-only-code) |
| 6 | Vital sign panel returns whole panel on single match | **Direct** | [`covid_with_custom_codes`](#covid-with-custom-codes), [`covid_with_multi_vital_sign_codes`](#covid-with-multi-vital-sign-codes) |

### Evidence per issue

**Issue 1 — Adding code sets removes relevant data** (Direct)

`covid_plus_unrelated_condition` adds Fertilizer Poisoning to the COVID configuration — the exact condition Tim cited in the original Roll-up sheet. The snapshot pins the refined output, which should track `covid_baseline` because Fertilizer Poisoning codes don't appear in the fixture. A regression of the bug would manifest as the size reduction percentage climbing above the baseline's: adding unrelated codes would once again be removing COVID-relevant content.

**Issue 2 — Immunization code matching across OID mismatch** (Direct)

`covid_with_custom_codes` adds CVX code 2563008 as a custom code. The fixture tags the same code value with the RxNorm OID. The snapshot pins whether the matcher accepts the cross-OID match.

**Issue 3 — Schematron validation of refined output** (Covered by validation)

Every refined eICR and RR is validated against CDA R2 XSD and schematron on every test run, before snapshot comparison. Errors and fatal severity fail the test; warnings are tolerated. Enforced by the `validate_refined_document` fixture in `tests/integration/scenarios/conftest.py`.

**Issue 4 — Custom codes in nested locations (entryRelationship/value, substanceAdministration)** (Direct)

`covid_with_custom_codes` adds 10628911000119103, which lives in the fixture's Problem List `entryRelationship/value`, covering the nested-observation half. `covid_with_substance_admin_custom_code` adds a custom code targeting a Medications `substanceAdministration` entry; both medication sections gain an entry (Medications Administered 1→2, History of Medication Use 1→2).

**Issue 5 — Procedures retained via unrelated entryRelationship codes** (Direct)

The concern has two halves.

**Negative case (procedures not retained via entryRelationship match):** Nausea (SNOMED 422587007) is in both the COVID and Influenza condition groupers, so it is a configured matching code under `covid_baseline`. The fixture's three procedure entries (Colonic polypectomy, ECMO, Ventilator care) all carry Nausea in their entryRelationship. Despite both conditions being true, `covid_baseline` shows the Procedures section stubbed at 0 entries — the matcher correctly does not retain procedures based on a match found only in entryRelationship. The explicit assertion `test_covid_baseline_does_not_retain_procedures_via_entry_relationship_only_match` in `tests/integration/scenarios/test_explicit_assertions.py` pins this directly with precondition guards that fail diagnostically if the fixture or configuration drifts.

**Positive case (procedures retained when their primary code matches as a custom code):** `covid_with_custom_codes` adds ECMO (SNOMED 233573008) as a custom code; `covid_with_procedure_only_code` adds Ventilator care (SNOMED 385857005). Both snapshots show the matching procedure surviving whole.

**Issue 6 — Vital sign panel returns whole panel on single match** (Direct)

`covid_with_custom_codes` adds Heart Rate (LOINC 8867-4) as a single custom code. Combined with body temperature (LOINC 8310-5) -- a member of the COVID condition grouper, matched from the baseline configuration -- the snapshot pins panel pruning at a two-of-nine cardinality. `covid_with_multi_vital_sign_codes` adds three more vital sign codes (8867-4, 8480-6, 9279-1) and pins the four-of-nine case (those three plus body temperature). The surviving sub-components are the configured-and-present codes, not only the custom additions. If the bug returned, both snapshots would shift to retaining all nine sub-components.


## Capability coverage

Behaviors the suite pins that are product capabilities rather than entries on the Roll-up sheet. Each scenario reference links to its detail section below.

| Capability | Status | Scenario(s) |
|------------|--------|-------------|
| Narrative reconstruction from surviving entries | **Direct** | [`covid_results_reconstruction`](#covid-results-reconstruction), [`problems_reconstruction`](#problems-reconstruction), [`immunizations_reconstruction`](#immunizations-reconstruction), [`medications_reconstruction`](#medications-reconstruction) |

### Evidence per capability

**Narrative reconstruction from surviving entries** (Direct)

`covid_results_reconstruction` configures the Results section (LOINC 30954-2) with `narrative="reconstruct"`. After entry refinement prunes the section to the surviving SARS-CoV-2 result, the engine rebuilds the section `<text>` from those entries rather than retaining the stale source narrative. The snapshot pins the reconstructed shape: a machine-derived `<text>` with a per-organizer context table (panel, date, specimen, target site) and a detail table (test, outcome, interpretation, date) whose rows carry minted xs:IDs the surviving entries are relinked to, plus the "machine-derived, not clinician-attested" provenance marker. `problems_reconstruction` does the same for the Problems section (LOINC 11450-4): a per-concern block carrying concern status + noted date as context and the surviving Problem Observations (type, problem, date) as detail rows. `immunizations_reconstruction` covers the flat case (LOINC 11369-6): a single table, one row per surviving substanceAdministration (vaccine, date, status), where the vaccine name resolves through the displayName/originalText/translation fallback that absorbs CVX/RxNorm sender variance. `medications_reconstruction` is the second flat section (LOINC 29549-3), reusing the same machinery with a different field map (medication, dose, duration, route). The validation layer confirms all four stay CDA R2 XSD- and schematron-valid. Reconstruction is only reachable on the refine path — a retained section never reconstructs — so a regression that stopped rebuilding the narrative would surface here as the section `<text>` reverting to the source narrative or a removal notice.


## Scenarios

Total: 12 scenarios across 1 fixture.

### covid_baseline

**Fixture:** `all_sections_covid_influenza`

**Snapshot files:** [trace JSON](snapshots/all_sections_covid_influenza/covid_baseline/expected_trace.json) · [refined eICR](snapshots/all_sections_covid_influenza/covid_baseline/expected_eICR.xml) · [refined RR](snapshots/all_sections_covid_influenza/covid_baseline/expected_RR.xml)

**Refinement summary**

| Field | Value |
|-------|-------|
| Outcome | `refined` |
| Configuration version | `1` |
| Configuration resolved | `True` |
| eICR size reduction | `56%` |
| Canonical URL | `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64` |
| Augmented eICR id | `dca02d8c-8b32-507c-91da-0ce03d64700b` |
| Augmented RR id | `65fbb67d-d377-5c19-838f-7856dcb7f16a` |
| Original eICR id | `2.16.840.1.113883.9.9.9.9.9` |
| Original RR id | `329b9b59-c1be-4036-8984-42266155b321` |

**Refined eICR — sections retained**

| LOINC | Section | Entries | Disposition |
|-------|---------|---------|-------------|
| `18776-5` | Plan of Treatment | 1 | refined or retained |
| `46240-8` | History of encounters | 1 | refined or retained |
| `10164-2` | HISTORY OF PRESENT ILLNESS | 0 | narrative-only |
| `11348-0` | HISTORY OF PAST ILLNESS | 0 | narrative-only |
| `29549-3` | Medications Administered | 1 | refined or retained |
| `10160-0` | HISTORY OF MEDICATION USE | 1 | refined or retained |
| `42346-7` | ? | 1 | refined or retained |
| `46241-6` | Hospital Admission             Diagnosis | 1 | refined or retained |
| `11535-2` | Hospital Discharge Diagnosis | 1 | refined or retained |
| `10187-3` | REVIEW OF SYSTEMS | 0 | narrative-only |
| `11450-4` | Problem List | 1 | refined or retained |
| `10154-3` | Chief complaint Narrative - Reported | 0 | narrative-only |
| `29299-5` | Reason for visit Narrative | 0 | narrative-only |
| `30954-2` | Relevant diagnostic tests and/or laboratory data | 1 | refined or retained |
| `47519-4` | History of Procedures | 0 | narrative-only |
| `11369-6` | Hx of Immunization | 1 | refined or retained |
| `29762-2` | Social History | 1 | refined or retained |
| `90767-5` | Pregnancy summary Document | 1 | refined or retained |
| `8716-3` | Vital Signs | 1 | refined or retained |
| `83910-0` | Public health Note | 2 | refined or retained |

**Pins Roll-up issues:** #1 (direct), #5 (direct)

### covid_plus_unrelated_condition

**Fixture:** `all_sections_covid_influenza`

**Snapshot files:** [trace JSON](snapshots/all_sections_covid_influenza/covid_plus_unrelated_condition/expected_trace.json) · [refined eICR](snapshots/all_sections_covid_influenza/covid_plus_unrelated_condition/expected_eICR.xml) · [refined RR](snapshots/all_sections_covid_influenza/covid_plus_unrelated_condition/expected_RR.xml)

**Refinement summary**

| Field | Value |
|-------|-------|
| Outcome | `refined` |
| Configuration version | `5` |
| Configuration resolved | `True` |
| eICR size reduction | `56%` |
| Canonical URL | `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64` |
| Augmented eICR id | `dca02d8c-8b32-507c-91da-0ce03d64700b` |
| Augmented RR id | `65fbb67d-d377-5c19-838f-7856dcb7f16a` |
| Original eICR id | `2.16.840.1.113883.9.9.9.9.9` |
| Original RR id | `329b9b59-c1be-4036-8984-42266155b321` |

**Refined eICR — sections retained**

| LOINC | Section | Entries | Disposition |
|-------|---------|---------|-------------|
| `18776-5` | Plan of Treatment | 1 | refined or retained |
| `46240-8` | History of encounters | 1 | refined or retained |
| `10164-2` | HISTORY OF PRESENT ILLNESS | 0 | narrative-only |
| `11348-0` | HISTORY OF PAST ILLNESS | 0 | narrative-only |
| `29549-3` | Medications Administered | 1 | refined or retained |
| `10160-0` | HISTORY OF MEDICATION USE | 1 | refined or retained |
| `42346-7` | ? | 1 | refined or retained |
| `46241-6` | Hospital Admission             Diagnosis | 1 | refined or retained |
| `11535-2` | Hospital Discharge Diagnosis | 1 | refined or retained |
| `10187-3` | REVIEW OF SYSTEMS | 0 | narrative-only |
| `11450-4` | Problem List | 1 | refined or retained |
| `10154-3` | Chief complaint Narrative - Reported | 0 | narrative-only |
| `29299-5` | Reason for visit Narrative | 0 | narrative-only |
| `30954-2` | Relevant diagnostic tests and/or laboratory data | 1 | refined or retained |
| `47519-4` | History of Procedures | 0 | narrative-only |
| `11369-6` | Hx of Immunization | 1 | refined or retained |
| `29762-2` | Social History | 1 | refined or retained |
| `90767-5` | Pregnancy summary Document | 1 | refined or retained |
| `8716-3` | Vital Signs | 1 | refined or retained |
| `83910-0` | Public health Note | 2 | refined or retained |

**Pins Roll-up issues:** #1 (direct)

### covid_results_reconstruction

**Fixture:** `all_sections_covid_influenza`

**Snapshot files:** [trace JSON](snapshots/all_sections_covid_influenza/covid_results_reconstruction/expected_trace.json) · [refined eICR](snapshots/all_sections_covid_influenza/covid_results_reconstruction/expected_eICR.xml) · [refined RR](snapshots/all_sections_covid_influenza/covid_results_reconstruction/expected_RR.xml)

**Refinement summary**

| Field | Value |
|-------|-------|
| Outcome | `refined` |
| Configuration version | `9` |
| Configuration resolved | `True` |
| eICR size reduction | `58%` |
| Canonical URL | `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64` |
| Augmented eICR id | `dca02d8c-8b32-507c-91da-0ce03d64700b` |
| Augmented RR id | `65fbb67d-d377-5c19-838f-7856dcb7f16a` |
| Original eICR id | `2.16.840.1.113883.9.9.9.9.9` |
| Original RR id | `329b9b59-c1be-4036-8984-42266155b321` |

**Refined eICR — sections retained**

| LOINC | Section | Entries | Disposition |
|-------|---------|---------|-------------|
| `18776-5` | Plan of Treatment | 1 | refined or retained |
| `46240-8` | History of encounters | 1 | refined or retained |
| `10164-2` | HISTORY OF PRESENT ILLNESS | 0 | narrative-only |
| `11348-0` | HISTORY OF PAST ILLNESS | 0 | narrative-only |
| `29549-3` | Medications Administered | 1 | refined or retained |
| `10160-0` | HISTORY OF MEDICATION USE | 1 | refined or retained |
| `42346-7` | ? | 1 | refined or retained |
| `46241-6` | Hospital Admission             Diagnosis | 1 | refined or retained |
| `11535-2` | Hospital Discharge Diagnosis | 1 | refined or retained |
| `10187-3` | REVIEW OF SYSTEMS | 0 | narrative-only |
| `11450-4` | Problem List | 1 | refined or retained |
| `10154-3` | Chief complaint Narrative - Reported | 0 | narrative-only |
| `29299-5` | Reason for visit Narrative | 0 | narrative-only |
| `30954-2` | Relevant diagnostic tests and/or laboratory data | 1 | refined or retained |
| `47519-4` | History of Procedures | 0 | narrative-only |
| `11369-6` | Hx of Immunization | 1 | refined or retained |
| `29762-2` | Social History | 1 | refined or retained |
| `90767-5` | Pregnancy summary Document | 1 | refined or retained |
| `8716-3` | Vital Signs | 1 | refined or retained |
| `83910-0` | Public health Note | 2 | refined or retained |

**Pins capabilities:** Narrative reconstruction from surviving entries (direct)

### covid_with_custom_codes

**Fixture:** `all_sections_covid_influenza`

**Snapshot files:** [trace JSON](snapshots/all_sections_covid_influenza/covid_with_custom_codes/expected_trace.json) · [refined eICR](snapshots/all_sections_covid_influenza/covid_with_custom_codes/expected_eICR.xml) · [refined RR](snapshots/all_sections_covid_influenza/covid_with_custom_codes/expected_RR.xml)

**Refinement summary**

| Field | Value |
|-------|-------|
| Outcome | `refined` |
| Configuration version | `3` |
| Configuration resolved | `True` |
| eICR size reduction | `41%` |
| Canonical URL | `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64` |
| Augmented eICR id | `dca02d8c-8b32-507c-91da-0ce03d64700b` |
| Augmented RR id | `65fbb67d-d377-5c19-838f-7856dcb7f16a` |
| Original eICR id | `2.16.840.1.113883.9.9.9.9.9` |
| Original RR id | `329b9b59-c1be-4036-8984-42266155b321` |

**Refined eICR — sections retained**

| LOINC | Section | Entries | Disposition |
|-------|---------|---------|-------------|
| `18776-5` | Plan of Treatment | 2 | refined or retained |
| `46240-8` | History of encounters | 1 | refined or retained |
| `10164-2` | HISTORY OF PRESENT ILLNESS | 0 | narrative-only |
| `11348-0` | HISTORY OF PAST ILLNESS | 0 | narrative-only |
| `29549-3` | Medications Administered | 1 | refined or retained |
| `10160-0` | HISTORY OF MEDICATION USE | 1 | refined or retained |
| `42346-7` | ? | 1 | refined or retained |
| `46241-6` | Hospital Admission             Diagnosis | 1 | refined or retained |
| `11535-2` | Hospital Discharge Diagnosis | 1 | refined or retained |
| `10187-3` | REVIEW OF SYSTEMS | 0 | narrative-only |
| `11450-4` | Problem List | 1 | refined or retained |
| `10154-3` | Chief complaint Narrative - Reported | 0 | narrative-only |
| `29299-5` | Reason for visit Narrative | 0 | narrative-only |
| `30954-2` | Relevant diagnostic tests and/or laboratory data | 1 | refined or retained |
| `47519-4` | History of Procedures | 1 | refined or retained |
| `11369-6` | Hx of Immunization | 2 | refined or retained |
| `29762-2` | Social History | 1 | refined or retained |
| `90767-5` | Pregnancy summary Document | 1 | refined or retained |
| `8716-3` | Vital Signs | 1 | refined or retained |
| `83910-0` | Public health Note | 2 | refined or retained |

**Pins Roll-up issues:** #2 (direct), #4 (direct), #5 (direct), #6 (direct)

### covid_with_multi_vital_sign_codes

**Fixture:** `all_sections_covid_influenza`

**Snapshot files:** [trace JSON](snapshots/all_sections_covid_influenza/covid_with_multi_vital_sign_codes/expected_trace.json) · [refined eICR](snapshots/all_sections_covid_influenza/covid_with_multi_vital_sign_codes/expected_eICR.xml) · [refined RR](snapshots/all_sections_covid_influenza/covid_with_multi_vital_sign_codes/expected_RR.xml)

**Refinement summary**

| Field | Value |
|-------|-------|
| Outcome | `refined` |
| Configuration version | `7` |
| Configuration resolved | `True` |
| eICR size reduction | `53%` |
| Canonical URL | `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64` |
| Augmented eICR id | `dca02d8c-8b32-507c-91da-0ce03d64700b` |
| Augmented RR id | `65fbb67d-d377-5c19-838f-7856dcb7f16a` |
| Original eICR id | `2.16.840.1.113883.9.9.9.9.9` |
| Original RR id | `329b9b59-c1be-4036-8984-42266155b321` |

**Refined eICR — sections retained**

| LOINC | Section | Entries | Disposition |
|-------|---------|---------|-------------|
| `18776-5` | Plan of Treatment | 1 | refined or retained |
| `46240-8` | History of encounters | 1 | refined or retained |
| `10164-2` | HISTORY OF PRESENT ILLNESS | 0 | narrative-only |
| `11348-0` | HISTORY OF PAST ILLNESS | 0 | narrative-only |
| `29549-3` | Medications Administered | 1 | refined or retained |
| `10160-0` | HISTORY OF MEDICATION USE | 1 | refined or retained |
| `42346-7` | ? | 1 | refined or retained |
| `46241-6` | Hospital Admission             Diagnosis | 1 | refined or retained |
| `11535-2` | Hospital Discharge Diagnosis | 1 | refined or retained |
| `10187-3` | REVIEW OF SYSTEMS | 0 | narrative-only |
| `11450-4` | Problem List | 1 | refined or retained |
| `10154-3` | Chief complaint Narrative - Reported | 0 | narrative-only |
| `29299-5` | Reason for visit Narrative | 0 | narrative-only |
| `30954-2` | Relevant diagnostic tests and/or laboratory data | 1 | refined or retained |
| `47519-4` | History of Procedures | 0 | narrative-only |
| `11369-6` | Hx of Immunization | 1 | refined or retained |
| `29762-2` | Social History | 1 | refined or retained |
| `90767-5` | Pregnancy summary Document | 1 | refined or retained |
| `8716-3` | Vital Signs | 1 | refined or retained |
| `83910-0` | Public health Note | 2 | refined or retained |

**Pins Roll-up issues:** #6 (direct)

### covid_with_procedure_only_code

**Fixture:** `all_sections_covid_influenza`

**Snapshot files:** [trace JSON](snapshots/all_sections_covid_influenza/covid_with_procedure_only_code/expected_trace.json) · [refined eICR](snapshots/all_sections_covid_influenza/covid_with_procedure_only_code/expected_eICR.xml) · [refined RR](snapshots/all_sections_covid_influenza/covid_with_procedure_only_code/expected_RR.xml)

**Refinement summary**

| Field | Value |
|-------|-------|
| Outcome | `refined` |
| Configuration version | `8` |
| Configuration resolved | `True` |
| eICR size reduction | `52%` |
| Canonical URL | `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64` |
| Augmented eICR id | `dca02d8c-8b32-507c-91da-0ce03d64700b` |
| Augmented RR id | `65fbb67d-d377-5c19-838f-7856dcb7f16a` |
| Original eICR id | `2.16.840.1.113883.9.9.9.9.9` |
| Original RR id | `329b9b59-c1be-4036-8984-42266155b321` |

**Refined eICR — sections retained**

| LOINC | Section | Entries | Disposition |
|-------|---------|---------|-------------|
| `18776-5` | Plan of Treatment | 2 | refined or retained |
| `46240-8` | History of encounters | 1 | refined or retained |
| `10164-2` | HISTORY OF PRESENT ILLNESS | 0 | narrative-only |
| `11348-0` | HISTORY OF PAST ILLNESS | 0 | narrative-only |
| `29549-3` | Medications Administered | 1 | refined or retained |
| `10160-0` | HISTORY OF MEDICATION USE | 1 | refined or retained |
| `42346-7` | ? | 1 | refined or retained |
| `46241-6` | Hospital Admission             Diagnosis | 1 | refined or retained |
| `11535-2` | Hospital Discharge Diagnosis | 1 | refined or retained |
| `10187-3` | REVIEW OF SYSTEMS | 0 | narrative-only |
| `11450-4` | Problem List | 1 | refined or retained |
| `10154-3` | Chief complaint Narrative - Reported | 0 | narrative-only |
| `29299-5` | Reason for visit Narrative | 0 | narrative-only |
| `30954-2` | Relevant diagnostic tests and/or laboratory data | 1 | refined or retained |
| `47519-4` | History of Procedures | 1 | refined or retained |
| `11369-6` | Hx of Immunization | 1 | refined or retained |
| `29762-2` | Social History | 1 | refined or retained |
| `90767-5` | Pregnancy summary Document | 1 | refined or retained |
| `8716-3` | Vital Signs | 1 | refined or retained |
| `83910-0` | Public health Note | 2 | refined or retained |

**Pins Roll-up issues:** #5 (direct)

### covid_with_section_overrides

**Fixture:** `all_sections_covid_influenza`

**Snapshot files:** [trace JSON](snapshots/all_sections_covid_influenza/covid_with_section_overrides/expected_trace.json) · [refined eICR](snapshots/all_sections_covid_influenza/covid_with_section_overrides/expected_eICR.xml) · [refined RR](snapshots/all_sections_covid_influenza/covid_with_section_overrides/expected_RR.xml)

**Refinement summary**

| Field | Value |
|-------|-------|
| Outcome | `refined` |
| Configuration version | `4` |
| Configuration resolved | `True` |
| eICR size reduction | `47%` |
| Canonical URL | `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64` |
| Augmented eICR id | `dca02d8c-8b32-507c-91da-0ce03d64700b` |
| Augmented RR id | `65fbb67d-d377-5c19-838f-7856dcb7f16a` |
| Original eICR id | `2.16.840.1.113883.9.9.9.9.9` |
| Original RR id | `329b9b59-c1be-4036-8984-42266155b321` |

**Refined eICR — sections retained**

| LOINC | Section | Entries | Disposition |
|-------|---------|---------|-------------|
| `18776-5` | Plan of Treatment | 1 | refined or retained |
| `46240-8` | History of encounters | 1 | refined or retained |
| `10164-2` | HISTORY OF PRESENT ILLNESS | 0 | removed by configuration |
| `11348-0` | HISTORY OF PAST ILLNESS | 0 | narrative-only |
| `29549-3` | Medications Administered | 1 | refined or retained |
| `10160-0` | HISTORY OF MEDICATION USE | 1 | refined or retained |
| `42346-7` | ? | 1 | refined or retained |
| `46241-6` | Hospital Admission             Diagnosis | 1 | refined or retained |
| `11535-2` | Hospital Discharge Diagnosis | 1 | refined or retained |
| `10187-3` | REVIEW OF SYSTEMS | 0 | narrative-only |
| `11450-4` | Problem List | 1 | refined or retained |
| `10154-3` | Chief complaint Narrative - Reported | 0 | removed by configuration |
| `29299-5` | Reason for visit Narrative | 0 | removed by configuration |
| `30954-2` | Relevant diagnostic tests and/or laboratory data | 1 | refined; narrative removed |
| `47519-4` | History of Procedures | 0 | narrative-only |
| `11369-6` | Hx of Immunization | 1 | refined or retained |
| `29762-2` | Social History | 22 | refined or retained |
| `90767-5` | Pregnancy summary Document | 1 | refined or retained |
| `8716-3` | Vital Signs | 1 | refined or retained |
| `83910-0` | Public health Note | 2 | refined or retained |

### covid_with_substance_admin_custom_code

**Fixture:** `all_sections_covid_influenza`

**Snapshot files:** [trace JSON](snapshots/all_sections_covid_influenza/covid_with_substance_admin_custom_code/expected_trace.json) · [refined eICR](snapshots/all_sections_covid_influenza/covid_with_substance_admin_custom_code/expected_eICR.xml) · [refined RR](snapshots/all_sections_covid_influenza/covid_with_substance_admin_custom_code/expected_RR.xml)

**Refinement summary**

| Field | Value |
|-------|-------|
| Outcome | `refined` |
| Configuration version | `6` |
| Configuration resolved | `True` |
| eICR size reduction | `50%` |
| Canonical URL | `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64` |
| Augmented eICR id | `dca02d8c-8b32-507c-91da-0ce03d64700b` |
| Augmented RR id | `65fbb67d-d377-5c19-838f-7856dcb7f16a` |
| Original eICR id | `2.16.840.1.113883.9.9.9.9.9` |
| Original RR id | `329b9b59-c1be-4036-8984-42266155b321` |

**Refined eICR — sections retained**

| LOINC | Section | Entries | Disposition |
|-------|---------|---------|-------------|
| `18776-5` | Plan of Treatment | 1 | refined or retained |
| `46240-8` | History of encounters | 1 | refined or retained |
| `10164-2` | HISTORY OF PRESENT ILLNESS | 0 | narrative-only |
| `11348-0` | HISTORY OF PAST ILLNESS | 0 | narrative-only |
| `29549-3` | Medications Administered | 2 | refined or retained |
| `10160-0` | HISTORY OF MEDICATION USE | 2 | refined or retained |
| `42346-7` | ? | 2 | refined or retained |
| `46241-6` | Hospital Admission             Diagnosis | 1 | refined or retained |
| `11535-2` | Hospital Discharge Diagnosis | 1 | refined or retained |
| `10187-3` | REVIEW OF SYSTEMS | 0 | narrative-only |
| `11450-4` | Problem List | 1 | refined or retained |
| `10154-3` | Chief complaint Narrative - Reported | 0 | narrative-only |
| `29299-5` | Reason for visit Narrative | 0 | narrative-only |
| `30954-2` | Relevant diagnostic tests and/or laboratory data | 1 | refined or retained |
| `47519-4` | History of Procedures | 0 | narrative-only |
| `11369-6` | Hx of Immunization | 1 | refined or retained |
| `29762-2` | Social History | 1 | refined or retained |
| `90767-5` | Pregnancy summary Document | 1 | refined or retained |
| `8716-3` | Vital Signs | 1 | refined or retained |
| `83910-0` | Public health Note | 2 | refined or retained |

**Pins Roll-up issues:** #4 (direct)

### immunizations_reconstruction

**Fixture:** `all_sections_covid_influenza`

**Snapshot files:** [trace JSON](snapshots/all_sections_covid_influenza/immunizations_reconstruction/expected_trace.json) · [refined eICR](snapshots/all_sections_covid_influenza/immunizations_reconstruction/expected_eICR.xml) · [refined RR](snapshots/all_sections_covid_influenza/immunizations_reconstruction/expected_RR.xml)

**Refinement summary**

| Field | Value |
|-------|-------|
| Outcome | `refined` |
| Configuration version | `11` |
| Configuration resolved | `True` |
| eICR size reduction | `50%` |
| Canonical URL | `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64` |
| Augmented eICR id | `dca02d8c-8b32-507c-91da-0ce03d64700b` |
| Augmented RR id | `65fbb67d-d377-5c19-838f-7856dcb7f16a` |
| Original eICR id | `2.16.840.1.113883.9.9.9.9.9` |
| Original RR id | `329b9b59-c1be-4036-8984-42266155b321` |

**Refined eICR — sections retained**

| LOINC | Section | Entries | Disposition |
|-------|---------|---------|-------------|
| `18776-5` | Plan of Treatment | 1 | refined or retained |
| `46240-8` | History of encounters | 1 | refined or retained |
| `10164-2` | HISTORY OF PRESENT ILLNESS | 0 | narrative-only |
| `11348-0` | HISTORY OF PAST ILLNESS | 0 | narrative-only |
| `29549-3` | Medications Administered | 1 | refined or retained |
| `10160-0` | HISTORY OF MEDICATION USE | 1 | refined or retained |
| `42346-7` | ? | 1 | refined or retained |
| `46241-6` | Hospital Admission             Diagnosis | 1 | refined or retained |
| `11535-2` | Hospital Discharge Diagnosis | 1 | refined or retained |
| `10187-3` | REVIEW OF SYSTEMS | 0 | narrative-only |
| `11450-4` | Problem List | 1 | refined or retained |
| `10154-3` | Chief complaint Narrative - Reported | 0 | narrative-only |
| `29299-5` | Reason for visit Narrative | 0 | narrative-only |
| `30954-2` | Relevant diagnostic tests and/or laboratory data | 1 | refined or retained |
| `47519-4` | History of Procedures | 0 | narrative-only |
| `11369-6` | Hx of Immunization | 2 | refined or retained |
| `29762-2` | Social History | 1 | refined or retained |
| `90767-5` | Pregnancy summary Document | 1 | refined or retained |
| `8716-3` | Vital Signs | 1 | refined or retained |
| `83910-0` | Public health Note | 2 | refined or retained |

**Pins capabilities:** Narrative reconstruction from surviving entries (direct)

### influenza_baseline

**Fixture:** `all_sections_covid_influenza`

**Snapshot files:** [trace JSON](snapshots/all_sections_covid_influenza/influenza_baseline/expected_trace.json) · [refined eICR](snapshots/all_sections_covid_influenza/influenza_baseline/expected_eICR.xml) · [refined RR](snapshots/all_sections_covid_influenza/influenza_baseline/expected_RR.xml)

**Refinement summary**

| Field | Value |
|-------|-------|
| Outcome | `refined` |
| Configuration version | `2` |
| Configuration resolved | `True` |
| eICR size reduction | `53%` |
| Canonical URL | `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/38475891-387a-4fa2-bbe9-1dc97ce415d1` |
| Augmented eICR id | `48c0d1c3-88a9-5604-8258-95023edd319a` |
| Augmented RR id | `545424f5-c84a-5e39-bc4a-436e79344df2` |
| Original eICR id | `2.16.840.1.113883.9.9.9.9.9` |
| Original RR id | `329b9b59-c1be-4036-8984-42266155b321` |

**Refined eICR — sections retained**

| LOINC | Section | Entries | Disposition |
|-------|---------|---------|-------------|
| `18776-5` | Plan of Treatment | 1 | refined or retained |
| `46240-8` | History of encounters | 1 | refined or retained |
| `10164-2` | HISTORY OF PRESENT ILLNESS | 0 | narrative-only |
| `11348-0` | HISTORY OF PAST ILLNESS | 0 | narrative-only |
| `29549-3` | Medications Administered | 1 | refined or retained |
| `10160-0` | HISTORY OF MEDICATION USE | 1 | refined or retained |
| `42346-7` | ? | 1 | refined or retained |
| `46241-6` | Hospital Admission             Diagnosis | 1 | refined or retained |
| `11535-2` | Hospital Discharge Diagnosis | 1 | refined or retained |
| `10187-3` | REVIEW OF SYSTEMS | 0 | narrative-only |
| `11450-4` | Problem List | 1 | refined or retained |
| `10154-3` | Chief complaint Narrative - Reported | 0 | narrative-only |
| `29299-5` | Reason for visit Narrative | 0 | narrative-only |
| `30954-2` | Relevant diagnostic tests and/or laboratory data | 1 | refined or retained |
| `47519-4` | History of Procedures | 0 | narrative-only |
| `11369-6` | Hx of Immunization | 1 | refined or retained |
| `29762-2` | Social History | 1 | refined or retained |
| `90767-5` | Pregnancy summary Document | 1 | refined or retained |
| `8716-3` | Vital Signs | 1 | refined or retained |
| `83910-0` | Public health Note | 2 | refined or retained |

### medications_reconstruction

**Fixture:** `all_sections_covid_influenza`

**Snapshot files:** [trace JSON](snapshots/all_sections_covid_influenza/medications_reconstruction/expected_trace.json) · [refined eICR](snapshots/all_sections_covid_influenza/medications_reconstruction/expected_eICR.xml) · [refined RR](snapshots/all_sections_covid_influenza/medications_reconstruction/expected_RR.xml)

**Refinement summary**

| Field | Value |
|-------|-------|
| Outcome | `refined` |
| Configuration version | `12` |
| Configuration resolved | `True` |
| eICR size reduction | `50%` |
| Canonical URL | `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64` |
| Augmented eICR id | `dca02d8c-8b32-507c-91da-0ce03d64700b` |
| Augmented RR id | `65fbb67d-d377-5c19-838f-7856dcb7f16a` |
| Original eICR id | `2.16.840.1.113883.9.9.9.9.9` |
| Original RR id | `329b9b59-c1be-4036-8984-42266155b321` |

**Refined eICR — sections retained**

| LOINC | Section | Entries | Disposition |
|-------|---------|---------|-------------|
| `18776-5` | Plan of Treatment | 1 | refined or retained |
| `46240-8` | History of encounters | 1 | refined or retained |
| `10164-2` | HISTORY OF PRESENT ILLNESS | 0 | narrative-only |
| `11348-0` | HISTORY OF PAST ILLNESS | 0 | narrative-only |
| `29549-3` | Medications Administered | 2 | refined or retained |
| `10160-0` | HISTORY OF MEDICATION USE | 2 | refined or retained |
| `42346-7` | ? | 2 | refined or retained |
| `46241-6` | Hospital Admission             Diagnosis | 1 | refined or retained |
| `11535-2` | Hospital Discharge Diagnosis | 1 | refined or retained |
| `10187-3` | REVIEW OF SYSTEMS | 0 | narrative-only |
| `11450-4` | Problem List | 1 | refined or retained |
| `10154-3` | Chief complaint Narrative - Reported | 0 | narrative-only |
| `29299-5` | Reason for visit Narrative | 0 | narrative-only |
| `30954-2` | Relevant diagnostic tests and/or laboratory data | 1 | refined or retained |
| `47519-4` | History of Procedures | 0 | narrative-only |
| `11369-6` | Hx of Immunization | 1 | refined or retained |
| `29762-2` | Social History | 1 | refined or retained |
| `90767-5` | Pregnancy summary Document | 1 | refined or retained |
| `8716-3` | Vital Signs | 1 | refined or retained |
| `83910-0` | Public health Note | 2 | refined or retained |

**Pins capabilities:** Narrative reconstruction from surviving entries (direct)

### problems_reconstruction

**Fixture:** `all_sections_covid_influenza`

**Snapshot files:** [trace JSON](snapshots/all_sections_covid_influenza/problems_reconstruction/expected_trace.json) · [refined eICR](snapshots/all_sections_covid_influenza/problems_reconstruction/expected_eICR.xml) · [refined RR](snapshots/all_sections_covid_influenza/problems_reconstruction/expected_RR.xml)

**Refinement summary**

| Field | Value |
|-------|-------|
| Outcome | `refined` |
| Configuration version | `10` |
| Configuration resolved | `True` |
| eICR size reduction | `56%` |
| Canonical URL | `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64` |
| Augmented eICR id | `dca02d8c-8b32-507c-91da-0ce03d64700b` |
| Augmented RR id | `65fbb67d-d377-5c19-838f-7856dcb7f16a` |
| Original eICR id | `2.16.840.1.113883.9.9.9.9.9` |
| Original RR id | `329b9b59-c1be-4036-8984-42266155b321` |

**Refined eICR — sections retained**

| LOINC | Section | Entries | Disposition |
|-------|---------|---------|-------------|
| `18776-5` | Plan of Treatment | 1 | refined or retained |
| `46240-8` | History of encounters | 1 | refined or retained |
| `10164-2` | HISTORY OF PRESENT ILLNESS | 0 | narrative-only |
| `11348-0` | HISTORY OF PAST ILLNESS | 0 | narrative-only |
| `29549-3` | Medications Administered | 1 | refined or retained |
| `10160-0` | HISTORY OF MEDICATION USE | 1 | refined or retained |
| `42346-7` | ? | 1 | refined or retained |
| `46241-6` | Hospital Admission             Diagnosis | 1 | refined or retained |
| `11535-2` | Hospital Discharge Diagnosis | 1 | refined or retained |
| `10187-3` | REVIEW OF SYSTEMS | 0 | narrative-only |
| `11450-4` | Problem List | 1 | refined or retained |
| `10154-3` | Chief complaint Narrative - Reported | 0 | narrative-only |
| `29299-5` | Reason for visit Narrative | 0 | narrative-only |
| `30954-2` | Relevant diagnostic tests and/or laboratory data | 1 | refined or retained |
| `47519-4` | History of Procedures | 0 | narrative-only |
| `11369-6` | Hx of Immunization | 1 | refined or retained |
| `29762-2` | Social History | 1 | refined or retained |
| `90767-5` | Pregnancy summary Document | 1 | refined or retained |
| `8716-3` | Vital Signs | 1 | refined or retained |
| `83910-0` | Public health Note | 2 | refined or retained |

**Pins capabilities:** Narrative reconstruction from surviving entries (direct)


## Appendix — running the suite

```
pytest tests/integration/scenarios/                                  # run all scenarios + smoke tests
pytest tests/integration/scenarios/test_<fixture>.py -k <scenario>   # one scenario
pytest tests/integration/scenarios/ --update-snapshots               # regenerate after intentional changes
python tests/integration/scenarios/build_report.py        # regenerate this report
```

See [`tests/integration/scenarios/README.md`](./README.md) for adding fixtures, configurations, and scenarios.
