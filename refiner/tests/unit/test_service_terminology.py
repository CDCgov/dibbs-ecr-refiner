from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.db.code_systems.db import DbCodeSystem
from app.db.conditions.model import DbCondition, DbConditionCoding
from app.db.configurations.model import (
    DbConfiguration,
    DbConfigurationCustomCode,
)
from tests.unit.helpers.configuration import create_processed_config


def make_db_condition_coding(code, display):
    return DbConditionCoding(code=code, display=display)


def make_condition(**kwargs) -> DbCondition:
    defaults = {
        "id": uuid4(),
        "display_name": "Condition",
        "canonical_url": "http://cond.com",
        "version": "1.0.0",
        "child_rsg_snomed_codes": [],
        "snomed_codes": [],
        "loinc_codes": [],
        "icd10_codes": [],
        "rxnorm_codes": [],
        "cvx_codes": [],
    }
    defaults.update(kwargs)
    return DbCondition(**defaults)


def make_dbconfiguration(**kwargs) -> DbConfiguration:
    defaults = {
        "id": uuid4(),
        "name": "Test Config",
        "jurisdiction_id": "JD-1",
        "condition_id": uuid4(),
        "included_conditions": [],
        "custom_codes": [],
        "section_processing": [],
        "version": 1,
        "status": "draft",
        "last_activated_at": None,
        "last_activated_by": None,
        "created_by": uuid4(),
        "s3_url": "",
    }
    defaults.update(kwargs)
    return DbConfiguration(**defaults)


@pytest.fixture(autouse=True)
def mock_db_functions(monkeypatch, mock_all_systems):
    """
    Mock return values of the `_db` functions called by the routes.
    """
    monkeypatch.setattr(
        "app.services.code_systems.get_all_code_systems_db",
        AsyncMock(return_value={m.id: m for m in mock_all_systems}),
    )

    monkeypatch.setattr(
        "app.services.configurations.get_all_code_systems_db",
        AsyncMock(return_value={m.id: m for m in mock_all_systems}),
    )

    monkeypatch.setattr(
        "app.services.configurations.get_code_system_by_key_db",
        AsyncMock(
            side_effect=lambda key, db: next(
                m for m in mock_all_systems if m.key == key
            ),
        ),
    )


def get_mock_system(key: str, systems: list[DbCodeSystem]) -> DbCodeSystem:
    return next(s for s in systems if s.key == key)


@pytest.mark.asyncio
class TestTerminologyService:
    async def test_processed_configuration_from_payload_and_xpath(
        self, mock_all_systems
    ):
        cond1: DbCondition = make_condition(
            snomed_codes=[make_db_condition_coding("A", "SNOMED")]
        )

        loinc = get_mock_system("loinc", mock_all_systems)

        config: DbConfiguration = make_dbconfiguration(
            custom_codes=[
                DbConfigurationCustomCode(
                    id="test-code",
                    code="B",
                    name="Custom LOINC",
                    system_id=str(loinc.id),
                )
            ]
        )
        processed = await create_processed_config(config=config, conditions=[cond1])
        assert processed.codes == {"A", "B"}

    async def test_processed_configuration_duplicate_codes(self, mock_all_systems):
        cond1: DbCondition = make_condition(
            snomed_codes=[make_db_condition_coding("DUP", "SNOMED")]
        )
        cond2: DbCondition = make_condition(
            loinc_codes=[make_db_condition_coding("DUP", "LOINC")]
        )
        loinc = get_mock_system("loinc", mock_all_systems)

        config: DbConfiguration = make_dbconfiguration(
            custom_codes=[
                DbConfigurationCustomCode(
                    id="test-code",
                    code="DUP",
                    name="Custom",
                    system_id=str(loinc.id),
                )
            ]
        )

        processed = await create_processed_config(
            config=config, conditions=[cond1, cond2]
        )
        assert processed.codes == {"DUP"}
