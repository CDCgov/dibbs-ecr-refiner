# Database for DIBBs eCR Refiner

This directory contains everything needed to create and test a self-contained PostgreSQL database environment for the DIBBS eCR Refiner.

The database is designed with a trigger-based automation pipeline to pre-calculate and cache refined code sets, ensuring high performance for the main application.

## Core Concepts

The data pipeline works in two stages, automated by database triggers:

1.  **Aggregation (Trigger 1):** When child `tes_reporting_spec_groupers` are linked to a parent `tes_condition_grouper` (or when the data in a child grouper is updated), this trigger fires. It aggregates all unique codes (LOINC, SNOMED, etc.) from all children into the parent's `jsonb` columns.

2.  **Refinement & Caching (Trigger 2):** This is the final and most critical step. The trigger populates the `refinement_cache` by combining the aggregated "base" codes from a parent grouper with the jurisdiction-specific codes from a user's `configuration`. This trigger is designed to fire in two distinct scenarios:
    *   **Directly**, when a user creates, updates, or deletes a record in the `configurations` table.
    *   **Indirectly**, when Trigger 1 updates a parent `tes_condition_grouper`. This change cascades, causing Trigger 2 to re-evaluate and update the cache for every single configuration linked to that parent.

## Prerequisites

*   Docker and Docker Compose
*   Python 3.10+
*   `pip` for installing Python packages

## Quickstart: Setup and Testing

To spin up the database and verify that the entire trigger pipeline is working correctly, follow these steps.

### 1. Install Dependencies

Install the required Python packages (currently just `psycopg` and `python-dotenv`).

```bash
pip install -r requirements.txt && pip install -r requirements-dev.txt
```

### 2. Start the Database

Use Docker Compose to build the PostgreSQL container. This command will also create the database schema and apply the triggers from the `schema/` and `triggers/` directories.

```bash
docker compose up -d
```

You can check the status of the container to ensure it's running and healthy:

```bash
docker ps
```

### 3. Run Unit Tests (Optional)

The project includes a simple `pytest` suite that verifies a connection to the database can be established. This is a quick way to check that your environment is configured correctly after starting the container.

Then, run the tests:

```bash
pytest -vv tests
```

### 4. Run the Full Integration Test

The `seed.py` script performs a full, end-to-end integration test of the data pipeline. It will:
1.  Wipe all existing data.
2.  Seed fictional, non-real data for jurisdictions, users, and base condition groupers.
3.  Fire **Trigger 1** by linking the test groupers and verify the result.
4.  Fire **Trigger 2** by creating a test user configuration and verify the cache.
5.  Simulate an update to the base data, which re-fires the trigger chain.
6.  Verify the cache was correctly and automatically updated after the change.

Execute the script from the `database` directory:

```bash
python seed.py
```

A successful run will end with the following message:

```
🎉 Success! The cache was correctly updated after a change to the base data
```

### 5. Shutting Down

To stop and remove the database container and its associated volume (deleting all data), run:

```bash
docker compose down -v
```
