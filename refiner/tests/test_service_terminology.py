from uuid import uuid4

from app.db.conditions.model import DbCondition, DbConditionCoding
from app.db.configurations.model import DbConfiguration, DbConfigurationCustomCode
from app.services.terminology import (
    ConditionPayload,
    ConfigurationPayload,
    ProcessedCondition,
    ProcessedConfiguration,
    aggregate_codes_from_conditions,
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
        "local_codes": [],
        "section_processing": [],
        "version": 1,
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
    xpath = processed.build_xpath()
    assert '@code="A"' in xpath
    assert '@code="B"' in xpath
    assert ".//hl7:code[" in xpath
    assert " | " in xpath


def test_processed_configuration_empty_codes():
    cond: DbCondition = make_condition()
    config: DbConfiguration = make_dbconfiguration()
    payload = ConfigurationPayload(conditions=[cond], configuration=config)
    processed = ProcessedConfiguration.from_payload(payload)
    assert processed.codes == set()
    assert processed.build_xpath() == ""


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


def test_processed_condition_from_payload():
    cond1: DbCondition = make_condition(
        snomed_codes=[make_db_condition_coding("C1", "SNOMED")]
    )
    cond2: DbCondition = make_condition(
        loinc_codes=[make_db_condition_coding("C2", "LOINC")]
    )
    payload = ConditionPayload(conditions=[cond1, cond2])
    processed = ProcessedCondition.from_payload(payload)
    assert processed.codes == {"C1", "C2"}
    xpath = processed.build_xpath()
    assert '@code="C1"' in xpath
    assert '@code="C2"' in xpath


def test_processed_condition_empty_codes():
    payload = ConditionPayload(conditions=[])
    processed = ProcessedCondition.from_payload(payload)
    assert processed.codes == set()
    assert processed.build_xpath() == ""


def test_aggregate_codes_from_conditions_various():
    cond1: DbCondition = make_condition(
        snomed_codes=[make_db_condition_coding("A", "SNOMED")],
        loinc_codes=[make_db_condition_coding("B", "LOINC")],
        icd10_codes=[make_db_condition_coding("C", "ICD10")],
        rxnorm_codes=[make_db_condition_coding("D", "RXNORM")],
    )
    cond2: DbCondition = make_condition(
        snomed_codes=[make_db_condition_coding("E", "SNOMED")]
    )
    codes = aggregate_codes_from_conditions([cond1, cond2])
    assert codes == {"A", "B", "C", "D", "E"}
    assert aggregate_codes_from_conditions([]) == set()


def test_payload_class_existence():
    # sanity checks for class existence
    assert ConfigurationPayload
    assert ConditionPayload
    assert ProcessedConfiguration
    assert ProcessedCondition
