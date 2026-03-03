# Refiner Database Migrations

This directory contains all of the SQL migration scripts that are required to run against the Refiner's PostgreSQL database. Migrations are managed using [dbmate](https://github.com/amacneil/dbmate).

When migrations are applied to a database, a `schema_migrations` table will be automatically created on the first run and automatically updated on subsequent runs.

## How to run the migration scripts

When setting up a local environment, the easiest way to run the migration scripts is to run `just migrate local`. This will apply all migration scripts to the local development database.

## Creating new migration scripts

`dbmate` has the ability to generate new migration scripts that will be automatically ordered appropriately. You can create a new script by running:

```sh
just migrate new my_script_name
```

You'll see output like:

```sh
Creating migration: /app/refiner/migrations/20260227163752_my_script_name.sql
```

Fill in the `up` portion of the script with your migration's creation details and fill in the `down` portion of the script with deletion details. [See the full details of creating migrations here.](https://github.com/amacneil/dbmate?tab=readme-ov-file#creating-migrations)

## Running `down` commands

While this likely should not need to happen often, we can run `down` commands as well using:

```sh
just migrate local down
```

This will run the `down` command for the most recently created migration script.

## Database management commands

We provide several `just` commands to simplify database management during development. You can see all available database-related commands by running:

```sh
just db help
```

Typical commands include:

- `just db clean`
  Completely wipes the Refiner local development database (alias: `just db c`).

- `just db refresh`
  Runs a full database refresh (wipe, migrate, seed).

- `just db seed`
  Runs the seeding script to populate the database with condition data.

These commands use Docker Compose and scripts to reset and initialize your local development database with minimal manual intervention.
