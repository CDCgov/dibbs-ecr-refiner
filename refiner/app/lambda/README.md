# DIBBs eCR Refiner - Lambda

This package is exclusively used to build a version of the Refiner intended to run as an AWS Lambda function.

## Running the eCR Refiner Lambda in production

### Docker image

Docker images for the Lambda can be found in the [project's image registry](https://github.com/CDCgov/dibbs-ecr-refiner/pkgs/container/dibbs-ecr-refiner%2Flambda).

These images are built based on [Dockerfile.lambda](../../../Dockerfile.lambda).

### Environment variables

The Lambda accepts the following environment variables, some of which are required.

| Name                      | Description                                                                                                                     | Required |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `S3_BUCKET_CONFIG`        | S3 directory containing jurisdiction configuration files                                                                        | Yes      |
| `S3_ENDPOINT_URL`         | Endpoint to use when configuring the S3 client. Primarily used for testing purposes and should not need to be set in production | No       |
| `EICR_INPUT_PREFIX`       | S3 directory containing eICR files                                                                                              | Yes      |
| `REFINER_INPUT_PREFIX`    | S3 directory containing RR files                                                                                                | Yes      |
| `REFINER_OUTPUT_PREFIX`   | S3 directory where refined files are written                                                                                    | Yes      |
| `REFINER_COMPLETE_PREFIX` | S3 directory where a completion file is written by the Refiner to indicate success                                              | Yes      |

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

## Seeding Localstack for manual testing

A script accessible via `just server seed-localstack` is available to put Localstack in a state suitable for local testing (ie hitting the `localhost:9000` endpoint with a POST command simulating an SQS event). The same code is used by Pytest to set up our integration tests.

After containers are spun up, run `just server seed-localstack` to seed Localstack accordingly. If all goes well, you should see an example POST body that you can use to further invoke / manually test the Lambda.

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

## Refinement pipeline architecture

The Refiner has two entry points that both need to produce identical refinement results:

- **Webapp** (`testing.py`): Interactive validation where a logged-in user tests an eICR/RR pair against a configuration resolved from the database.
- **Lambda** (`lambda_function.py`): Production refinement where an incoming eICR/RR pair is refined against configurations resolved from S3.

Both entry points share a common refinement pipeline defined in `app/services/pipeline.py`. The pipeline exposes two stages:

1. **Discovery** (`discover_reportable_conditions`): Parses the RR to extract which conditions are reportable and to which jurisdictions. Both the webapp and Lambda call this identically.
2. **Refinement** (`refine_for_condition`): Takes a `ProcessedConfiguration` and an eICR/RR pair, creates refinement plans, and executes them. The refined output is identical regardless of how the configuration was sourced.

### The activation bridge

The connection between the webapp and Lambda is the activation step. When a user activates a configuration in the webapp, `convert_config_to_storage_payload` in `app/services/configurations.py` serializes the configuration to S3. This includes both a flat `codes` list (for backward compatibility with the generic matching path) and a structured `code_system_sets` field (for section-aware matching). Lambda reads this file at runtime and deserializes it back into the same data structures the webapp uses.

The S3 file structure for a jurisdiction's configuration:

- `configurations/<jurisdiction_id>/rsg_cg_mapping.json` — maps RSG SNOMED codes to condition grouper names and canonical URLs
- `configurations/<jurisdiction_id>/<canonical_url_uuid>/current.json` — points to the active version number (supports rollback)
- `configurations/<jurisdiction_id>/<canonical_url_uuid>/<version>/active.json` — the serialized configuration used for refinement

### Unrefined conditions RR

When the RR contains reportable conditions for a jurisdiction but only some have active configurations, conditions that go through full refinement get their own refined eICR and RR. The remaining conditions (those without active configurations) still need their reportability information preserved. The `create_unrefined_conditions_rr` function in `app/services/ecr/refine.py` produces a filtered RR containing only those unrefined conditions. This prevents downstream systems from seeing duplicate condition information when they receive the full output package.

### Observability

Both entry points use `RefinementTrace` objects (defined in `pipeline.py`) to track what happened during refinement. Each trace captures the jurisdiction, condition code, whether a configuration was resolved, the refinement outcome (refined, skipped, or error), and the skip reason if applicable. Lambda logs a summary of all traces at the end of each invocation.

### Stage and Role metadata

Every function and class in `lambda_function.py` has a docstring with `Stage:`
and `Role:` metadata fields. These drive the auto-generated [Lambda Function
Reference docs](/docs/reference/lambda/) - they determine which pipeline stage a
function appears under and what color-coded role badge it gets.

> [!IMPORTANT]
> Without these specific metadata fields, the `just docs::sync` command will
> fail and local docs will not be able to render. Please keep this in mind when
> you disregard adding the metadata fields.

#### Conventions

**Stage** = where in the pipeline the function logically belongs (not where it's
called from).

| Stage                   | When to use                                                                  |
| ----------------------- | ---------------------------------------------------------------------------- |
| `Entry`                 | Guard checks before any pipeline processing (lock checks, environment setup) |
| `S3 Retrieval`          | Reading data from S3 (GET, HEAD, JSON parse of S3 content)                   |
| `Configuration Loading` | Reading mapping files, `current.json`, `active.json` from config bucket      |
| `Refinement Pipeline`   | Orchestration functions that drive the refinement process                    |
| `Output Writing`        | Writing refined results back to S3 (refined eICR/RR, remainder RRs)          |
| `Skip/Error Handling`   | Functions that mark conditions as skipped or raise/handle refinement errors  |
| `Types`                 | Data types, dataclasses, TypedDicts, exception classes, enums                |

**Role** = the functional responsibility.

| Role             | When to use                                                        |
| ---------------- | ------------------------------------------------------------------ |
| `Handler`        | Entry point orchestration, Lambda handler logic                    |
| `S3 I/O`         | Direct S3 API calls (GET, HEAD, PUT, JSON parse)                   |
| `Configuration`  | Reading and interpreting configuration data                        |
| `Orchestrator`   | Coordinating multi-step refinement across jurisdictions/conditions |
| `Output`         | Writing output artifacts to S3                                     |
| `Error Handling` | Exception types, skip logic, error manifests                       |
| `Data Type`      | Classes, TypedDicts, enums, dataclasses                            |

#### When to update

Add or update `Stage:` / `Role:` in a docstring whenever you:

1. **Add a new function or class** to `lambda_function.py` - it won't appear in
   the function reference docs without these fields.
2. **Change what a function does** - if its primary responsibility shifts to a
   different pipeline stage, update both fields.
3. **Introduce a new stage or role** - add it to
   `docs/_includes/lambda-stage-data.liquid` in the `stageOrder` and
   `roleColors` arrays.

#### Auto-extraction pipeline

A docstring parser scans `lambda_function.py` and writes the results to
`docs/_data/lambda-api.json`. The site reads `stage` and `role` from this JSON
to group functions and assign badge colors. The parser looks for literal
`Stage:` and `Role:` at the start of a line with the value on the next indented
line:

```
Stage:
    My Stage
Role:
    My Role
```

After updating `lambda_function.py`, regenerate the JSON with `just docs::sync`
or have it continuously updated with `just docs::serve`.

#### Diagram

The pipeline diagram at `docs/reference/lambda/diagram/` is maintained by hand
using [asciiflow.com](https://asciiflow.com). You can find the link to the
current diagram in an HTML comment within the Liquid template
(`docs/reference/lambda/diagram/index.liquid`). Please update this diagram when
the high-level flow changes (new branches, new pipeline stages). Internal helper
renames don't require diagram changes.
