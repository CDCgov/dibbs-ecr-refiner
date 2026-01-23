from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from psycopg.rows import dict_row

from tests.test_conditions import TEST_SESSION_TOKEN

LOCALSTACK_BASE_URL = "http://localhost:4566/local-config-bucket/SDDH"
EXPECTED_DROWNING_RSG_CODE = "212962007"


@pytest.mark.integration
@pytest.mark.asyncio
class TestConfigurations:
    async def test_create_configuration(
        self, setup, authed_client, test_username, db_conn
    ):
        # Get a condition to use to create a config
        async with db_conn.cursor(row_factory=dict_row) as cur:
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

    async def test_activate_configuration(self, setup, authed_client, db_conn):
        # Ensure the condition exists
        async with db_conn.cursor(row_factory=dict_row) as cur:
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

        # Activate any existing draft configuration for this condition
        async with db_conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id FROM configurations
                WHERE name = 'Drowning and Submersion' AND status = 'draft';
                """
            )
            draft_config = await cur.fetchone()

        if draft_config:
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
            TOTAL_EXPECTED_SECTION_COUNT = 9
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
            assert len(metadata_file_json["child_rsg_snomed_codes"]) == 1
            assert (
                metadata_file_json["child_rsg_snomed_codes"][0]
                == EXPECTED_DROWNING_RSG_CODE
            )
            assert metadata_file_json["jurisdiction_code"] == "SDDH"
            assert metadata_file_json["active_version"] == 1

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

    async def test_activate_rollback(self, setup, authed_client, db_conn):
        async with db_conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                    SELECT id, condition_canonical_url, condition_id
                    FROM configurations
                    WHERE name = 'Drowning and Submersion';
                    """
            )
            configuration = await cur.fetchone()
            assert configuration is not None
        initial_configuration_id = str(configuration["id"])

        # create a new test client with a mocked deactivate function that throws
        # an error to test the rollback. The existing fixture has the real function bundled in it
        # that doesn't allow us to hotswap it at runtime
        with patch(
            "app.db.configurations.activations.db._deactivate_configuration_db",
            new_callable=AsyncMock,
            side_effect=Exception("Simulated failure"),
        ):
            from app.main import app as patched_app

            transport = ASGITransport(app=patched_app)
            async with AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                client.cookies.update({"refiner-session": TEST_SESSION_TOKEN})

                response = await client.patch(
                    f"/api/v1/configurations/{initial_configuration_id}/activate"
                )

                async with db_conn.cursor(row_factory=dict_row) as cur:
                    query = """
                            SELECT id, condition_canonical_url, condition_id, status
                            FROM configurations
                            WHERE id = %s;
                        """

                    await cur.execute(query, (initial_configuration_id,))
                    configuration = await cur.fetchone()
                    assert configuration is not None
                    assert configuration["status"] == "inactive"

                    # Expect previous version to still be the active version
                    current_file_resp = await authed_client.get(
                        f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_RSG_CODE}/current.json"
                    )
                    assert current_file_resp.status_code == 200

                    # This is the previously activated version from the test above
                    assert current_file_resp.json()["version"] == 3

                assert response.status_code == 500

    async def test_deactivate_configuration(self, setup, authed_client, db_conn):
        # Get the activated configuration from the previous tests
        async with db_conn.cursor(row_factory=dict_row) as cur:
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
