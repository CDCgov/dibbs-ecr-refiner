# Refiner Database Migrations

This directory contains all of the SQL migration scripts that are required to run against the Refiner's PostgreSQL database. Migrations are managed using [migrate](https://github.com/golang-migrate/migrate).

When migrations are applied to a database, a `schema_migrations` table will be automatically created on the first run and automatically updated on subsequent runs.

## How to run the migration scripts

When setting up a local environment, the easiest way to run the migration scripts is to run `just migrate local`. This will apply all migration scripts to the local development database.

## Creating new migration scripts

`migrate` has the ability to generate new migration scripts that will be automatically ordered appropriately. You can create a new up/down script pair by running `just migrate create my_script_name`.

You'll see an output that looks something like this:

```sh
/app/refiner/migrations/000002_my_script_name.up.sql
/app/refiner/migrations/000002_my_script_name.down.sql
```

Fill in the `up` script with your migration's creation details and fill in the `down` script with deletion details.

## Running "down" commands

While this likely should not need to happen often, we can run `down` commands as well using `just migrate local down 1`. This will run the `down` command for the most recently created migration script.
