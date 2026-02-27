from unittest.mock import patch
from uuid import uuid4

import pytest
from psycopg.rows import dict_row

from app.db.configurations.activations.db import activate_configuration_db
from app.db.configurations.db import get_configuration_by_id_db

LOCALSTACK_BASE_URL = "http://localhost:4566/local-config-bucket/configurations/SDDH"
EXPECTED_DROWNING_RSG_CODE = "212962007"


@pytest.mark.integration
@pytest.mark.asyncio
class TestConfigurations:
    async def test_create_configuration(
        self, setup, authed_client, test_username, db_pool
    ):
        # Get a condition to use to create a config
        async with db_pool.get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT id, display_name
                    FROM conditions
                    WHERE display_name = 'Drowning and Submersion'
                    AND version = '4.0.0'
                    """
                )
                condition = await cur.fetchone()
                assert condition is not None

        # Create config
        payload = {"condition_id": str(condition["id"])}
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        assert response.status_code == 200
        assert "id" in response.json()
        assert "name" in response.json()
        assert response.json()["name"] == "Drowning and Submersion"

        # Assert that associated config creation event was logged
        response = await authed_client.get("/api/v1/events/")
        assert response.status_code == 200
        audit_events = response.json()["audit_events"]
        assert len(audit_events) == 1

        creation_event = audit_events[0]
        assert creation_event is not None
        assert creation_event["username"] == test_username
        assert creation_event["configuration_name"] == condition["display_name"]

        # Attempt to create the same config again (should fail)
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        assert response.status_code == 409

        # Make sure no new event was created during failure
        response = await authed_client.get("/api/v1/events/")
        assert response.status_code == 200
        failure_audit_events = response.json()["audit_events"]
        assert len(failure_audit_events) == 1

    async def test_activate_configuration(self, setup, authed_client, db_pool):
        # Ensure the condition exists
        async with db_pool.get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT id, display_name, version, canonical_url
                    FROM conditions
                    WHERE display_name = 'Drowning and Submersion'
                    AND version = '4.0.0'
                    """
                )
                condition = await cur.fetchone()
                assert condition is not None

            # Activate any existing draft configuration for this condition
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT id, jurisdiction_id, version
                    FROM configurations
                    WHERE name = 'Drowning and Submersion'
                    AND status = 'draft';
                    """
                )
                draft_config = await cur.fetchone()
                assert draft_config is not None

            draft_id = draft_config["id"]
            response = await authed_client.patch(
                f"/api/v1/configurations/{draft_id}/activate"
            )
            assert response.status_code == 200

            # Activation file and content
            activation_file = await authed_client.get(
                f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_RSG_CODE}/1/active.json"
            )
            activation_file_json = activation_file.json()

            TOTAL_EXPECTED_CONDITION_CODE_COUNT = 481
            TOTAL_EXPECTED_SECTION_COUNT = 19
            TOTAL_EXPECTED_INCLUDED_CONDITION_RSG_CODES = (
                1  # No other conditions were included
            )

            assert (
                len(activation_file_json["codes"])
                == TOTAL_EXPECTED_CONDITION_CODE_COUNT
            )
            assert len(activation_file_json["sections"]) == TOTAL_EXPECTED_SECTION_COUNT
            assert (
                len(activation_file_json["included_condition_rsg_codes"])
                == TOTAL_EXPECTED_INCLUDED_CONDITION_RSG_CODES
            )
            assert (
                activation_file_json["included_condition_rsg_codes"][0]
                == EXPECTED_DROWNING_RSG_CODE
            )

            # Metadata file and content
            metadata_file = await authed_client.get(
                f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_RSG_CODE}/1/metadata.json"
            )
            metadata_file_json = metadata_file.json()
            assert metadata_file_json["condition_name"] == condition["display_name"]
            assert metadata_file_json["canonical_url"] == condition["canonical_url"]
            assert metadata_file_json["tes_version"] == condition["version"]
            assert (
                metadata_file_json["jurisdiction_id"] == draft_config["jurisdiction_id"]
            )
            assert (
                metadata_file_json["configuration_version"] == draft_config["version"]
            )
            assert len(metadata_file_json["child_rsg_snomed_codes"]) == 1
            assert (
                metadata_file_json["child_rsg_snomed_codes"][0]
                == EXPECTED_DROWNING_RSG_CODE
            )

            # Current file and content
            current_file = await authed_client.get(
                f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_RSG_CODE}/current.json"
            )
            assert current_file.json()["version"] == 1

        # Now create a new configuration for activation
        payload = {"condition_id": str(condition["id"])}
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        assert response.status_code == 200
        config_data = response.json()
        initial_configuration_id = config_data["id"]
        # Use the condition_id from the payload for subsequent steps
        condition_id_to_test = payload["condition_id"]

        # Activate config
        response = await authed_client.patch(
            f"/api/v1/configurations/{initial_configuration_id}/activate"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["configuration_id"] == initial_configuration_id
        assert data["status"] == "active"

        # Check that new files exist in S3
        activation_file = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_RSG_CODE}/2/active.json"
        )
        activation_file_json = activation_file.json()

        current_file = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_RSG_CODE}/current.json"
        )
        assert current_file.json()["version"] == 2

        # Create another configuration draft and try to activate it. Assert that the confirmation
        # returned matches the new draft ID.
        payload = {"condition_id": condition_id_to_test}
        new_draft_response = await authed_client.post(
            "/api/v1/configurations/", json=payload
        )
        new_draft_response_data = new_draft_response.json()
        assert new_draft_response.status_code == 200
        assert "id" in new_draft_response_data

        new_draft_response_id = new_draft_response_data["id"]
        new_draft_activation_response = await authed_client.patch(
            f"/api/v1/configurations/{new_draft_response_id}/activate"
        )
        assert new_draft_activation_response.status_code == 200
        new_draft_activation_data = new_draft_activation_response.json()
        assert new_draft_activation_data["configuration_id"] == new_draft_response_id
        assert new_draft_activation_data["status"] == "active"

        # check that the old configuration isn't active anymore
        validation_response = await authed_client.get(
            f"/api/v1/configurations/{initial_configuration_id}"
        )
        assert validation_response.status_code == 200

        validation_response_data = validation_response.json()
        assert validation_response_data["id"] == initial_configuration_id
        assert validation_response_data["status"] == "inactive"

    async def test_transaction_rollback_on_activation_failure(self, db_pool):
        """
        Verifies rollback when activation fails after deactivation.
        """
        # Set the config to be active
        async with db_pool.get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    UPDATE configurations
                    SET status = 'active'
                    WHERE name = 'Drowning and Submersion'
                    AND version = 3
                    RETURNING id, condition_canonical_url, condition_id;
                    """
                )
                configuration = await cur.fetchone()
                assert configuration is not None
            old_config_id = str(configuration["id"])

            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT id, condition_canonical_url, condition_id
                    FROM configurations
                    WHERE name = 'Drowning and Submersion'
                    AND version = 2;
                    """
                )
                configuration = await cur.fetchone()
                assert configuration is not None
            new_config_id = str(configuration["id"])

        # Patch _activate_configuration_db to fail after deactivation
        with patch(
            "app.db.configurations.activations.db._activate_configuration_db",
            return_value=None,
        ):
            result = await activate_configuration_db(
                configuration_id=new_config_id,
                activated_by_user_id=uuid4(),
                canonical_url="https://mock.com",
                jurisdiction_id="SDDH",
                s3_urls=["s3://bucket/key"],
                db=db_pool,
            )

            assert result is None  # activation failed

            old_config = await get_configuration_by_id_db(
                id=old_config_id, jurisdiction_id="SDDH", db=db_pool
            )

            assert old_config.status == "active"  # Should remain active due to rollback

            new_config = await get_configuration_by_id_db(
                id=new_config_id, jurisdiction_id="SDDH", db=db_pool
            )
            assert new_config.status == "inactive"  # Should remain inactive

    async def test_deactivate_configuration(self, setup, authed_client, db_pool):
        # Get the activated configuration from the previous tests
        async with db_pool.get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT id, condition_canonical_url, condition_id
                    FROM configurations
                    WHERE name = 'Drowning and Submersion' AND status = 'active';
                    """
                )
                configuration = await cur.fetchone()
                assert configuration is not None

        initial_configuration_id = str(configuration["id"])

        # Deactivate config
        response = await authed_client.patch(
            f"/api/v1/configurations/{initial_configuration_id}/deactivate",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["configuration_id"] == initial_configuration_id
        assert data["status"] == "inactive"

        # Expect null version when deactivated
        current_file_resp = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_RSG_CODE}/current.json"
        )
        assert current_file_resp.status_code == 200

        # This is the previously activated version from the test above
        assert current_file_resp.json()["version"] is None
