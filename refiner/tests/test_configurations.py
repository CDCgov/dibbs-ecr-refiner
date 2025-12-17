from dataclasses import replace
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.api.auth.middleware import get_logged_in_user
from app.api.v1.configurations import GetConfigurationsResponse, _upload_to_s3
from app.db.conditions.model import DbCondition, DbConditionCoding
from app.db.configurations.db import GetConfigurationResponseVersion
from app.db.configurations.model import (
    DbConfiguration,
    DbConfigurationCondition,
    DbConfigurationCustomCode,
)
from app.db.users.model import DbUser
from app.main import app
from app.services.ecr.models import RefinedDocument, ReportableCondition
from app.services.testing import InlineTestingResult

# User info
TEST_SESSION_TOKEN = "test-token"
MOCK_LOGGED_IN_USER_ID = "5deb43c2-6a82-4052-9918-616e01d255c7"


def make_db_condition_coding(code, display):
    return DbConditionCoding(code=code, display=display)


def mock_user():
    return DbUser(
        id=MOCK_LOGGED_IN_USER_ID,
        username="tester",
        email="tester@test.com",
        jurisdiction_id="JD-1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest_asyncio.fixture
async def authed_client(mock_logged_in_user, mock_db_functions):
    """
    Mock an authenticated client.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        client.cookies.update({"refiner-session": TEST_SESSION_TOKEN})
        yield client


@pytest.fixture(autouse=True)
def mock_logged_in_user():
    """
    Mock the logged-in user dependency
    """

    app.dependency_overrides[get_logged_in_user] = mock_user
    yield
    app.dependency_overrides.pop(get_logged_in_user, None)


@pytest.fixture(autouse=True)
def mock_db_functions(monkeypatch):
    """
    Mock return values of the `_db` functions called by the routes.
    """

    # prepare a fake condition with codes
    condition_mock = DbCondition(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        display_name="Condition A",
        canonical_url="url-1",
        version="3.0.0",
        child_rsg_snomed_codes=["12345"],
        snomed_codes=[make_db_condition_coding("12345", "SNOMED Description")],
        loinc_codes=[make_db_condition_coding("54321", "LOINC Description")],
        icd10_codes=[make_db_condition_coding("A00", "ICD10 Description")],
        rxnorm_codes=[make_db_condition_coding("99999", "RXNORM Description")],
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.get_condition_by_id_db",
        AsyncMock(return_value=condition_mock),
    )

    fake_condition = DbCondition(
        id=uuid4(),
        display_name="Hypertension",
        canonical_url="http://url.com",
        version="3.0.0",
        child_rsg_snomed_codes=["11111"],
        snomed_codes=[make_db_condition_coding("11111", "Hypertension SNOMED")],
        loinc_codes=[make_db_condition_coding("22222", "Hypertension LOINC")],
        icd10_codes=[make_db_condition_coding("I10", "Essential hypertension")],
        rxnorm_codes=[make_db_condition_coding("33333", "Hypertension RXNORM")],
    )

    monkeypatch.setattr(
        "app.api.v1.configurations.get_conditions_db",
        AsyncMock(return_value=[fake_condition]),
    )

    # mock get_configuration_by_id_db with default: no custom codes
    config_by_id_mock = DbConfiguration(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        name="test config",
        jurisdiction_id="SDDH",
        condition_id=UUID("22222222-2222-2222-2222-222222222222"),
        included_conditions=[],
        custom_codes=[],
        local_codes=[],
        section_processing=[],
        version=1,
        status="draft",
        last_activated_at=None,
        last_activated_by=None,
        created_by=MOCK_LOGGED_IN_USER_ID,
        condition_canonical_url="url-1",
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_by_id_db",
        AsyncMock(return_value=config_by_id_mock),
    )

    monkeypatch.setattr(
        "app.api.v1.configurations.get_latest_config_db",
        AsyncMock(return_value=config_by_id_mock),
    )

    versions_mock = [
        GetConfigurationResponseVersion(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            status="draft",
            version=1,
            condition_canonical_url="https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123",
            created_by=MOCK_LOGGED_IN_USER_ID,
            created_at=datetime.now(),
            last_activated_at=None,
            last_activated_by=None,
        )
    ]

    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_versions_db",
        AsyncMock(return_value=versions_mock),
    )

    # Mock get_configurations_db
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configurations_db",
        AsyncMock(return_value=[config_by_id_mock]),
    )

    # Mock is_config_valid_to_insert_db
    monkeypatch.setattr(
        "app.api.v1.configurations.is_config_valid_to_insert_db",
        AsyncMock(return_value=True),
    )

    # Mock insert_configuration_db
    new_config_mock = GetConfigurationsResponse(
        id=UUID("33333333-3333-3333-3333-333333333333"),
        name="New Config",
        status="draft",
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.insert_configuration_db",
        AsyncMock(return_value=new_config_mock),
    )

    # mock associate_condition_codeset_with_configuration_db
    assoc_condition = DbConfigurationCondition(
        UUID("22222222-2222-2222-2222-222222222222"),
    )
    updated_config_mock = DbConfiguration(
        id=UUID("33333333-3333-3333-3333-333333333333"),
        name="New Config",
        jurisdiction_id="JD-1",
        condition_id=UUID("22222222-2222-2222-2222-222222222222"),
        included_conditions=[assoc_condition],
        custom_codes=[],
        local_codes=[],
        section_processing=[],
        version=1,
        status="draft",
        last_activated_at=None,
        last_activated_by=None,
        created_by=MOCK_LOGGED_IN_USER_ID,
        condition_canonical_url="https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123",
    )

    monkeypatch.setattr(
        "app.api.v1.configurations.associate_condition_codeset_with_configuration_db",
        AsyncMock(return_value=updated_config_mock),
    )

    # Mock disassociate_condition_codeset_with_configuration_db
    updated_config_mock_disassoc = AsyncMock()
    updated_config_mock_disassoc.id = UUID("33333333-3333-3333-3333-333333333333")
    updated_config_mock_disassoc.included_conditions = []

    monkeypatch.setattr(
        "app.api.v1.configurations.disassociate_condition_codeset_with_configuration_db",
        AsyncMock(return_value=updated_config_mock_disassoc),
    )

    # for get_total_condition_code_counts_by_configuration_db, could use a list of count objects if needed
    monkeypatch.setattr(
        "app.api.v1.configurations.get_total_condition_code_counts_by_configuration_db",
        AsyncMock(return_value=[]),
    )

    # Mock adding custom code to a config
    custom_code_config_mock = replace(
        config_by_id_mock,
        custom_codes=[
            DbConfigurationCustomCode(
                code="test-code", name="test-name", system="LOINC"
            )
        ],
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.add_custom_code_to_configuration_db",
        AsyncMock(return_value=custom_code_config_mock),
    )

    # Mock deleting a custom code from a config
    custom_code_deletion_mock = replace(
        config_by_id_mock,
        custom_codes=[],
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.delete_custom_code_from_configuration_db",
        AsyncMock(return_value=custom_code_deletion_mock),
    )

    # Mock editing a custom code from a config
    custom_code_edit_mock = replace(
        config_by_id_mock,
        custom_codes=[
            DbConfigurationCustomCode(
                code="edited-code", name="updated-name", system="SNOMED"
            )
        ],
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.edit_custom_code_from_configuration_db",
        AsyncMock(return_value=custom_code_edit_mock),
    )

    # Mock ConfigurationLock methods
    monkeypatch.setattr(
        "app.api.v1.configurations.ConfigurationLock.acquire_lock",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.ConfigurationLock.get_lock",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.ConfigurationLock.release_lock",
        AsyncMock(return_value=True),
    )

    yield


@pytest.mark.asyncio
async def test_get_configurations_returns_list(authed_client):
    response = await authed_client.get("/api/v1/configurations/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["name"] == "test config"


@pytest.mark.asyncio
async def test_create_configuration_success(authed_client):
    payload = {"condition_id": "22222222-2222-2222-2222-222222222222"}
    response = await authed_client.post("/api/v1/configurations/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Config"


@pytest.mark.asyncio
async def test_get_configuration_by_id(authed_client):
    config_id = "11111111-1111-1111-1111-111111111111"
    response = await authed_client.get(f"/api/v1/configurations/{config_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "test config"


@pytest.mark.asyncio
async def test_associate_codeset_with_configuration(authed_client):
    config_id = "33333333-3333-3333-3333-333333333333"
    payload = {"condition_id": "22222222-2222-2222-2222-222222222222"}
    response = await authed_client.put(
        f"/api/v1/configurations/{config_id}/code-sets", json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["included_conditions"]) == 1
    assert (
        data["included_conditions"][0]["id"] == "22222222-2222-2222-2222-222222222222"
    )


@pytest.mark.asyncio
async def test_disassociate_codeset_with_configuration(authed_client):
    config_id = "33333333-3333-3333-3333-333333333333"
    payload = {"condition_id": "22222222-2222-2222-2222-222222222222"}
    response = await authed_client.delete(
        f"/api/v1/configurations/{config_id}/code-sets/{payload['condition_id']}",
    )
    assert response.status_code == 200
    data = response.json()
    # After disassociation, included_conditions should be empty or not contain the removed condition
    included_conditions = data.get("included_conditions", [])
    assert isinstance(included_conditions, list)
    assert all(
        c.get("id") != "22222222-2222-2222-2222-222222222222"
        for c in included_conditions
    )


@pytest.mark.asyncio
async def test_add_custom_code_to_configuration(authed_client):
    config_id = "11111111-1111-1111-1111-111111111111"
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
async def test_delete_custom_code_from_configuration(authed_client):
    config_id = "11111111-1111-1111-1111-111111111111"
    system = "LOINC"
    code = "test-code"

    response = await authed_client.delete(
        f"/api/v1/configurations/{config_id}/custom-codes/{system}/{code}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["custom_codes"]) == 0


@pytest.mark.asyncio
async def test_edit_custom_code_from_configuration(authed_client, monkeypatch):
    config_id = "11111111-1111-1111-1111-111111111111"
    # explicitly monkeypatch to ensure the code to edit is present
    mock_config = DbConfiguration(
        id=UUID(config_id),
        name="test config",
        jurisdiction_id="SDDH",
        condition_id=UUID("22222222-2222-2222-2222-222222222222"),
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
        created_by=MOCK_LOGGED_IN_USER_ID,
        condition_canonical_url="https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123",
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_by_id_db",
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
async def test_inline_example_file_success(authed_client, monkeypatch):
    def mock_s3_upload(*args, **kwargs):
        return "http://fake-s3-url.com"

    app.dependency_overrides[_upload_to_s3] = lambda: mock_s3_upload

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
        "app.api.v1.configurations.inline_testing",
        AsyncMock(return_value=mock_result),
    )

    payload = {"id": "11111111-1111-1111-1111-111111111111"}

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

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_inline_allow_custom_zip(test_assets_path, authed_client, monkeypatch):
    def mock_s3_upload(*args, **kwargs):
        return "http://fake-s3-url.com"

    app.dependency_overrides[_upload_to_s3] = lambda: mock_s3_upload

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
        "app.api.v1.configurations.inline_testing",
        AsyncMock(return_value=mock_result),
    )

    payload = {"id": "11111111-1111-1111-1111-111111111111"}

    uploaded_file = test_assets_path / "demo" / "monmothma.zip"
    with open(uploaded_file, "rb") as file_data:
        response = await authed_client.post(
            "/api/v1/configurations/test",
            files={"uploaded_file": ("monmothma.zip", file_data, "application/zip")},
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

    app.dependency_overrides.clear()
