"""
Regenerate active configuration artifacts in S3.

This script:

1. Creates a maintenance lock in S3.
2. Waits for Lambda executions that started before the lock to finish.
3. Queries Postgres for all currently active configurations.
4. Rebuilds each active.json and metadata.json using current application code.
5. Uploads the files to their existing S3 locations.
6. Removes the maintenance lock after all files are regenerated successfully.

This script does not:

- Reactivate configurations in Postgres.
- Change configuration versions.
- Update activation history.
- Rewrite current.json.
- Rewrite the jurisdiction condition mapping file.
"""

import asyncio
import json
import logging
import os
import time
from datetime import UTC, datetime, timedelta

from botocore.exceptions import ClientError
from dotenv import load_dotenv
from psycopg.rows import dict_row

from app.db.configurations.db import get_configurations_db
from app.db.configurations.model import DbConfiguration
from app.db.pool import AsyncDatabaseConnection, create_db
from app.services.aws.s3 import (
    S3_CONFIGURATION_BUCKET_NAME,
    s3_client,
    upload_configuration_payload,
)
from app.services.configurations import (
    convert_config_to_storage_payload,
    get_config_payload_metadata,
)

logger = logging.getLogger(__name__)

MAINTENANCE_LOCK_KEY = "configurations/maintenance.lock"
MIGRATION_NAME = "active-payload-schema-v2"

DEFAULT_LAMBDA_DRAIN_SECONDS = 60
DEFAULT_LOCK_EXPIRATION_MINUTES = 60


def configure_logging() -> None:
    """Configure logging for the migration script."""

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def get_required_environment_variable(name: str) -> str:
    """
    Return a required environment variable.

    Raises:
        RuntimeError: If the environment variable is missing.
    """

    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"{name} environment variable must be set.")

    return value


def get_integer_environment_variable(
    name: str,
    default: int,
) -> int:
    """
    Return an integer environment variable or its default value.

    Raises:
        RuntimeError: If the environment variable is not a valid integer.
    """

    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise RuntimeError(
            f"{name} must be a valid integer. Received: {raw_value}"
        ) from exc


def get_lock_expiration(lock: dict[str, object]) -> datetime | None:
    """Parse the expiration time from an existing maintenance lock."""

    raw_expiration = lock.get("expires_at")

    if not isinstance(raw_expiration, str):
        return None

    try:
        expiration = datetime.fromisoformat(raw_expiration)
    except ValueError:
        return None

    if expiration.tzinfo is None:
        expiration = expiration.replace(tzinfo=UTC)

    return expiration


def delete_maintenance_lock() -> None:
    """Delete the maintenance lock from S3."""

    s3_client.delete_object(
        Bucket=S3_CONFIGURATION_BUCKET_NAME,
        Key=MAINTENANCE_LOCK_KEY,
    )

    logger.info(
        "Deleted active configuration maintenance lock.",
        extra={
            "bucket": S3_CONFIGURATION_BUCKET_NAME,
            "key": MAINTENANCE_LOCK_KEY,
        },
    )


def remove_expired_maintenance_lock() -> bool:
    """
    Remove an existing maintenance lock if it has expired.

    Returns:
        bool: True if an expired lock was removed, otherwise False.
    """

    try:
        response = s3_client.get_object(
            Bucket=S3_CONFIGURATION_BUCKET_NAME,
            Key=MAINTENANCE_LOCK_KEY,
        )
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")

        if error_code in {"404", "NoSuchKey", "NotFound"}:
            return False

        raise

    try:
        lock = json.loads(response["Body"].read())
    except (json.JSONDecodeError, TypeError) as exc:
        raise RuntimeError(
            "The existing maintenance lock contains invalid JSON."
        ) from exc

    expiration = get_lock_expiration(lock)

    if expiration is None:
        raise RuntimeError(
            "The existing maintenance lock does not contain a valid expires_at value."
        )

    if expiration > datetime.now(UTC):
        return False

    logger.warning(
        "Removing expired active configuration maintenance lock.",
        extra={
            "bucket": S3_CONFIGURATION_BUCKET_NAME,
            "key": MAINTENANCE_LOCK_KEY,
            "expires_at": expiration.isoformat(),
        },
    )

    delete_maintenance_lock()

    return True


def create_maintenance_lock(
    *,
    expiration_minutes: int,
) -> None:
    """
    Create the active configuration maintenance lock in S3.

    The conditional write prevents multiple migrations from acquiring
    the lock at the same time.

    If an existing lock has expired, it is removed and creation is
    attempted one more time.
    """

    now = datetime.now(UTC)

    lock_payload = {
        "reason": "active_configuration_migration",
        "migration": MIGRATION_NAME,
        "owner": "ops-container",
        "started_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=expiration_minutes)).isoformat(),
    }

    def put_lock() -> None:
        s3_client.put_object(
            Bucket=S3_CONFIGURATION_BUCKET_NAME,
            Key=MAINTENANCE_LOCK_KEY,
            Body=json.dumps(lock_payload, indent=2).encode("utf-8"),
            ContentType="application/json",
            IfNoneMatch="*",
        )

    try:
        put_lock()
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")

        if error_code not in {
            "PreconditionFailed",
            "ConditionalRequestConflict",
            "412",
        }:
            raise

        expired_lock_removed = remove_expired_maintenance_lock()

        if not expired_lock_removed:
            raise RuntimeError(
                "The active configuration maintenance lock already exists. "
                "Another migration may already be running."
            ) from exc

        try:
            put_lock()
        except ClientError as retry_exc:
            retry_error_code = retry_exc.response.get("Error", {}).get("Code")

            if retry_error_code in {
                "PreconditionFailed",
                "ConditionalRequestConflict",
                "412",
            }:
                raise RuntimeError(
                    "The maintenance lock was acquired by another process "
                    "before this migration could retry."
                ) from retry_exc

            raise

    logger.info(
        "Created active configuration maintenance lock.",
        extra={
            "bucket": S3_CONFIGURATION_BUCKET_NAME,
            "key": MAINTENANCE_LOCK_KEY,
            "migration": MIGRATION_NAME,
            "expires_at": lock_payload["expires_at"],
        },
    )


def remove_maintenance_lock() -> None:
    """Remove the maintenance lock after a successful migration."""

    delete_maintenance_lock()


async def wait_for_lambda_to_drain(
    *,
    drain_seconds: int,
) -> None:
    """
    Wait for Lambda executions that started before the lock was created.

    This prototype uses a fixed delay. It does not currently check
    Lambda concurrency directly.
    """

    if drain_seconds <= 0:
        logger.info("Skipping Lambda drain wait.")
        return

    logger.info(
        "Waiting for existing Lambda executions to finish.",
        extra={"drain_seconds": drain_seconds},
    )

    await asyncio.sleep(drain_seconds)

    logger.info("Lambda drain wait complete.")


async def get_active_jurisdiction_ids_db(
    *,
    db: AsyncDatabaseConnection,
) -> list[str]:
    """
    Return jurisdiction IDs that currently have active configurations.

    This allows the migration to reuse get_configurations_db(), which
    expects a jurisdiction ID.
    """

    query = """
        SELECT DISTINCT jurisdiction_id
        FROM configurations
        WHERE status = 'active'
        ORDER BY jurisdiction_id;
    """

    async with db.get_connection() as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(query)
            rows = await cursor.fetchall()

    return [row["jurisdiction_id"] for row in rows]


async def get_all_active_configurations_db(
    *,
    db: AsyncDatabaseConnection,
) -> list[DbConfiguration]:
    """
    Return all active configurations across all jurisdictions.

    The existing get_configurations_db() function is reused so each
    row is converted into a complete DbConfiguration model.
    """

    jurisdiction_ids = await get_active_jurisdiction_ids_db(db=db)

    active_configurations: list[DbConfiguration] = []

    for jurisdiction_id in jurisdiction_ids:
        jurisdiction_configurations = await get_configurations_db(
            jurisdiction_id=jurisdiction_id,
            status="active",
            db=db,
        )

        active_configurations.extend(jurisdiction_configurations)

    return active_configurations


async def regenerate_active_configuration(
    *,
    configuration: DbConfiguration,
    db: AsyncDatabaseConnection,
) -> None:
    """
    Rebuild and upload one active configuration.

    The existing configuration version and S3 path remain unchanged.
    """

    started_at = time.perf_counter()

    logger.info(
        "Regenerating active configuration.",
        extra={
            "configuration_id": str(configuration.id),
            "configuration_version": configuration.version,
            "jurisdiction_id": configuration.jurisdiction_id,
        },
    )

    payload_started_at = time.perf_counter()

    config_payload = await convert_config_to_storage_payload(
        configuration=configuration,
        db=db,
    )

    payload_finished_at = time.perf_counter()

    if config_payload is None:
        raise RuntimeError(
            "Configuration payload could not be created for "
            f"configuration {configuration.id}."
        )

    config_metadata = await get_config_payload_metadata(
        configuration=configuration,
        logger=logger,
        db=db,
    )

    metadata_finished_at = time.perf_counter()

    if config_metadata is None:
        raise RuntimeError(
            "Configuration metadata could not be created for "
            f"configuration {configuration.id}."
        )

    # upload_configuration_payload() is synchronous. The normal activation
    # endpoint runs it in a thread pool, so asyncio.to_thread() is used here.
    await asyncio.to_thread(
        upload_configuration_payload,
        config_payload,
        config_metadata,
        logger,
    )

    upload_finished_at = time.perf_counter()

    logger.info(
        "Regenerated active configuration.",
        extra={
            "configuration_id": str(configuration.id),
            "configuration_version": configuration.version,
            "jurisdiction_id": configuration.jurisdiction_id,
            "payload_generation_ms": round(
                (payload_finished_at - payload_started_at) * 1000,
                2,
            ),
            "metadata_generation_ms": round(
                (metadata_finished_at - payload_finished_at) * 1000,
                2,
            ),
            "upload_ms": round(
                (upload_finished_at - metadata_finished_at) * 1000,
                2,
            ),
            "total_ms": round(
                (upload_finished_at - started_at) * 1000,
                2,
            ),
        },
    )


async def regenerate_active_configs(
    *,
    db: AsyncDatabaseConnection,
    limit: int | None = None,
) -> None:
    """
    Query Postgres and regenerate all currently active configurations.

    Args:
        db: Open application database pool.
        limit: Optional number of configurations to process for testing.
    """

    active_configurations = await get_all_active_configurations_db(db=db)

    if limit is not None:
        active_configurations = active_configurations[:limit]

    total = len(active_configurations)
    successful = 0
    failures: list[str] = []

    logger.info(
        "Starting active configuration regeneration.",
        extra={
            "configuration_count": total,
            "limit": limit,
        },
    )

    for configuration in active_configurations:
        try:
            await regenerate_active_configuration(
                configuration=configuration,
                db=db,
            )
        except Exception:
            configuration_id = str(configuration.id)
            failures.append(configuration_id)

            logger.exception(
                "Failed to regenerate active configuration.",
                extra={
                    "configuration_id": configuration_id,
                    "configuration_version": configuration.version,
                    "jurisdiction_id": configuration.jurisdiction_id,
                },
            )
        else:
            successful += 1

    logger.info(
        "Active configuration regeneration finished.",
        extra={
            "total": total,
            "successful": successful,
            "failed": len(failures),
        },
    )

    if failures:
        raise RuntimeError(
            "Failed to regenerate active configurations: " + ", ".join(failures)
        )


async def main() -> None:
    """Run the complete active configuration migration."""

    load_dotenv()
    configure_logging()

    db_url = get_required_environment_variable("DB_URL")
    db_password = get_required_environment_variable("DB_PASSWORD")

    drain_seconds = get_integer_environment_variable(
        "LAMBDA_DRAIN_SECONDS",
        DEFAULT_LAMBDA_DRAIN_SECONDS,
    )

    lock_expiration_minutes = get_integer_environment_variable(
        "MAINTENANCE_LOCK_EXPIRATION_MINUTES",
        DEFAULT_LOCK_EXPIRATION_MINUTES,
    )

    migration_limit = get_integer_environment_variable(
        "ACTIVE_CONFIG_MIGRATION_LIMIT",
        0,
    )

    if migration_limit <= 0:
        migration_limit_value: int | None = None
    else:
        migration_limit_value = migration_limit

    db = create_db(
        db_url=db_url,
        db_password=db_password,
    )

    lock_created = False

    try:
        await db.connect()

        create_maintenance_lock(
            expiration_minutes=lock_expiration_minutes,
        )
        lock_created = True

        await wait_for_lambda_to_drain(
            drain_seconds=drain_seconds,
        )

        await regenerate_active_configs(
            db=db,
            limit=migration_limit_value,
        )
    except Exception:
        logger.exception(
            "Active configuration migration failed. "
            "The maintenance lock was not removed."
        )
        raise
    else:
        remove_maintenance_lock()
        lock_created = False

        logger.info("Active configuration migration completed successfully.")
    finally:
        await db.close()

        if lock_created:
            logger.error(
                "The migration failed while the maintenance lock was active. "
                "The lock remains in S3 and must be reviewed before processing "
                "is resumed.",
                extra={
                    "bucket": S3_CONFIGURATION_BUCKET_NAME,
                    "key": MAINTENANCE_LOCK_KEY,
                },
            )


if __name__ == "__main__":
    asyncio.run(main())
