# DIBBs eCR Refiner

> [!TIP]
> This project leverages `just` as a command runner. To learn more about `just`
> [view the documentation](https://just.systems/man/en). Run `just help` for a
> list of commands.

The DIBBs eCR Refiner reduces eICR and RR files down to the most useful, necessary information to alleviate performance and storage burden on eCR data pipelines and disease surveillance systems and bring focus to pertinent data for a given reportable condition.

For more detailed information about the relationship between the eICR and RR documents and what informs the design of the eCR Refiner please see [this document](/refiner/eCR-CDA-Notes.md).

## Running the project locally

> [!TIP]
> When running containers locally on macOS or Windows, please ensure your host
> VM's defaults are increased. _Specifically, CPU cores must be set to 2 cores
> or above, Memory must be set at least 4 GiB, and Disk should be at least 100
> GiB_. These changes will ensure that all scripting and application code run
> correctly without issues.

The Refiner is a containerized application and can be easily run using [Docker](https://www.docker.com/). With Docker installed, run the following command from the top-level directory containing the `docker-compose.yml` file:

```sh
just dev up -d
```

or

```sh
docker compose up -d
```

Next run the database migrations:

```sh
just migrate local
```

Lastly, seed the database with the required condition data:

```sh
just db seed
```

The application can be accessed in your browser at [http://localhost:8081/](http://localhost:8081/). The sample user login credentials are:

- `username`: `refiner`
- `password`: `refiner`

There is also secondary user that is setup locally with the following
credentials:

- `username`: `refiner2`
- `password`: `refiner2`

You should be redirected to the configurations page upon successful login.

### Docker Compose setup

The Refiner has three Docker compose files:

1. `docker-compose.yml` - This is the base configuration shared by the other two files
2. `docker-compose.override.yml` - This is the override file used for the local development environment
3. `docker-compose.ci.yml` - This is a "CI" file used to run an environment that is closer to being production-like. It makes use of the `Dockerfile.app` image and the `Dockerfile.ops` image

Running `docker compose up` will automatically merge `docker-compose.yml` and `docker-compose.override.yml`.

#### Running the CI environment locally

If you'd like to run the CI environment locally for any reason, we can run the following command:

```sh
docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d
```

## Running the eCR Refiner application in production

The eCR Refiner requires the following environment variables to be specified in order to run the application.

### Web application

| Name | Description | Required | Default value |
| --- | --- | --- | --- |
| ENV | The environment name (`local`, `dev`, `test`, `prod`, etc.) | Yes | N/A |
| DB_URL | The PostgreSQL connection string | Yes | N/A |
| DB_PASSWORD | The PostgreSQL password | Yes | N/A |
| SESSION_SECRET_KEY | Used to compute user session hashes stored in the `sessions` table | Yes | N/A |
| AUTH_PROVIDER | Name of the OIDC authentication provider (`keycloak`, `google`, `fusionauth`, etc.) | Yes | N/A |
| AUTH_CLIENT_ID | OIDC client ID | Yes | N/A |
| AUTH_CLIENT_SECRET | OIDC client secret string | Yes | N/A |
| AUTH_ISSUER | OIDC authentication issuer string | Yes | N/A |
| AWS_REGION | The AWS region to use | Yes | N/A |
| S3_BUCKET_CONFIG | Name of the S3 bucket holding condition configurations | Yes | N/A |
| LOG_LEVEL | Controls application log output verbosity | No | N/A |

Examples of the required environment variables can be seen in the project's [docker-compose.yaml](./docker-compose.yaml) file under `server`.

### Lambda

Please refer to the [Lambda README](./refiner/app/lambda/README.md).

### Ops (Maintenance tasks)

Please refer to the [Ops README](./ops/README.md).

## Creating a production build

The DIBBs eCR Refiner runs entirely within a single container in a production environment. All build versions, including the very latest, can be downloaded from the [Refiner's GitHub Container Registry](https://github.com/CDCgov/dibbs-ecr-refiner/pkgs/container/dibbs-ecr-refiner).

### Automatic builds

A production-ready Docker image is created automatically every time code is merged into `main`. The Docker image produced will be tagged as both `main` and `latest`.

### Manually creating a production build

A production build of the application can be created using the [`Build and push Refiner image to GHCR`](https://github.com/CDCgov/dibbs-ecr-refiner/actions/workflows/docker-image-push.yml) GitHub Actions workflow. This will build the image and will store it in the Refiner's GitHub Container Registry.

## Running the linter

The linter can be run two different ways: either manually via the `ruff` command or automatically when you go to create a new commit, which is powered by `pre-commit`.

### Manually

1. Activate the `refiner` virtual environment (steps listed [in the run from source instructions](./refiner/README.md#running-from-python-source-code))
2. Install dev dependencies with `pip install -r requirements.txt -r requirements-dev.txt`
3. Run any `ruff` command you'd like (see [the ruff documentation for more details](https://docs.astral.sh/ruff/linter/))

### Pre-commit

1. Install [pre-commit](https://pre-commit.com/)
2. Run `pre-commit install`
3. Run `pre-commit run --all-files` to check that the tool is working properly

The `pre-commit` hook will automatically fix any linter issues and will also format the code.

## Type checking

The Refiner's Python server code is type checked using `mypy`. Activate your virtual environment and install all dependencies (using the directions above) and run `mypy` in your terminal within the `refiner` directory.
