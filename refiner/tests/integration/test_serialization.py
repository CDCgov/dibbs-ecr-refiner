import pytest

from app.db.configurations.db import get_configuration_by_id_db
from app.services.configurations import convert_config_to_storage_payload
from app.services.ecr.specification.constants import OID_TO_SYSTEM_KEY_MAP


@pytest.mark.integration
@pytest.mark.asyncio
class TestSerialization:
    async def test_successful_serialization(
        self,
        create_config,
        activate_config,
        get_condition_id,
        test_user_jurisdiction_id,
        db_pool,
    ):
        condition_name = "Ophthalmia Neonatorum"
        condition_id = await get_condition_id(condition_name)

        config_metadata = await create_config(condition_id)
        config_id = config_metadata["id"]
        await activate_config(config_id)
        ophtalmia_config = await get_configuration_by_id_db(
            id=config_id, jurisdiction_id=test_user_jurisdiction_id, db=db_pool
        )
        assert ophtalmia_config

        payload = await convert_config_to_storage_payload(
            configuration=ophtalmia_config, db=db_pool
        )

        assert payload

        for k, coding in payload.code_system_sets.items():
            assert k in OID_TO_SYSTEM_KEY_MAP.values()

            for c in coding:
                assert c["code"] and c["code"] != ""
                assert c["display"] and c["display"] != ""
                assert c["system"] in OID_TO_SYSTEM_KEY_MAP.keys()
