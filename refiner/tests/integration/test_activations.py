import json
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import UUID

import httpx
import pytest
from fastapi import status
from jsonschema import Draft202012Validator
from psycopg.rows import dict_row

from app.db.configurations.db import get_configuration_by_id_db
from app.db.configurations.model import CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION
from app.services.configurations import convert_config_to_storage_payload
from scripts.migrations import regenerate_active_configs as reactivation
from scripts.migrations.regenerate_active_configs import regenerate_active_configuration

LOCALSTACK_BASE_URL = "http://localhost:4566/local-config-bucket/configurations/SDDH"
EXPECTED_DROWNING_CG_UUID = "c05cab96-c023-4ee2-bb7d-071fb600be7b"
ACTIVE_CONFIG_PAYLOAD_SCHEMA_FIXTURE = (
    Path(__file__).parents[1]
    / "fixtures"
    / "lambda"
    / "active_config_payload_schema_v1.json"
)


def make_json_serializable(value):
    """
    Convert payload objects into JSON-serializable values.

    The normal S3 upload path handles serialization internally. These tests patch
    that upload boundary so regenerated artifacts are written to the same
    LocalStack setup used by the integration API tests.
    """

    if hasattr(value, "to_dict"):
        return make_json_serializable(value.to_dict())

    if is_dataclass(value):
        return make_json_serializable(asdict(value))

    if isinstance(value, dict):
        return {
            str(key): make_json_serializable(nested_value)
            for key, nested_value in value.items()
        }

    if isinstance(value, list):
        return [make_json_serializable(item) for item in value]

    if isinstance(value, tuple):
        return [make_json_serializable(item) for item in value]

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, datetime | date):
        return value.isoformat()

    return value


async def get_audit_events(authed_client):
    response = await authed_client.get("/api/v1/events/")
    assert response.status_code == status.HTTP_200_OK
    return response.json()["audit_events"]


async def clear_reactivation_tracking_records(*, db_pool) -> None:
    async with db_pool.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM active_payload_schema_reactivations;
                """
            )
            await conn.commit()


async def create_complete_reactivation_tracking_record(
    *,
    db_pool,
    target_schema_version: int,
    success_count: int = 1,
    failure_count: int = 0,
) -> None:
    async with db_pool.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO active_payload_schema_reactivations (
                    target_schema_version,
                    status,
                    started_at,
                    completed_at,
                    success_count,
                    failure_count
                )
                VALUES (%s, 'COMPLETE', NOW(), NOW(), %s, %s);
                """,
                (
                    target_schema_version,
                    success_count,
                    failure_count,
                ),
            )
            await conn.commit()


async def get_reactivation_tracking_rows(*, db_pool):
    async with db_pool.get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT
                    id,
                    target_schema_version,
                    status,
                    success_count,
                    failure_count,
                    started_at,
                    completed_at
                FROM active_payload_schema_reactivations
                ORDER BY created_at, id;
                """
            )
            return await cur.fetchall()


def upload_regenerated_payload_to_localstack(config_payload, config_metadata, logger):
    """
    Test replacement for upload_configuration_payload().

    regenerate_active_configuration() calls upload_configuration_payload() in a
    background thread. The real function uses the app-level S3 client and bucket
    env, which does not match this integration test's LocalStack HTTP setup.
    This replacement writes the same active.json and metadata.json files to the
    LocalStack object URLs the rest of these integration tests already use.
    """

    active_payload = make_json_serializable(config_payload)
    metadata_payload = make_json_serializable(config_metadata)

    with httpx.Client() as client:
        active_response = client.put(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/1/active.json",
            json=active_payload,
        )
        active_response.raise_for_status()

        metadata_response = client.put(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/1/metadata.json",
            json=metadata_payload,
        )
        metadata_response.raise_for_status()


@pytest.mark.integration
@pytest.mark.asyncio
class TestActivations:
    async def test_active_config_payload_matches_approved_schema(
        self,
        setup,
        authed_client,
        get_condition_id,
        db_pool,
    ):
        """
        Verify that generated active.json payloads match the approved schema.

        This test should fail when the serialized active payload shape changes
        unexpectedly. For an intentional shape change, the developer should:

        1. Review the serialization diff.
        2. Increment CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION.
        3. Update the approved schema fixture.
        4. Confirm the reactivation script and Lambda validation support the new version.

        The schema fixture should not update automatically.
        """

        condition_id = await get_condition_id("Drowning and Submersion")

        response = await authed_client.post(
            "/api/v1/configurations/",
            json={"condition_id": str(condition_id)},
        )

        assert response.status_code == status.HTTP_200_OK

        configuration_id = UUID(response.json()["id"])

        configuration = await get_configuration_by_id_db(
            id=configuration_id,
            jurisdiction_id="SDDH",
            db=db_pool,
        )

        assert configuration is not None

        payload = await convert_config_to_storage_payload(
            configuration=configuration,
            db=db_pool,
        )

        assert payload is not None

        serialized_payload = payload.to_dict()

        assert (
            serialized_payload["schema_version"] == CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION
        )

        with ACTIVE_CONFIG_PAYLOAD_SCHEMA_FIXTURE.open() as fixture:
            approved_schema = json.load(fixture)

        validator = Draft202012Validator(approved_schema)
        errors = sorted(
            validator.iter_errors(serialized_payload),
            key=lambda error: list(error.path),
        )

        assert errors == [], "\n".join(
            f"{list(error.path)}: {error.message}" for error in errors
        )

    async def test_active_config_regeneration_only_updates_existing_s3_payloads(
        self,
        setup,
        authed_client,
        get_condition_id,
        get_config_by_id,
        db_pool,
    ):
        """
        Verify that active configuration regeneration updates the generated S3
        payload without changing activation state.

        Regeneration should update active.json and metadata.json for the existing
        active configuration version. It should not change the configuration
        version, status, activation history, condition mapping, or current.json.
        """

        condition_name = "Drowning and Submersion"
        condition_id = await get_condition_id(condition_name)

        response = await authed_client.post(
            "/api/v1/configurations/",
            json={"condition_id": str(condition_id)},
        )
        assert response.status_code == status.HTTP_200_OK

        configuration_id = response.json()["id"]

        response = await authed_client.patch(
            f"/api/v1/configurations/{configuration_id}/activate"
        )
        assert response.status_code == status.HTTP_200_OK

        config_before = await get_config_by_id(configuration_id)
        audit_events_before = await get_audit_events(authed_client)

        active_file_response = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/1/active.json"
        )
        assert active_file_response.status_code == status.HTTP_200_OK
        active_payload_before = active_file_response.json()

        metadata_file_response = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/1/metadata.json"
        )
        assert metadata_file_response.status_code == status.HTTP_200_OK
        metadata_payload_before = metadata_file_response.json()

        current_file_response = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/current.json"
        )
        assert current_file_response.status_code == status.HTTP_200_OK
        current_payload_before = current_file_response.json()

        mapping_file_response = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/rsg_cg_mapping.json"
        )
        assert mapping_file_response.status_code == status.HTTP_200_OK
        mapping_payload_before = mapping_file_response.json()

        stale_active_payload = deepcopy(active_payload_before)
        stale_active_payload.pop("schema_version", None)

        response = await authed_client.put(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/1/active.json",
            json=stale_active_payload,
        )
        assert response.status_code == status.HTTP_200_OK

        stale_active_file_response = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/1/active.json"
        )
        assert stale_active_file_response.status_code == status.HTTP_200_OK
        assert "schema_version" not in stale_active_file_response.json()

        configuration = await get_configuration_by_id_db(
            id=UUID(configuration_id),
            jurisdiction_id="SDDH",
            db=db_pool,
        )
        assert configuration is not None

        with patch(
            "scripts.migrations.regenerate_active_configs.upload_configuration_payload",
            side_effect=upload_regenerated_payload_to_localstack,
        ):
            await regenerate_active_configuration(
                configuration=configuration,
                db=db_pool,
            )

        active_file_response = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/1/active.json"
        )
        assert active_file_response.status_code == status.HTTP_200_OK
        active_payload_after = active_file_response.json()

        metadata_file_response = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/1/metadata.json"
        )
        assert metadata_file_response.status_code == status.HTTP_200_OK
        metadata_payload_after = metadata_file_response.json()

        current_file_response = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/current.json"
        )
        assert current_file_response.status_code == status.HTTP_200_OK
        current_payload_after = current_file_response.json()

        mapping_file_response = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/rsg_cg_mapping.json"
        )
        assert mapping_file_response.status_code == status.HTTP_200_OK
        mapping_payload_after = mapping_file_response.json()

        config_after = await get_config_by_id(configuration_id)
        audit_events_after = await get_audit_events(authed_client)

        assert active_payload_before != stale_active_payload
        assert active_payload_after == active_payload_before
        assert (
            active_payload_after["schema_version"]
            == CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION
        )

        assert metadata_payload_after == metadata_payload_before

        assert config_after["version"] == config_before["version"]
        assert config_after["status"] == config_before["status"]
        assert config_after["status"] == "active"

        assert audit_events_after == audit_events_before
        assert current_payload_after == current_payload_before
        assert mapping_payload_after == mapping_payload_before

    async def test_active_config_regeneration_skips_when_schema_version_already_complete(
        self,
        setup,
        db_pool,
    ):
        """
        If the current active payload schema version has already been completely
        applied, reactivation should exit before taking the maintenance lock or
        rewriting any active configuration artifacts.
        """

        await clear_reactivation_tracking_records(db_pool=db_pool)

        await create_complete_reactivation_tracking_record(
            db_pool=db_pool,
            target_schema_version=reactivation.CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION,
            success_count=3,
            failure_count=0,
        )

        rows_before = await get_reactivation_tracking_rows(db_pool=db_pool)

        with (
            patch(
                "scripts.migrations.regenerate_active_configs.create_maintenance_lock"
            ) as create_lock_mock,
            patch(
                "scripts.migrations.regenerate_active_configs.wait_for_lambda_to_drain",
                new_callable=AsyncMock,
            ) as wait_for_lambda_to_drain_mock,
            patch(
                "scripts.migrations.regenerate_active_configs.regenerate_active_configs",
                new_callable=AsyncMock,
            ) as regenerate_active_configs_mock,
            patch(
                "scripts.migrations.regenerate_active_configs.remove_maintenance_lock"
            ) as remove_lock_mock,
        ):
            await reactivation.run_active_config_reactivation(db=db_pool)

        rows_after = await get_reactivation_tracking_rows(db_pool=db_pool)

        assert rows_after == rows_before

        create_lock_mock.assert_not_called()
        wait_for_lambda_to_drain_mock.assert_not_awaited()
        regenerate_active_configs_mock.assert_not_awaited()
        remove_lock_mock.assert_not_called()

    async def test_active_config_regeneration_records_complete_tracking_result(
        self,
        setup,
        db_pool,
    ):
        """
        A successful active configuration reactivation should create a tracking
        record for the target schema version and mark it COMPLETE with the
        regeneration success and failure counts.
        """

        await clear_reactivation_tracking_records(db_pool=db_pool)

        with (
            patch(
                "scripts.migrations.regenerate_active_configs.create_maintenance_lock"
            ) as create_lock_mock,
            patch(
                "scripts.migrations.regenerate_active_configs.wait_for_lambda_to_drain",
                new_callable=AsyncMock,
            ) as wait_for_lambda_to_drain_mock,
            patch(
                "scripts.migrations.regenerate_active_configs.regenerate_active_configs",
                new_callable=AsyncMock,
                return_value={
                    "total": 2,
                    "successful": 2,
                    "failures": [],
                },
            ) as regenerate_active_configs_mock,
            patch(
                "scripts.migrations.regenerate_active_configs.remove_maintenance_lock"
            ) as remove_lock_mock,
        ):
            await reactivation.run_active_config_reactivation(db=db_pool)

        create_lock_mock.assert_called_once_with(
            expiration_minutes=reactivation.LOCK_EXPIRATION_MINUTES,
        )
        wait_for_lambda_to_drain_mock.assert_awaited_once_with(
            drain_seconds=reactivation.LAMBDA_DRAIN_SECONDS,
        )
        regenerate_active_configs_mock.assert_awaited_once_with(
            db=db_pool,
            limit=None,
        )
        remove_lock_mock.assert_called_once_with()

        rows = await get_reactivation_tracking_rows(db_pool=db_pool)

        assert len(rows) == 1

        tracking_row = rows[0]

        assert (
            tracking_row["target_schema_version"]
            == reactivation.CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION
        )
        assert tracking_row["status"] == "COMPLETE"
        assert tracking_row["success_count"] == 2
        assert tracking_row["failure_count"] == 0
        assert tracking_row["started_at"] is not None
        assert tracking_row["completed_at"] is not None
