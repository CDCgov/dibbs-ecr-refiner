# 6. S3 Adjustments for Display Name

Date: 2026-03-07

## Status

Accepted

## Context and Problem Statement

Following the implementation of ADR 0006 and ADR 0007, the team realized the approach to configuration storage needed some adjusting to support the enriched data needs of the display name processing. This document outlines the relevant changes to S3 serialized configurations and the overall lambda architecture.

## Decision Drivers

Lambda supports refining in the same manner as application functionality.

## Decision Outcome

We have decided to make one modification to the S3 configuration storage and one overall architectural change in order to support these needs:

1. Add a serialized version of `CodeSystemSets`, which are a mapping between code system and `Coding` display name, code value, and system OID values to the serialized S3 configuration
2. Introduce a pipeline service that unifies the refinement process between application and lambda implementations to reduce the future likelihood of drift between the two methods
3. Modify Lambda and application refinement pipelines to invoke the changed organization.

### S3 file storage

The files decribed in [the original file format write-up](./0004_2026-01-14_file-format-spike.md) and [the condition grouper architecture write-up](./0006_2026-03-11_cg-level-lambda.md) still apply, however, they now store an extra `code_system_sets` block. These are consumed in the enriched portions of the refinement process. An example value for COVID is included below, which will be appended to the end of the file activation accordingly. Utility methods to support these operations were added to the classes themselves to assist with tasks like re/de-serialization and processing.

It's worth mentioning that these values are a duplicate version of the codes included under `codes`. This decision was done to speed up implementation in the short term, but may be changed if issues around data drift, storage performance, etc. arise in the future.

```json
  "code_system_sets": {
    "snomed": [
      {
        "code": "299899002",
        "display": "Problem of sense of smell (finding)",
        "system": "2.16.840.1.113883.6.96"
      },
      {
        "code": "3368006",
        "display": "Dull chest pain (finding)",
        "system": "2.16.840.1.113883.6.96"
      },
    // ... other codes ommited for brevity
    ],
    "loinc": [
      {
        "code": "95941-1",
        "display": "Influenza virus A and B and SARS-CoV-2 (COVID-19) and Respiratory syncytial virus RNA panel - Respiratory specimen by NAA with probe detection",
        "system": "2.16.840.1.113883.6.1"
      },
      {
        "code": "100157-7",
        "display": "SARS-CoV-2 (COVID-19) lineage [Type] in Specimen by Sequencing",
        "system": "2.16.840.1.113883.6.1"
      },
          // ... other codes ommited for brevity

    ],
      "rxnorm": [
      {
        "code": "1007256",
        "display": "clioquinol / dexamethasone",
        "system": "2.16.840.1.113883.6.88"
      },
      {
        "code": "369461",
        "display": "dexamethasone Oral Tablet [Decadron]",
        "system": "2.16.840.1.113883.6.88"
      },
          // ... other codes ommited for brevity
      ],
    "cvx": [],
    "other": []
  }
```

### Introduction of a pipeline service

The motivation incident for this change also revealed that there were duplicate implementations of the refinement pipeline across the application and Lambda implementations. As a result, these processes were unified into one shared pipeline service that are involed across the reportability discovery and condition-level refinement processes, which are the parts of the refinement process that are agnostic to the format of the configuration (S3 serialized vs database store). A unified `RefinementTrace` class was also introduced to help track the various steps of refinement in logging and debugging processes. These refactors were done to help ensure similar levels of misalignment don't surprise the team in the future.

Finalized refined outputs are stored in their raw string format for appropriate post-refinement packaging in different contexts. Refer to previous ADR's to learn more.

Implementation of this new service can be found in the relevant Lambda and application refinement files.
