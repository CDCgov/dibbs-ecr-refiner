# 9. Normalizing Storage of Codes

Date: 2026-04-17

## Status

Proposed

## Context and Problem Statement

After deciding to implement [1099](https://app.zenhub.com/workspaces/dibbs-ecr-refiner-67ddd053d70b9f000ffbb542/issues/gh/cdcgov/dibbs-ecr-refiner/1099), the team decided to explore a long-desired refactor of our codeset schema. Several forthcoming features will need to manipulate codeset metadata beyond what the existing JSON array pattern conveniently allows, and the storage of this information is a section of the codebase with high maintenance complexity.

Storing codes as JSONB was a decision made when the Refiner was a much different application, one where codesets reads were the optimized operation and writes/updates weren't as common. With the evolution of the lambda, syncing operations for TES updates, and the development of current and upcoming web app features, this storage decision is in need of revisiting. Below are our explorations of

1. Whether / how to refactor our schema to better support codeset information
2. How to roll out the proposed refactor
3. Related concerns for future exploration.

## Decision Drivers

- Support future application development while maintaining current application functionality around codesets.
- Allow for dynamic retreival of codeset information, including the code itself and useful metadata (display name, code system, TES version membership, etc.) and easy manipulation of metadata for feature needs.
- Leverage the relational benefits of Postgres. Avoid unnecessary JSONB.
- Minimize the necessary refactoring needed across seeding, retreival, rendering, and other necessary application functions while maximizing storage flexibility and maintainbility of codeset storage as needed for current and future feature work.
- If possible, be able to add a code system without having to write a migration
- Make the engineering team feeling good about the way codes are stored. Does it spark joy?

The work should enable easier development / ongoing maintenance of

- Upcoming work for child RSG rendering / code search
- Upcoming work for TES update status descriptions and rendering
- Upcoming work around custom code activity log updates
- The TES update script and internal code relating to code CRUD operations

## Considered Options

### 1. Do nothing, store more JSON

The simplest option is to extend the existing JSON storage with the required data. This baseline minimally disrupts application code at the cost of maintaining the storage model's JSON patterns.

To begin, the conditions table's `child_rsg_snomed_codes` column would need extending to store `displayName` to support upcoming features. Future functionality would follow this duplication pattern, as well as requiring extending JSON search, parsing, and update functionality. Existing [SQL manipulation of JSON implemented for section processing](https://github.com/CDCgov/dibbs-ecr-refiner/blob/main/refiner/app/db/configurations/db.py#L456) would need to be extended in each instance of a column being added with code information.

### 2. Store normalized codes

Storing a normalized version of codeset information is the other way to modify our data model to support future functionality. These approaches would require significant application refactoring, touching our storage of custom codes, object creation and storage of related conditions / configurations, and ingest from the TES, amongst other modules. In return, it would simplify the maintence and data schema related to codeset storage and take advantage of oure relational data store for a large piece of relevant application data.

Two main decisions need to be made regarding normalization: the code schema and how to manage join relationship to parent condition / configuration objects.

### 2.1 Code storage schema

The core of the stored code information would include the following columns

| column       | datatype                |
| ------------ | ----------------------- |
| id           | UUID                    |
| displayName  | string                  |
| value        | string                  |
| system       | `fkey to systems table` |
| created_at   | DateTime                |
| last_updated | DateTime                |

To accomplish the goal of migration-free code system addition while maintaining maximal data guarentees, the `systems` column of the new codes table will reference a foreign key of a new table that stores system metadata that would look something like the below:

| column | datatype |
| ------ | -------- |
| id     | UUID     |
| name   | string   |
| oid    | string   |

Future code system addition will be enabled by adding a new row in the systems table that we can populate via a seeding script. To fully align this new table with the backend code, some refactoring will need to be done in the `terminology.py` file to derive backend `CodeSystem` enum values with the values in the new table.

#### 2.1.1 Storing codes in one table

#### 2.1.2 Storing custom codes and TES codes in separate tables

### 2.2 Managing the relationship between codes <> condition/configurations

#### 2.2.1 Managing joins via a junction table

The standard option for this many-to-many relationship is to store a single copy of a code and associate it with the condition / configuration in question via a junction table. Minimally, this junction table would be a primary key and the two columns storing the ID's of the code and configuration / condition row requiring a join table respectively. This setup would allow the pulling of other associated metadata needed for that code when performing queries.

This option would minimize the amount of code-related data that we need to store, with the added complexity of having to manage a centralized table to maintain code <> parent object relationships via another table(s). The TES seeding script would need to parse and insert these relationships on update, but would allow referential integrity to be maintained by Postgres should a code be deleted.

#### 2.2.2 Managing joins via an array of foreign keys

The second option is to replicate the existing JSON storage pattern and store a copy of each code per condition / configuration, with a foreign key array column from the parent entity to the list of codes. This maintains the current way that the application thinks about codes: within the condition / configuration context that the code exists in rather than as a standalone object.

This option stores more code information than strictly necessary, but allows for row-level relationships via foreign keys to drive the configuration and condition relationships between custom and TES-derived codes. In this pattern, the same code could exist in multiple rows, but would be unique within the configuration / condition entity it's stored within.

## Decision Outcome

### Store normalized codesets in a single code table

### Manage joins via a junction table

Compared with the other option of storing code relationships in an array, the junction table approach is the more standard way of modeling relationships. It gives guarentees such as referential integrity, cascade deletes, and key-based queries on the table itself that the array approach doesn't afford.

An example seeding script is stubbed out in `load_tes_data_into_normalized_table.py`

## Appendix

### Implementation rollout

1. Seed the new schema
1. Backport existing data into the new table structure
1. Add elements of the TES update script to munge and seed existing data into the new table structure
1. Refactor existing code to use the new data structure
1. Drop the relevant code columns in the conditions and configurations table
1. Remove unneeded code in the update script
