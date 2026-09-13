# Refiner Scripts

This directory contains all scripts and resources for managing the DIBBS eCR Refiner database seeding, maintenance, validation workflows, and exports. The organization is shaped to keep app-facing data, foundational test sources, validation logic, and pipeline operations clearly separated.

## Directory Purposes

| Directory      | Purpose / Contents                                                                                                 |
| -------------- | ------------------------------------------------------------------------------------------------------------------ |
| `data/`        | All data used by scripts. Includes raw source eICR/RR files, TES groupers, config samples, and generated packages. |
| `exports/`     | Scripts and ephemeral output for internal/client engagement (e.g., CSVs, CG-RSG relationships, etc).               |
| `maintenance/` | Sanity and integrity checks for DB/data (structure, relationship validation, etc).                                 |
| `pipeline/`    | Update-detection, download, and hash scripts for TES and related artifacts.                                        |
| `seeding/`     | Main logic and scripts for database seeding, typically called through orchestration/just commands.                 |
| `validation/`  | HL7 eICR/RR document validation engine, including Schematron, XSLT, and automation scripts.                        |

---

## Local Development Workflow

### Prerequisites

- Docker and Docker Compose
- Python 3.13 & `pip`
- (Recommended) `just` command runner for scripted workflows/helpers

### Step 1: Install Dependencies

```bash
just server install-dev
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

The main seeding script lives in `seeding/load_processed_data.py`. It reads the
flat tables in `refiner/tes/data/processed/` -- produced once per TES release by
`tes/normalize` -- and COPYs them into the database. It does not read the raw
FHIR bundles and has no knowledge of TES versions.

While you can run it directly with `python seeding/load_processed_data.py`, the recommended way is:

```bash
just db seed
```

But the full workflow looks like:

```bash
just dev up -d db migrate
just db clean
just migrate local
just db seed
```

or; more simply:

```bash
just dev up -d db migrate
just db refresh
```

The `just db refresh` command will combine the cleaning, migration, and seeding in one go.

### Step 5: Run Sanity Checks (Optional)

**Maintenance & Exports**

- **Maintenance scripts**: use for verifying data integrity and structure before/after seeding.
- **Exports**: use scripts in `exports/` for generating CSVs or other data artifacts to share with stakeholders.

Verification lives with the TES pipeline rather than here. After seeding, check
that the database is a faithful projection of the processed tables:

```bash
just tes verify-db        # processed data vs database; safe against a live database
just tes verify-processed # processed data vs the raw bundles it came from
just tes verify           # both, plus structural checks on the raw FHIR
```

`just tes verify-processed` also asserts the data-quality properties that used to
live in `check_seeded_db.py` -- every condition resolves to codes, self-naming
SNOMED codes belong to one condition, categories are known slugs, no valueset is
empty, and no unexpected code system is being dropped.

#### Additional `just` utility commands

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
just dev down
```
