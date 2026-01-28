# DIBBs eCR Refiner - Lambda

This package is exclusively used to build a version of the Refiner intended to run as an AWS Lambda function.

## Running the eCR Refiner Lambda in production

### Environment variables

| Name | Description | Required | Default value |
| --- | --- | --- | --- |
| `S3_BUCKET_CONFIG` | S3 directory containing jurisdiction configuration files | Yes | N/A |
| `EICR_INPUT_PREFIX` | S3 directory containing eICR files | No | `eCRMessageV2/` |
| `REFINER_INPUT_PREFIX` | S3 directory containing RR files | No | `RefinerInput/` |
| `REFINER_OUTPUT_PREFIX` | S3 directory where refined files are written | No | `eCRMessageV2/` |
| `REFINER_COMPLETE_PREFIX` | S3 directory where a completion file is written by the Refiner to indicate success | No | `eCRMessageV2/` |

## Build & File Structure

The Lambda function is packaged as a Docker image and is defined by [Dockerfile.lambda](/Dockerfile.lambda).

You'll notice that this code is packaged in a way where `app` is the top-level and other required modules are siblings to the `lambda` directory. The reason for this is because we want to be able to import core Refiner functionality into the Lambda module in the same way that we do for the FastAPI version of the Refiner, which this structure mirrors exactly.

This Docker image, along with [Dockerfile.app](/Dockerfile.app), is built, tagged, and pushed automatically when a branch is merged into `main` as part of the [Build and push Refiner image to GHCR](/.github/workflows/docker-image-push.yml) job.
