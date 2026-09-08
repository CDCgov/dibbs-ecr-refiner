from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.db.codes.model import DbCode
from app.db.conditions.model import DbCondition
from app.db.configurations.custom_codes.model import DbCustomCode
from app.db.configurations.model import (
    DbConfiguration,
)
from tests.unit.conftest import get_mock_system_id_by_name
from tests.unit.helpers.configuration import create_processed_config


def make_code_response(code, display, system_name):
    return DbCode(
        code=code,
        display=display,
        system_id=get_mock_system_id_by_name(system_name),
        system_name=system_name,
    )


def make_condition(**kwargs) -> DbCondition:
    defaults = {
        "id": uuid4(),
        "display_name": "Condition",
        "canonical_url": "http://cond.com",
        "version": "1.0.0",
        "codes": [],
        "child_rsg_snomed_codes": [],
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
        "app.services.code_systems.get_code_systems_db",
        AsyncMock(return_value=mock_all_systems),
    )

    monkeypatch.setattr(
        "app.services.configurations.get_id_to_code_system_dict_db",
        AsyncMock(return_value={m.id: m for m in mock_all_systems}),
    )


@pytest.mark.asyncio
class TestTerminologyService:
    async def test_processed_configuration_from_payload_and_xpath(
        self, get_mock_system
    ):
        cond1: DbCondition = make_condition(
            codes=[make_code_response(code="A", display="SNOMED", system_name="SNOMED")]
        )

        loinc = get_mock_system("loinc")

        mock_config_id = uuid4()
        config: DbConfiguration = make_dbconfiguration(
            id=mock_config_id,
            custom_codes=[
                DbCustomCode(
                    id=uuid4(),
                    code="B",
                    display="Custom LOINC",
                    system_id=loinc.id,
                    updated_at=datetime.now(),
                    created_at=datetime.now(),
                    configuration_id=mock_config_id,
                )
            ],
        )
        processed = await create_processed_config(config=config, conditions=[cond1])
        assert processed.codes == {"A", "B"}

    async def test_processed_configuration_duplicate_codes(self, get_mock_system):
        cond1: DbCondition = make_condition(
            codes=[
                make_code_response(code="DUP", display="SNOMED", system_name="SNOMED")
            ]
        )
        cond2: DbCondition = make_condition(
            codes=[make_code_response(code="DUP", display="LOINC", system_name="LOINC")]
        )
        loinc = get_mock_system("loinc")

        mock_config_id = uuid4()
        config: DbConfiguration = make_dbconfiguration(
            custom_codes=[
                DbCustomCode(
                    id=uuid4(),
                    code="DUP",
                    display="Custom",
                    system_id=loinc.id,
                    updated_at=datetime.now(),
                    created_at=datetime.now(),
                    configuration_id=mock_config_id,
                )
            ]
        )

        processed = await create_processed_config(
            config=config, conditions=[cond1, cond2]
        )
        assert processed.codes == {"DUP"}
