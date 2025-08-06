# Database for the DIBBs eCR Refiner

This directory contains the complete, self-contained PostgreSQL database environment for the DIBBS eCR Refiner. It includes the schema definition, data pipeline, and seeding scripts required to create a fully functional database instance.

The database is designed to store and manage public health condition definitions and jurisdiction-specific configurations, enabling the Refiner application to resolve a trigger code (e.g., a SNOMED code from a Reportability Response) into a complete set of associated clinical codes.

## Directory Structure

The project is organized into the following key directories:

- `data/`: Stores the raw JSON ValueSet files downloaded from the APHL TES API. This directory is populated by the `pipeline` scripts.
- `docker-compose.yaml` & `Dockerfile`: Defines the Docker environment for building and running the PostgreSQL container.
- `pipeline/`: Python scripts responsible for fetching the latest TES data (ValueSets) from the source API, checking for changes using a checksum process, and saving them as flat files in the `data/` directory.
- `schema/`: Contains the core SQL `CREATE TABLE` statements that define the database structure (e.g., `100-schema-base.sql`).
- `scripts/`: Contains the Python scripts for orchestrating the database setup, including `database_seeding.py` for the initial data load from the files in `data/`.
- `tests/`: Contains integration and unit tests for the database logic and pipeline scripts.

### Naming conventions

To ensure that we have an extensible structure in place for naming as the database grows into a mature production PostgrSQL database, we are using the following as a classification schema for naming a[...]

| Series | Range   | Directory   | Purpose/Examples                          | Example File                                      |
|--------|---------|-------------|-------------------------------------------|--------------------------------------------------|
| **100s**   | `100–199` | `schema`      | Table/view definitions, indexes           | `100-schema-base.sql`                            |
| **200s**   | `200–299` | (future)    | SQL/stored functions, procedures          | `200-functions-aggregated-child-codes.sql`       |
| **400s**   | `400–499` | (future)    | Initial/reference data, fixtures          | `400-data-countries.sql` (future)                |
| **500s**   | `500–599` | (future)    | Migrations                                | `500-migration-add-user-profile.sql` (future)    |

## Core Concepts

Here are the four essential tables and how they work together:

1.  **`conditions` Table**: This is the foundational data.
    *   **What it is**: It contains the pre-aggregated, "base" sets of codes (LOINC, SNOMED, etc.) for a given condition as defined by APHL's Terminology Exchange Service (TES). Each row represents a specific version of a ValueSet.
    *   **Why it's needed**: It provides the official, trusted starting point for any configuration. This data is populated by the seeding script from the JSON files in the `/data` directory.

2.  **`configurations` Table**: This represents a high-level "idea" or workspace.
    *   **What it is**: A conceptual container for a jurisdiction's work on a specific condition (e.g., "Example County Influenza Surveillance").
    *   **Why it's needed**: It groups multiple versions of a configuration under a single name and description, owned by a specific jurisdiction.

3.  **`configuration_versions` Table**: This is an immutable, versioned snapshot of a configuration.
    *   **What it is**: Every time a user saves changes, a new row is created here. It references one or more "base" `conditions` and can include additional codes (`loinc_codes_additions`, etc.) that are layered on top. Each version has a `status` (`draft`, `active`, `archived`).
    *   **Why it's needed**: It provides a full audit history of changes and allows jurisdictions to work on drafts without affecting the "live" version.

4.  **`activations` Table**: This is the "on switch".
    *   **What it is**: The most critical table for the Refiner application. It's a simple mapping that explicitly links a trigger SNOMED code to a specific `configuration_version_id`.
    *   **Why it's needed**: This record makes a configuration "live". When the Refiner encounters a SNOMED code in an eCR, it queries this table to find exactly which configuration version to use. **No activation record, no refined codes.**

## Example Queries

These queries demonstrate how to interact with the data model to retrieve useful information. They are designed to be run directly against the database for testing, debugging, or integration purposes.

### 1. Find a Condition by a Child SNOMED Code

Since conditions in the `conditions` table have an array of `child_rsg_snomed_codes` we can very easily start with our input, which will be SNOMED condition codes from the RR's coded information organizer (either one or many as a list) and we can retrieve the parent condition grouper's complete list of ValueSets as `jsonb` with both the code and display name by code system:

```sql
-- Find a specific version of a condition by a child SNOMED code.
-- This uses the && operator (overlap) to efficiently search inside the text array.

SELECT
  display_name,
  version,
  canonical_url,
  child_rsg_snomed_codes,
  -- The jsonb_pretty function formats the JSON output for better readability.
  jsonb_pretty(loinc_codes) as loinc_codes,
  jsonb_pretty(snomed_codes) as snomed_codes,
  jsonb_pretty(icd10_codes) as icd10_codes,
  jsonb_pretty(rxnorm_codes) as rxnorm_codes
FROM
  conditions
WHERE
  -- The '&&' operator checks if the child_rsg_snomed_codes array
  -- has any elements in common with the array provided.
  -- This is a very fast way to check for membership.
  child_rsg_snomed_codes && ARRAY['840539006', '772828001']
  -- You can optionally filter to a specific version of the condition definition.
  AND version = '2.0.0';
```

### 2. Get All Codes for a Configuration

This is the primary query the Refiner application will use. Given a list of input SNOMED codes, it returns the complete, aggregated set of final codes for each corresponding active configuration. This is a combination of **any** condition included in the configuration as well as user defined ValueSets by code system.

```sql
-- This query is broken into three parts (Common Table Expressions or CTEs) for clarity and performance.

-- CTE 1: Define the list of input SNOMED codes we want to process.
-- In a real application, this list would be dynamically generated from incoming eCR data.
WITH InputCodes (snomed_code) AS (
  VALUES
    ('840539006'), -- COVID-19
    ('772828001')  -- Influenza A
),

-- CTE 2: Find the active configuration for EACH input code and gather its base conditions.
-- This CTE joins the input codes with the activation table to find the live configuration.
ActiveConfigsAndConditions AS (
  SELECT
    i.snomed_code AS triggering_snomed_code, -- Carry the input code through for final grouping.
    conf.name AS configuration_name,
    cv.version AS configuration_version,
    -- This aggregates all the JSON data from the base `conditions` into a single JSON array.
    -- This is efficient because we are not yet looking inside the code arrays.
    jsonb_agg(
      jsonb_build_object(
        'loinc_codes', c.loinc_codes, 'snomed_codes', c.snomed_codes,
        'icd10_codes', c.icd10_codes, 'rxnorm_codes', c.rxnorm_codes
      )
    ) AS base_conditions_data,
    -- Pass along the version-specific additions to be combined later.
    cv.loinc_codes_additions, cv.snomed_codes_additions,
    cv.icd10_codes_additions, cv.rxnorm_codes_additions
  FROM InputCodes i
  JOIN activations a ON i.snomed_code = a.snomed_code
  JOIN configuration_versions cv ON a.configuration_version_id = cv.id
  JOIN configurations conf ON cv.configuration_id = conf.id
  -- A LATERAL join is like a for-each loop in SQL. It expands the `included_conditions`
  -- JSON array so we can join each entry against the `conditions` table.
  CROSS JOIN LATERAL jsonb_to_recordset(cv.included_conditions) AS ic(canonical_url TEXT, version TEXT)
  JOIN conditions c ON c.canonical_url = ic.canonical_url AND c.version = ic.version
  -- Ensure we only use configurations that are explicitly marked as 'active'.
  WHERE cv.status = 'active'
  GROUP BY i.snomed_code, cv.id, conf.name, cv.version
),

-- CTE 3: Create a flat, "long-formatted" list of all unique codes.
-- This CTE unnests all the code arrays (base + additions) into a simple list.
-- Using UNION automatically handles de-duplication of codes.
AllCodesFlat AS (
  -- Get all LOINC codes from both additions and base conditions
  SELECT triggering_snomed_code, configuration_name, configuration_version, 'LOINC' AS code_system, elem->>'code' AS code, elem->>'display' AS display
  FROM ActiveConfigsAndConditions, jsonb_array_elements(loinc_codes_additions) elem
  UNION
  SELECT triggering_snomed_code, configuration_name, configuration_version, 'LOINC' AS code_system, elem->>'code', elem->>'display'
  FROM ActiveConfigsAndConditions, jsonb_array_elements(base_conditions_data) AS d, jsonb_array_elements(d->'loinc_codes') elem
  -- ... this pattern repeats for SNOMED, ICD-10, and RxNorm ...
  UNION
  SELECT triggering_snomed_code, configuration_name, configuration_version, 'SNOMED' AS code_system, elem->>'code', elem->>'display'
  FROM ActiveConfigsAndConditions, jsonb_array_elements(snomed_codes_additions) elem
  UNION
  SELECT triggering_snomed_code, configuration_name, configuration_version, 'SNOMED' AS code_system, elem->>'code', elem->>'display'
  FROM ActiveConfigsAndConditions, jsonb_array_elements(base_conditions_data) AS d, jsonb_array_elements(d->'snomed_codes') elem
  UNION
  SELECT triggering_snomed_code, configuration_name, configuration_version, 'ICD-10' AS code_system, elem->>'code', elem->>'display'
  FROM ActiveConfigsAndConditions, jsonb_array_elements(icd10_codes_additions) elem
  UNION
  SELECT triggering_snomed_code, configuration_name, configuration_version, 'ICD-10' AS code_system, elem->>'code', elem->>'display'
  FROM ActiveConfigsAndConditions, jsonb_array_elements(base_conditions_data) AS d, jsonb_array_elements(d->'icd10_codes') elem
  UNION
  SELECT triggering_snomed_code, configuration_name, configuration_version, 'RxNorm' AS code_system, elem->>'code', elem->>'display'
  FROM ActiveConfigsAndConditions, jsonb_array_elements(rxnorm_codes_additions) elem
  UNION
  SELECT triggering_snomed_code, configuration_name, configuration_version, 'RxNorm' AS code_system, elem->>'code', elem->>'display'
  FROM ActiveConfigsAndConditions, jsonb_array_elements(base_conditions_data) AS d, jsonb_array_elements(d->'rxnorm_codes') elem
)

-- Final Step: Pivot the flat data back into the "wide" format the application expects.
-- This creates one row for each `triggering_snomed_code`.
SELECT
  triggering_snomed_code,
  configuration_name,
  configuration_version,
  -- This is a conditional aggregation. It builds a JSON array of all rows
  -- from the CTE above, but only if they match the FILTER condition.
  jsonb_agg(jsonb_build_object('code', code, 'display', display)) FILTER (WHERE code_system = 'LOINC') AS loinc_codes,
  jsonb_agg(jsonb_build_object('code', code, 'display', display)) FILTER (WHERE code_system = 'SNOMED') AS snomed_codes,
  jsonb_agg(jsonb_build_object('code', code, 'display', display)) FILTER (WHERE code_system = 'ICD-10') AS icd10_codes,
  jsonb_agg(jsonb_build_object('code', code, 'display', display)) FILTER (WHERE code_system = 'RxNorm') AS rxnorm_codes
FROM AllCodesFlat
-- The final GROUP BY creates one output row for each unique combination of trigger code and configuration.
GROUP BY triggering_snomed_code, configuration_name, configuration_version;
```

You can see how the data returned is in the `GrouperRow` shape, which we might consider renaming to `ConditionRow`.

## Local Development Workflow

Follow these steps to set up and run the database environment on your local machine.

### Prerequisites

*   Docker and Docker Compose
*   Python 3.13 & `pip`

### Step 1: Install Dependencies

Install the required Python packages from the requirements files.

```bash
pip install -r requirements.txt && pip install -r requirements-dev.txt
```

### Step 2: Fetch TES Data

Run the pipeline script to download the latest ValueSet data from the TES source API. This script will:
1. Fetch a manifest of all available ValueSets.
2. For each ValueSet, calculate a checksum of its content.
3. Compare the new checksum against the one stored in the local `manifest.json`.
4. If the checksum is new or different, it downloads the full ValueSet JSON and saves it to the `./data` directory.

This process ensures that we only download data when it has actually changed, saving time and bandwidth.

> [!NOTE]
> You will need an API key and it will need to be in your `.env` file in order for the scripts to work.

```bash
# in the database/ directory
python pipeline/detect_changes.py
```

### Step 3: Build and Start the Database

Use Docker Compose to build and start the PostgreSQL container. On the first run, Docker will:
1.  Initialize the PostgreSQL server.
2.  Apply the schemas from `./schema/`.
3.  Execute the `./scripts/run_seeding.sh` script, which runs `database_seeding.py` to populate the database with the data from `./data` and `scripts/sample_configuration_seed_data.json`.

```bash
docker compose up --build -d
```

You can view the logs to monitor the startup and seeding process:

```bash
docker logs -f database-refiner-db-dev-1
```

### Step 4: Connect and Verify (Optional)

You can connect to the running database using any standard PostgreSQL client (like `psql`, Beekeeper, DBeaver, or DataGrip) to run the example queries and verify the data was seeded correctly.

**Connection Details:**
- **Host**: `localhost`
- **Port**: `5432`
- **User**: `postgres`
- **Password**: `postgres`
- **Database**: `refiner`

### Step 5: Run Tests (Optional)

To run the full test suite, which includes tests for the data pipeline and database logic, use `pytest`.

```bash
pytest -vv tests/
```

> [!NOTE]
> You do not need to have the container running for the tests. We are using the `testcontainers` library to run all of our unit and integration tests.

### Step 6: Shutting Down

To stop and remove the database container and its associated data volume, run:

```bash
docker compose down -v
```
