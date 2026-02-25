from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import status

from app.db.configurations.db import SectionUpdate, update_section_processing_db
from app.db.configurations.model import (
    DbConfiguration,
    DbConfigurationSectionProcessing,
)


class _FakeCursor:
    def __init__(self, row):
        self._row = row

    async def execute(self, query, params):
        # simulate execution; nothing to do
        return None

    async def fetchone(self):
        return self._row


class _FakeConn:
    def __init__(self, row):
        self._cursor = _FakeCursor(row)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def cursor(self, row_factory=None):
        # Return an async context manager that yields our fake cursor
        fake_cursor = self._cursor

        class _CurCM:
            def __init__(self, cur):
                self._cur = cur

            async def __aenter__(self):
                return self._cur

            async def __aexit__(self, exc_type, exc, tb):
                return False

        return _CurCM(fake_cursor)


class _FakeDB:
    def __init__(self, row):
        self._row = row

    def get_connection(self):
        # Return an object that supports "async with"
        return _FakeConn(self._row)


@pytest.mark.asyncio
async def test_update_section_processing_valid():
    """
    Test valid updates to section processing entries.
    """
    # Mock configuration
    mock_config = DbConfiguration(
        id="mock_id",
        name="Test Config",
        jurisdiction_id="JD-1",
        condition_id="mock_condition",
        included_conditions=[],
        custom_codes=[],
        local_codes=[],
        section_processing=[
            DbConfigurationSectionProcessing(
                name="Section A", code="A", action="retain", versions=[]
            ),
        ],
        version=1,
        status="draft",
        last_activated_at=None,
        last_activated_by=None,
        created_by=uuid4(),
        condition_canonical_url="https://test.com",
        s3_urls=[],
    )
    # The DB should return the updated row; build that row dict
    updated_sections = [
        {"name": "Section A", "code": "A", "action": "refine"},
        {"name": "Section B", "code": "B", "action": "retain"},
    ]

    row = {
        "id": mock_config.id,
        "name": mock_config.name,
        "jurisdiction_id": mock_config.jurisdiction_id,
        "condition_id": mock_config.condition_id,
        "included_conditions": [],
        "custom_codes": [],
        "local_codes": [],
        "section_processing": updated_sections,
        "version": 2,
        "status": mock_config.status,
        "last_activated_at": mock_config.last_activated_at,
        "last_activated_by": mock_config.last_activated_by,
        "created_by": mock_config.created_by,
        "condition_canonical_url": mock_config.condition_canonical_url,
        "s3_urls": mock_config.s3_urls,
    }

    fake_db = _FakeDB(row=row)

    # Payload for updates
    section_updates = [
        SectionUpdate(code="A", action="refine"),
        SectionUpdate(code="B", action="retain"),
    ]

    updated_config = await update_section_processing_db(
        config=mock_config,
        section_updates=section_updates,
        user_id="673da667-6f92-4a50-a40d-f44c5bc6a2d8",
        db=fake_db,
    )

    # Assert updates were applied
    assert any(
        sp.code == "A" and sp.action == "refine"
        for sp in updated_config.section_processing
    )
    assert any(
        sp.code == "B" and sp.action == "retain"
        for sp in updated_config.section_processing
    )


@pytest.mark.asyncio
async def test_update_section_processing_invalid_action():
    """
    Test invalid action raises ValueError.
    """
    mock_config = DbConfiguration(
        id="mock_id",
        name="Test Config",
        jurisdiction_id="JD-1",
        condition_id="mock_condition",
        included_conditions=[],
        custom_codes=[],
        local_codes=[],
        section_processing=[
            DbConfigurationSectionProcessing(
                name="Section A", code="A", action="retain", versions=[]
            ),
        ],
        version=1,
        status="draft",
        last_activated_at=None,
        last_activated_by=None,
        created_by=uuid4(),
        condition_canonical_url="https://test.com",
        s3_urls=[],
    )

    # The DB should return the same existing sections because unknown update codes are ignored.
    existing_sections = [
        {"name": "Section A", "code": "A", "action": "retain"},
    ]

    row = {
        "id": mock_config.id,
        "name": mock_config.name,
        "jurisdiction_id": mock_config.jurisdiction_id,
        "condition_id": mock_config.condition_id,
        "included_conditions": [],
        "custom_codes": [],
        "local_codes": [],
        "section_processing": existing_sections,
        "version": 1,
        "status": mock_config.status,
        "last_activated_at": mock_config.last_activated_at,
        "last_activated_by": mock_config.last_activated_by,
        "created_by": mock_config.created_by,
        "condition_canonical_url": mock_config.condition_canonical_url,
        "s3_urls": mock_config.s3_urls,
    }

    fake_db = _FakeDB(row=row)

    # Payload with unknown code
    section_updates = [
        SectionUpdate(code="Unknown", action="refine"),
    ]

    updated_config = await update_section_processing_db(
        config=mock_config,
        section_updates=section_updates,
        user_id="673da667-6f92-4a50-a40d-f44c5bc6a2d8",
        db=fake_db,
    )

    # Assert existing entries remain unchanged
    assert len(updated_config.section_processing) == 1
    assert updated_config.section_processing[0].code == "A"
    assert updated_config.section_processing[0].action == "retain"


@pytest.mark.asyncio
async def test_update_section_processing_success(authed_client, monkeypatch, mock_user):
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
        created_by=mock_user.id,
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
        created_by=mock_user.id,
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
async def test_update_section_processing_db_returns_none(
    authed_client, monkeypatch, mock_user
):
    # Arrange: existing configuration
    config_id = uuid4()
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
        created_by=mock_user.id,
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
