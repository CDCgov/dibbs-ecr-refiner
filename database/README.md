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
-- Complete query to get all codes for activated configurations
-- This breaks down the complex logic into clear, debuggable steps using CTEs

WITH
-- Step 1: Define our input - the (jurisdiction, SNOMED code) pairs we want to look up
input_codes AS (
    SELECT * FROM (VALUES
        ('SDDH', '840539006'), -- COVID-19
        ('SDDH', '772828001')  -- Influenza
    ) AS t(jurisdiction_id, snomed_code)
),

-- Step 2: Find active configurations for our input codes
-- This joins through the activation system to get the config details
active_configs AS (
    SELECT
        i.snomed_code,
        i.jurisdiction_id,
        c.name as configuration_name,
        cv.version as config_version,
        cv.included_conditions,        -- JSON array of {canonical_url, version} references
        cv.loinc_codes_additions,      -- JSON array of jurisdiction-specific LOINC codes
        cv.snomed_codes_additions,     -- JSON array of jurisdiction-specific SNOMED codes
        cv.icd10_codes_additions,      -- JSON array of jurisdiction-specific ICD10 codes
        cv.rxnorm_codes_additions      -- JSON array of jurisdiction-specific RxNorm codes
    FROM input_codes i
    JOIN activations a ON a.snomed_code = i.snomed_code AND a.jurisdiction_id = i.jurisdiction_id
    JOIN configuration_versions cv ON a.configuration_version_id = cv.id AND cv.status = 'active'
    JOIN configurations c ON cv.configuration_id = c.id
),

-- Step 3a: Get base LOINC codes from referenced conditions
-- This unpacks the included_conditions JSON and joins to the conditions table
base_loinc AS (
    SELECT
        ac.snomed_code,
        ac.jurisdiction_id,
        -- Aggregate all LOINC codes from all referenced conditions into one JSON array
        jsonb_agg(elem) as base_codes
    FROM active_configs ac
    -- Unpack the included_conditions JSON array into rows with canonical_url and version
    CROSS JOIN LATERAL jsonb_to_recordset(ac.included_conditions) AS ic(canonical_url TEXT, version TEXT)
    -- Join to conditions table to get the actual code data
    JOIN conditions cond ON cond.canonical_url = ic.canonical_url AND cond.version = ic.version
    -- Unpack the loinc_codes JSON array from conditions into individual code elements
    CROSS JOIN LATERAL jsonb_array_elements(cond.loinc_codes) elem
    GROUP BY ac.snomed_code, ac.jurisdiction_id
),

-- Step 3b: Get base SNOMED codes from referenced conditions
base_snomed AS (
    SELECT
        ac.snomed_code,
        ac.jurisdiction_id,
        jsonb_agg(elem) as base_codes
    FROM active_configs ac
    CROSS JOIN LATERAL jsonb_to_recordset(ac.included_conditions) AS ic(canonical_url TEXT, version TEXT)
    JOIN conditions cond ON cond.canonical_url = ic.canonical_url AND cond.version = ic.version
    CROSS JOIN LATERAL jsonb_array_elements(cond.snomed_codes) elem
    GROUP BY ac.snomed_code, ac.jurisdiction_id
),

-- Step 3c: Get base ICD10 codes from referenced conditions
base_icd10 AS (
    SELECT
        ac.snomed_code,
        ac.jurisdiction_id,
        jsonb_agg(elem) as base_codes
    FROM active_configs ac
    CROSS JOIN LATERAL jsonb_to_recordset(ac.included_conditions) AS ic(canonical_url TEXT, version TEXT)
    JOIN conditions cond ON cond.canonical_url = ic.canonical_url AND cond.version = ic.version
    CROSS JOIN LATERAL jsonb_array_elements(cond.icd10_codes) elem
    GROUP BY ac.snomed_code, ac.jurisdiction_id
),

-- Step 3d: Get base RxNorm codes from referenced conditions
base_rxnorm AS (
    SELECT
        ac.snomed_code,
        ac.jurisdiction_id,
        jsonb_agg(elem) as base_codes
    FROM active_configs ac
    CROSS JOIN LATERAL jsonb_to_recordset(ac.included_conditions) AS ic(canonical_url TEXT, version TEXT)
    JOIN conditions cond ON cond.canonical_url = ic.canonical_url AND cond.version = ic.version
    CROSS JOIN LATERAL jsonb_array_elements(cond.rxnorm_codes) elem
    GROUP BY ac.snomed_code, ac.jurisdiction_id
),

-- Step 4a: Merge base LOINC codes with jurisdiction-specific additions
final_loinc AS (
    SELECT
        ac.snomed_code,
        ac.jurisdiction_id,
        -- Combine base codes (from conditions) with additions (from config)
        -- Use COALESCE to handle cases where either might be null/empty
        -- The || operator concatenates JSON arrays
        COALESCE(bl.base_codes, '[]'::jsonb) || COALESCE(ac.loinc_codes_additions, '[]'::jsonb) as final_codes
    FROM active_configs ac
    LEFT JOIN base_loinc bl ON ac.snomed_code = bl.snomed_code AND ac.jurisdiction_id = bl.jurisdiction_id
),

-- Step 4b: Merge base SNOMED codes with jurisdiction-specific additions
final_snomed AS (
    SELECT
        ac.snomed_code,
        ac.jurisdiction_id,
        COALESCE(bs.base_codes, '[]'::jsonb) || COALESCE(ac.snomed_codes_additions, '[]'::jsonb) as final_codes
    FROM active_configs ac
    LEFT JOIN base_snomed bs ON ac.snomed_code = bs.snomed_code AND ac.jurisdiction_id = bs.jurisdiction_id
),

-- Step 4c: Merge base ICD10 codes with jurisdiction-specific additions
final_icd10 AS (
    SELECT
        ac.snomed_code,
        ac.jurisdiction_id,
        COALESCE(bi.base_codes, '[]'::jsonb) || COALESCE(ac.icd10_codes_additions, '[]'::jsonb) as final_codes
    FROM active_configs ac
    LEFT JOIN base_icd10 bi ON ac.snomed_code = bi.snomed_code AND ac.jurisdiction_id = bi.jurisdiction_id
),

-- Step 4d: Merge base RxNorm codes with jurisdiction-specific additions
final_rxnorm AS (
    SELECT
        ac.snomed_code,
        ac.jurisdiction_id,
        COALESCE(br.base_codes, '[]'::jsonb) || COALESCE(ac.rxnorm_codes_additions, '[]'::jsonb) as final_codes
    FROM active_configs ac
    LEFT JOIN base_rxnorm br ON ac.snomed_code = br.snomed_code AND ac.jurisdiction_id = br.jurisdiction_id
)

-- Step 5: Final assembly - bring together all the merged code systems
SELECT
    ac.snomed_code as triggering_snomed_code,
    ac.jurisdiction_id,
    ac.configuration_name,
    ac.config_version,
    -- Build a single JSON object containing all code systems
    jsonb_build_object(
        'loinc_codes', COALESCE(fl.final_codes, '[]'::jsonb),
        'snomed_codes', COALESCE(fs.final_codes, '[]'::jsonb),
        'icd10_codes', COALESCE(fi.final_codes, '[]'::jsonb),
        'rxnorm_codes', COALESCE(fr.final_codes, '[]'::jsonb)
    ) as complete_valuesets
FROM active_configs ac
-- Left joins ensure we get results even if some code systems have no codes
LEFT JOIN final_loinc fl ON ac.snomed_code = fl.snomed_code AND ac.jurisdiction_id = fl.jurisdiction_id
LEFT JOIN final_snomed fs ON ac.snomed_code = fs.snomed_code AND ac.jurisdiction_id = fs.jurisdiction_id
LEFT JOIN final_icd10 fi ON ac.snomed_code = fi.snomed_code AND ac.jurisdiction_id = fi.jurisdiction_id
LEFT JOIN final_rxnorm fr ON ac.snomed_code = fr.snomed_code AND ac.jurisdiction_id = fr.jurisdiction_id
ORDER BY ac.jurisdiction_id, ac.configuration_name, ac.snomed_code;
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
