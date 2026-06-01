# Reproduce `covid_with_section_overrides` configuration

This configuration starts from the COVID baseline (no custom codes) and overrides per-section processing to exercise the suite's coverage of the section action and narrative flag dimensions that aren't covered by default behavior elsewhere.

Unlike the code-upload scenarios in this directory, the values below can't be uploaded as a CSV; they're set per-section in the app's UI.

## Reproduction

1. Start from the COVID baseline configuration.
2. In the app's section processing editor, set the following overrides:

| Section                    | LOINC   | Action   | Narrative | Why this combination                                                                                                                                            |
| -------------------------- | ------- | -------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Vital Signs                | 8716-3  | `remove` | n/a       | `remove` on an entry-based section. The fixture's Vital Signs panel has matchable codes; this confirms `remove` drops the section regardless of matches.        |
| Procedures                 | 47519-4 | `refine` | `false`   | Narrative-removal under `refine`. The retained entries should appear without the original narrative block.                                                      |
| Chief Complaint            | 10154-3 | `remove` | n/a       | `remove` on a narrative-only section. Exercises a different code path than `remove` on entry-based sections — there are no entries to drop, only the narrative. |
| History of Present Illness | 10164-2 | `remove` | n/a       | Same as above; verifies removal works consistently across multiple narrative-only sections.                                                                     |
| Reason for Visit           | 29299-5 | `remove` | n/a       | Same.                                                                                                                                                           |
| Review of Systems          | 10187-3 | `remove` | n/a       | Same.                                                                                                                                                           |

1. Activate the configuration.
2. Pull the activation JSON from localstack per the standard authoring workflow:

```bash
docker compose exec localstack awslocal s3 cp \
  s3://local-config-bucket/configurations/SDDH/07221093-b8a1-4b1d-8678-259277bfba64/<version>/active.json \
  - > covid_with_section_overrides.json
```

1. Move the JSON to `tests/fixtures/all_sections_COVID_INFLUENZA/configurations/covid_with_section_overrides.json`.

## What this scenario pins

- **Section removal across section types.** `remove` works on both entry-based sections (Vital Signs, with matchable content) and narrative-only sections (Chief Complaint et al, with free-text content). Both paths are pinned by the snapshot.
- **Narrative removal under `refine`.** Procedures retains its entries but drops the original narrative block.
- **The three section dispositions in the refined output** (`removed by configuration`, `refined; narrative removed`, default refinement) are all present in a single snapshot for direct comparison.
