from unittest.mock import AsyncMock
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.auth.middleware import get_logged_in_user
from app.api.v1.configurations import (
    GetConfigurationsResponse,
)
from app.db.conditions.model import DbCondition
from app.db.configurations.model import DbConfiguration, DbConfigurationCustomCode
from app.db.users.model import DbUser
from app.main import app

# User info
TEST_SESSION_TOKEN = "test-token"


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

    def mock_user():
        return {
            "id": "5deb43c2-6a82-4052-9918-616e01d255c7",
            "username": "tester",
            "email": "tester@test.com",
            "jurisdiction_id": "JD-1",
        }

    app.dependency_overrides[get_logged_in_user] = mock_user
    yield
    app.dependency_overrides.pop(get_logged_in_user, None)


@pytest.fixture(autouse=True)
def mock_db_functions(monkeypatch):
    """
    Mock return values of the `_db` functions called by the routes.
    """
    # Mock get_user_by_id_db
    user_mock = DbUser(
        id="5deb43c2-6a82-4052-9918-616e01d255c7",
        username="tester",
        email="tester@test.com",
        jurisdiction_id="JD-1",
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.get_user_by_id_db", AsyncMock(return_value=user_mock)
    )

    # Mock get_configurations_db
    config_mock = GetConfigurationsResponse(
        id=UUID("b3096f08-8cf4-4276-a1e9-03634c9f618b"),
        name="Config A",
        is_active=False,
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configurations_db",
        AsyncMock(return_value=[config_mock]),
    )

    # Mock get_configuration_by_id_db
    config_by_id_mock = DbConfiguration(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        family_id=1,
        jurisdiction_id="SDDH",
        name="test config",
        description="test config desc",
        included_conditions=[],
        loinc_codes_additions=[],
        snomed_codes_additions=[],
        icd10_codes_additions=[],
        rxnorm_codes_additions=[],
        custom_codes=[],
        sections_to_include=[],
        cloned_from_configuration_id=None,
    )
    # Mock adding custom code to a config
    custom_code_config_mock = config_by_id_mock.model_copy(
        update={
            "custom_codes": [
                {"code": "test-code", "name": "test-name", "system": "LOINC"}
            ],
        }
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_by_id_db",
        AsyncMock(return_value=config_by_id_mock),
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
        is_active=False,
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.insert_configuration_db",
        AsyncMock(return_value=new_config_mock),
    )

    # Mock get_condition_by_id_db
    condition_mock = DbCondition(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        display_name="Condition A",
        canonical_url="url-1",
        version="2.0.0",
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.get_condition_by_id_db",
        AsyncMock(return_value=condition_mock),
    )

    # Mock associate_condition_codeset_with_configuration_db
    assoc_condition = AsyncMock()
    assoc_condition.canonical_url = "url-1"
    assoc_condition.version = "2.0.0"

    updated_config_mock = AsyncMock()
    updated_config_mock.id = UUID("33333333-3333-3333-3333-333333333333")
    updated_config_mock.included_conditions = [assoc_condition]

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

    # Mock adding custom code to a config
    custom_code_config_mock = config_by_id_mock.model_copy(
        update={
            "custom_codes": [
                DbConfigurationCustomCode(
                    code="test-code", name="test-name", system="LOINC"
                )
            ],
        }
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.add_custom_code_to_configuration_db",
        AsyncMock(return_value=custom_code_config_mock),
    )

    # Mock deleting a custom code from a config
    custom_code_deletion_mock = custom_code_config_mock.model_copy(
        update={
            "custom_codes": [],
        }
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.delete_custom_code_from_configuration_db",
        AsyncMock(return_value=custom_code_deletion_mock),
    )

    # Mock editing a custom code from a config
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_by_id_db",
        AsyncMock(return_value=custom_code_config_mock),
    )
    custom_code_edit_mock = custom_code_config_mock.model_copy(
        update={
            "custom_codes": [
                DbConfigurationCustomCode(
                    code="edited-code", name="test-name", system="SNOMED"
                )
            ],
        }
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.edit_custom_code_from_configuration_db",
        AsyncMock(return_value=custom_code_edit_mock),
    )

    yield


@pytest.mark.asyncio
async def test_get_configurations_returns_list(authed_client):
    response = await authed_client.get("/api/v1/configurations/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["name"] == "Config A"


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
    assert data["included_conditions"][0]["canonical_url"] == "url-1"


@pytest.mark.asyncio
async def test_disassociate_codeset_with_configuration(authed_client):
    config_id = "33333333-3333-3333-3333-333333333333"
    payload = {"condition_id": "22222222-2222-2222-2222-222222222222"}
    response = await authed_client.request(
        "DELETE",
        f"/api/v1/configurations/{config_id}/code-sets/{payload['condition_id']}",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    data = response.json()
    # After disassociation, included_conditions should be empty or not contain the removed condition
    included_conditions = data.get("included_conditions", [])
    assert isinstance(included_conditions, list)
    assert all(
        c.get("canonical_url") != "url-1" or c.get("version") != "2.0.0"
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
async def test_edit_custom_code_from_configuration(authed_client):
    config_id = "11111111-1111-1111-1111-111111111111"

    payload = {
        "code": "test-code",
        "system": "loinc",
        "new_code": "edited-code",
        "new_system": "snomed",
        "new_name": "test-name",
    }

    response = await authed_client.put(
        f"/api/v1/configurations/{config_id}/custom-codes", json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["custom_codes"]) == 1
    assert data["custom_codes"][0]["code"] == "edited-code"
    assert data["custom_codes"][0]["system"] == "SNOMED"
