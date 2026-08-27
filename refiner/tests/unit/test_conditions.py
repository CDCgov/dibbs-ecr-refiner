from uuid import uuid4

import pytest
from fastapi import status

from app.db.codes.model import CodedConcept, DbCode
from app.db.conditions.model import ConditionSummary
from tests.unit.conftest import get_mock_system_id_by_name


@pytest.mark.asyncio
async def test_get_latest_conditions(monkeypatch, authed_client):
    fake_condition_summary = ConditionSummary(
        id=uuid4(),
        display_name="Hypospadias",
        rsg_codes=[CodedConcept(display="Hypospadias (disorder)", code="416010008")],
    )

    async def fake_get_latest_conditions_db(db):
        return [fake_condition_summary]

    monkeypatch.setattr(
        "app.api.v1.conditions.get_conditions_with_rsg_codes_db",
        fake_get_latest_conditions_db,
    )

    response = await authed_client.get("/api/v1/conditions/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["id"] == str(fake_condition_summary.id)
    assert data[0]["display_name"] == fake_condition_summary.display_name
    assert "associated" not in data[0]


@pytest.mark.asyncio
async def test_get_condition_found(monkeypatch, authed_client, mock_condition):
    fake_codes = [
        DbCode(
            system_name="LOINC",
            code="1234-5",
            display="test-code-1",
            system_id=get_mock_system_id_by_name("LOINC"),
        ),
        DbCode(
            system_name="SNOMED",
            code="67890",
            display="test-code-2",
            system_id=get_mock_system_id_by_name("SNOMED"),
        ),
    ]

    async def fake_get_condition_by_id_db(id, db):
        return mock_condition if id == mock_condition.id else None

    async def fake_get_condition_codes_by_condition_id_db(condition_id, db):
        return fake_codes

    monkeypatch.setattr(
        "app.api.v1.conditions.get_condition_by_id_db",
        fake_get_condition_by_id_db,
    )
    monkeypatch.setattr(
        "app.api.v1.conditions.get_condition_codes_by_condition_id_db",
        fake_get_condition_codes_by_condition_id_db,
    )

    response = await authed_client.get(f"/api/v1/conditions/{mock_condition.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(mock_condition.id)
    assert data["display_name"] == "Hypertension"
    assert any(code["system_name"] == "LOINC" for code in data["codes"])
    assert any(code["system_name"] == "SNOMED" for code in data["codes"])


@pytest.mark.asyncio
async def test_get_condition_not_found(monkeypatch, authed_client):
    async def fake_get_condition_by_id_db(id, db):
        return None

    monkeypatch.setattr(
        "app.api.v1.conditions.get_condition_by_id_db",
        fake_get_condition_by_id_db,
    )

    response = await authed_client.get(f"/api/v1/conditions/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Condition not found."
