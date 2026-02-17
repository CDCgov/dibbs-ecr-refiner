# RefinerComplete JSON Schema

The `RefinerComplete` file is written to S3 after the refiner finishes processing an eCR. It contains three fields:

## `RefinerMetadata`

A nested object that records which jurisdiction/condition combinations from the Reportability Response (RR) were processed. The outer keys are **jurisdiction codes** (e.g. `"CA"`, `"NY"`), and each maps to an object whose keys are **condition codes** (SNOMED codes like `"27836007"`). The boolean value indicates whether refinement was performed:

- **`true`** — an active configuration was found and the eICR/RR were refined for this combination.
- **`false`** — no active configuration existed, so refinement was skipped.

## `RefinerOutputFiles`

An array of S3 keys pointing to the refined output files. Each successfully refined jurisdiction/condition combination produces two entries:

- `RefinerOutput/<persistence_id>/<jurisdiction_code>/<condition_code>/refined_eICR.xml`
- `RefinerOutput/<persistence_id>/<jurisdiction_code>/<condition_code>/refined_RR.xml`

Combinations marked `false` in `RefinerMetadata` will have no corresponding entries here.

## `RefinerSkip`

A boolean indicating whether the refiner skipped processing entirely. When `false`, the refiner ran its normal processing loop (though individual jurisdiction/condition pairs may still have been skipped, as indicated by `RefinerMetadata`).

## Example

```json
{
  "RefinerMetadata": {
    "CA": {
      "27836007": true,
      "840539006": false
    },
    "NY": {
      "27836007": false,
      "840539006": true
    }
  },
  "RefinerSkip": false,
  "RefinerOutputFiles": [
    "RefinerOutput/<persistence_id>/CA/27836007/refined_eICR.xml",
    "RefinerOutput/<persistence_id>/CA/27836007/refined_RR.xml",
    "RefinerOutput/<persistence_id>/NY/840539006/refined_eICR.xml",
    "RefinerOutput/<persistence_id>/NY/840539006/refined_RR.xml"
  ]
}
```
