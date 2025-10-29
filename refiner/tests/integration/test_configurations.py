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
        assert len(response.json()) == 1
        event = response.json()[0]
        assert event["username"] == test_username
        assert event["configuration_name"] == condition["display_name"]
        assert event["action_text"] == "Created configuration"

        # Attempt to create the same config again (should fail)
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        assert response.status_code == 409

        # Make sure no event was created during failure
        response = await authed_client.get("/api/v1/events/")
        assert response.status_code == 200
        assert len(response.json()) == 1
