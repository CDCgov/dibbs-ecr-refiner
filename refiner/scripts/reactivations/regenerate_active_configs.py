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
from typing import Literal, TypedDict

from botocore.exceptions import ClientError
from dotenv import load_dotenv
from psycopg.rows import dict_row

from app.db.configurations.db import get_configurations_db
from app.db.configurations.model import (
    CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION,
    DbConfiguration,
)
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
REACTIVATION_NAME = "active-payload-schema-v2"

LAMBDA_DRAIN_SECONDS = 30
LOCK_EXPIRATION_MINUTES = 15

# Set to None to process all active configurations.
# Set to an integer, such as 1 or 100, for local testing.
REACTIVATION_LIMIT: int | None = None

REACTIVATION_MAX_ATTEMPTS = 3
REACTIVATION_RETRY_BASE_DELAY_SECONDS = 1.0


class MaintenanceLock(TypedDict):
    """Maintenance lock payload written to S3 during active config reactivation."""

    reason: str
    reactivation: str
    owner: str
    started_at: str
    expires_at: str


ReactivationStatus = Literal[
    "IN_PROGRESS",
    "COMPLETE",
    "PARTIAL_FAILURE",
    "FAILED",
]


class RegenerationResult(TypedDict):
    """Summary of active configuration regeneration results."""

    total: int
    successful: int
    failures: list[str]


def configure_logging() -> None:
    """Configure logging for the reactivation script."""

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def get_lock_expiration(lock: MaintenanceLock) -> datetime | None:
    """Return the parsed lock expiration time, if present and valid."""

    expires_at = lock.get("expires_at")

    if not expires_at:
        return None

    try:
        return datetime.fromisoformat(expires_at)
    except ValueError:
        return None


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

    The conditional write prevents multiple reactivations from acquiring
    the lock at the same time.

    If an existing lock has expired, it is removed and creation is
    attempted one more time.
    """

    now = datetime.now(UTC)

    lock_payload: MaintenanceLock = {
        "reason": "active_configuration_reactivation",
        "reactivation": REACTIVATION_NAME,
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
                "Another reactivation may already be running."
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
                    "before this reactivation could retry."
                ) from retry_exc

            raise

    logger.info(
        "Created active configuration maintenance lock.",
        extra={
            "bucket": S3_CONFIGURATION_BUCKET_NAME,
            "key": MAINTENANCE_LOCK_KEY,
            "reactivation": REACTIVATION_NAME,
            "expires_at": lock_payload["expires_at"],
        },
    )


def remove_maintenance_lock() -> None:
    """Remove the maintenance lock after a successful reactivation."""

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

    This allows the reactivation to reuse get_configurations_db(), which
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


async def get_latest_complete_reactivation_schema_version_db(
    *,
    db: AsyncDatabaseConnection,
) -> int | None:
    """
    Return the latest active payload schema version that was completely applied.

    Only COMPLETE records count as successfully applied. Failed or partial records
    should not prevent another reactivation attempt.
    """

    query = """
        SELECT target_schema_version
        FROM active_payload_schema_reactivations
        WHERE status = 'COMPLETE'
        ORDER BY completed_at DESC, created_at DESC
        LIMIT 1;
    """

    async with db.get_connection() as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(query)
            row = await cursor.fetchone()

    if row is None:
        return None

    return row["target_schema_version"]


async def create_reactivation_tracking_record_db(
    *,
    db: AsyncDatabaseConnection,
    target_schema_version: int,
) -> str:
    """
    Create an IN_PROGRESS tracking record for active payload schema reactivation.
    """

    query = """
        INSERT INTO active_payload_schema_reactivations (
            target_schema_version,
            status,
            started_at,
            success_count,
            failure_count
        )
        VALUES (%s, 'IN_PROGRESS', NOW(), 0, 0)
        RETURNING id;
    """

    async with db.get_connection() as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(query, (target_schema_version,))
            row = await cursor.fetchone()
            await connection.commit()

    return str(row["id"])


async def update_reactivation_tracking_record_db(
    *,
    db: AsyncDatabaseConnection,
    reactivation_id: str,
    status: ReactivationStatus,
    success_count: int,
    failure_count: int,
) -> None:
    """
    Update the active payload schema reactivation tracking record.

    COMPLETE is the only status treated as successfully applying the target
    schema version.
    """

    query = """
        UPDATE active_payload_schema_reactivations
        SET
            status = %s,
            completed_at = NOW(),
            success_count = %s,
            failure_count = %s,
            updated_at = NOW()
        WHERE id = %s;
    """

    async with db.get_connection() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                query,
                (
                    status,
                    success_count,
                    failure_count,
                    reactivation_id,
                ),
            )
            await connection.commit()


async def regenerate_active_configuration(
    *,
    configuration: DbConfiguration,
    db: AsyncDatabaseConnection,
) -> None:
    """
    Rebuild and upload one active configuration.

    The existing configuration version and S3 path remain unchanged.
    """

    for attempt in range(1, REACTIVATION_MAX_ATTEMPTS + 1):
        started_at = time.perf_counter()

        logger.info(
            "Regenerating active configuration.",
            extra={
                "configuration_id": str(configuration.id),
                "configuration_version": configuration.version,
                "jurisdiction_id": configuration.jurisdiction_id,
                "attempt": attempt,
                "max_attempts": REACTIVATION_MAX_ATTEMPTS,
            },
        )

        try:
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
                    "attempt": attempt,
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

            return

        except Exception:
            if attempt == REACTIVATION_MAX_ATTEMPTS:
                logger.exception(
                    "Active configuration regeneration failed after retries.",
                    extra={
                        "configuration_id": str(configuration.id),
                        "configuration_version": configuration.version,
                        "jurisdiction_id": configuration.jurisdiction_id,
                        "attempt": attempt,
                        "max_attempts": REACTIVATION_MAX_ATTEMPTS,
                    },
                )
                raise

            delay_seconds = REACTIVATION_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))

            logger.warning(
                "Active configuration regeneration failed; retrying.",
                extra={
                    "configuration_id": str(configuration.id),
                    "configuration_version": configuration.version,
                    "jurisdiction_id": configuration.jurisdiction_id,
                    "attempt": attempt,
                    "max_attempts": REACTIVATION_MAX_ATTEMPTS,
                    "retry_delay_seconds": delay_seconds,
                },
                exc_info=True,
            )

            await asyncio.sleep(delay_seconds)


async def regenerate_active_configs(
    *,
    db: AsyncDatabaseConnection,
    limit: int | None = None,
) -> RegenerationResult:
    """
    Query Postgres and regenerate all currently active configurations.

    Args:
        db: Open application database pool.
        limit: Optional number of configurations to process for testing.

    Returns:
        RegenerationResult: Counts and failure IDs from regeneration.
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
            "target_schema_version": CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION,
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
            "target_schema_version": CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION,
        },
    )

    return {
        "total": total,
        "successful": successful,
        "failures": failures,
    }


async def run_active_config_reactivation(
    *,
    db: AsyncDatabaseConnection,
    limit: int | None = None,
) -> None:
    """
    Run active configuration reactivation using an existing database connection.

    This is separated from main() so integration tests can exercise the
    reactivation tracking behavior without creating a new DB connection from env.
    """

    latest_complete_schema_version = (
        await get_latest_complete_reactivation_schema_version_db(db=db)
    )

    if latest_complete_schema_version == CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION:
        logger.info(
            "Active payload schema version already applied; skipping reactivation.",
            extra={
                "target_schema_version": CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION,
                "latest_complete_schema_version": latest_complete_schema_version,
            },
        )
        return

    reactivation_id = await create_reactivation_tracking_record_db(
        db=db,
        target_schema_version=CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION,
    )

    lock_created = False
    tracking_record_finalized = False

    try:
        create_maintenance_lock(
            expiration_minutes=LOCK_EXPIRATION_MINUTES,
        )
        lock_created = True

        await wait_for_lambda_to_drain(
            drain_seconds=LAMBDA_DRAIN_SECONDS,
        )

        result = await regenerate_active_configs(
            db=db,
            limit=limit,
        )

        failure_count = len(result["failures"])

        if failure_count > 0:
            await update_reactivation_tracking_record_db(
                db=db,
                reactivation_id=reactivation_id,
                status="PARTIAL_FAILURE",
                success_count=result["successful"],
                failure_count=failure_count,
            )
            tracking_record_finalized = True

            raise RuntimeError(
                "Failed to regenerate active configurations: "
                + ", ".join(result["failures"])
            )

        await update_reactivation_tracking_record_db(
            db=db,
            reactivation_id=reactivation_id,
            status="COMPLETE",
            success_count=result["successful"],
            failure_count=0,
        )
        tracking_record_finalized = True

    except Exception:
        if not tracking_record_finalized:
            await update_reactivation_tracking_record_db(
                db=db,
                reactivation_id=reactivation_id,
                status="FAILED",
                success_count=0,
                failure_count=0,
            )

        logger.exception(
            "Active configuration reactivation failed. "
            "The maintenance lock was not removed."
        )
        raise

    else:
        remove_maintenance_lock()
        lock_created = False

        logger.info(
            "Active configuration reactivation completed successfully.",
            extra={
                "target_schema_version": CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION,
            },
        )

    finally:
        if lock_created:
            logger.error(
                "The reactivation failed while the maintenance lock was active. "
                "The lock remains in S3 and must be reviewed before processing "
                "is resumed.",
                extra={
                    "bucket": S3_CONFIGURATION_BUCKET_NAME,
                    "key": MAINTENANCE_LOCK_KEY,
                },
            )


async def main() -> None:
    """Run the complete active configuration reactivation."""

    load_dotenv()
    configure_logging()

    db_url = os.environ["DB_URL"]
    db_password = os.environ["DB_PASSWORD"]

    db = create_db(
        db_url=db_url,
        db_password=db_password,
    )

    try:
        await db.connect()

        await run_active_config_reactivation(
            db=db,
            limit=REACTIVATION_LIMIT,
        )
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
