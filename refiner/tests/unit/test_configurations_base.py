from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from app.api.v1.configurations.models import GetConfigurationsResponse
from app.db.conditions.model import DbCondition, DbConditionCoding
from app.db.configurations.db import GetConfigurationResponseVersion


@pytest.fixture
def new_config_id():
    return UUID("33333333-3333-3333-3333-333333333333")


@pytest.fixture(autouse=True)
def mock_db_functions(
    monkeypatch, mock_condition, mock_configuration, mock_user, new_config_id
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

    # for get_total_condition_code_counts_by_configuration_db, could use a list of count objects if needed
    monkeypatch.setattr(
        "app.api.v1.configurations.base.get_total_condition_code_counts_by_configuration_db",
        AsyncMock(return_value=[]),
    )

    monkeypatch.setattr(
        "app.api.v1.configurations.base.ConfigurationLock.get_lock",
        AsyncMock(return_value=None),
    )

    monkeypatch.setattr(
        "app.api.v1.configurations.base.ConfigurationLock.acquire_lock",
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
async def test_create_configuration_success(authed_client, mock_condition):
    payload = {"condition_id": str(mock_condition.id)}
    response = await authed_client.post("/api/v1/configurations/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Config"


@pytest.mark.asyncio
async def test_get_configuration_by_id(authed_client, mock_configuration):
    config_id = str(mock_configuration.id)
    response = await authed_client.get(f"/api/v1/configurations/{config_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "test config"
