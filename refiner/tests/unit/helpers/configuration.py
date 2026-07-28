import unittest

from app.db.conditions.model import DbCondition
from app.db.configurations.model import DbConfiguration
from app.services.configurations import convert_config_to_storage_payload
from app.services.terminology import ProcessedConfiguration
from tests.unit.conftest import create_mock_systems


async def create_processed_config(
    config: DbConfiguration, conditions: list[DbCondition]
):
    mock_systems = create_mock_systems()
    with (
        unittest.mock.patch(
            "app.services.configurations.get_included_conditions_db",
            return_value=conditions,
        ),
        unittest.mock.patch(
            "app.services.configurations.get_all_code_systems_db",
            new=unittest.mock.AsyncMock(return_value={m.id: m for m in mock_systems}),
        ),
    ):
        storage_payload = await convert_config_to_storage_payload(
            configuration=config,
            db=unittest.mock.AsyncMock(),
        )

    if storage_payload is None:
        raise ValueError("convert_config_to_storage_payload returned None unexpectedly")

    return ProcessedConfiguration.from_dict(storage_payload.to_dict())
