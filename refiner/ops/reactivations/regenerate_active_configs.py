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

from app.core.config import get_aws_config
from app.db.configurations.db import get_configurations_db
from app.db.configurations.model import (
    CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION,
    MAINTENANCE_LOCK_KEY,
    DbConfiguration,
)
from app.db.pool import AsyncDatabaseConnection, create_db
from app.services.aws.s3 import (
    s3_client,
    upload_configuration_payload,
)
from app.services.configurations import (
    convert_config_to_storage_payload,
    get_config_payload_metadata,
)

"""
Regenerate active configuration artifacts in S3.

This script:

1. Checks whether the current active payload schema version has already been
   regenerated successfully.
2. Creates a maintenance lock in S3 to temporarily pause Lambda processing.
3. Records the reactivation attempt in Postgres.
4. Queries Postgres for all currently active configurations.
5. Rebuilds each active.json and metadata.json using current application code.
6. Uploads the files to their existing S3 locations.
7. Records the final reactivation status, success count, and failure count.
8. Removes the maintenance lock after all files are regenerated successfully.

This script does not:

- Reactivate configurations in Postgres.
- Change configuration versions.
- Update activation history.
- Rewrite current.json.
- Rewrite the jurisdiction condition mapping file.

If the script fails while the maintenance lock is active, Lambda processing may be
paused until the lock expires or the ops command is rerun successfully.
"""

logger = logging.getLogger(__name__)

REACTIVATION_NAME = f"active-payload-schema-v{CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION}"

LOCK_EXPIRATION_MINUTES = 15

# Set to None to process all active configurations.
# Set to an integer, such as 1 or 100, for local testing.
REACTIVATION_LIMIT: int | None = None

REACTIVATION_MAX_ATTEMPTS = 3
REACTIVATION_RETRY_BASE_DELAY_SECONDS = 1.0
MAX_FAILURE_IDS_IN_ERROR = 10


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
        Bucket=get_aws_config().S3_BUCKET_CONFIG,
        Key=MAINTENANCE_LOCK_KEY,
    )

    logger.info(
        "Deleted active configuration maintenance lock. bucket=%s key=%s",
        get_aws_config().S3_BUCKET_CONFIG,
        MAINTENANCE_LOCK_KEY,
    )


def remove_expired_maintenance_lock() -> bool:
    """
    Remove an existing maintenance lock if it has expired.

    Returns:
        bool: True if an expired lock was removed, otherwise False.
    """

    try:
        response = s3_client.get_object(
            Bucket=get_aws_config().S3_BUCKET_CONFIG,
            Key=MAINTENANCE_LOCK_KEY,
        )
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")

        if error_code in {"404", "NoSuchKey", "NotFound"}:
            return False

        raise

    try:
        lock = json.loads(response["Body"].read())
    except (json.JSONDecodeError, TypeError):
        logger.warning(
            "Removing corrupt active configuration maintenance lock. "
            "bucket=%s key=%s reason=invalid_json",
            get_aws_config().S3_BUCKET_CONFIG,
            MAINTENANCE_LOCK_KEY,
            exc_info=True,
        )

        delete_maintenance_lock()
        return True

    if not isinstance(lock, dict):
        logger.warning(
            "Removing corrupt active configuration maintenance lock. "
            "bucket=%s key=%s reason=unexpected_json_type lock_type=%s",
            get_aws_config().S3_BUCKET_CONFIG,
            MAINTENANCE_LOCK_KEY,
            type(lock).__name__,
        )

        delete_maintenance_lock()
        return True

    expiration = get_lock_expiration(lock)

    if expiration is None:
        logger.warning(
            "Removing corrupt active configuration maintenance lock. "
            "bucket=%s key=%s reason=missing_or_invalid_expires_at",
            get_aws_config().S3_BUCKET_CONFIG,
            MAINTENANCE_LOCK_KEY,
        )

        delete_maintenance_lock()
        return True

    if expiration > datetime.now(UTC):
        return False

    logger.warning(
        "Removing expired active configuration maintenance lock. "
        "bucket=%s key=%s expires_at=%s",
        get_aws_config().S3_BUCKET_CONFIG,
        MAINTENANCE_LOCK_KEY,
        expiration.isoformat(),
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
            Bucket=get_aws_config().S3_BUCKET_CONFIG,
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
        "Created active configuration maintenance lock. "
        "bucket=%s key=%s reactivation=%s expires_at=%s",
        get_aws_config().S3_BUCKET_CONFIG,
        MAINTENANCE_LOCK_KEY,
        REACTIVATION_NAME,
        lock_payload["expires_at"],
    )


def remove_maintenance_lock() -> None:
    """Remove the maintenance lock after a successful reactivation."""

    delete_maintenance_lock()


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
            "Regenerating active configuration. "
            "configuration_id=%s configuration_version=%s jurisdiction_id=%s "
            "attempt=%s max_attempts=%s",
            configuration.id,
            configuration.version,
            configuration.jurisdiction_id,
            attempt,
            REACTIVATION_MAX_ATTEMPTS,
        )

        try:
            payload_started_at = time.perf_counter()

            config_payload = await convert_config_to_storage_payload(
                configuration=configuration, db=db, logger=logger
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
                "Regenerated active configuration. "
                "configuration_id=%s configuration_version=%s jurisdiction_id=%s attempt=%s "
                "payload_generation_ms=%s metadata_generation_ms=%s upload_ms=%s total_ms=%s",
                configuration.id,
                configuration.version,
                configuration.jurisdiction_id,
                attempt,
                round((payload_finished_at - payload_started_at) * 1000, 2),
                round((metadata_finished_at - payload_finished_at) * 1000, 2),
                round((upload_finished_at - metadata_finished_at) * 1000, 2),
                round((upload_finished_at - started_at) * 1000, 2),
            )

            return

        except Exception:
            if attempt == REACTIVATION_MAX_ATTEMPTS:
                logger.exception(
                    "Active configuration regeneration failed after retries. "
                    "configuration_id=%s configuration_version=%s jurisdiction_id=%s "
                    "attempt=%s max_attempts=%s",
                    configuration.id,
                    configuration.version,
                    configuration.jurisdiction_id,
                    attempt,
                    REACTIVATION_MAX_ATTEMPTS,
                )
                raise

            delay_seconds = REACTIVATION_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))

            logger.warning(
                "Active configuration regeneration failed; retrying. "
                "configuration_id=%s configuration_version=%s jurisdiction_id=%s "
                "attempt=%s max_attempts=%s retry_delay_seconds=%s",
                configuration.id,
                configuration.version,
                configuration.jurisdiction_id,
                attempt,
                REACTIVATION_MAX_ATTEMPTS,
                delay_seconds,
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
        "Starting active configuration regeneration. "
        "configuration_count=%s limit=%s target_schema_version=%s",
        total,
        limit,
        CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION,
    )

    for configuration in active_configurations:
        try:
            await regenerate_active_configuration(
                configuration=configuration,
                db=db,
            )
            successful += 1
        except Exception:
            configuration_id = str(configuration.id)
            failures.append(configuration_id)

            logger.exception(
                "Failed to regenerate active configuration. "
                "configuration_id=%s configuration_version=%s jurisdiction_id=%s",
                configuration_id,
                configuration.version,
                configuration.jurisdiction_id,
            )

    logger.info(
        "Active configuration regeneration finished. "
        "total=%s successful=%s failed=%s target_schema_version=%s",
        total,
        successful,
        len(failures),
        CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION,
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
            "Active payload schema version already applied; skipping reactivation. "
            "target_schema_version=%s latest_complete_schema_version=%s",
            CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION,
            latest_complete_schema_version,
        )
        return

    reactivation_id: str | None = None
    lock_created = False
    tracking_record_finalized = False

    try:
        create_maintenance_lock(
            expiration_minutes=LOCK_EXPIRATION_MINUTES,
        )
        lock_created = True

        try:
            reactivation_id = await create_reactivation_tracking_record_db(
                db=db,
                target_schema_version=CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION,
            )
        except Exception:
            remove_maintenance_lock()
            lock_created = False
            raise

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

            failure_ids_for_error = result["failures"][:MAX_FAILURE_IDS_IN_ERROR]
            remaining_failure_count = failure_count - len(failure_ids_for_error)

            error_message = (
                "Failed to regenerate active configurations. "
                f"failure_count={failure_count} "
                f"first_failure_ids={', '.join(failure_ids_for_error)}"
            )

            if remaining_failure_count > 0:
                error_message += f" remaining_failure_count={remaining_failure_count}"

            raise RuntimeError(error_message)

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
            "Active configuration reactivation completed successfully. "
            "target_schema_version=%s",
            CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION,
        )

        if lock_created:
            logger.error(
                "The reactivation failed while the maintenance lock was active. "
                "Lambda processing may be paused until the lock expires or the ops command "
                "is rerun successfully. bucket=%s key=%s expiration_minutes=%s",
                get_aws_config().S3_BUCKET_CONFIG,
                MAINTENANCE_LOCK_KEY,
                LOCK_EXPIRATION_MINUTES,
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
