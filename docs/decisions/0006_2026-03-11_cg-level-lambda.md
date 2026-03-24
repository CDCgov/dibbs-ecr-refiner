# 6. Condition grouper-level Lambda outputs

Date: 2026-03-11

## Status

Accepted

## Context and Problem Statement

The Lambda operates at the reporting specification grouper level but the desire is for it to operate at the condition grouper level instead. This document will outline how S3 file writing during activation has changed and the impact of that on the Lambda.

## Decision Drivers

Outputs from the Lambda at the condition grouper level is the desire from partners and prospective consumers.

## Decision Outcome

We have decided to make three major modifications to what exists today in order to support this feature:

1. Write S3 files to a CG level key instead of RSG level keys
2. Introduce an RSG -> CG mapping file
3. Modify Lambda to make use of the new file locations, the mapping file, and write CG level outputs

### S3 file storage

The files decribed in [the original activation process write-up](./0003_2026-01-06_activation-s3-file-structure.md) still apply, however, their locations have changed.

Upon configuration activation, the files are now written to the following locations:

- `/configurations/{jurisdiction}/{condition-grouper-uuid}/current.json`
- `/configurations/{jurisdiction}/{condition-grouper-uuid}/{config-version}/metadata.json`
- `/configurations/{jurisdiction}/{condition-grouper-uuid}/{config-version}/active.json`

The `condition-grouper-uuid` is the UUID that uniquely identifies a condition grouper, which can be found at the end of its canonical URL. For example, COVID-19's condition grouper UUID is `07221093-b8a1-4b1d-8678-259277bfba64` since its canonical URL is `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64`.

When a user in the SDDH jurisdiction activates a COVID-19 configuration for the first time (version 1), the following files are produced at these keys in S3:

- `/configurations/SDDH/07221093-b8a1-4b1d-8678-259277bfba64/current.json`
- `/configurations/SDDH/07221093-b8a1-4b1d-8678-259277bfba64/1/metadata.json`
- `/configurations/SDDH/07221093-b8a1-4b1d-8678-259277bfba64/1/active.json`

### Reporting specification grouper to condition grouper mapping file

Since the Lambda will be pulling RSG codes out of the RR, it needs to be able to somehow map an RSG SNOMED code to a condition grouper. For example, if an RR contained the RSG code `186747009` and/or `840539006`, these codes now need to map to a COVID-19 CG level configuration.

The way we do this mapping is by introducing a new file at the jurisdiction level:

- `/configurations/{jurisdiction}/rsg_cg_mapping.json`

For every jurisdiction with activated configurations this file will contain the data required for the Lambda to determine the S3 keys described in the section above.

For example, if the SDDH jurisdiction has a configuration active for COVID-19 and the Lambda is processing an RR with the COVID-19 RSG `186747009`, the following steps will occur:

1. Lambda processes the RR and finds COVID-19 RSG `186747009`
2. Lambda attempts to pull in the map at `/configurations/SDDH/rsg_cg_mapping.json`
3. Lambda reads the map data and determines that `186747009` maps to the COVID-19 canonical URL `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64`
4. With this information, Lambda determines that the files required for processing COVID-19 will be found at the following keys
   - `/configurations/SDDH/07221093-b8a1-4b1d-8678-259277bfba64/current.json`
   - `/configurations/SDDH/07221093-b8a1-4b1d-8678-259277bfba64/1/metadata.json`
   - `/configurations/SDDH/07221093-b8a1-4b1d-8678-259277bfba64/1/active.json`
5. Lambda processes the eICR/RR pair and produces CG level outputs

#### Producing CG level outputs

Continuing with the COVID-19 example, it's worth noting that COVID-19 has more than a single RSG. It has both `186747009` and `840539006`. This means that when a COVID-19 configuration has been activated, two entries (one for each RSG) will be added to `rsg_cg_mapping.json` and both will point to COVID-19.

In the RSG level implementation, this would result in duplicate refined documents for COVID-19. However, in the CG level implementation, if COVID-19 has already been processed once during this run of the Refiner, any additional COVID-19 RSG codes will be skipped.

Regardless of how many RSG codes are found in an RR that map to the same condition grouper, only one copy of a refined output will be produced per condition.

### Lambda makes use of the new S3 file locations

As mentioned above, Lambda will be using each jurisdiction's `rsg_cg_mapping.json` to figure out which configurations they have activated and where those files are stored in S3.

There are a few things worth noting about this process:

1. If Lambda cannot find `/configurations/{jurisdiction}/rsg_cg_mapping.json` or the file is empty, this indicates a JD has no active configurations and no refining will occur
2. If Lambda cannot find `/configurations/{jurisdiction}/{condition-grouper-uuid}/current.json` or the `version` is `null`, this indicates there is no active configuration for this condition
3. If Lambda cannot find or parse `/configurations/{jurisdiction}/{condition-grouper-uuid}/{config-version}/active.json` this indicates an error with the configuration file, which will be logged and refining will be skipped

### Drawback of introducing the mapping file

The `rsg_cg_mapping.json` mapping file introduces a single point of failure on a per jurisdiction basis. If this file doesn't get written, is written incorrectly, or has other errors, it's possible that the Lambda will function improperly for all configurations within a jurisdiction.

Previously, errors were localized to a per configuration level. Meaning if one configuration in a jurisdiction was broken others could still function normally. This is no longer the case since all refining within a jurisdiction now depends on the mapping file.

Introducing the mapping file does not negate other safeguards we have in place when it comes to processing confiugrations, such as making use of the `current.json` file to determine that a specific version of a configuration has been written and is ready for Lambda to read from.

## Summary

This section will describe the Lambda inputs and outputs using COVID-19 as the activated configuration and SDDH as the jurisdiction.

### Inputs

SQS event, which includes:

- RR S3 bucket name
- RR S3 key

Matching eICR S3 key is constructed by Lambda using this data.

### Outputs

- `RefinerOutput/persistence/id/SDDH/COVID19/refined_eICR.xml`
- `RefinerOutput/persistence/id/SDDH/COVID19/refined_RR.xml`
- `RefinerOutput/persistence/id/SDDH/unrefined_rr/refined_RR.xml` (Shadow RR - only if other reportable conditions were found in the RR that are not configured by the JD)
