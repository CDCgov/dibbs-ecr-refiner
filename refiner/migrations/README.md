# Refiner Database Migrations

This directory contains all of the SQL migration scripts that are required to run against the Refiner's PostgreSQL database. Migrations are managed using [migrate](https://github.com/golang-migrate/migrate).

When migrations are applied to a database, a `schema_migrations` table will be automatically created on the first run and automatically updated on subsequent runs.

## How to run the migration scripts

When setting up a local environment, the easiest way to run the migration scripts is to run `just migrate local`. This will apply all migration scripts to the local development database.

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

## Creating new migration scripts

`migrate` has the ability to generate new migration scripts that will be automatically ordered appropriately. You can create a new up/down script pair by running:

```sh
just migrate create my_script_name
```

You'll see output like:

```sh
/app/refiner/migrations/000002_my_script_name.up.sql
/app/refiner/migrations/000002_my_script_name.down.sql
```

Fill in the `up` script with your migration's creation details and fill in the `down` script with deletion details.

## Running "down" commands

While this likely should not need to happen often, we can run `down` commands as well using:

```sh
just migrate local down 1
```

This will run the `down` command for the most recently created migration script.

## Migration Strictness and Failure Policy

**Intentional Omission of `IF EXISTS` and Loud Failure Mode**

As a team, we have intentionally chosen **not** to use `IF EXISTS` (or `IF NOT EXISTS`) clauses in our migration scripts. This means that if a migration attempts to drop or modify an object that does not exist, the migration will fail loudly and immediately.

We do this to maximize auditability, enforce a single source of truth for database state, and ensure that any accidental drift, manual intervention, or missed migration is caught right away. This approach helps maintain strict consistency between our migrations and the database schema, and ensures that all changes are intentional and tracked.

If you encounter a migration failure due to a missing object, it is a signal that the database is not in the expected state and should be investigated and corrected rather than bypassed.
