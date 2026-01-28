from uuid import uuid4

import pytest

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
        tes_version="1.0.0",
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
        "tes_version": "1.0.0",
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
        tes_version="1.0.0",
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
        "tes_version": "1.0.0",
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
