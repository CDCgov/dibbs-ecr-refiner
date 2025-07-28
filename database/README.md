# Database for the DIBBs eCR Refiner

This directory contains the complete, self-contained PostgreSQL database environment for the DIBBS eCR Refiner. It includes the schema, data pipeline, seeding scripts, and Docker configuration required to build, populate, and run the database.

## Directory Structure

The project is organized into the following key directories:

- `data/`: Stores the raw JSON ValueSet files downloaded from the TES API source. This directory is populated by the `pipeline` scripts.
- `docker-compose.yaml` & `Dockerfile`: Defines the Docker environment for building and running the PostgreSQL container.
- `functions/`: Contains SQL function definitions that are applied to the database.
- `pipeline/`: Python scripts responsible for fetching the latest TES data (ValueSets) from the source API and saving them as flat files in the `data/` directory.
- `schema/`: Contains the core SQL `CREATE TABLE` statements that define the database structure.
- `scripts/`: Contains the Python scripts for orchestrating the database setup, including `database_seeding.py` for the initial data load and `check_seeded_db.py` for verification/sanity check.
- `tests/`: Contains integration and unit tests for the database logic and pipeline scripts.
- `triggers/`: Contains the SQL trigger definitions that handle ongoing, incremental data updates after the initial seed.

## Core Concepts

The database is designed to pre-calculate and cache refined code sets, ensuring high performance for the main Refiner application. While database triggers are in place to handle incremental updates during normal operation, the initial setup is performed by a dedicated seeding script for reliability and speed.

### The `refinement_cache` Table

The primary goal of this database is to populate the `refinement_cache` table. To get a single row in this table, you need a complete, unbroken chain of five distinct records across five different tables. The cache generation process is driven entirely by the `configurations` table.

Here are the five essential ingredients, in logical order:

1. **A "Parent" Grouper**: A record in `tes_condition_groupers`.
  * **What it is**: A broad category of a condition (e.g., "COVID-19"). It contains all of the RS Grouper ValueSets that are referenced by the parent Condition Grouper.
  * **Why it's needed**: This is the foundational set of codes that will give us the right context to start as our "blank slate" in a Configuration.
2. **A "Child" Grouper**: A record in `tes_reporting_spec_groupers`.
  * **What it is**: The RS Grouper matches 1:1 with the SNOMED code that is found both in the RR's Coded Information Organizer (`RR11`) and the codes in RCKMS used to author the condition rulesets.
  * **Why it's needed**: The SNOMED code in the RR, in addition to the STLT's jurisdiction code, are how the Refiner will know what set of codes should be used in the refining process.
3. **A Link**: A record in `tes_condition_grouper_references`.
  * **What it is**: The "glue" that explicitly connects the Parent Grouper (Ingredient #1) to the Child Grouper (Ingredient #2).
  * **Why it's needed**: Without this reference, the system has no way of knowing that the specific "Child" belongs to the broader "Parent" category. This is a part of our normalized "source of truth".
4. **A Jurisdiction**: A record in the `jurisdictions` table.
  * **What it is**: The entity (e.g., a state or local health department) that is applying the refinement rules.
  * **Why it's needed**: The cache is jurisdiction-specific. This is how the Refiner will be able to work independently on AIMS to process eCR data at scale.
5. **A Configuration**: A record in the `configurations` table.
  * **What it is**: This is the **most critical ingredient**. It's the "activator" record that ties everything together. It explicitly states: "Jurisdiction X (Ingredient #4) wants to apply a specific set of override rules to Child Grouper Y (Ingredient #2)."
  * **Why it's needed**: This record initiates the entire cache generation process for a specific `snomed_code` and `jurisdiction_id`. **No configuration, no cache entry**.

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

Run the pipeline script to download the latest ValueSet data from the TES source API. This will populate the `./data` directory with the JSON files needed for seeding.

> [!NOTE]
> You will need an API key and it will need to be in your `.env` file in order for the scripts to work.

```bash
# in the database/ directory
python pipeline/detect_changes.py

# or if the above doesn't work
python -m pipeline.detect_changes
```

### Step 3: Build and Start the Database

Use Docker Compose to build and start the PostgreSQL container. On the first run, Docker will:
1.  Initialize the PostgreSQL server.
2.  Apply the schemas from `./schema/`.
3.  Apply the functions and triggers from `./functions/` and `./triggers/`.
4.  Execute the `./scripts/run_seeding.sh` script, which runs `database_seeding.py` to populate the database with the data from `./data`.

```bash
docker compose up --build -d
```

You can view the logs to monitor the startup and seeding process:

```bash
docker logs -f database-refiner-db-dev-1
```

> [!TIP]
> You can also try the wonderful [LazyDocker](https://github.com/jesseduffield/lazydocker) tool!

### Step 4: Verify the Seeded Database

After the container is running and the seeding script has finished, run the `check_seeded_db.py` script. This performs a series of sanity checks to ensure the database was populated correctly.

```bash
# you can run this from database/ or database/scripts/
python scripts/check_seeded_db.py
```

A successful run will end with the message: `🎉 All critical sanity checks passed.` and look roughly like this:

```
🧪 Running Database Sanity Checks...
🔎 Running check: No Orphaned References... ✅ PASSED
🔎 Running check: No Duplicate Condition Groupers... ✅ PASSED
🔎 Running check: No Duplicate Reporting Spec Groupers... ✅ PASSED
🔎 Running check: Refinement Cache Populated... ✅ PASSED

🎉 All critical sanity checks passed.

──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

📊 Database Summary Statistics

                Table Row Counts
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Table Name                       ┃ Row Count ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ tes_condition_groupers           │       419 │
│ tes_reporting_spec_groupers      │       502 │
│ tes_condition_grouper_references │       500 │
│ refinement_cache                 │         1 │
└──────────────────────────────────┴───────────┘

```

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
