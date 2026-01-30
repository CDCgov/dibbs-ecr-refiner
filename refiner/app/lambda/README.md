# DIBBs eCR Refiner - Lambda

This package is exclusively used to build a version of the Refiner intended to run as an AWS Lambda function.

## Running the eCR Refiner Lambda in production

### Docker image

Docker images for the Lambda can be found in the [project's image registry](https://github.com/CDCgov/dibbs-ecr-refiner/pkgs/container/dibbs-ecr-refiner%2Flambda).

These images are built based on [Dockerfile.lambda](../../../Dockerfile.lambda).

### Environment variables

The Lambda accepts the following environment variables, some of which are required.

| Name | Description | Required | Default value |
| --- | --- | --- | --- |
| `S3_BUCKET_CONFIG` | S3 directory containing jurisdiction configuration files | Yes | N/A |
| `S3_ENDPOINT_URL` | Endpoint to use when configuring the S3 client. Primarily used for testing purposes and should not need to be set in production | No | N/A |
| `EICR_INPUT_PREFIX` | S3 directory containing eICR files | No | `eCRMessageV2/` |
| `REFINER_INPUT_PREFIX` | S3 directory containing RR files | No | `RefinerInput/` |
| `REFINER_OUTPUT_PREFIX` | S3 directory where refined files are written | No | `RefinerOutput/` |
| `REFINER_COMPLETE_PREFIX` | S3 directory where a completion file is written by the Refiner to indicate success | No | `RefinerComplete/` |

## File structure and build

You'll notice that this code is packaged in a way where `app` is the top-level and other required modules are siblings to the `lambda` directory. The reason for this is because we want to be able to import core Refiner functionality into the Lambda module in the same way that we do for the FastAPI version of the Refiner, which this structure mirrors exactly.

This Docker image, along with [Dockerfile.app](/Dockerfile.app), is built, tagged, and pushed automatically when a branch is merged into `main` as part of the [Build and push Refiner image to GHCR](/.github/workflows/docker-image-push.yml) job.

## Building the Docker image locally

The Docker image can be built with the following command:

```sh
docker compose build --no-cache lambda
```

## Running the Docker container locally

The Lambda Docker container starts up as part of the project's [Docker Compose file](../../../docker-compose.yaml). When the container is running it will accept HTTP requests at the following endpoint:

`http://localhost:9000/2015-03-31/functions/function/invocations`

This endpoint can be requested using an HTTP client of your choice in order to invoke the Lambda function. Note that the Lambda function expects an SQS-style JSON event as part of the request. Please refer to the [Lambda integration tests](../../tests/integration/test_lambda.py) for an example event.
