import pytest


@pytest.mark.integration
@pytest.mark.asyncio
class TestConfigurations:
    async def test_create_configuration(self, setup, authed_client, test_username):
        # Get a condition to use to create a config
        response = await authed_client.get("/api/v1/conditions/")
        conditions = response.json()

        matched_condition = next(
            (c for c in conditions if c["display_name"] == "Drowning and Submersion"),
            None,
        )

        # Create config
        payload = {
            "condition_id": matched_condition["id"] if matched_condition else None
        }
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        # assert response.status_code == 200
        assert "id" in response.json()
        assert "name" in response.json()
        assert response.json()["name"] == "Drowning and Submersion"

        # Assert that associated config creation event was logged
        response = await authed_client.get("/api/v1/events/")
        assert response.status_code == 200
        assert len(response.json()) == 1
        event = response.json()[0]
        assert event["username"] == test_username
        assert event["configuration_name"] == matched_condition["display_name"]
        assert event["action_text"] == "Created configuration."
