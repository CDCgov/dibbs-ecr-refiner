import pytest
from psycopg.rows import dict_row


@pytest.mark.integration
@pytest.mark.asyncio
class TestTesUpdates:
    async def test_create_drafts_from_active_configurations_logs_event(
        self,
        authed_client,
        get_condition_id,
        create_config,
        activate_config,
        db_pool,
        test_user_id,
        previous_tes_version,
    ):
        condition_id = await get_condition_id("Acanthamoeba", previous_tes_version)
        config = await create_config(condition_id)
        await activate_config(config["id"])

        response = await authed_client.post(
            "/api/v1/tes/configurations/drafts-from-active",
            json={"configuration_ids": [config["id"]]},
        )
        assert response.status_code == 200

        body = response.json()
        assert body["created_count"] == 1
        assert len(body["created_configuration_ids"]) == 1

        draft_id = body["created_configuration_ids"][0]

        async with db_pool.get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT *
                    FROM events
                    WHERE configuration_id = %s
                      AND event_type = 'tes_create_draft_from_active'
                    """,
                    (draft_id,),
                )
                rows = await cur.fetchall()

        assert len(rows) == 1
        assert rows[0]["action_text"] == (
            "Created draft from active configuration with TES updates"
        )
        assert str(rows[0]["user_id"]) == test_user_id
