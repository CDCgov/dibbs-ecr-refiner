# 11. Updating Active Configs in S3

**Date:** 2026-06-24  
**Status:** Accepted

## Context and Problem Statement

The Refiner writes an `active.json` file to S3 whenever a configuration is activated. Lambda later reads that file and validates it with `ProcessedConfiguration.from_dict()` before using it to refine incoming eCRs.

As the application changes, the expected shape of `active.json` may also change. An older active file can then become incompatible with the current Lambda code. When that happens, Lambda fails while loading the configuration and refinement stops for that condition.

The current workaround is for a user to deactivate and reactivate the configuration so the application writes a new `active.json` file. This is not a reliable production solution because users may not know the file is incompatible, the application does not currently surface the issue, and the team does not have visibility into which configurations are failing.

`active.json` should be treated as a generated artifact. Postgres remains the source of truth for the configuration, while S3 stores the generated payload used by Lambda.

## Decision Drivers

The solution should:

- Keep Postgres as the source of truth.
- Avoid requiring users to manually deactivate and reactivate configurations.
- Prevent incompatible active files from stopping refinement without a clear error.
- Reuse the same payload generation logic as the normal activation flow.
- Avoid adding recurring background work to the app container.
- Avoid changing the existing configuration version or activation history.
- Keep the current Lambda lookup flow based on `current.json` and the configuration version.
- Give the team visibility when a migration is missed or an incompatible file is found.
- Be reusable when the `active.json` format changes again in the future.
- Avoid unnecessary S3 writes when the current `active.json` schema has already been applied.
- Account for the application, Lambda, and ops containers running concurrently during deployment.

## Considered Options

### Option 1: Allow the app to re-activate configurations

The app already has access to Postgres and can write configuration files to S3. However, this would add extra work to the application and could affect normal app performance.

It is also unclear what would trigger the app to rebuild the files. The app does not currently receive information about Lambda failures, so this would likely require a scheduled job that repeatedly scans active configurations.

### Option 2: Allow the ops container to update active files

The ops container can run a migration after database migrations and TES data loading are complete. It can query Postgres for active configurations, rebuild their activation payloads, and overwrite the existing files in S3.

This requires the ops container to have access to Postgres and permission to read and write configuration artifacts in S3. It should reuse the same payload generation and upload functions as the normal activation endpoint so the logic is not duplicated.

### Option 3: Change the storage format

Changing from JSON to another file format would not solve the main problem. The issue is that the expected schema can change between software versions.

Any storage format would still need schema versioning, compatibility checks, and a migration strategy.

### Option 4: Add infrastructure dedicated to this task

A separate Lambda or another service could rebuild active files. This would isolate the work from the app, but it would add more infrastructure to deploy, monitor, and maintain.

It would also still need access to Postgres, S3, and the same activation logic already used by the app.

## Decision Outcome

Use the ops container to run an active configuration migration whenever the `active.json` schema changes.

The migration will treat `active.json` as a generated artifact and rebuild it from the configuration data in Postgres. It will not transform the existing S3 JSON directly.

### Add explicit schema versioning

Every newly generated `active.json` file should declare the schema it uses:

```json
{
  "schema_version": 2,
  "sections": [],
  "included_condition_rsg_codes": [],
  "code_system_sets": {}
}
```

This version is only for the shape of `active.json`. It is separate from the existing configuration version used in the S3 path and `current.json`.

Lambda should validate this value after loading the file. If the version is not supported, it should raise and log a clear compatibility error instead of only returning a Pydantic validation error.

```py
if data.get("schema_version") != CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION:
    raise IncompatibleActiveConfigurationError(...)
```

The current schema version should be defined as a shared constant in code:

```py
CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION = 2
```

This constant should be used by both the payload generation code and Lambda validation so that the supported version is defined in one place.

### Track the applied schema version

To avoid rewriting every active configuration during each deployment, Postgres should track the most recently applied active payload schema version.

Before starting the regeneration, the ops container should compare the successfully applied schema version in Postgres with `CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION`. If they match, the migration can log that no work is required and exit without rewriting the S3 files.

The tracking record should include the schema version, migration status, start and completion times, and success and failure counts. Suggested statuses are:

* `IN_PROGRESS`
* `COMPLETE`
* `PARTIAL_FAILURE`
* `FAILED`

Only a migration marked `COMPLETE` should be treated as successfully applying the schema version.

### Reuse the existing activation functions

The activation endpoint already uses the functions needed to rebuild the S3 artifacts:

```py
convert_config_to_storage_payload()
get_config_payload_metadata()
upload_configuration_payload()
```

The ops migration should import and call these functions directly. It should not call the activation endpoint over HTTP.

The migration should not call:

```py
activate_configuration_db()
upload_condition_mapping_payload()
upload_current_version_file()
```

The configuration is already active, so the migration should not change its status, activation history, configuration version, condition mapping, or `current.json`.

### Deployment race condition

The application, Lambda, and ops containers may be deployed or started at approximately the same time. The implementation should not rely on the ops migration finishing before the new Lambda code begins processing messages.

The migration will create a temporary maintenance-lock object in the configuration S3 bucket before updating active files. Lambda will check for this lock before processing each SQS record. If the lock is active, Lambda will return the record through `batchItemFailures` without writing a fatal `RefinerComplete` file.

The SQS visibility timeout and retry behavior will act as a buffer during the migration. Messages received while the lock is active will return to the queue and be retried after the migration finishes.

There is still a small race where a Lambda invocation may check for the lock immediately before it is created. The ops migration should therefore wait for existing Lambda executions to drain before overwriting any active files.

### Migration flow

```text
Ops container starts
    ↓
Database migrations run
    ↓
TES data is loaded
    ↓
Compare the applied schema version in Postgres with
CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION
    ↓
If they match, log that no migration is required and exit
    ↓
Record the migration as IN_PROGRESS
    ↓
Create the S3 maintenance lock
    ↓
Wait for existing Lambda executions to drain
    ↓
Query active configurations from Postgres
    ↓
Rebuild each active.json using current code
    ↓
Overwrite the existing active.json in S3
    ↓
Record the final migration status
    ↓
Remove the maintenance lock after a successful migration
```


For each active configuration, the migration should:

1. Load the active configuration from Postgres.
2. Build the current payload with `convert_config_to_storage_payload()`.
3. Build the metadata with `get_config_payload_metadata()`.
4. Upload the files with `upload_configuration_payload()`.
5. Log whether the rebuild succeeded or failed. A failure for one configuration should not prevent the migration from attempting the remaining active configurations.

The regenerated payload should be written to the same S3 key:

```text
configurations/{jurisdiction}/{condition_uuid}/{configuration_version}/active.json
```

The existing file does not need to be deleted first. Writing to the same S3 key replaces the object.

The existing configuration version and `current.json` stay unchanged. Lambda continues loading the same path it uses today.

### Logging and observability

The migration should log:

- configuration ID
- configuration version
- jurisdiction
- condition UUID
- S3 key
- schema version written
- migration success or failure

Lambda should log similar information when it finds a missing, invalid, or incompatible active file, including the expected and actual schema versions.

If an individual configuration fails to rebuild, the migration should log a critical error for that configuration and continue processing the remaining configurations.

After all configurations have been attempted:

* Mark the migration `COMPLETE` if all configurations succeeded.
* Mark it `PARTIAL_FAILURE` if only some configurations succeeded.
* Mark it `FAILED` if the migration could not run successfully.

A `PARTIAL_FAILURE` should trigger an alert for manual intervention. The maintenance lock should remain in place after a partial or complete failure so Lambda does not resume processing while incompatible configurations may still exist.

This gives the team visibility if a migration is missed or fails in production.

### Why this option was selected

This option best matches the decision drivers because:

- Postgres remains the source of truth.
- Users do not need to manually reactivate configurations.
- The app does not need a recurring background job.
- Lambda does not need to support multiple active files or choose between schema-specific paths.
- Existing configuration versions and `current.json` behavior stay the same.
- The migration reuses the normal activation payload generation and upload logic.
- The configuration's active status and history are not changed.
- Schema versioning and logging make future compatibility problems easier to detect and migrate.

## Appendix

### Suggested Implementation Tickets

#### `feat: add active payload schema version`

Add a `schema_version` field to newly generated `active.json` files and define the current supported schema version.

#### `feat: validate active configuration schema version`

Update Lambda to validate `schema_version` before processing an active configuration and return a clear compatibility error when the version is unsupported.

#### `feat: add active configuration compatibility logging`

Add structured logging and metrics when Lambda encounters a missing, invalid, or incompatible `active.json` file.

#### `feat: add active configuration query`

Add a database query that returns all currently active configurations and the information needed to rebuild their S3 artifacts.

#### `feat: add active payload regeneration service`

Create a shared service that rebuilds and uploads an active configuration without reactivating it or changing its activation history.

#### `feat: add active configuration regeneration command`

Add an ops command that queries active configurations and regenerates their existing `active.json` files in S3.

#### `feat: run active payload migration during startup`

Run the active payload migration after database migrations and TES data loading are complete.

#### `feat: track active payload migrations`

Add a Postgres table that records the target schema version, migration status, timestamps, success count, and failure count.

#### `feat: add active configuration maintenance lock`

Add an S3 maintenance lock that is created by the ops migration and checked by Lambda before processing each SQS record.

#### `chore: add ops permissions for configuration storage`

Give the ops container the permissions required to read and overwrite active configuration artifacts in S3.

#### `test: cover active payload regeneration`

Verify that regeneration updates the S3 payload without changing the configuration version, status, activation history, condition mapping, or `current.json`.

#### `test: detect active payload schema changes`

Add an integration test that generates an active payload using `convert_config_to_storage_payload()` and compares the serialized result against an approved fixture, snapshot, or JSON Schema.

The test should fail when the serialized shape changes unexpectedly. For an intentional schema change, the developer should:

1. Review the serialization diff.
2. Increment `CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION`.
3. Update the approved fixture or schema.
4. Confirm that the migration and Lambda validation support the new version.

The fixture should not update automatically. The payload change and schema-version increase should be reviewed together in the pull request.

#### `docs: document active payload migrations`

Document the difference between configuration versions and active payload schema versions and describe the process for future schema changes.

### Open Questions and Next Steps

- Enumerate possible race conditions when the ops migration runs while Lambda is processing eCRs.
- Review the deployment ordering between the ops container, application container, and Lambda.
- Read the ADR guidance in `CONTRIBUTING` and update formatting or required fields if needed.
