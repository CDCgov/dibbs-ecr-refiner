from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import status

from app.api.v1.conditions import _get_code_category_statuses
from app.core.models.terminology import CodeLabel
from app.db.conditions.model import DbConditionsContextGrouper, DbConditionSummary


@pytest.mark.asyncio
async def test_get_latest_conditions(monkeypatch, authed_client):
    fake_condition_summary = DbConditionSummary(
        id=uuid4(),
        display_name="Hypospadias",
        rsg_codes=[CodeLabel(code="416010008", display_name="Hypospadias (disorder)")],
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
    async def fake_get_condition_by_id_db(id, db):
        return mock_condition if id == mock_condition.id else None

    monkeypatch.setattr(
        "app.api.v1.conditions.get_condition_by_id_db",
        fake_get_condition_by_id_db,
    )

    response = await authed_client.get(f"/api/v1/conditions/{mock_condition.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(mock_condition.id)
    assert data["display_name"] == "Hypertension"
    assert "completeness_status" in data

    # this route served every code for the condition -- tens of thousands of rows --
    # and its one caller renders `completeness_status` alone. codes are paged through
    # `configurations/{id}/codes` instead, so re-adding them here is a regression
    assert set(data) == {"id", "display_name", "completeness_status"}


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


def _grouper(category: str, completeness: str | None) -> DbConditionsContextGrouper:
    now = datetime.now(UTC)
    return DbConditionsContextGrouper(
        id=uuid4(),
        condition_id=uuid4(),
        display_name=f"{category} grouper",
        category=category,
        canonical_url=f"http://example.org/ValueSet/{category}",
        code_count=1,
        completeness=completeness,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.parametrize(
    ("completeness_values", "expected"),
    [
        (["fully complete", "partially complete"], "partially complete"),
        (["partially complete", "fully complete"], "partially complete"),
        (["fully complete", None], "not included"),
        ([None, "fully complete"], "not included"),
        (["fully complete", "fully complete"], "fully complete"),
    ],
)
def test_code_category_status_takes_the_least_complete_grouper(
    completeness_values, expected
):
    # the database does not define the order these rows come back in, so the
    # result must not depend on it -- both orderings are asserted above
    groupers = [_grouper("symptom", value) for value in completeness_values]

    statuses = _get_code_category_statuses(groupers=groupers)
    symptom = next(s for s in statuses if s.category == "symptom")

    assert symptom.completeness == expected


def test_code_category_status_reports_every_known_category():
    statuses = _get_code_category_statuses(groupers=[])

    assert {s.category for s in statuses} == {
        "symptom",
        "medication",
        "diagnosis",
        "clinical_lab_result",
        "immunization",
        "specimen_source",
    }
    assert all(s.completeness == "not included" for s in statuses)
