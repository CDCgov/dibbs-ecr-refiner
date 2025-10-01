from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.api.auth.middleware import get_logged_in_user
from app.db.configurations.model import (
    DbConfiguration,
    DbConfigurationSectionProcessing,
)
from app.db.users.model import DbUser
from app.main import app

TEST_SESSION_TOKEN = "test-token"


def mock_user():
    return DbUser(
        id="5deb43c2-6a82-4052-9918-616e01d255c7",
        username="tester",
        email="tester@test.com",
        jurisdiction_id="JD-1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture(autouse=True)
def _override_user():
    app.dependency_overrides[get_logged_in_user] = mock_user
    yield
    app.dependency_overrides.pop(get_logged_in_user, None)


@pytest_asyncio.fixture
async def authed_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        client.cookies.update({"refiner-session": TEST_SESSION_TOKEN})
        yield client


@pytest.mark.asyncio
async def test_update_section_processing_success(authed_client, monkeypatch):
    # Arrange: existing configuration with two section_processing entries
    config_id = UUID(str(uuid4()))
    existing_sections = [
        DbConfigurationSectionProcessing(name="Sec A", code="A", action="retain"),
        DbConfigurationSectionProcessing(name="Sec B", code="B", action="refine"),
    ]

    initial_config = DbConfiguration(
        id=config_id,
        name="test config",
        jurisdiction_id="JD-1",
        condition_id=UUID(int=0),
        included_conditions=[],
        custom_codes=[],
        local_codes=[],
        section_processing=existing_sections,
        version=1,
    )

    # Updated config returned by DB helper
    updated_sections = [
        DbConfigurationSectionProcessing(name="Sec A", code="A", action="remove"),
        DbConfigurationSectionProcessing(name="Sec B", code="B", action="refine"),
    ]
    updated_config = DbConfiguration(
        id=initial_config.id,
        name=initial_config.name,
        jurisdiction_id=initial_config.jurisdiction_id,
        condition_id=initial_config.condition_id,
        included_conditions=initial_config.included_conditions,
        custom_codes=initial_config.custom_codes,
        local_codes=initial_config.local_codes,
        section_processing=updated_sections,
        version=2,
    )

    # Monkeypatch DB calls
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_by_id_db",
        AsyncMock(return_value=initial_config),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.update_section_processing_db",
        AsyncMock(return_value=updated_config),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.get_total_condition_code_counts_by_configuration_db",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.get_conditions_db",
        AsyncMock(return_value=[]),
    )

    payload = {"sections": [{"code": "A", "action": "remove"}]}

    # Act
    response = await authed_client.patch(
        f"/api/v1/configurations/{config_id}/section-processing",
        json=payload,
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(config_id)
    assert isinstance(data.get("section_processing"), list)

    # Ensure the updated action is reflected in the response
    codes_actions = {
        entry["code"]: entry["action"] for entry in data["section_processing"]
    }
    assert codes_actions.get("A") == "remove"
    assert codes_actions.get("B") == "refine"


@pytest.mark.asyncio
async def test_update_section_processing_db_returns_none(authed_client, monkeypatch):
    # Arrange: existing configuration
    config_id = UUID(str(uuid4()))
    existing_sections = [
        DbConfigurationSectionProcessing(name="Sec A", code="A", action="retain"),
    ]

    initial_config = DbConfiguration(
        id=config_id,
        name="test config",
        jurisdiction_id="JD-1",
        condition_id=UUID(int=0),
        included_conditions=[],
        custom_codes=[],
        local_codes=[],
        section_processing=existing_sections,
        version=1,
    )

    # Monkeypatch DB calls: update returns None to simulate failure
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_by_id_db",
        AsyncMock(return_value=initial_config),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.update_section_processing_db",
        AsyncMock(return_value=None),
    )

    payload = {"sections": [{"code": "A", "action": "remove"}]}

    # Act
    response = await authed_client.patch(
        f"/api/v1/configurations/{config_id}/section-processing",
        json=payload,
    )

    # Assert: should surface 500 and not cause FastAPI ResponseValidationError
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json().get("detail") is not None
