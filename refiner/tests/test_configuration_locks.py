from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.api.auth.middleware import get_logged_in_user
from app.db.configurations.db import DbConfigurationLock
from app.db.configurations.model import DbConfiguration
from app.db.users.model import DbUser
from app.main import app

TEST_SESSION_TOKEN = "test-token"
CONFIG_ID = UUID("11111111-1111-1111-1111-111111111111")
USER_ID = UUID("5deb43c2-6a82-4052-9918-616e01d255c7")
OTHER_USER_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def mock_user():
    return DbUser(
        id=USER_ID,
        username="tester",
        email="tester@test.com",
        jurisdiction_id="JD-1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest_asyncio.fixture
async def authed_client(mock_logged_in_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        client.cookies.update({"refiner-session": TEST_SESSION_TOKEN})
        yield client


@pytest.fixture(autouse=True)
def mock_logged_in_user():
    app.dependency_overrides[get_logged_in_user] = mock_user
    yield
    app.dependency_overrides.pop(get_logged_in_user, None)


@pytest.fixture(autouse=True)
def mock_config(monkeypatch):
    config_row = DbConfiguration(
        id=CONFIG_ID,
        name="test config",
        jurisdiction_id="JD-1",
        condition_id=UUID("22222222-2222-2222-2222-222222222222"),
        included_conditions=[],
        custom_codes=[],
        local_codes=[],
        section_processing=[],
        version=1,
        status="draft",
        last_activated_at=None,
        last_activated_by=None,
        condition_canonical_url="https://test.com",
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_by_id_db",
        AsyncMock(return_value=config_row),
    )
    yield


def make_lock(user_id, username, minutes=30):
    return DbConfigurationLock(
        configuration_id=CONFIG_ID,
        user_id=user_id,
        username=username,
        expires_at=datetime.now() + timedelta(minutes=minutes),
    )


@pytest.mark.asyncio
async def test_acquire_new_lock_success(authed_client, monkeypatch):
    # No existing lock -> acquire new
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_lock_db",
        AsyncMock(return_value=None),
    )
    new_lock = make_lock(USER_ID, "tester")
    # Return acquired_new False to skip event emission (avoids real DB connection in tests)
    monkeypatch.setattr(
        "app.api.v1.configurations.acquire_or_refresh_lock_db",
        AsyncMock(return_value=(new_lock, False)),
    )
    response = await authed_client.post(f"/api/v1/configurations/{CONFIG_ID}/lock")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["locked"] is True
    assert data["username"] == "tester"


@pytest.mark.asyncio
async def test_acquire_lock_conflict_other_user(authed_client, monkeypatch):
    holder_lock = make_lock(OTHER_USER_ID, "other")
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_lock_db",
        AsyncMock(return_value=holder_lock),
    )
    # attempt returns None indicating conflict
    monkeypatch.setattr(
        "app.api.v1.configurations.acquire_or_refresh_lock_db",
        AsyncMock(return_value=(None, False)),
    )
    response = await authed_client.post(f"/api/v1/configurations/{CONFIG_ID}/lock")
    assert response.status_code == status.HTTP_409_CONFLICT
    data = response.json()
    assert data["detail"]["locked"] is True
    assert data["detail"]["username"] == "other"


@pytest.mark.asyncio
async def test_refresh_existing_lock_same_user(authed_client, monkeypatch):
    existing_lock = make_lock(USER_ID, "tester")
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_lock_db",
        AsyncMock(return_value=existing_lock),
    )
    refreshed_lock = make_lock(USER_ID, "tester")
    monkeypatch.setattr(
        "app.api.v1.configurations.acquire_or_refresh_lock_db",
        AsyncMock(return_value=(refreshed_lock, False)),
    )
    response = await authed_client.post(f"/api/v1/configurations/{CONFIG_ID}/lock")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["locked"] is True
    assert data["username"] == "tester"


@pytest.mark.asyncio
async def test_release_lock_always_204(authed_client, monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.configurations.release_lock_db",
        AsyncMock(return_value=True),
    )
    response = await authed_client.delete(f"/api/v1/configurations/{CONFIG_ID}/lock")
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_enforce_lock_no_lock_conflict_on_mutation(authed_client, monkeypatch):
    # Mutation endpoint should 409 when no lock
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_lock_db",
        AsyncMock(return_value=None),
    )
    config_id = CONFIG_ID
    payload = {"condition_id": "22222222-2222-2222-2222-222222222222"}
    response = await authed_client.put(
        f"/api/v1/configurations/{config_id}/code-sets", json=payload
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    data = response.json()
    assert data["detail"]["locked"] is False


@pytest.mark.asyncio
async def test_enforce_lock_other_user_conflict_on_mutation(authed_client, monkeypatch):
    other_lock = make_lock(OTHER_USER_ID, "other")
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_lock_db",
        AsyncMock(return_value=other_lock),
    )
    config_id = CONFIG_ID
    payload = {"condition_id": "22222222-2222-2222-2222-222222222222"}
    response = await authed_client.put(
        f"/api/v1/configurations/{config_id}/code-sets", json=payload
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    data = response.json()
    assert data["detail"]["locked"] is True
    assert data["detail"]["username"] == "other"


@pytest.mark.asyncio
async def test_enforce_lock_success_on_mutation(authed_client, monkeypatch):
    user_lock = make_lock(USER_ID, "tester")
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_lock_db",
        AsyncMock(return_value=user_lock),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.acquire_or_refresh_lock_db",
        AsyncMock(return_value=(user_lock, False)),
    )
    # mock associate update
    updated_config_mock = DbConfiguration(
        id=CONFIG_ID,
        name="test config",
        jurisdiction_id="JD-1",
        condition_id=UUID("22222222-2222-2222-2222-222222222222"),
        included_conditions=[],
        custom_codes=[],
        local_codes=[],
        section_processing=[],
        version=1,
        status="draft",
        last_activated_at=None,
        last_activated_by=None,
        condition_canonical_url="https://test.com",
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.associate_condition_codeset_with_configuration_db",
        AsyncMock(return_value=updated_config_mock),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.get_total_condition_code_counts_by_configuration_db",
        AsyncMock(return_value=[]),
    )
    # condition fetch (avoid real DB)
    stub_condition = SimpleNamespace(
        id=UUID("22222222-2222-2222-2222-222222222222"), display_name="Cond X"
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.get_condition_by_id_db",
        AsyncMock(return_value=stub_condition),
    )
    config_id = CONFIG_ID
    payload = {"condition_id": "22222222-2222-2222-2222-222222222222"}
    response = await authed_client.put(
        f"/api/v1/configurations/{config_id}/code-sets", json=payload
    )
    # Success -> status 200
    assert response.status_code == status.HTTP_200_OK
