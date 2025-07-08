# Seeding the Terminology Exchange Service (TES) Data

Running the `seed_terminology_db.py` script will create and populate tables in the application's PostgreSQL database with data. These tables will then be queried to fetch condition and concept information used by the Refiner.

## Prerequisites

Before you can run the seed script, you'll need to acquire a TES API key. Make a TES account [here](https://tes.tools.aimsplatform.org/) and the `API-KEY` menu will be available to you once you log in.

## Running the script

1. Get set up to run the Refiner locally ([see here](../README.md#running-from-python-source-code))
2. Ensure dependencies have been installed (`pip install -r requirements.txt -r requirements-dev.txt`)
3. Update (or create) your `scripts/.env` file to include your TES API key. Ex: `TES_API_KEY=xxxx....`. You'll also need to ensure the scripts can access your local database by adding `DB_URL=postgresql://postgres:refiner@localhost:5432/refiner` to the file
4. Navigate into the `/scripts` directory (`cd /scripts`) and run the `seed_terminology_db.py` script with `python seed_terminology_db.py`
5. You should see the output from the script and a newly created `filters` and `groupers` tables in your database
6. You should run the `check_terminology_db.py` file to ensure both the schema and data are in the correct shape. This script will validate that the schema is correct and will run through some sample queries so you can inspect the output and verify that the data is structured correctly.

> [!TIP]
> Each time you run `check_terminology_db.py` a random sample will select new data from the database for you to inspect. You can run it as many times as you like.
