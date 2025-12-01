import pytest


@pytest.mark.integration
@pytest.mark.asyncio
class TestConfigurations:
    async def test_create_configuration(
        self, setup, authed_client, test_username, db_conn
    ):
        # Get a condition to use to create a config
        async with db_conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, display_name
                FROM conditions
                WHERE display_name = 'Drowning and Submersion'
                AND version = '3.0.0'
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
        event = audit_events[0]
        assert event["username"] == test_username
        assert event["configuration_name"] == condition["display_name"]
        assert event["action_text"] == "Created configuration"

        # Attempt to create the same config again (should fail)
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        assert response.status_code == 409

        # Make sure no event was created during failure
        response = await authed_client.get("/api/v1/events/")
        assert response.status_code == 200
        failure_audit_events = response.json()["audit_events"]
        assert len(failure_audit_events) == 1

    async def test_activate_configuration(self, setup, authed_client, db_conn):
        # Get a configuration from the created config
        async with db_conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, condition_canonical_url, condition_id
                FROM configurations
                WHERE name = 'Drowning and Submersion';
                """
            )
            configuration = await cur.fetchone()
            assert configuration is not None

        condition_id_to_test = str(configuration["condition_id"])
        initial_configuration_id = str(configuration["id"])
        canonical_url = str(configuration["condition_canonical_url"])

        # Activate config
        payload = {"condition_canonical_url": canonical_url}
        response = await authed_client.patch(
            f"/api/v1/configurations/{initial_configuration_id}/activate-configuration",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["configuration_id"] == initial_configuration_id
        assert data["status"] == "active"

        # Create another configuration draft and try to activate it. Assert that the confirmation
        # returned matches the new draft ID
        payload = {"condition_id": condition_id_to_test}
        new_draft_response = await authed_client.post(
            "/api/v1/configurations/", json=payload
        )
        new_draft_response_data = new_draft_response.json()
        assert new_draft_response.status_code == 200
        assert "id" in new_draft_response_data

        new_draft_response_id = new_draft_response_data["id"]
        payload = {"condition_canonical_url": canonical_url}
        new_draft_activation_response = await authed_client.patch(
            f"/api/v1/configurations/{new_draft_response_id}/activate-configuration",
            json=payload,
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
