from unittest.mock import AsyncMock
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.auth.middleware import get_logged_in_user
from app.api.v1.configurations import GetConfigurationsResponse
from app.db.conditions.model import DbCondition
from app.db.configurations.db import DbTotalConditionCodeCount
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
    config_by_id_mock = GetConfigurationsResponse(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        name="Config A",
        is_active=False,
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

    # Total counts
    DbTotalConditionCodeCount(
        condition_id=UUID("22222222-2222-2222-2222-222222222222"),
        display_name="Condition A",
        total_codes=3,
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.get_total_condition_code_counts_by_configuration_db",
        AsyncMock(return_value=updated_config_mock),
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
    assert data["display_name"] == "Config A"


@pytest.mark.asyncio
async def test_associate_codeset_with_configuration(authed_client):
    config_id = "33333333-3333-3333-3333-333333333333"
    payload = {"condition_id": "22222222-2222-2222-2222-222222222222"}
    response = await authed_client.put(
        f"/api/v1/configurations/{config_id}/code-set", json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["included_conditions"]) == 1
    assert data["included_conditions"][0]["canonical_url"] == "url-1"
