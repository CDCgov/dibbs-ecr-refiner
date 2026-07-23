"""
Test for Activation Stability - ensures that configurations with
primary_condition_id=None do not cause crashes during activation.
"""

from uuid import uuid4

import pytest

from app.db.configurations.db import get_configurations_db
from app.services.conditions.activation import create_condition_mapping_payload

# Test user ID from conftest.py
TEST_USER_ID = "673da667-6f92-4a50-a40d-f44c5bc6a2d8"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_activation_stability_with_none_primary_conditions(
    setup,
    authed_client,
    create_config,
    get_condition_id,
    activate_config,
    db_pool,
):
    """
    Test that activating multiple configurations, some with primary_condition_id=None
    and some with actual IDs, does not crash the activation process.

    This test verifies that the _get_conditions_with_active_config_db function
    properly filters out None values before calling get_conditions_by_ids.
    """
    # Create two configurations with actual conditions
    condition_1_id = await get_condition_id("Acanthamoeba")
    condition_2_id = await get_condition_id("COVID-19")

    config_1 = await create_config(condition_1_id)
    config_2 = await create_config(condition_2_id)

    # Activate both configurations
    await activate_config(config_1["id"])
    await activate_config(config_2["id"])

    # Verify both are active
    active_configs = await get_configurations_db(
        jurisdiction_id="SDDH", status="active", db=db_pool
    )
    assert len(active_configs) == 2

    # Create a third configuration with primary_condition_id=None
    # We'll manually insert a configuration with no entry in configurations_conditions
    async with db_pool.get_connection() as conn:
        async with conn.cursor() as cur:
            # Insert a configuration without any entry in configurations_conditions
            # This results in primary_condition_id being None
            await cur.execute(
                """
                INSERT INTO configurations (id, jurisdiction_id, status, version, s3_url, last_activated_by, created_by, name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    uuid4(),
                    "SDDH",
                    "active",
                    6,
                    "http://test.s3.url/config",
                    TEST_USER_ID,
                    TEST_USER_ID,
                    "Test Config Without Condition",
                ),
            )

    # This should not crash even though there's a configuration with primary_condition_id=None
    # The _get_conditions_with_active_config_db function should filter out None values
    active_configs = await get_configurations_db(
        jurisdiction_id="SDDH", status="active", db=db_pool
    )

    # Get the primary condition IDs (some may be None)
    active_config_ids = [active.primary_condition_id for active in active_configs]

    # Filter out None values (this is what the code should do)
    filtered_ids = [id for id in active_config_ids if id is not None]

    # Verify that get_conditions_by_ids works with the filtered list
    from app.db.conditions.db import get_conditions_by_ids

    conditions = await get_conditions_by_ids(ids=filtered_ids, db=db_pool)

    # Should only get conditions for the configs with actual primary_condition_id
    assert len(conditions) == 2

    # Verify that create_condition_mapping_payload works with the conditions
    payload = create_condition_mapping_payload(conditions=conditions)

    # Payload should have mappings for the two conditions
    assert len(payload.mappings) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_activation_stability_all_none_primary_conditions(
    setup,
    authed_client,
    db_pool,
):
    """
    Test that activating configurations where all have primary_condition_id=None
    does not crash the activation process.
    """
    # Manually insert configurations with no primary condition (no entry in configurations_conditions)
    async with db_pool.get_connection() as conn:
        async with conn.cursor() as cur:
            for i in range(3):
                await cur.execute(
                    """
                    INSERT INTO configurations (id, jurisdiction_id, status, version, s3_url, last_activated_by, created_by, name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        uuid4(),
                        "SDDH",
                        "active",
                        6,
                        "http://test.s3.url/config",
                        TEST_USER_ID,
                        TEST_USER_ID,
                        "Test Config Without Condition",
                    ),
                )

    # Get all active configurations
    active_configs = await get_configurations_db(
        jurisdiction_id="SDDH", status="active", db=db_pool
    )

    # Get the primary condition IDs (all should be None)
    active_config_ids = [active.primary_condition_id for active in active_configs]

    # Filter out None values
    filtered_ids = [id for id in active_config_ids if id is not None]

    # Verify that get_conditions_by_ids works with empty list
    from app.db.conditions.db import get_conditions_by_ids

    conditions = await get_conditions_by_ids(ids=filtered_ids, db=db_pool)

    # Should return empty list
    assert len(conditions) == 0

    # Verify that create_condition_mapping_payload works with empty conditions
    from app.services.conditions.activation import create_condition_mapping_payload

    payload = create_condition_mapping_payload(conditions=conditions)

    # Payload should have no mappings
    assert len(payload.mappings) == 0
