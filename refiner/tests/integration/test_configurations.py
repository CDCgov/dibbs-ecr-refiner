from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import status
from psycopg.rows import dict_row

from app.db.configurations.activations.db import activate_configuration_db
from app.db.configurations.db import get_configuration_by_id_db

LOCALSTACK_BASE_URL = "http://localhost:4566/local-config-bucket/configurations/SDDH"
EXPECTED_DROWNING_CG_UUID = "c05cab96-c023-4ee2-bb7d-071fb600be7b"
EXPECTED_DROWNING_RSG_CODE = "212962007"


@pytest.mark.integration
@pytest.mark.asyncio
class TestConfigurations:
    async def test_create_configuration(
        self, setup, authed_client, test_username, get_condition_id
    ):
        condition_name = "Drowning and Submersion"
        condition_id = await get_condition_id(condition_name)

        # Create config
        payload = {"condition_id": str(condition_id)}
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert "id" in response.json()
        assert "name" in response.json()
        assert response.json()["name"] == "Drowning and Submersion"

        # Assert that associated config creation event was logged
        response = await authed_client.get("/api/v1/events/")
        assert response.status_code == status.HTTP_200_OK
        audit_events = response.json()["audit_events"]
        assert len(audit_events) == 1

        creation_event = audit_events[0]
        assert creation_event is not None
        assert creation_event["username"] == test_username
        assert creation_event["configuration_name"] == condition_name

        # Attempt to create the same config again (should fail)
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        assert response.status_code == status.HTTP_409_CONFLICT

        # Make sure no new event was created during failure
        response = await authed_client.get("/api/v1/events/")
        assert response.status_code == status.HTTP_200_OK
        failure_audit_events = response.json()["audit_events"]
        assert len(failure_audit_events) == 1

    async def test_custom_sections(self, setup, authed_client, get_condition_id):
        condition_id = await get_condition_id("Glanders")
        # Create config
        payload = {"condition_id": str(condition_id)}
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        assert response.status_code == status.HTTP_200_OK

        # create a new custom section
        config_id = response.json()["id"]
        original_payload = {"name": "test section name", "code": "section-code123"}
        payload = original_payload
        response = await authed_client.post(
            f"/api/v1/configurations/{config_id}/sections", json=payload
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == "section-code123"

        # try adding one with a duplicate name
        payload = {"name": "test section name", "code": "new-code"}
        response = await authed_client.post(
            f"/api/v1/configurations/{config_id}/sections", json=payload
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Section name is already in use."

        # try adding one with a duplicate code
        payload = {"name": "new name", "code": "section-code123"}
        response = await authed_client.post(
            f"/api/v1/configurations/{config_id}/sections", json=payload
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Section code is already in use."

        # editing the custom section with the original values should work
        payload = {
            "name": original_payload["name"],
            "current_code": original_payload["code"],
            "new_code": original_payload["code"],
        }
        response = await authed_client.patch(
            f"/api/v1/configurations/{config_id}/sections", json=payload
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == payload["new_code"]

        # try editing in a new name and new code
        payload = {
            "name": "new name",
            "current_code": original_payload["code"],
            "new_code": "new-code",
        }

        response = await authed_client.patch(
            f"/api/v1/configurations/{config_id}/sections", json=payload
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == payload["new_code"]

        # for good measure, try editing a standard section's name and code which shouldn't work
        medications_admin_code = "29549-3"
        payload = {
            "name": "This should not work",
            "new_code": "This also should not work",
            "current_code": medications_admin_code,
        }
        response = await authed_client.patch(
            f"/api/v1/configurations/{config_id}/sections", json=payload
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == medications_admin_code

    async def test_section_updates_success(
        self, setup, authed_client, get_condition_id
    ):
        # helper function to get section
        def require_section_by_code(sections, code):
            section = next((s for s in sections if s["code"] == code), None)
            assert section is not None, f"Section with code {code} not found"
            return section

        condition_name = "Drowning and Submersion"
        condition_id = await get_condition_id(condition_name)

        # Create config
        payload = {"condition_id": str(condition_id)}
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        assert response.status_code == status.HTTP_200_OK

        draft_id = response.json()["id"]
        admission_diagnosis_code = "46241-6"

        response = await authed_client.get(f"/api/v1/configurations/{draft_id}")
        response.status_code == status.HTTP_200_OK

        # Get the admission diagnosis section
        admission_diagnosis_section = require_section_by_code(
            response.json()["section_processing"], admission_diagnosis_code
        )
        expected_section_defaults = {
            "include": True,
            "narrative": True,
            "action": "refine",
            "name": "Admission Diagnosis",
            "code": "46241-6",
            "versions": ["3.1", "3.1.1"],
            "section_type": "standard",
        }

        assert admission_diagnosis_section is not None
        assert admission_diagnosis_section == expected_section_defaults

        url = f"/api/v1/configurations/{draft_id}/sections"

        # set to "retain" and exclude
        response = await authed_client.patch(
            url,
            json={
                "action": "retain",
                "current_code": admission_diagnosis_code,
                "include": False,
                "narrative": False,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.text == f'"{admission_diagnosis_code}"'

        # Get the updated admission diagnosis section
        response = await authed_client.get(f"/api/v1/configurations/{draft_id}")
        response.status_code == status.HTTP_200_OK
        admission_diagnosis_section = require_section_by_code(
            response.json()["section_processing"], admission_diagnosis_code
        )
        expected_section_updates = {
            "include": False,
            "narrative": False,
            "action": "retain",
            "name": "Admission Diagnosis",
            "code": "46241-6",
            "versions": ["3.1", "3.1.1"],
            "section_type": "standard",
        }

        assert admission_diagnosis_section is not None
        assert admission_diagnosis_section == expected_section_updates

    async def test_section_updates_failure(
        self, setup, authed_client, get_condition_id
    ):
        condition_name = "Drowning and Submersion"
        condition_id = await get_condition_id(condition_name)

        # Create config
        payload = {"condition_id": str(condition_id)}
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        assert response.status_code == status.HTTP_200_OK

        draft_id = response.json()["id"]

        response = await authed_client.get(f"/api/v1/configurations/{draft_id}")
        response.status_code == status.HTTP_200_OK

        url = f"/api/v1/configurations/{draft_id}/sections"

        # try to update a code that doesn't exist
        nonexistent_code = "fakecode"
        response = await authed_client.patch(
            url,
            json={
                "action": "retain",
                "current_code": nonexistent_code,
                "include": False,
                "narrative": False,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.json()["detail"]
            == f"Section with code {nonexistent_code} is invalid and can't be updated."
        )

        admission_diagnosis_code = "46241-6"
        # try an invalid action
        response = await authed_client.patch(
            url,
            json={
                "action": "remove",
                "current_code": admission_diagnosis_code,
                "include": False,
                "narrative": False,
            },
        )
        # FastAPI shouldn't allow this to work
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_activate_configuration(
        self,
        setup,
        authed_client,
        get_condition_id,
        get_condition_by_id,
        get_config_by_id,
    ):
        condition_name = "Drowning and Submersion"
        condition_id = await get_condition_id(condition_name)

        # Create config
        payload = {"condition_id": str(condition_id)}
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        assert response.status_code == status.HTTP_200_OK

        draft_id = response.json()["id"]
        response = await authed_client.patch(
            f"/api/v1/configurations/{draft_id}/activate"
        )
        assert response.status_code == status.HTTP_200_OK

        # Mapping file and content
        mapping_file = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/rsg_cg_mapping.json"
        )

        mapping_file_json = mapping_file.json()
        assert EXPECTED_DROWNING_RSG_CODE in mapping_file_json
        assert (
            mapping_file_json[EXPECTED_DROWNING_RSG_CODE]["canonical_url"]
            == f"https://tes.tools.aimsplatform.org/api/fhir/ValueSet/{EXPECTED_DROWNING_CG_UUID}"
        )
        assert (
            mapping_file_json[EXPECTED_DROWNING_RSG_CODE]["name"]
            == "DrowningandSubmersion"
        )
        assert mapping_file_json[EXPECTED_DROWNING_RSG_CODE]["tes_version"] is not None

        # Activation file and content
        activation_file = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/1/active.json"
        )
        activation_file_json = activation_file.json()

        TOTAL_EXPECTED_CONDITION_CODE_COUNT = 481
        TOTAL_EXPECTED_SECTION_COUNT = 21
        TOTAL_EXPECTED_INCLUDED_CONDITION_RSG_CODES = (
            1  # No other conditions were included
        )

        assert len(activation_file_json["codes"]) == TOTAL_EXPECTED_CONDITION_CODE_COUNT
        assert len(activation_file_json["sections"]) == TOTAL_EXPECTED_SECTION_COUNT
        assert (
            len(activation_file_json["included_condition_rsg_codes"])
            == TOTAL_EXPECTED_INCLUDED_CONDITION_RSG_CODES
        )
        assert (
            activation_file_json["included_condition_rsg_codes"][0]
            == EXPECTED_DROWNING_RSG_CODE
        )

        # Metadata file and content
        metadata_file = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/1/metadata.json"
        )
        metadata_file_json = metadata_file.json()
        condition = await get_condition_by_id(condition_id)
        draft_config = await get_config_by_id(draft_id)

        assert metadata_file_json["condition_name"] == condition["display_name"]
        assert metadata_file_json["canonical_url"] == condition["canonical_url"]
        assert metadata_file_json["tes_version"] == condition["version"]
        assert metadata_file_json["jurisdiction_id"] == draft_config["jurisdiction_id"]
        assert metadata_file_json["configuration_version"] == draft_config["version"]
        assert len(metadata_file_json["child_rsg_snomed_codes"]) == 1
        assert (
            metadata_file_json["child_rsg_snomed_codes"][0]
            == EXPECTED_DROWNING_RSG_CODE
        )

        # Current file and content
        current_file = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/current.json"
        )
        assert current_file.json()["version"] == 1

        # Now create a new configuration for activation
        payload = {"condition_id": str(condition_id)}
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        assert response.status_code == status.HTTP_200_OK
        config_data = response.json()
        initial_configuration_id = config_data["id"]
        # Use the condition_id from the payload for subsequent steps
        condition_id_to_test = payload["condition_id"]

        # Activate config
        response = await authed_client.patch(
            f"/api/v1/configurations/{initial_configuration_id}/activate"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["configuration_id"] == initial_configuration_id
        assert data["status"] == "active"

        # Check that new files exist in S3
        activation_file = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/2/active.json"
        )
        activation_file_json = activation_file.json()

        current_file = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/current.json"
        )
        assert current_file.json()["version"] == 2

        # Create another configuration draft and try to activate it. Assert that the confirmation
        # returned matches the new draft ID.
        payload = {"condition_id": condition_id_to_test}
        new_draft_response = await authed_client.post(
            "/api/v1/configurations/", json=payload
        )
        new_draft_response_data = new_draft_response.json()
        assert new_draft_response.status_code == status.HTTP_200_OK
        assert "id" in new_draft_response_data

        new_draft_response_id = new_draft_response_data["id"]
        new_draft_activation_response = await authed_client.patch(
            f"/api/v1/configurations/{new_draft_response_id}/activate"
        )
        assert new_draft_activation_response.status_code == status.HTTP_200_OK
        new_draft_activation_data = new_draft_activation_response.json()
        assert new_draft_activation_data["configuration_id"] == new_draft_response_id
        assert new_draft_activation_data["status"] == "active"

        # check that the old configuration isn't active anymore
        validation_response = await authed_client.get(
            f"/api/v1/configurations/{initial_configuration_id}"
        )
        assert validation_response.status_code == status.HTTP_200_OK

        validation_response_data = validation_response.json()
        assert validation_response_data["id"] == initial_configuration_id
        assert validation_response_data["status"] == "inactive"

    async def test_transaction_rollback_on_activation_failure(
        self, authed_client, get_condition_id, db_pool
    ):
        """
        Verifies rollback when activation fails after deactivation.
        """
        condition_name = "Drowning and Submersion"
        condition_id = await get_condition_id(condition_name)

        # Create v1 config
        payload = {"condition_id": str(condition_id)}
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        assert response.status_code == status.HTTP_200_OK

        # activate v1
        v1_config_id = response.json()["id"]
        response = await authed_client.patch(
            f"/api/v1/configurations/{v1_config_id}/activate"
        )
        assert response.status_code == status.HTTP_200_OK
        old_config_id = response.json()["configuration_id"]

        # Create v2 draft
        payload = {"condition_id": str(condition_id)}
        response = await authed_client.post("/api/v1/configurations/", json=payload)
        assert response.status_code == status.HTTP_200_OK
        new_config_id = response.json()["id"]

        # Patch _activate_configuration_db to fail after deactivation
        with patch(
            "app.db.configurations.activations.db._activate_configuration_db",
            return_value=None,
        ):
            result = await activate_configuration_db(
                configuration_id=new_config_id,
                activated_by_user_id=uuid4(),
                canonical_url="https://mock.com",
                jurisdiction_id="SDDH",
                s3_urls=["s3://bucket/key"],
                db=db_pool,
            )

            assert result is None  # activation failed

            old_config = await get_configuration_by_id_db(
                id=old_config_id, jurisdiction_id="SDDH", db=db_pool
            )

            assert old_config.status == "active"  # Should remain active due to rollback

            new_config = await get_configuration_by_id_db(
                id=new_config_id, jurisdiction_id="SDDH", db=db_pool
            )
            assert new_config.status == "draft"  # Should remain as draft

    async def test_deactivate_configuration(self, setup, authed_client, db_pool):
        # Get the activated configuration from the previous tests
        async with db_pool.get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT id, condition_canonical_url, condition_id
                    FROM configurations
                    WHERE name = 'Drowning and Submersion' AND status = 'active';
                    """
                )
                configuration = await cur.fetchone()
                assert configuration is not None

        initial_configuration_id = str(configuration["id"])

        # Deactivate config
        response = await authed_client.patch(
            f"/api/v1/configurations/{initial_configuration_id}/deactivate",
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["configuration_id"] == initial_configuration_id
        assert data["status"] == "inactive"

        mapping_file = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/rsg_cg_mapping.json"
        )

        # Drowning mapping should be removed from the file on deactivation
        mapping_file_json = mapping_file.json()
        assert EXPECTED_DROWNING_RSG_CODE not in mapping_file_json

        # Expect null version when deactivated
        current_file_resp = await authed_client.get(
            f"{LOCALSTACK_BASE_URL}/{EXPECTED_DROWNING_CG_UUID}/current.json"
        )
        assert current_file_resp.status_code == status.HTTP_200_OK

        # This is the previously activated version from the test above
        assert current_file_resp.json()["version"] is None
