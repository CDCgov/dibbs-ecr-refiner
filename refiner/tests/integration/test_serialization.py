from dataclasses import replace

import pytest
from fastapi import status

from app.db.configurations.db import get_configuration_by_id_db
from app.services.configurations import convert_config_to_storage_payload
from app.services.ecr.specification.constants import OID_TO_SYSTEM_KEY_MAP
from app.services.logger import get_logger


@pytest.mark.integration
@pytest.mark.asyncio
class TestSerialization:
    async def test_stale_trigger_section_is_normalized_before_serialization(
        self,
        create_config,
        get_condition_id,
        test_user_jurisdiction_id,
        db_pool,
    ):
        """
        Activation serializes straight from the database rows, so a stale
        include=false on a trigger code section must be corrected here — an
        inactive configuration can be re-activated without passing through
        the API validators or the clone path.
        """

        condition_id = await get_condition_id("Ophthalmia Neonatorum")
        config_metadata = await create_config(condition_id)
        config = await get_configuration_by_id_db(
            id=config_metadata["id"],
            jurisdiction_id=test_user_jurisdiction_id,
            db=db_pool,
        )
        assert config

        results_code = "30954-2"
        stale_sections = [
            replace(section, include=False) if section.code == results_code else section
            for section in config.section_processing
        ]
        assert any(
            s.code == results_code and s.include is False for s in stale_sections
        ), "fixture must contain the Results section to exercise this path"

        payload = await convert_config_to_storage_payload(
            configuration=replace(config, section_processing=stale_sections),
            db=db_pool,
            logger=get_logger(),
        )
        assert payload

        serialized = {s["code"]: s for s in payload.sections}
        assert serialized[results_code]["include"] is True

        # a section that carries no trigger codes is left exactly as configured
        social_history_code = "29762-2"
        assert serialized[social_history_code]["include"] is True

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
            configuration=ophtalmia_config, db=db_pool, logger=get_logger()
        )

        assert payload

        for k, coding in payload.code_system_sets.items():
            assert k in OID_TO_SYSTEM_KEY_MAP.values()

            for c in coding:
                assert c["code"] and c["code"] != ""
                assert c["display"] and c["display"] != ""
                assert c["system"] in OID_TO_SYSTEM_KEY_MAP.keys()

    async def test_exclusion_excludes_code_from_serialization(
        self,
        create_config,
        get_code_ids_by_value,
        get_condition_id,
        test_user_jurisdiction_id,
        db_pool,
        authed_client,
    ):
        condition_name = "Ophthalmia Neonatorum"
        condition_id = await get_condition_id(condition_name)

        config_metadata = await create_config(condition_id)
        config_id = config_metadata["id"]

        ophtalmia_config = await get_configuration_by_id_db(
            id=config_id, jurisdiction_id=test_user_jurisdiction_id, db=db_pool
        )
        assert ophtalmia_config

        payload = await convert_config_to_storage_payload(
            configuration=ophtalmia_config, db=db_pool, logger=get_logger()
        )

        assert payload
        payload_without_exclusion_length = 0

        for k, coding in payload.code_system_sets.items():
            assert k in OID_TO_SYSTEM_KEY_MAP.values()

            for c in coding:
                payload_without_exclusion_length += 1
                assert c["code"] and c["code"] != "" and c["code"]
                assert c["display"] and c["display"] != ""
                assert c["system"] in OID_TO_SYSTEM_KEY_MAP.keys()

        # exclude codes and ensure the payloads on reserialization pick up the change
        # both must be non-trigger codes for the condition: the primary
        # condition's eICR trigger codes are rejected by set-status
        codes_to_exclude = ["12236161000119108", "12236121000119103"]
        code_ids_to_exclude = await get_code_ids_by_value(
            condition_id=condition_id, code_values=codes_to_exclude
        )

        response = await authed_client.post(
            f"/api/v1/configurations/{config_id}/set-status?status=excluded&update_beyond_rendered_set=false",
            json={
                "code_ids": [str(c["id"]) for c in code_ids_to_exclude],
                "code_ids_to_skip": [],
            },
        )
        assert response.status_code == status.HTTP_200_OK

        payload_with_exclusion = await convert_config_to_storage_payload(
            configuration=ophtalmia_config, db=db_pool, logger=get_logger()
        )
        assert payload_with_exclusion
        payload_with_exclusion_length = 0

        for k, coding in payload_with_exclusion.code_system_sets.items():
            assert k in OID_TO_SYSTEM_KEY_MAP.values()

            for c in coding:
                payload_with_exclusion_length += 1
                assert (
                    c["code"] and c["code"] != "" and c["code"] not in codes_to_exclude
                )

        assert payload_without_exclusion_length == payload_with_exclusion_length + len(
            codes_to_exclude
        )

    async def test_exclusion_and_codeset_disassociation_properly_cleans_codes(
        self,
        create_config,
        get_code_ids_by_value,
        get_condition_id,
        test_user_jurisdiction_id,
        db_pool,
        authed_client,
        associate_codeset,
        disassociate_codeset,
        get_condition_by_id,
    ):
        condition_name = "COVID-19"
        condition_id = await get_condition_id(condition_name)

        config_metadata = await create_config(condition_id)
        config_id = config_metadata["id"]

        covid_config = await get_configuration_by_id_db(
            id=config_id, jurisdiction_id=test_user_jurisdiction_id, db=db_pool
        )
        assert covid_config

        # associate a code set
        alpha_gal_id = await get_condition_id("Alpha-gal Syndrome")
        await associate_codeset(config_id, alpha_gal_id)

        # exclude codes from alpha gal
        alpha_gal_code_to_exclude = ["Z91.014", "703930000"]
        code_ids_to_exclude = await get_code_ids_by_value(
            condition_id=condition_id, code_values=alpha_gal_code_to_exclude
        )

        exclusion_response = await authed_client.post(
            f"/api/v1/configurations/{config_id}/set-status?status=excluded&update_beyond_rendered_set=false",
            json={
                "code_ids": [str(c["id"]) for c in code_ids_to_exclude],
                "code_ids_to_skip": [],
            },
        )
        assert exclusion_response.status_code == status.HTTP_200_OK

        # disassociate alpha gal
        await disassociate_codeset(config_id, alpha_gal_id)

        payload = await convert_config_to_storage_payload(
            configuration=covid_config, db=db_pool, logger=get_logger()
        )
        assert payload

        alpha_gal_codes = (await get_condition_by_id(id=alpha_gal_id))["codes"]

        # make sure the code sets don't include the excluded codes
        for k, coding in payload.code_system_sets.items():
            assert k in OID_TO_SYSTEM_KEY_MAP.values()

            for c in coding:
                assert (
                    c["code"] and c["code"] != "" and c["code"] not in alpha_gal_codes
                )
