# Operations

## entrypoint.sh

The `entrypoint.sh` file in this directory is used as the entrypoint for the `Dockerfile.ops` container image. This exists to create an `ops` container that is cable of running Refiner operational tasks in CI, such as:

- Running migration software and applying changes to database schema
- Running TES seeding/updating scripts

The `entrypoint.sh` file handles the following:

- Guarantees `DB_URL` and `DB_PASSWORD` variables are present in the environment
- Automatically assembles a `DATABASE_URL` compatible with `migrate`
- Provides simple commands to run for common tasks
  - `migrate`
  - `import`
  - `python`
  - `prepare-db`
- Allows for custom commands

## Using the `ops` container

The `ops` container image builds can be found in [Refiner's GHCR](https://github.com/CDCgov/dibbs-ecr-refiner/pkgs/container/dibbs-ecr-refiner%2Fops).

The most common production task will be to run migrations and seed the database. We can do that with this single command:

```sh
docker run \
  -e DB_URL=postgresql://postgres@localhost:5432/refiner \
  -e DB_PASSWORD=refiner \
  ops prepare-db
```

We can run migration commands independently as well:

```sh
docker run \
  -e DB_URL=postgresql://postgres@localhost:5432/refiner \
  -e DB_PASSWORD=refiner \
  ops migrate up
```

We are also able to seed the database with TES data independently:

```sh
docker run \
  -e DB_URL=postgresql://postgres@localhost:5432/refiner \
  -e DB_PASSWORD=refiner \
  ops import
```
