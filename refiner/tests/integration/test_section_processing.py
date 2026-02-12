from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.db.configurations.model import (
    DbConfiguration,
    DbConfigurationSectionProcessing,
)
from app.db.users.model import DbUser

TEST_SESSION_TOKEN = "test-token"
TEST_LOGGED_IN_USER_ID = "5deb43c2-6a82-4052-9918-616e01d255c7"


def mock_user():
    return DbUser(
        id=TEST_LOGGED_IN_USER_ID,
        username="tester",
        email="tester@test.com",
        jurisdiction_id="JD-1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest_asyncio.fixture
async def authed_client(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        client.cookies.update({"refiner-session": TEST_SESSION_TOKEN})
        yield client


@pytest.mark.asyncio
async def test_update_section_processing_success(authed_client, monkeypatch):
    # Arrange: existing configuration with two section_processing entries
    config_id = UUID(str(uuid4()))
    existing_sections = [
        DbConfigurationSectionProcessing(
            name="Sec A", code="A", action="retain", versions=[]
        ),
        DbConfigurationSectionProcessing(
            name="Sec B", code="B", action="refine", versions=[]
        ),
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
        status="draft",
        last_activated_at=None,
        last_activated_by=None,
        created_by=TEST_LOGGED_IN_USER_ID,
        condition_canonical_url="https://test.com",
        s3_urls=[],
    )

    # Updated config returned by DB helper
    updated_sections = [
        DbConfigurationSectionProcessing(
            name="Sec A", code="A", action="remove", versions=[]
        ),
        DbConfigurationSectionProcessing(
            name="Sec B", code="B", action="refine", versions=[]
        ),
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
        status=initial_config.status,
        last_activated_at=initial_config.last_activated_at,
        last_activated_by=initial_config.last_activated_by,
        created_by=TEST_LOGGED_IN_USER_ID,
        condition_canonical_url=initial_config.condition_canonical_url,
        s3_urls=initial_config.s3_urls,
    )

    # Monkeypatch DB calls
    monkeypatch.setattr(
        "app.api.v1.configurations.sections.get_configuration_by_id_db",
        AsyncMock(return_value=initial_config),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.sections.update_section_processing_db",
        AsyncMock(return_value=updated_config),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.base.get_total_condition_code_counts_by_configuration_db",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.base.get_conditions_by_version_db",
        AsyncMock(return_value=[]),
    )
    # Mock ConfigurationLock
    monkeypatch.setattr(
        "app.api.v1.configurations.base.ConfigurationLock.get_lock",
        AsyncMock(return_value=None),
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
    assert data["message"] == "Section processed successfully."


@pytest.mark.asyncio
async def test_update_section_processing_db_returns_none(authed_client, monkeypatch):
    # Arrange: existing configuration
    config_id = UUID(str(uuid4()))
    existing_sections = [
        DbConfigurationSectionProcessing(
            name="Sec A", code="A", action="retain", versions=[]
        ),
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
        status="draft",
        last_activated_at=None,
        last_activated_by=None,
        created_by=TEST_LOGGED_IN_USER_ID,
        condition_canonical_url="https://test.com",
        s3_urls=[],
    )

    # Monkeypatch DB calls: update returns None to simulate failure
    monkeypatch.setattr(
        "app.api.v1.configurations.sections.get_configuration_by_id_db",
        AsyncMock(return_value=initial_config),
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.sections.update_section_processing_db",
        AsyncMock(return_value=None),
    )
    # Mock ConfigurationLock
    monkeypatch.setattr(
        "app.api.v1.configurations.sections.ConfigurationLock.get_lock",
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
