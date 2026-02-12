from dataclasses import replace
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import status

from app.api.v1.configurations.models import GetConfigurationsResponse
from app.api.v1.configurations.testing import _upload_to_s3
from app.db.conditions.model import DbCondition, DbConditionCoding
from app.db.configurations.db import GetConfigurationResponseVersion
from app.db.configurations.model import (
    DbConfiguration,
    DbConfigurationCondition,
    DbConfigurationCustomCode,
)
from app.services.ecr.models import RefinedDocument, ReportableCondition
from app.services.testing import InlineTestingResult


@pytest.fixture
def new_config_id():
    return UUID("33333333-3333-3333-3333-333333333333")


@pytest.fixture(autouse=True)
def mock_db_functions(
    monkeypatch,
    mock_user,
    mock_configuration,
    mock_condition,
    new_config_id,
):
    """
    Mock return values of the `_db` functions called by the routes.
    """

    # prepare a fake condition with codes
    monkeypatch.setattr(
        "app.api.v1.configurations.base.get_condition_by_id_db",
        AsyncMock(return_value=mock_condition),
    )

    fake_condition = DbCondition(
        id=uuid4(),
        display_name="Hypertension",
        canonical_url="http://url.com",
        version="3.0.0",
        child_rsg_snomed_codes=["11111"],
        snomed_codes=[DbConditionCoding("11111", "Hypertension SNOMED")],
        loinc_codes=[DbConditionCoding("22222", "Hypertension LOINC")],
        icd10_codes=[DbConditionCoding("I10", "Essential hypertension")],
        rxnorm_codes=[DbConditionCoding("33333", "Hypertension RXNORM")],
    )

    monkeypatch.setattr(
        "app.api.v1.configurations.base.get_conditions_by_version_db",
        AsyncMock(return_value=[fake_condition]),
    )

    monkeypatch.setattr(
        "app.api.v1.configurations.base.get_configuration_by_id_db",
        AsyncMock(return_value=mock_configuration),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.base.get_included_conditions_db",
        AsyncMock(return_value=[mock_condition]),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.base.get_latest_config_db",
        AsyncMock(return_value=mock_configuration),
    )

    versions_mock = [
        GetConfigurationResponseVersion(
            id=mock_configuration.id,
            status="draft",
            version=1,
            condition_canonical_url="https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123",
            created_by=mock_user.id,
            created_at=datetime.now(),
            last_activated_at=None,
            last_activated_by=None,
        )
    ]

    monkeypatch.setattr(
        "app.api.v1.configurations.base.get_configuration_versions_db",
        AsyncMock(return_value=versions_mock),
    )

    # Mock get_configurations_db
    monkeypatch.setattr(
        "app.api.v1.configurations.base.get_configurations_db",
        AsyncMock(return_value=[mock_configuration]),
    )

    # Mock is_config_valid_to_insert_db
    monkeypatch.setattr(
        "app.api.v1.configurations.base.is_config_valid_to_insert_db",
        AsyncMock(return_value=True),
    )

    # Mock insert_configuration_db
    new_config_mock = GetConfigurationsResponse(
        id=new_config_id,
        name="New Config",
        status="draft",
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.base.insert_configuration_db",
        AsyncMock(return_value=new_config_mock),
    )

    # mock associate_condition_codeset_with_configuration_db
    assoc_condition = DbConfigurationCondition(
        mock_condition.id,
    )
    updated_config_mock = DbConfiguration(
        id=new_config_id,
        name="New Config",
        jurisdiction_id="JD-1",
        condition_id=mock_condition.id,
        included_conditions=[assoc_condition],
        custom_codes=[],
        local_codes=[],
        section_processing=[],
        version=1,
        status="draft",
        last_activated_at=None,
        last_activated_by=None,
        created_by=mock_user.id,
        condition_canonical_url="https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123",
        s3_urls=[],
    )

    monkeypatch.setattr(
        "app.api.v1.configurations.codesets.associate_condition_codeset_with_configuration_db",
        AsyncMock(return_value=updated_config_mock),
    )

    # Mock disassociate_condition_codeset_with_configuration_db
    updated_config_mock_disassoc = AsyncMock()
    updated_config_mock_disassoc.id = new_config_id
    updated_config_mock_disassoc.included_conditions = []

    monkeypatch.setattr(
        "app.api.v1.configurations.codesets.disassociate_condition_codeset_with_configuration_db",
        AsyncMock(return_value=updated_config_mock_disassoc),
    )

    # for get_total_condition_code_counts_by_configuration_db, could use a list of count objects if needed
    monkeypatch.setattr(
        "app.api.v1.configurations.custom_codes.get_total_condition_code_counts_by_configuration_db",
        AsyncMock(return_value=[]),
    )

    # Mock ConfigurationLock methods
    monkeypatch.setattr(
        "app.api.v1.configurations.base.ConfigurationLock.acquire_lock",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.base.ConfigurationLock.get_lock",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.base.ConfigurationLock.release_if_owned",
        AsyncMock(return_value=None),
    )

    yield


@pytest.mark.asyncio
async def test_associate_codeset_with_configuration(
    authed_client, mock_condition, new_config_id, monkeypatch, mock_configuration
):
    monkeypatch.setattr(
        "app.api.v1.configurations.codesets.get_configuration_by_id_db",
        AsyncMock(return_value=mock_configuration),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.codesets.get_condition_by_id_db",
        AsyncMock(return_value=mock_condition),
    )

    config_id = str(new_config_id)
    payload = {"condition_id": str(mock_condition.id)}
    response = await authed_client.put(
        f"/api/v1/configurations/{config_id}/code-sets", json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["included_conditions"]) == 1
    assert data["included_conditions"][0]["id"] == str(mock_condition.id)


@pytest.mark.asyncio
async def test_disassociate_codeset_with_configuration(
    authed_client, mock_condition, new_config_id, mock_configuration, monkeypatch
):
    monkeypatch.setattr(
        "app.api.v1.configurations.codesets.get_configuration_by_id_db",
        AsyncMock(return_value=mock_configuration),
    )

    monkeypatch.setattr(
        "app.api.v1.configurations.codesets.get_condition_by_id_db",
        AsyncMock(return_value=mock_condition),
    )

    config_id = str(new_config_id)
    payload = {"condition_id": str(mock_condition.id)}
    response = await authed_client.delete(
        f"/api/v1/configurations/{config_id}/code-sets/{payload['condition_id']}",
    )
    assert response.status_code == 200
    data = response.json()
    # After disassociation, included_conditions should be empty or not contain the removed condition
    included_conditions = data.get("included_conditions", [])
    assert isinstance(included_conditions, list)
    assert all(c.get("id") != str(mock_condition.id) for c in included_conditions)


@pytest.mark.asyncio
async def test_add_custom_code_to_configuration(
    authed_client, mock_configuration, monkeypatch
):
    monkeypatch.setattr(
        "app.api.v1.configurations.custom_codes.get_configuration_by_id_db",
        AsyncMock(return_value=mock_configuration),
    )
    # Mock adding custom code to a config
    custom_code_config_mock = replace(
        mock_configuration,
        custom_codes=[
            DbConfigurationCustomCode(
                code="test-code", name="test-name", system="LOINC"
            )
        ],
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.custom_codes.add_custom_code_to_configuration_db",
        AsyncMock(return_value=custom_code_config_mock),
    )

    config_id = str(mock_configuration.id)
    payload = {"code": "test-code", "name": "test-name", "system": "loinc"}
    response = await authed_client.post(
        f"/api/v1/configurations/{config_id}/custom-codes", json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["custom_codes"]) == 1
    assert data["custom_codes"][0]["code"] == "test-code"
    assert data["custom_codes"][0]["system"] == "LOINC"


@pytest.mark.asyncio
async def test_delete_custom_code_from_configuration(
    authed_client, mock_configuration, monkeypatch
):
    monkeypatch.setattr(
        "app.api.v1.configurations.custom_codes.get_configuration_by_id_db",
        AsyncMock(return_value=mock_configuration),
    )
    # Mock deleting a custom code from a config
    custom_code_deletion_mock = replace(
        mock_configuration,
        custom_codes=[],
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.custom_codes.delete_custom_code_from_configuration_db",
        AsyncMock(return_value=custom_code_deletion_mock),
    )

    config_id = str(mock_configuration.id)
    system = "LOINC"
    code = "test-code"

    response = await authed_client.delete(
        f"/api/v1/configurations/{config_id}/custom-codes/{system}/{code}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["custom_codes"]) == 0


@pytest.mark.asyncio
async def test_edit_custom_code_from_configuration(
    authed_client, monkeypatch, mock_configuration, mock_condition, mock_user
):
    # Mock editing a custom code from a config
    custom_code_edit_mock = replace(
        mock_configuration,
        custom_codes=[
            DbConfigurationCustomCode(
                code="edited-code", name="updated-name", system="SNOMED"
            )
        ],
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.custom_codes.edit_custom_code_from_configuration_db",
        AsyncMock(return_value=custom_code_edit_mock),
    )

    config_id = str(mock_configuration.id)
    # explicitly monkeypatch to ensure the code to edit is present
    mock_config = DbConfiguration(
        id=UUID(config_id),
        name="test config",
        jurisdiction_id="SDDH",
        condition_id=mock_condition.id,
        included_conditions=[],
        custom_codes=[
            DbConfigurationCustomCode(
                code="test-code", name="test-name", system="LOINC"
            )
        ],
        local_codes=[],
        section_processing=[],
        version=1,
        status="draft",
        last_activated_at=None,
        last_activated_by=None,
        created_by=mock_user.id,
        condition_canonical_url="https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123",
        s3_urls=[],
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.custom_codes.get_configuration_by_id_db",
        AsyncMock(return_value=mock_config),
    )

    payload = {
        "code": "test-code",
        "system": "loinc",
        "name": "test-name",
        "new_code": "edited-code",
        "new_system": "snomed",
        "new_name": "updated-name",
    }

    response = await authed_client.put(
        f"/api/v1/configurations/{config_id}/custom-codes", json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["custom_codes"]) == 1
    assert data["custom_codes"][0]["code"] == "edited-code"
    assert data["custom_codes"][0]["system"] == "SNOMED"
    assert data["custom_codes"][0]["name"] == "updated-name"


@pytest.mark.asyncio
async def test_inline_example_file_success(
    authed_client, monkeypatch, mock_configuration, mock_condition, test_app
):
    monkeypatch.setattr(
        "app.api.v1.configurations.testing.get_configuration_by_id_db",
        AsyncMock(return_value=mock_configuration),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.testing.get_condition_by_id_db",
        AsyncMock(return_value=mock_condition),
    )

    def mock_s3_upload(*args, **kwargs):
        return "http://fake-s3-url.com"

    test_app.dependency_overrides[_upload_to_s3] = lambda: mock_s3_upload

    # the route now calls `inline_testing`
    mock_result = InlineTestingResult(
        refined_document=RefinedDocument(
            reportable_condition=ReportableCondition(
                code="12345",
                display_name="Condition A",
            ),
            refined_eicr="<xml>refined eicr for Condition A</xml>",
            refined_rr="<xml>refined rr for Condition A</xml>",
        ),
        configuration_does_not_match_conditions=None,
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.testing.inline_testing",
        AsyncMock(return_value=mock_result),
    )

    payload = {"id": str(mock_configuration.id)}

    # it tests the fallback mechanism where the API uses the default sample file;
    # we just send the data payload
    response = await authed_client.post(
        "/api/v1/configurations/test",
        data=payload,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["condition"]["code"] == "12345"
    assert response.json()["condition"]["display_name"] == "Condition A"
    assert (
        response.json()["condition"]["refined_eicr"].strip()
        == "<xml>refined eicr for Condition A</xml>"
    )

    test_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_inline_allow_custom_zip(
    covid_influenza_v1_1_zip_path: Path,
    authed_client,
    monkeypatch,
    mock_configuration,
    mock_condition,
    test_app,
):
    monkeypatch.setattr(
        "app.api.v1.configurations.testing.get_configuration_by_id_db",
        AsyncMock(return_value=mock_configuration),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.testing.get_condition_by_id_db",
        AsyncMock(return_value=mock_condition),
    )

    def mock_s3_upload(*args, **kwargs):
        return "http://fake-s3-url.com"

    test_app.dependency_overrides[_upload_to_s3] = lambda: mock_s3_upload

    # the route now calls `inline_testing`
    mock_result = InlineTestingResult(
        refined_document=RefinedDocument(
            reportable_condition=ReportableCondition(
                code="840539006", display_name="COVID-19"
            ),
            refined_eicr="<xml>COVID-19 refined eICR doc</xml>",
            refined_rr="<xml>COVID-19 refined RR doc</xml>",
        ),
        configuration_does_not_match_conditions=None,
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.testing.inline_testing",
        AsyncMock(return_value=mock_result),
    )

    payload = {"id": str(mock_configuration.id)}

    uploaded_file = covid_influenza_v1_1_zip_path
    with open(uploaded_file, "rb") as file_data:
        response = await authed_client.post(
            "/api/v1/configurations/test",
            files={
                "uploaded_file": (
                    "mon_mothma_covid_influenza_1.1.zip",
                    file_data,
                    "application/zip",
                )
            },
            data=payload,
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["condition"]["code"] == "840539006"
    assert response.json()["condition"]["display_name"] == "COVID-19"
    assert (
        response.json()["condition"]["refined_eicr"].strip()
        == "<xml>COVID-19 refined eICR doc</xml>"
    )
    assert (
        response.json()["condition"]["refined_rr"].strip()
        == "<xml>COVID-19 refined RR doc</xml>"
    )

    test_app.dependency_overrides.clear()
