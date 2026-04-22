# 9. Normalizing Storage of Codes

Date: 2026-04-17

## Status

Proposed

## Context and Problem Statement

Following a Slack discussion about implementation of [1099](https://app.zenhub.com/workspaces/dibbs-ecr-refiner-67ddd053d70b9f000ffbb542/issues/gh/cdcgov/dibbs-ecr-refiner/1099), it was determined that this feature may be a chance to implement a long-desired refactor of the schema we're using to store codesets. Several forthcoming features will need to retreive granular versions of this data beyond current storage schema allows. The engineering team has acknowledged for a while that this area of the codebase has needed refactoring and is using this opportunity to explore approaches. The current decision to store codes as JSONB was made when the Refiner was a much different application, where codesets reads from the database scoped to a configuration were the optimized operation, over writes/updates and reads outside the configuration context. With the evolution of the lambda, syncing operations for TES updates, and the development of current and upcoming web app features, this storage decision is in need of revisiting.

Below are our exploration of 1. Whether / how to refactor our schema to better support codeset information and 2. How to roll out the proposed refactorcodebase.

## Decision Drivers

- Support future application development while maintaining current application functionality / validation around codeset information.
- Allow for dynamic retreival of codeset information, including the code itself and useful metadata (display name, code system, TES version membership, etc.)
- Leverage the relational benefits of Postgres. Avoid unnecessary JSONB.
- Minimize the necessary refactoring needed across seeding, retreival, rendering, and other necessary application functions while maximizing storage flexibility and maintainbility of codeset storage as needed for current and future feature work.

- If possible, be able to add a code system without having to write a migration
- Make the engineering team feeling good about the way codes are stored. Does it spark joy?

## Considered Options

### 1. Do nothing, store more JSON

The simplest option is to extend the existing JSON storage to support this and other features. This baseline minimally disrupts application code at the cost of extending the data model with more JSON.

To begin, the `child_rsg_snomed_codes` column in the existing conditions table would need to be extended to store display name information. Future features, such as TES updates, condition grouper search, and other improvements would have to implement JSON search, parsing, and update functionality. Existing SQL operations that handle these operations are already quite complex since JSON mainpulation is being done at the data level. This level of complexity would need to be maintained if future code storage remains in JSON.

### 2. Store normalized codes

The following options would be to store a normalized version of codeset information, with different approaches to handling custom codes, relationships to conditions / configurations, and ingest from the TES. These approaches would require significant application refactoring related to TES synchronization and codeset reads, but would simplify the maintence and data schema related to codeset storage.

The first decision we'll need to make we will need to determine whether to maintain the existing per-configuration copy of codes within the code(s) tables, or take advantage of normalization to store a single set of codes that we associate to the relevant elements of the configuration / condition entities via a junction table.

#### 2.1 Duplicate storage of codes with a composite system / code key, unique per configuration

The first option is to replicate the existing JSON storage pattern and store a copy of each code unique only to the condition / configuration in question, with a foreign key out to the relevant entity linking the code and the parent object. This maintains the current way that the application thinks about codes, which is within the context that the code exists in rather than as a standalone entity.

This option stores more code information than strictly necessary, but allows for row-level relationships via foreign keys to drive the configuration and condition relationships between custom and TES-derived codes.

#### 2.2 Deduplicated storage of codes via a junction table, unique globally

The second option is to store a single code copy of a code and associate it with the condition / configuration in question via a junction. This storage paradigm considers the individual codes as atomic entities, and uses relationality to associate them with standalone conditions / configuration objects only in the context of the junction.

This option would minimize the amount of data that we need to store, with the added complexity of having to manage a centralized table to maintain code <> parent object relationships rather than doing so at the individual row level.

### 3. Code storage schema

#### Base schema

The base schema normalization approaches would include the following columns. These represent the core of the stored code information, which are extended with different options for handling custom codes, relationship to conditions / configurations, and other related considerations.

| column       | datatype       |
| ------------ | -------------- |
| id           | UUID           |
| displayName  | string         |
| value        | string         |
| system       | string or Enum |
| created_at   | DateTime       |
| last_updated | DateTime       |

The choice of data type for system could either be a raw string (enforced by the `CodeSystem` enum in our backend code) or a Postgres enum that enforces system values at the data level. A discussion of the benefits of each is included in Decision Outcomes.

#### 2.1 Storing TES codes together with custom codes

The most straightforward option for code storage is to store custom codes and TES codes in a single table, using boolean columns to differentiate the two. The main complication would be the need to link custom code rows to configurations and TES code rows to conditions, since custom codes only exist in a configuration context while TES codes exist to condition codesets. The extended schema under this option would look something like the following:

| column               | datatype                        |
| -------------------- | ------------------------------- |
| id                   | UUID                            |
| displayName          | string                          |
| value                | string                          |
| system               | string or Enum                  |
| created_at           | DateTime                        |
| last_updated         | DateTime                        |
| **is_custom**        | **Boolean**                     |
| **condition_id**     | **UUID, fkey `conditions`**     |
| **configuration_id** | **UUID, fkey `configurations`** |

_the foreign key columns may not be necessary if we decide to store relationships in a junction table_

This option trades simplicity in Python interface and data schema for complexity in the data layer, as the two foreign key columns and the boolean column would need to be managed whenever there's an update to either side. We'd also have to allow for null foreign keys across the codes table, since configuration and condition relationships wouldn't exist for TES codes and custom codes respectively.

In return, reads and writes from / to this table would be much more straightforward, since they can be manged by a single database service shared by both the condition and configuration modules. The codes object could contain all the relevant metadata provide only the necessary information around custom code / TES status to the caller, which may allow us to simplify the differentiation between the our models of codes.

#### 2.2 Storing TES codes separately from custom codes

A secondary option is to store custom codes and TES codes separately, duplicating the base schema in both tables and only adding a foreign key to the relevant configuration or conditions table. The main complication would be the need to link custom code rows to configurations and TES code rows to conditions, since custom codes only exist in a configuration context while TES codes exist to condition codesets. The extended schema under this option would look something like the following:

##### Custom codes table

| column               | datatype                        |
| -------------------- | ------------------------------- |
| id                   | UUID                            |
| displayName          | string                          |
| value                | string                          |
| system               | string or Enum                  |
| created_at           | DateTime                        |
| last_updated         | DateTime                        |
| **configuration_id** | **UUID, fkey `configurations`** |

##### TES codes table

| column           | datatype                    |
| ---------------- | --------------------------- |
| id               | UUID                        |
| displayName      | string                      |
| value            | string                      |
| system           | string or Enum              |
| created_at       | DateTime                    |
| last_updated     | DateTime                    |
| **condition_id** | **UUID, fkey `conditions`** |

_the foreign key columns may not be necessary if we decide to store relationships in a junction table_

This option trades simplicity in the data layer for complexity in the Python interface. Although the data schema has one rather than two tables, each individual table is much more straightforward with fewer potentially nullable fields. Reads and writes to each table would be more straightforward, as we can tailor the respective inputs based on the needs of the table.

In return, reads and writes from / to this table would require separate services, used respectively by the condition and configuration modules. Serialization from the database would also require separate serialization and / or custom and TES code objects.

## Decision Outcome

### Store system values as raw strings, enforced by the CodeSystem Python enum

While a Postgres enum would give us stricter data guarentees, enforcing things in backend code would give much more flexibility for adding new system values: specifically, without needing to perform data migrations for additions. Since we control the interfaces for reading / writing codes within Python, the additional data guarentee of storing the enum at the data level are marginal as long as we centralize the interfaces against the database. Thus, we'll store system information as raw strings and enforce conformance to the set of allowed systems at the code level.

### Storing TES codes separately from custom codes

### Duplicate storage of codes with a composite system / code key, unique per configuration

## Implementation considerations

1. Seed the new schema
1. Backport existing data from the `child_rsg_snomed_codes` column into the new table structure
1. Add elements of the TES update script to munge and seed existing data into the new table structure
1. Refactor existing code to use the new data structure
1. Drop the relevant code columns in the conditions and configurations table
1. Remove unneeded code in the update script

## Appendix (OPTIONAL)

Add any links here that are relevant for understanding your proposal or its background.

**Be sure to read the information about this in [CONTRIBUTING](https://github.com/CDCgov/dibbs-ecr-refiner/blob/main/CONTRIBUTING.md##Request-for-comment)**
