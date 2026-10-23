import unittest

from app.db.codes.model import DbConfigurationCode
from app.db.conditions.model import DbCondition
from app.db.configurations.model import DbConfiguration
from app.services.configurations import convert_config_to_storage_payload
from app.services.ecr.specification.constants import OTHER_OID
from app.services.terminology import ProcessedConfiguration
from tests.unit.conftest import create_mock_systems


async def create_processed_config(
    config: DbConfiguration, conditions: list[DbCondition]
):
    mock_systems = create_mock_systems()
    systems_by_id = {m.id: m for m in mock_systems}

    def _as_row(code) -> DbConfigurationCode:
        """
        Mirrors what `get_pruned_configuration_codes_db` resolves in SQL.

        The real query joins `systems` and returns an OID, so the mock hands back
        `DbConfigurationCode` too -- a mock returning any other shape would let a
        signature change pass silently here.
        """

        system = systems_by_id.get(code.system_id)
        return DbConfigurationCode(
            code=code.code,
            display_name=code.display_name,
            system_oid=system.oid if system and system.oid else OTHER_OID,
        )

    pruned = [
        _as_row(code)
        for code in (
            list(config.custom_codes) + [item for c in conditions for item in c.codes]
        )
    ]

    with (
        unittest.mock.patch(
            "app.services.configurations.get_included_conditions_db",
            return_value=conditions,
        ),
        unittest.mock.patch(
            "app.services.configurations.get_id_to_code_system_dict_db",
            new=unittest.mock.AsyncMock(return_value=systems_by_id),
        ),
        unittest.mock.patch(
            "app.services.configurations.get_pruned_configuration_codes_db",
            new=unittest.mock.AsyncMock(return_value=pruned),
        ),
    ):
        storage_payload = await convert_config_to_storage_payload(
            configuration=config,
            db=unittest.mock.AsyncMock(),
            logger=unittest.mock.AsyncMock(),
        )

    if storage_payload is None:
        raise ValueError("convert_config_to_storage_payload returned None unexpectedly")

    return ProcessedConfiguration.from_dict(storage_payload.to_dict())
