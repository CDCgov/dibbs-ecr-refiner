# DIBBs eCR Refiner - Lambda

This package is exclusively used to build a version of the Refiner intended to run as an AWS Lambda function.

## Running the eCR Refiner Lambda in production

### Docker image

Docker images for the Lambda can be found in the [project's image registry](https://github.com/CDCgov/dibbs-ecr-refiner/pkgs/container/dibbs-ecr-refiner%2Flambda).

These images are built based on [Dockerfile.lambda](../../../Dockerfile.lambda).

### Environment variables

The Lambda accepts the following environment variables, some of which are required.

| Name                      | Description                                                                                                                     | Required | Default value      |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------ |
| `S3_BUCKET_CONFIG`        | S3 directory containing jurisdiction configuration files                                                                        | Yes      | N/A                |
| `S3_ENDPOINT_URL`         | Endpoint to use when configuring the S3 client. Primarily used for testing purposes and should not need to be set in production | No       | N/A                |
| `EICR_INPUT_PREFIX`       | S3 directory containing eICR files                                                                                              | No       | `eCRMessageV2/`    |
| `REFINER_INPUT_PREFIX`    | S3 directory containing RR files                                                                                                | No       | `RefinerInput/`    |
| `REFINER_OUTPUT_PREFIX`   | S3 directory where refined files are written                                                                                    | No       | `RefinerOutput/`   |
| `REFINER_COMPLETE_PREFIX` | S3 directory where a completion file is written by the Refiner to indicate success                                              | No       | `RefinerComplete/` |

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

## Seeding localstack for manual testing

A script accessible via `just cloud seed-localstack` is available to put Localstack in a state suitable for local testing (ie hitting the `localhost:9000` endpoint with a POST command simulating an SQS event). The same code is used by Pytest to set up our integration tests.

After containers are spun up, run `just cloud seed-localstack` to seed Localstack accordingly. If all goes well, you should see an example POST body that you can use to further invoke / manually test the Lambda.

```json
Seeding complete. Bucket: local-config-bucket
Sample SQS Event to trigger Lambda:
{
  "Records": [
    {
      "messageId": "72c00f4d-ab8a-45ad-b312-b40cba7bf70d",
      "receiptHandle": "3eb200c6-9291-4074-b7d8-e5e057f6f7b1",
      "body": "{\"version\": \"0\", \"id\": \"c2739b79-e0c4-44c1-b241-b1be983ef146\", \"detail-type\": \"Object Created\", \"source\": \"aws.s3\", \"account\": \"123456789012\", \"time\": \"2026-01-27T00:00:00Z\", \"region\": \"us-east-1\", \"resources\": [\"arn:aws:s3:::local-config-bucket\"], \"detail\": {\"version\": \"0\", \"bucket\": {\"name\": \"local-config-bucket\"}, \"object\": {\"key\": \"RefinerInput/persistence/id\"}, \"size\": 123}}",
      "attributes": {},
      "messageAttributes": {},
      "md5OfBody": "",
      "eventSource": "aws:sqs",
      "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:local-queue",
      "awsRegion": "us-east-1"
    }
  ]
}
```
