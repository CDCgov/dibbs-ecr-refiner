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

        async with (
            db_pool.get_connection() as conn,
            conn.cursor(row_factory=dict_row) as cur,
        ):
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

    async def test_configurations_to_update_route_runs(
        self,
        authed_client,
        get_condition_id,
        create_config,
        activate_config,
        previous_tes_version,
    ):
        """
        Exercises `GET /tes/configurations-to-update` end to end.

        This route had **no** coverage, and its query referenced `conf.name` after
        that column became `conf.display_name` -- so it raised `UndefinedColumn` in
        production while every other suite stayed green. The assertions are
        deliberately shallow: the point is that the SQL executes and the response
        model builds, which is exactly what nothing was checking.
        """

        condition_id = await get_condition_id("Acanthamoeba", previous_tes_version)
        config = await create_config(condition_id)
        await activate_config(config["id"])

        response = await authed_client.get("/api/v1/tes/configurations-to-update")
        assert response.status_code == 200

        body = response.json()
        assert set(body) == {"existing_drafts", "drafts_to_create"}

        # the label field the rename touched has to come back populated
        for bucket in ("existing_drafts", "drafts_to_create"):
            for entry in body[bucket]:
                assert entry["configuration_display_name"]
                assert "configuration_name" not in entry
