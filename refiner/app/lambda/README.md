# DIBBs eCR Refiner Lambda

This package is exclusively used to build a version of the Refiner that runs as an AWS Lambda function.

## Build

The Lambda function is packaged as a Docker image and is defined by [Dockerfile.lambda](/Dockerfile.lambda).

You'll notice that this code is packaged in a way where `app` is the top level and other required modules are siblings to the `lambda` directory. The reason for this is because we want to be able to import core Refiner functionality into the Lambda module in the same way that we do for the FastAPI version of the Refiner, which this structure mirrors.

This Docker image is built and pushed automatically when a branch is merged into `main` as part of the [Build and push Refiner image to GHCR](/.github/workflows/docker-build-ghcr.yml) job.
