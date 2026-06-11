# Operations

## Environment variables

| Name          | Description                 | Required | Default value |
| ------------- | --------------------------- | -------- | ------------- |
| `DB_URL`      | The PostgreSQL database URL | Yes      | N/A           |
| `DB_PASSWORD` | The PostgreSQL password     | Yes      | N/A           |
| `SSL_MODE`    | PostgreSQL `sslmode` value  | No       | `require`     |

## entrypoint.sh

The `entrypoint.sh` file in this directory is used as the entrypoint for the `Dockerfile.ops` container image. This exists to create an `ops` container that is capable of running Refiner operational tasks in CI, such as:

- Running migration software and applying changes to database schema
- Running TES data seeding/updating scripts

This script does the following:

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

## Running the `ops` container against the Azure demo environment

To run the ops image against the Skylight DIBBs demo environment, make sure you have the correct ops image installed locally from which to run the commands. For example, if you're deploying tagged image 0.0.12, make sure the ops image tag matches the tag for the image you're seeking to deploy.

You'll also need the DB demo creds. Get this from a developer on the team.

You'll also need to check that your local IP address is allowlist in [the global DB firewall settings.](https://portal.azure.com/?l=en.en-us#@skylighthq.onmicrosoft.com/resource/subscriptions/6848426c-8ca8-4832-b493-fed851be1f95/resourceGroups/skylight-dibbs-global/providers/Microsoft.DBforPostgreSQL/flexibleServers/dibbs-global-postgres/networking). To do so

1. Navigate to the DIBBs global postgres database (or the equivalent DB that is supporting the demo environment)
1. Navigate to Settings > Networking
1. Confirm that your IP address is listed in the allowlist. If not, add it and hit save! Note the handy "add current client IP address" option.
1. From there, you should be able to access the DB connection locally to run the relevant ops container commands.
