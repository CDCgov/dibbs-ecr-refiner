from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import status

from app.db.configurations.model import DbConfiguration
from tests.conftest import MOCK_LOGGED_IN_USER_ID

ACTIVE_CONFIGURATION_ID = UUID("44444444-4444-4444-4444-444444444444")

active_config = DbConfiguration(
    id=ACTIVE_CONFIGURATION_ID,
    name="Activated Config",
    jurisdiction_id="JD-1",
    condition_id=UUID("22222222-2222-2222-2222-222222222222"),
    included_conditions=[],
    custom_codes=[],
    local_codes=[],
    section_processing=[],
    version=1,
    status="active",
    last_activated_at=datetime.now(),
    last_activated_by=MOCK_LOGGED_IN_USER_ID,
    condition_canonical_url="https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123",
)

DRAFT_CONFIG_ID = UUID("11111111-1111-1111-1111-111111111111")
# mock get_configuration_by_id_db with default: no custom codes
draft_config = DbConfiguration(
    id=DRAFT_CONFIG_ID,
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
    condition_canonical_url="url-1",
)


@pytest.fixture(autouse=True)
def mock_db_functions(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_by_id_db",
        AsyncMock(return_value=draft_config),
    )

    monkeypatch.setattr(
        "app.api.v1.configurations.activate_configuration_db",
        AsyncMock(return_value=active_config),
    )

    inactive_configuration = DbConfiguration(
        id=UUID("44444444-4444-4444-4444-444444444444"),
        name="Activated Config",
        jurisdiction_id="JD-1",
        condition_id=UUID("22222222-2222-2222-2222-222222222222"),
        included_conditions=[],
        custom_codes=[],
        local_codes=[],
        section_processing=[],
        version=1,
        status="inactive",
        last_activated_at=datetime.now(),
        last_activated_by=MOCK_LOGGED_IN_USER_ID,
        condition_canonical_url="https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123",
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.deactivate_configuration_db",
        AsyncMock(return_value=inactive_configuration),
    )


@pytest.mark.asyncio
async def test_activate_config_no_other_active_config(authed_client, monkeypatch):
    payload = {
        "condition_canonical_url": "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123",
    }

    # set the get for active config to none so we just test the activate
    # flow fallthrough
    monkeypatch.setattr(
        "app.api.v1.configurations.get_active_config_db",
        AsyncMock(return_value=None),
    )

    response = await authed_client.patch(
        f"/api/v1/configurations/{ACTIVE_CONFIGURATION_ID}/activate", json=payload
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "active"
    assert data["configuration_id"] == str(ACTIVE_CONFIGURATION_ID)


@pytest.mark.asyncio
async def test_activate_config_other_active_config(authed_client, monkeypatch):
    other_active_config_id = UUID("55555555-5555-5555-5555-555555555555")
    payload = {
        "condition_canonical_url": "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123",
    }

    other_active_configuration = DbConfiguration(
        id=other_active_config_id,
        name="Other Active Config",
        jurisdiction_id="JD-1",
        condition_id=UUID("22222222-2222-2222-2222-222222222222"),
        included_conditions=[],
        custom_codes=[],
        local_codes=[],
        section_processing=[],
        version=1,
        status="active",
        last_activated_at=datetime.now(),
        last_activated_by=MOCK_LOGGED_IN_USER_ID,
        condition_canonical_url="https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123",
    )

    # flow fallthrough
    monkeypatch.setattr(
        "app.api.v1.configurations.update_configuration_activation_db",
        AsyncMock(return_value=other_active_configuration),
    )

    response = await authed_client.patch(
        f"/api/v1/configurations/{other_active_config_id}/activate", json=payload
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "active"
    assert data["configuration_id"] == str(other_active_config_id)


@pytest.mark.asyncio
async def test_deactivate_config(authed_client):
    config_id = "11111111-1111-1111-1111-111111111111"

    response = await authed_client.patch(
        f"/api/v1/configurations/{config_id}/deactivate"
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "inactive"
