# DIBBs eCR Refiner

> [!TIP]
> This project leverages `just` as a command runner. To learn more about `just`
> view the documentation at: [https://just.systems/man/en](). Run `just help`
> for a list of commands.

The DIBBs eCR Refiner reduces eICR and RR files down to only the most useful, necessary information to alleviate performance and storage burden on eCR data pipelines and disease surveillance systems and bring focus to pertinent data for a given reportable condition.

For more detailed information about the relationship between the eICR and RR documents and what informs the design of the eCR Refiner please see [this document](/refiner/eCR-CDA-Notes.md).

## Running the project locally

The Refiner is a containerized application and can be easily run using [Docker](https://www.docker.com/). With Docker installed, run the following command from the top-level directory containing the `.docker-compose.yaml` file:

```sh
just dev up -d
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

- `username`: refiner
- `password`: refiner

You should be redirected to the configurations page upon successful login.

## Running the eCR Refiner application in production

The eCR Refiner requires the following environment variables to be specified in order to run the application:

- `ENV`: The environment name (`local`, `dev`, `test`, `prod`, etc.)
- `DB_URL`: The PostgreSQL connection string
- `SESSION_SECRET_KEY`: A string used to compute user session hashes that are stored in the `sessions` table
- `AUTH_PROVIDER`: Name of the OIDC authentication provider (`keycloak`, `google`, etc.)
- `AUTH_CLIENT_ID`: OIDC client ID
- `AUTH_CLIENT_SECRET`: OIDC client secret string
- `AUTH_ISSUER`: OIDC auth issuer string
- `AWS_ACCESS_KEY_ID`: The access key for your AWS account
- `AWS_SECRET_ACCESS_KEY`: The secret key for your AWS account
- `AWS_REGION`: The AWS region to use
- `S3_UPLOADED_FILES_BUCKET_NAME`: Name of the S3 bucket that holds user-uploaded eICR/RR pairs

Examples of the required environment variables can be seen in the project's [docker-compose.yaml](./docker-compose.yaml) file under `refiner-service`.

## Creating a production build

The DIBBs eCR Refiner runs entirely within a single container in a production environment. All build versions, including the very latest, can be downloaded from the [Refiner's GitHub Container Registry](https://github.com/CDCgov/dibbs-ecr-refiner/pkgs/container/dibbs-ecr-refiner).

### Automatic builds

A production-ready Docker image is created automatically every time code is merged into `main`. The Docker image produced will be tagged as both `main` and `latest`.

### Manually creating a production build

A production build of the application can be created using the [`Build and push Refiner image to GHCR`](https://github.com/CDCgov/dibbs-ecr-refiner/actions/workflows/docker-build-ghcr.yml) GitHub Actions workflow. This will build the image and will store it in the Refiner's GitHub Container Registry.

## Running the linter

The linter can be run two different ways: either manually via the `ruff` command or automatically when you go to create a new commit, which is powered by `pre-commit`.

### Manually

1. Activate the `refiner` virtual environment (steps listed [here](./refiner/README.md#running-from-python-source-code))
2. Install dev dependencies with `pip install -r requirements.txt -r requirements-dev.txt`
3. Run any `ruff` command you'd like (see [here](https://docs.astral.sh/ruff/linter/))

### Pre-commit

1. Install [pre-commit](https://pre-commit.com/)
2. Run `pre-commit install`
3. Run `pre-commit run --all-files` to check that the tool is working properly

The `pre-commit` hook will automatically fix any linter issues and will also format the code.

## Type checking

The Refiner's Python server code is type checked using `mypy`. Activate your virtual environment and install all dependencies (using the directions above) and run `mypy` in your terminal within the `refiner` directory.
