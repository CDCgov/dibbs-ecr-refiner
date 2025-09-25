# Refiner Scripts

This directory now contains all scripts and resources for managing the DIBBS eCR Refiner database seeding, TES data pipeline operations, maintenance checks, and exports. The organization is designed to provide a complete, self-contained environment for building, running, and maintaining the PostgreSQL database used by the Refiner application.

Below you'll find an overview of the high-level structure, directory purposes, and a guide to getting started.

## Directory Structure

**Current file tree:**

```
.
├── data
│   ├── seeding
│   │   └── sample_configuration_seed_data.json
│   └── tes
│       ├── additional_context_grouper_2.0.0.json
│       ├── additional_context_grouper_3.0.0.json
│       ├── condition_grouper_1.0.0.json
│       ├── condition_grouper_2.0.0.json
│       ├── condition_grouper_3.0.0.json
│       ├── manifest.json
│       ├── reporting_spec_grouper_20241008.json
│       ├── reporting_spec_grouper_20250328.json
│       └── reporting_spec_grouper_20250829.json
├── exports
│   ├── export_groupers.py
│   └── tes-export-groupers-2025-09-24.csv
├── maintenance
│   ├── check_seeded_db.py
│   └── validate_parsing.py
├── pipeline
│   ├── detect_changes.py
│   ├── fetch_api_data.py
│   └── __init__.py
├── README.md
└── seeding
    └── seed_db.py
```

## Directory Purpose Table

| directory      | purpose                                                                                                                             | contains                                                               |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `data`           | Data required to seed the db (e.g., `conditions` table) and test data for app actions (e.g., `configurations`)                     | `tes` and `seeding`                                                    |
| `data/seeding`   | Flat files for seeding realistic test data (configurations, users, jurisdictions) matching test files used by the app               | Sample configuration seed data, sample user or jurisdiction seed data   |
| `data/tes`       | Flat files for each CG, RSG, and ACG by version, plus `manifest.json` with checksums to track updates from TES API                  | `manifest.json`, TES API-downloaded JSON files                         |
| `exports`        | Ephemeral scripts and data for internal/client engagements to help illustrate or explain database relationships                      | Scripts to understand CG-RSG relationships, CSV outputs                |
| `maintenance`    | Sanity/preflight checks (not quite unit/integration tests) to validate data structure and post-seeding relationships                | Scripts for data structure validation, seeded DB relationship checks    |
| `pipeline`       | Scripts to check for TES updates, download new files, and compute hashes to detect changes                                          | Scripts for update detection, TES downloads                            |
| `seeding`        | Database seeding script and related resources (SQL, Python), including gitignored data                                              | Seeding script, seed-data SQL                                          |

## Local Development Workflow

### Prerequisites

- Docker and Docker Compose
- Python 3.13 & `pip`

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt && pip install -r requirements-dev.txt
```

### Step 2: Fetch TES Data

> [!NOTE]
> This is not something that needs to be run very often. Typically APHL will shoot out an email about updates so this is still a fairly manual process. In the future we may create a cron style GitHub Action to perform this task.

Run the pipeline script to download the latest ValueSet data from the TES source API.
Requires a TES API key in your `.env` file.

```bash
just db fetch-tes-data
```

And once this is finished, and if and only if there are either new files or changed files, validate them prior to seeding with:

```bash
just db validate-tes-data
```

> [!NOTE]
> Since `docker compose` mounts the `refiner` directory, when you run these commands, if new files are detected they will sync with your local files. So no need to worry that running in the container will **not** update files locally. The plan for now is to update the TES files as a single PR with other changes made as necessary.

### Step 3: Build, Start, and Seed the Database

Use Docker Compose to build and start the PostgreSQL container.
On first run, this will initialize the server, apply schemas, and run the seeding script to populate the database.

The main seeding script lives in `seeding/seed_db.py`.
While you can run it directly with `python seeding/seed_db.py`, the recommended way is:

```bash
just db seed
```

But the full workflow looks like:

```bash
docker compose up -d db migrate
just db clean
just migrate local
just db seed
```

or; more simply:

```bash
docker compose up -d db migrate
just db refresh
```

The `just db refresh` command will combine the cleaning, migration, and seeding in one go.

### Step 5: Run Sanity Checks (Optional)

**Maintenance & Exports**

- **Maintenance scripts**: use for verifying data integrity and structure before/after seeding.
- **Exports**: use scripts in `exports/` for generating CSVs or other data artifacts to share with stakeholders.

There are a handful of helpful `just` commands that you can run to check that the seeding was successful but the `check_seeding` command in `maintenance` is going to contain a suite of helpful checks that we can quickly run to verify things are working as expected (and it should evolve over time):

```bash
just db check-seeding
```

The script `validate_parsing.py` is designed to run **after** you've run the TES pipeline and there are changes to the `manifest.json` file. This script will check that the structure is unchanged.

#### Additional `just` utility commands:

 ```bash
just db help
Available recipes:
    [db]
    check-condition-version VERSION                   # Check if conditions exist for a specific version (e.g., `just db check-condition-version 3.0.0`)
    check-config-combo JURISDICTION_ID CONDITION_NAME # Find configurations for a jurisdiction and condition name (e.g., `just db check-config-combo wa zika`)
    check-configs-by-jurisdiction JURISDICTION_ID     # Find all configurations for a specific jurisdiction (e.g., `just db check-configs-by-jurisdiction wa`)
    check-seeding                                     # Run all DB sanity checks (seeding, integrity, etc)
    clean                                             # Completely wipes the refiner local development database [alias: c]
    count-conditions                                  # Get the count of conditions, grouped by version
    fetch-tes-data                                    # Runs the pipeline scripts that fetch data from the TES API (you must have a TES_API_KEY in your local .env file)
    find-condition NAME                               # Find a condition by its name (case-insensitive search)
    query +QUERY                                      # Run a raw SQL query against the database (e.g., `just db query "SELECT * FROM conditions LIMIT 5;"`)
    recent-configurations                             # Show the 5 most recently created configurations
    refresh                                           # Runs a full database refresh (wipe, migrate, seed)
    seed                                              # Runs the seeding script to seed the database with condition data
    table TABLE                                       # Describe the schema of a table (e.g., `just db table conditions`)
    tables                                            # List all tables in the public schema
    validate-tes-data                                 # If new or changed file from `fetch-tes-data` are found, check that their stucture supports the seeding process.
```

Try:

```bash
# schema for all tables and an individual table
just db tables
just db table users
just db table conditions
just db table configurations
```

```bash
# make sure those 3.0.0 CGs were seeded correctly
just db check-condition-version "3.0.0"
```

```bash
# find a condition by name
just db find-condition "COVID-19"
```

### Step 6: Shutting Down

To stop and remove the database container and its data volume:

```bash
docker compose down -v
```
