from datetime import datetime
from uuid import uuid4

import pytest
from fastapi import status

from app.db.conditions.db import GetConditionCode
from app.db.conditions.model import DbCondition, DbConditionCoding


@pytest.mark.asyncio
async def test_get_latest_conditions(monkeypatch, authed_client):
    fake_condition = DbCondition(
        id=uuid4(),
        display_name="Hypertension",
        canonical_url="http://url.com",
        version="4.0.0",
        child_rsg_snomed_codes=["11111"],
        snomed_codes=[DbConditionCoding("11111", "Hypertension SNOMED")],
        loinc_codes=[DbConditionCoding("22222", "Hypertension LOINC")],
        icd10_codes=[DbConditionCoding("I10", "Essential hypertension")],
        rxnorm_codes=[DbConditionCoding("33333", "Hypertension RXNORM")],
        cvx_codes=[DbConditionCoding("124124", "Hypertension CVX")],
    )

    async def fake_get_latest_conditions_db(db):
        return [fake_condition]

    monkeypatch.setattr(
        "app.api.v1.conditions.get_latest_conditions_db", fake_get_latest_conditions_db
    )

    response = await authed_client.get("/api/v1/conditions/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["id"] == str(fake_condition.id)
    assert data[0]["display_name"] == fake_condition.display_name
    assert "associated" not in data[0]


@pytest.mark.asyncio
async def test_get_condition_found(monkeypatch, authed_client):
    condition_id = uuid4()

    fake_condition = DbCondition(
        id=condition_id,
        display_name="Asthma",
        canonical_url="http://asthma.com",
        version="4.0.0",
        child_rsg_snomed_codes=["67890"],
        snomed_codes=[DbConditionCoding("67890", "Asthma SNOMED")],
        loinc_codes=[DbConditionCoding("1234-5", "Asthma LOINC")],
        icd10_codes=[DbConditionCoding("J45", "Asthma ICD10")],
        rxnorm_codes=[DbConditionCoding("55555", "Asthma RXNORM")],
        cvx_codes=[DbConditionCoding("15125", "Asthma CVX")],
    )

    fake_codes = [
        GetConditionCode(system="LOINC", code="1234-5", description="test-code-1"),
        GetConditionCode(system="SNOMED", code="67890", description="test-code-2"),
    ]

    async def fake_get_condition_by_id_db(id, db):
        return fake_condition if id == condition_id else None

    async def fake_get_condition_codes_by_condition_id_db(id, db):
        return fake_codes

    monkeypatch.setattr(
        "app.api.v1.conditions.get_condition_by_id_db",
        fake_get_condition_by_id_db,
    )
    monkeypatch.setattr(
        "app.api.v1.conditions.get_condition_codes_by_condition_id_db",
        fake_get_condition_codes_by_condition_id_db,
    )

    response = await authed_client.get(f"/api/v1/conditions/{condition_id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(condition_id)
    assert data["display_name"] == "Asthma"
    assert any(code["system"] == "LOINC" for code in data["codes"])
    assert any(code["system"] == "SNOMED" for code in data["codes"])


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


@pytest.mark.asyncio
async def test_get_condition_coverage_data(monkeypatch, authed_client):
    condition_id = uuid4()

    fake_condition = DbCondition(
        id=condition_id,
        display_name="Coverage Test",
        canonical_url="http://coverage.com",
        version="4.0.0",
        child_rsg_snomed_codes=["111"],
        snomed_codes=[DbConditionCoding("111", "Test")],
        loinc_codes=[],
        icd10_codes=[],
        rxnorm_codes=[],
        cvx_codes=[],
        coverage_level="partial",
        coverage_level_reason="Missing some codes",
        coverage_level_date=datetime(2026, 1, 1),
    )

    fake_codes = [
        GetConditionCode(
            system="SNOMED",
            code="111",
            description="Test",
            coverage_level="partial",
            coverage_level_reason="Missing some codes",
            coverage_level_date=None,
        ),
    ]

    async def fake_get_condition_by_id_db(id, db):
        return fake_condition if id == condition_id else None

    async def fake_get_condition_codes_by_condition_id_db(id, db):
        return fake_codes

    monkeypatch.setattr(
        "app.api.v1.conditions.get_condition_by_id_db",
        fake_get_condition_by_id_db,
    )
    monkeypatch.setattr(
        "app.api.v1.conditions.get_condition_codes_by_condition_id_db",
        fake_get_condition_codes_by_condition_id_db,
    )

    response = await authed_client.get(f"/api/v1/conditions/{condition_id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    code = data["codes"][0]
    assert code["coverage_level"] == "partial"
    assert code["coverage_level_reason"] == "Missing some codes"
    assert code["coverage_level_date"] is None
