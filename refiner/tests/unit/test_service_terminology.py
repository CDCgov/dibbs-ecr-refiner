from uuid import uuid4

from app.db.conditions.model import DbCondition, DbConditionCoding
from app.db.configurations.model import DbConfiguration, DbConfigurationCustomCode
from app.services.terminology import (
    ConfigurationPayload,
    ProcessedConfiguration,
)


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


def test_processed_configuration_from_payload_and_xpath():
    cond1: DbCondition = make_condition(
        snomed_codes=[make_db_condition_coding("A", "SNOMED")]
    )
    config: DbConfiguration = make_dbconfiguration(
        custom_codes=[
            DbConfigurationCustomCode(code="B", system="LOINC", name="Custom LOINC")
        ]
    )
    payload = ConfigurationPayload(conditions=[cond1], configuration=config)
    processed = ProcessedConfiguration.from_payload(payload)
    assert processed.codes == {"A", "B"}


def test_processed_configuration_empty_codes():
    cond: DbCondition = make_condition()
    config: DbConfiguration = make_dbconfiguration()
    payload = ConfigurationPayload(conditions=[cond], configuration=config)
    processed = ProcessedConfiguration.from_payload(payload)
    assert processed.codes == set()


def test_processed_configuration_duplicate_codes():
    cond1: DbCondition = make_condition(
        snomed_codes=[make_db_condition_coding("DUP", "SNOMED")]
    )
    cond2: DbCondition = make_condition(
        loinc_codes=[make_db_condition_coding("DUP", "LOINC")]
    )
    config: DbConfiguration = make_dbconfiguration(
        custom_codes=[
            DbConfigurationCustomCode(code="DUP", system="LOINC", name="Custom")
        ]
    )
    payload = ConfigurationPayload(conditions=[cond1, cond2], configuration=config)
    processed = ProcessedConfiguration.from_payload(payload)
    assert processed.codes == {"DUP"}


def test_payload_class_existence():
    # sanity checks for class existence
    assert ConfigurationPayload
    assert ProcessedConfiguration
