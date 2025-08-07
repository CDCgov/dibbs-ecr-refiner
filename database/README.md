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

Here are the three essential tables and how they work together:

1. **`conditions` Table**: This is the foundational data.
   - **What it is**: It contains the pre-aggregated, "base" sets of codes (LOINC, SNOMED, etc.) for a given condition as defined by APHL's Terminology Exchange Service (TES). Each row represents a specific version of a ValueSet.
   - **Why it's needed**: It provides the official, trusted starting point for any configuration. This data is populated by the seeding script from the JSON files in the `/data` directory.

2. **`configurations` Table**: This represents a complete, immutable configuration version.
   - **What it is**: Each row is a specific, versioned configuration that references one or more base conditions and can include additional jurisdiction-specific codes. The `id` field serves as the user-facing version number (e.g., "Configuration #47").
   - **Why it's needed**: It provides a complete audit history of changes and allows jurisdictions to create new versions without affecting existing activations.

3. **`activations` Table**: This is the "on switch" with full lifecycle tracking.
   - **What it is**: The most critical table for the Refiner application. It explicitly links a trigger SNOMED code to a specific configuration, with time-based activation/deactivation tracking and pre-computed code payloads.
   - **Why it's needed**: This record makes a configuration "live" for a specific condition. When the Refiner encounters a SNOMED code in an eCR, it queries this table to find exactly which configuration to use. **No activation record, no refined codes.**

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

### 2. View All Configurations with Their Details

This query shows all configurations with their included conditions and any jurisdiction-specific additions:

```sql
-- Get an overview of all configurations
-- Shows which conditions each configuration includes and any custom additions

SELECT
    c.id as configuration_id,
    c.name,
    c.description,
    c.jurisdiction_id,
    c.created_at,

    -- Show which conditions are included
    jsonb_pretty(c.included_conditions) as included_conditions,

    -- Show jurisdiction-specific additions (only if they exist)
    CASE
        WHEN jsonb_array_length(c.loinc_codes_additions) > 0
        THEN jsonb_pretty(c.loinc_codes_additions)
        ELSE NULL
    END as loinc_additions,

    CASE
        WHEN jsonb_array_length(c.snomed_codes_additions) > 0
        THEN jsonb_pretty(c.snomed_codes_additions)
        ELSE NULL
    END as snomed_additions,

    CASE
        WHEN jsonb_array_length(c.icd10_codes_additions) > 0
        THEN jsonb_pretty(c.icd10_codes_additions)
        ELSE NULL
    END as icd10_additions,

    CASE
        WHEN jsonb_array_length(c.rxnorm_codes_additions) > 0
        THEN jsonb_pretty(c.rxnorm_codes_additions)
        ELSE NULL
    END as rxnorm_additions

FROM configurations c
ORDER BY c.jurisdiction_id, c.created_at DESC;
```

### 3. View Active and Historical Activations

This query shows the activation status for each jurisdiction and SNOMED code combination, including historical activations:

```sql
-- Get activation status overview
-- Shows current and historical activations with their lifecycle

SELECT
    a.jurisdiction_id,
    a.snomed_code,
    a.configuration_id,
    c.name as configuration_name,
    a.activated_at,
    a.deactivated_at,

    -- Show activation status
    CASE
        WHEN a.deactivated_at IS NULL THEN 'ACTIVE'
        ELSE 'DEACTIVATED'
    END as status,

    -- Show how long the activation was/has been active
    CASE
        WHEN a.deactivated_at IS NULL
        THEN EXTRACT(EPOCH FROM (NOW() - a.activated_at)) / 86400 || ' days (ongoing)'
        ELSE EXTRACT(EPOCH FROM (a.deactivated_at - a.activated_at)) / 86400 || ' days'
    END as duration,

    -- Show a preview of the computed codes structure
    jsonb_pretty(
        jsonb_build_object(
            'loinc_count', jsonb_array_length(a.computed_codes->'loinc_codes'),
            'snomed_count', jsonb_array_length(a.computed_codes->'snomed_codes'),
            'icd10_count', jsonb_array_length(a.computed_codes->'icd10_codes'),
            'rxnorm_count', jsonb_array_length(a.computed_codes->'rxnorm_codes')
        )
    ) as code_counts

FROM activations a
JOIN configurations c ON a.configuration_id = c.id
ORDER BY
    a.jurisdiction_id,
    a.snomed_code,
    a.activated_at DESC;
```

### 4. Primary Runtime Query - Get Active Configuration for SNOMED Code

This is the primary query the Refiner application will use at runtime. It's optimized for fast lookups of currently active configurations:

```sql
-- Fast runtime lookup for active configurations
-- This is the primary query pattern for the Refiner application

SELECT
    a.jurisdiction_id,
    a.snomed_code,
    c.name as configuration_name,
    c.id as configuration_id,
    a.computed_codes
FROM activations a
JOIN configurations c ON a.configuration_id = c.id
WHERE
    a.jurisdiction_id = 'SDDH'
    AND a.snomed_code = '840539006'
    AND a.deactivated_at IS NULL  -- Only get currently active
LIMIT 1;
```

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
