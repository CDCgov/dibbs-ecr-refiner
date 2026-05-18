from uuid import uuid4

import pytest

from app.db.conditions.model import DbCondition, DbConditionCoding
from app.db.configurations.model import (
    DbConfiguration,
    DbConfigurationCustomCode,
)
from app.services.terminology import (
    CodeSystems,
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
        "condition_canonical_url": "https://test.com",
        "s3_urls": [],
    }
    defaults.update(kwargs)
    return DbConfiguration(**defaults)


@pytest.mark.asyncio
class TestTerminologyService:
    async def test_processed_configuration_from_payload_and_xpath(self):

        cond1: DbCondition = make_condition(
            snomed_codes=[make_db_condition_coding("A", "SNOMED")]
        )
        config: DbConfiguration = make_dbconfiguration(
            custom_codes=[
                DbConfigurationCustomCode(
                    code="B",
                    system=CodeSystems.get_by_key_or_raise("loinc").name,
                    name="Custom LOINC",
                )
            ]
        )
        processed = await create_processed_config(config=config, conditions=[cond1])
        assert processed.codes == {"A", "B"}

    async def test_processed_configuration_duplicate_codes(self):
        cond1: DbCondition = make_condition(
            snomed_codes=[make_db_condition_coding("DUP", "SNOMED")]
        )
        cond2: DbCondition = make_condition(
            loinc_codes=[make_db_condition_coding("DUP", "LOINC")]
        )
        config: DbConfiguration = make_dbconfiguration(
            custom_codes=[
                DbConfigurationCustomCode(
                    code="DUP",
                    system=CodeSystems.get_by_key_or_raise("loinc").name,
                    name="Custom",
                )
            ]
        )
        processed = await create_processed_config(
            config=config, conditions=[cond1, cond2]
        )
        assert processed.codes == {"DUP"}
