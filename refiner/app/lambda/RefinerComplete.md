# RefinerComplete JSON Schema

The `RefinerComplete` file is written to S3 after the refiner finishes
processing an eCR. It can take one of two mutually exclusive shapes: a
**Success** signal or an **Error** signal.

## Success Signal

A success signal is sent when the refiner completes processing (even if some
conditions were skipped due to missing configurations).

### Fields

- **`RefinerMetadata`**: A nested object that records which jurisdiction/condition combinations from the Reportability Response (RR) were processed. The outer keys are **jurisdiction codes** (e.g. `"CA"`, `"NY"`), and each maps to an object whose keys are **condition codes** (SNOMED codes like `"27836007"`). The boolean value indicates whether refinement was performed:
  - **`true`** — an active configuration was found and the eICR/RR were
    refined for this combination.
  - **`false`** — no active configuration existed, so refinement was skipped.
- **`RefinerOutputFiles`**: An array of S3 keys pointing to the refined output files. Each successfully refined jurisdiction/condition combination produces two entries:
  - `RefinerOutput/<persistence_id>/<jurisdiction_code>/<condition_grouper_names_no_spaces>/refined_eICR.xml`
  - `RefinerOutput/<persistence_id>/<jurisdiction_code>/<condition_grouper_names_no_spaces>/refined_RR.xml`
- **`RefinerSkip`**: Set to `false`.

### Example

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
    "RefinerOutput/<persistence_id>/CA/Pertussis/refined_RR.xml",
    "RefinerOutput/<persistence_id>/CA/Pertussis/refined_eICR.xml",
    "RefinerOutput/<persistence_id>/NY/COVID19/refined_eICR.xml",
    "RefinerOutput/<persistence_id>/NY/COVID19/refined_RR.xml"
  ]
}
```

## Error Signal

An error signal is sent when the refiner encounters a fatal execution error that
prevents the refinement process from completing.

### Fields

- **`RefinerSkip`**: Set to `true`.
- **`Error`**: A string containing the diagnostic error message.

**Note:** When an Error signal is sent, `RefinerMetadata` and
`RefinerOutputFiles` are omitted.

### Example

```json
{
  "RefinerSkip": true,
  "Error": "Fatal error: setId missing from document"
}
```
