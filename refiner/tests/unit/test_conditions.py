from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.api.auth.middleware import get_logged_in_user
from app.db.conditions.db import GetConditionCode
from app.db.conditions.model import DbCondition, DbConditionCoding
from app.main import app

# User info
TEST_SESSION_TOKEN = "test-token"


def make_db_condition_coding(code, display):
    return DbConditionCoding(code=code, display=display)


@pytest_asyncio.fixture
async def authed_client(mock_logged_in_user):
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


@pytest.mark.asyncio
async def test_get_latest_conditions(monkeypatch, authed_client):
    fake_condition = DbCondition(
        id=uuid4(),
        display_name="Hypertension",
        canonical_url="http://url.com",
        version="4.0.0",
        child_rsg_snomed_codes=["11111"],
        snomed_codes=[make_db_condition_coding("11111", "Hypertension SNOMED")],
        loinc_codes=[make_db_condition_coding("22222", "Hypertension LOINC")],
        icd10_codes=[make_db_condition_coding("I10", "Essential hypertension")],
        rxnorm_codes=[make_db_condition_coding("33333", "Hypertension RXNORM")],
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
        snomed_codes=[make_db_condition_coding("67890", "Asthma SNOMED")],
        loinc_codes=[make_db_condition_coding("1234-5", "Asthma LOINC")],
        icd10_codes=[make_db_condition_coding("J45", "Asthma ICD10")],
        rxnorm_codes=[make_db_condition_coding("55555", "Asthma RXNORM")],
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
    assert sorted(data["available_systems"]) == ["LOINC", "SNOMED"]
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
