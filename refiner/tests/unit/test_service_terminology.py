from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.models.terminology import Coding
from app.db.codes.model import DbConditionCode
from app.db.conditions.model import DbCondition
from app.db.configurations.custom_codes.model import DbCustomCode
from app.db.configurations.model import (
    DbConfiguration,
)
from app.services.configurations import index_code_list_by_system_key
from app.services.ecr.specification.constants import OID_TO_SYSTEM_KEY_MAP
from app.services.logger import get_logger
from app.services.terminology import CodeSystemSets
from tests.unit.conftest import get_mock_system_id_by_name
from tests.unit.helpers.configuration import create_processed_config


def make_code_response(code, display_name, system_name):
    return DbConditionCode(
        code=code,
        display_name=display_name,
        system_id=get_mock_system_id_by_name(system_name),
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
        "display_name": "Test Config",
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
            codes=[
                make_code_response(
                    code="A", display_name="SNOMED", system_name="SNOMED"
                )
            ]
        )

        loinc = get_mock_system("loinc")

        mock_config_id = uuid4()
        config: DbConfiguration = make_dbconfiguration(
            id=mock_config_id,
            custom_codes=[
                DbCustomCode(
                    id=uuid4(),
                    code="B",
                    display_name="Custom LOINC",
                    system_id=loinc.id,
                    updated_at=datetime.now(UTC),
                    created_at=datetime.now(UTC),
                    configuration_id=mock_config_id,
                )
            ],
        )
        processed = await create_processed_config(config=config, conditions=[cond1])
        assert processed.codes == {"A", "B"}

    async def test_processed_configuration_duplicate_codes(self, get_mock_system):
        cond1: DbCondition = make_condition(
            codes=[
                make_code_response(
                    code="DUP", display_name="SNOMED", system_name="SNOMED"
                )
            ]
        )
        cond2: DbCondition = make_condition(
            codes=[
                make_code_response(
                    code="DUP", display_name="LOINC", system_name="LOINC"
                )
            ]
        )
        loinc = get_mock_system("loinc")

        mock_config_id = uuid4()
        config: DbConfiguration = make_dbconfiguration(
            custom_codes=[
                DbCustomCode(
                    id=uuid4(),
                    code="DUP",
                    display_name="Custom",
                    system_id=loinc.id,
                    updated_at=datetime.now(UTC),
                    created_at=datetime.now(UTC),
                    configuration_id=mock_config_id,
                )
            ]
        )

        processed = await create_processed_config(
            config=config, conditions=[cond1, cond2]
        )
        assert processed.codes == {"DUP"}


class TestCodingKeyContract:
    """
    Pins the writer/reader agreement on the `active.json` coding keys.

    Nothing guarded this before, which is how #967 lived for seven months:
    `CodeSystemSets.to_dict` wrote `"system"` while `from_dict` read `"system_oid"`,
    so every `Coding` the Lambda rebuilt had `system_oid=""`. The same shape of
    mismatch reappeared while renaming `Coding.display` -> `display_name`, because
    `index_code_list_by_system_key` had been emitting `asdict(Coding(...))` and so
    inherited its keys from field names. These two tests fail on either mistake.
    """

    def test_index_output_is_readable_by_from_dict(self, mock_all_systems):
        """The in-process hop: activation writes these dicts, the refiner reads them."""

        loinc = next(s for s in mock_all_systems if s.key == "loinc")
        indexed = index_code_list_by_system_key(
            codes=[
                Coding(
                    code="94759-8",
                    display_name="SARS-CoV-2 RNA",
                    system_oid=loinc.oid,
                )
            ],
            logger=get_logger(),
        )

        sets = CodeSystemSets.from_dict(
            coding_by_code_system=indexed,
            oid_to_system_map=OID_TO_SYSTEM_KEY_MAP,
        )
        coding = sets.find_match("94759-8")

        assert coding is not None, "from_dict could not read what index_* wrote"
        # the display surviving the hop is the part that silently broke
        assert coding.display_name == "SARS-CoV-2 RNA"
        assert coding.system_oid == loinc.oid

    def test_to_dict_is_readable_by_from_dict(self, mock_all_systems):
        """The S3 hop: one deploy writes active.json, a different one reads it."""

        snomed = next(s for s in mock_all_systems if s.key == "snomed")
        original = CodeSystemSets.from_dict(
            coding_by_code_system=index_code_list_by_system_key(
                codes=[
                    Coding(
                        code="260373001",
                        display_name="Detected",
                        system_oid=snomed.oid,
                    )
                ],
                logger=get_logger(),
            ),
            oid_to_system_map=OID_TO_SYSTEM_KEY_MAP,
        )

        round_tripped = CodeSystemSets.from_dict(
            coding_by_code_system=original.to_dict(),
            oid_to_system_map=OID_TO_SYSTEM_KEY_MAP,
        )

        before, after = (
            original.find_match("260373001"),
            round_tripped.find_match("260373001"),
        )
        assert before is not None and after is not None
        assert before.code == after.code
        assert before.display_name == after.display_name
