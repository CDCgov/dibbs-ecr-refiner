"""
Test for Activation Stability - ensures that configurations with
primary_condition_id=None do not cause crashes during activation.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.v1.configurations.activation import _get_conditions_with_active_config_db
from app.db.configurations.model import DbConfiguration


@pytest.mark.asyncio
async def test_get_conditions_with_active_config_filters_none_primary_condition_ids():
    """
    Test that _get_conditions_with_active_config_db filters out None values
    from primary_condition_id before calling get_conditions_by_ids.
    """
    # Create mock database
    mock_db = MagicMock()
    mock_cursor = AsyncMock()
    mock_cursor.fetchall = AsyncMock(return_value=[])
    mock_cursor.execute = AsyncMock()

    mock_conn = AsyncMock()
    mock_conn.cursor = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_cursor),
            __aexit__=AsyncMock(return_value=None),
        )
    )

    mock_db.get_connection = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=None),
        )
    )

    # Create mock configurations - some with primary_condition_id=None, some with valid UUIDs
    config_with_condition = DbConfiguration(
        id=uuid4(),
        name="Config with condition",
        jurisdiction_id="SDDH",
        primary_condition_id=uuid4(),  # Valid UUID
        original_condition_id=uuid4(),
        included_conditions=[],
        custom_codes=[],
        section_processing=[],
        version=1,
        status="active",
        last_activated_at=None,
        last_activated_by=None,
        created_by=uuid4(),
        s3_url="http://test.s3.url/config",
    )

    config_without_condition = DbConfiguration(
        id=uuid4(),
        name="Config without condition",
        jurisdiction_id="SDDH",
        primary_condition_id=None,  # None value
        original_condition_id=None,
        included_conditions=[],
        custom_codes=[],
        section_processing=[],
        version=1,
        status="active",
        last_activated_at=None,
        last_activated_by=None,
        created_by=uuid4(),
        s3_url="http://test.s3.url/config2",
    )

    another_config_with_condition = DbConfiguration(
        id=uuid4(),
        name="Another config with condition",
        jurisdiction_id="SDDH",
        primary_condition_id=uuid4(),  # Valid UUID
        original_condition_id=uuid4(),
        included_conditions=[],
        custom_codes=[],
        section_processing=[],
        version=1,
        status="active",
        last_activated_at=None,
        last_activated_by=None,
        created_by=uuid4(),
        s3_url="http://test.s3.url/config3",
    )

    active_configs = [
        config_with_condition,
        config_without_condition,
        another_config_with_condition,
    ]

    # Mock get_configurations_db to return our test configs
    with patch(
        "app.api.v1.configurations.activation.get_configurations_db",
        new_callable=AsyncMock,
    ) as mock_get_configs:
        mock_get_configs.return_value = active_configs

        # Track what IDs were passed to get_conditions_by_ids
        captured_ids = []

        async def mock_get_conditions_by_ids(ids, db):
            captured_ids.extend(ids)
            return []

        with patch(
            "app.api.v1.configurations.activation.get_conditions_by_ids",
            new_callable=AsyncMock,
        ) as mock_get_conditions:
            mock_get_conditions.side_effect = mock_get_conditions_by_ids

            # Call the function
            await _get_conditions_with_active_config_db(
                jurisdiction_id="SDDH", db=mock_db
            )

            # Verify get_configurations_db was called
            mock_get_configs.assert_called_once()

            # Verify get_conditions_by_ids was called
            mock_get_conditions.assert_called_once()

            # Get the IDs that were passed
            call_args = mock_get_conditions.call_args
            passed_ids = call_args[1]["ids"]  # keyword argument

            # Assert that None was NOT in the list of IDs passed to get_conditions_by_ids
            assert None not in passed_ids, (
                "None values should be filtered out before calling get_conditions_by_ids"
            )

            # Assert that only valid UUIDs were passed
            assert len(passed_ids) == 2, (
                "Should only pass 2 valid UUIDs (excluding the None)"
            )

            # Assert that the IDs are valid UUIDs
            for id in passed_ids:
                assert isinstance(id, uuid4.__class__) or isinstance(id, type(uuid4()))


@pytest.mark.asyncio
async def test_get_conditions_with_active_config_all_none_primary_condition_ids():
    """
    Test that _get_conditions_with_active_config_db handles the case where
    all configurations have primary_condition_id=None.
    """
    # Create mock database
    mock_db = MagicMock()
    mock_cursor = AsyncMock()
    mock_cursor.fetchall = AsyncMock(return_value=[])
    mock_cursor.execute = AsyncMock()

    mock_conn = AsyncMock()
    mock_conn.cursor = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_cursor),
            __aexit__=AsyncMock(return_value=None),
        )
    )

    mock_db.get_connection = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=None),
        )
    )

    # Create mock configurations - all with primary_condition_id=None
    config_without_condition_1 = DbConfiguration(
        id=uuid4(),
        name="Config without condition 1",
        jurisdiction_id="SDDH",
        primary_condition_id=None,
        included_conditions=[],
        custom_codes=[],
        section_processing=[],
        version=1,
        status="active",
        last_activated_at=None,
        last_activated_by=None,
        created_by=uuid4(),
        s3_url="http://test.s3.url/config1",
    )

    config_without_condition_2 = DbConfiguration(
        id=uuid4(),
        name="Config without condition 2",
        jurisdiction_id="SDDH",
        primary_condition_id=None,
        included_conditions=[],
        custom_codes=[],
        section_processing=[],
        version=1,
        status="active",
        last_activated_at=None,
        last_activated_by=None,
        created_by=uuid4(),
        s3_url="http://test.s3.url/config2",
    )

    active_configs = [config_without_condition_1, config_without_condition_2]

    # Mock get_configurations_db to return our test configs
    with patch(
        "app.api.v1.configurations.activation.get_configurations_db",
        new_callable=AsyncMock,
    ) as mock_get_configs:
        mock_get_configs.return_value = active_configs

        # Track what IDs were passed to get_conditions_by_ids
        captured_ids = []

        async def mock_get_conditions_by_ids(ids, db):
            captured_ids.extend(ids)
            return []

        with patch(
            "app.api.v1.configurations.activation.get_conditions_by_ids",
            new_callable=AsyncMock,
        ) as mock_get_conditions:
            mock_get_conditions.side_effect = mock_get_conditions_by_ids

            # Call the function - should not crash
            await _get_conditions_with_active_config_db(
                jurisdiction_id="SDDH", db=mock_db
            )

            # Verify get_conditions_by_ids was called
            mock_get_conditions.assert_called_once()

            # Get the IDs that were passed
            call_args = mock_get_conditions.call_args
            passed_ids = call_args[1]["ids"]  # keyword argument

            # Assert that the list is empty (all None values filtered out)
            assert len(passed_ids) == 0, (
                "Should pass empty list when all primary_condition_ids are None"
            )

            # Assert that None was NOT in the list
            assert None not in passed_ids, "None values should be filtered out"


@pytest.mark.asyncio
async def test_get_conditions_with_active_config_mixed_active_configs():
    """
    Test that _get_conditions_with_active_config_db correctly handles a mix
    of configurations with and without primary_condition_id.
    """
    # Create mock database
    mock_db = MagicMock()
    mock_cursor = AsyncMock()
    mock_cursor.fetchall = AsyncMock(return_value=[])
    mock_cursor.execute = AsyncMock()

    mock_conn = AsyncMock()
    mock_conn.cursor = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_cursor),
            __aexit__=AsyncMock(return_value=None),
        )
    )

    mock_db.get_connection = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=None),
        )
    )

    # Create a mix of configurations
    configs = []
    valid_uuids = [uuid4() for _ in range(5)]

    for i in range(10):
        if i % 2 == 0:
            # Config with valid primary_condition_id
            configs.append(
                DbConfiguration(
                    id=uuid4(),
                    name=f"Config {i}",
                    jurisdiction_id="SDDH",
                    primary_condition_id=valid_uuids[i // 2],
                    included_conditions=[],
                    custom_codes=[],
                    section_processing=[],
                    version=1,
                    status="active",
                    last_activated_at=None,
                    last_activated_by=None,
                    created_by=uuid4(),
                    s3_url=f"http://test.s3.url/config{i}",
                )
            )
        else:
            # Config without primary_condition_id
            configs.append(
                DbConfiguration(
                    id=uuid4(),
                    name=f"Config {i}",
                    jurisdiction_id="SDDH",
                    primary_condition_id=None,
                    included_conditions=[],
                    custom_codes=[],
                    section_processing=[],
                    version=1,
                    status="active",
                    last_activated_at=None,
                    last_activated_by=None,
                    created_by=uuid4(),
                    s3_url=f"http://test.s3.url/config{i}",
                )
            )

    # Mock get_configurations_db to return our test configs
    with patch(
        "app.api.v1.configurations.activation.get_configurations_db",
        new_callable=AsyncMock,
    ) as mock_get_configs:
        mock_get_configs.return_value = configs

        # Track what IDs were passed to get_conditions_by_ids
        captured_ids = []

        async def mock_get_conditions_by_ids(ids, db):
            captured_ids.extend(ids)
            return []

        with patch(
            "app.api.v1.configurations.activation.get_conditions_by_ids",
            new_callable=AsyncMock,
        ) as mock_get_conditions:
            mock_get_conditions.side_effect = mock_get_conditions_by_ids

            # Call the function
            await _get_conditions_with_active_config_db(
                jurisdiction_id="SDDH", db=mock_db
            )

            # Verify get_conditions_by_ids was called
            mock_get_conditions.assert_called_once()

            # Get the IDs that were passed
            call_args = mock_get_conditions.call_args
            passed_ids = call_args[1]["ids"]  # keyword argument

            # Assert that None was NOT in the list
            assert None not in passed_ids, "None values should be filtered out"

            # Assert that exactly 5 valid UUIDs were passed (5 configs with conditions)
            assert len(passed_ids) == 5, "Should pass exactly 5 valid UUIDs"

            # Assert all passed IDs are valid UUIDs
            for id in passed_ids:
                assert id is not None
