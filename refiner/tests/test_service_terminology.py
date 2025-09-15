from uuid import uuid4

from app.db.conditions.model import DbCondition, DbConditionCoding
from app.db.configurations.model import DbConfiguration, DbConfigurationCustomCode
from app.db.models import GrouperRow
from app.services.terminology import (
    Configuration,
    ProcessedConfiguration,
    ProcessedGrouper,
    aggregate_codes_from_conditions,
)


def make_db_condition_coding(code, display):
    return DbConditionCoding(code=code, display=display)


def make_condition(**kwargs):
    """
    Helper to create a DbCondition with all code fields present.
    """

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


def make_dbconfiguration(**kwargs):
    """
    Helper to create a DbConfiguration with required fields.
    """

    defaults = {
        "id": uuid4(),
        "name": "Test Config",
        "jurisdiction_id": "JD-1",
        "condition_id": uuid4(),
        "included_conditions": [],
        "custom_codes": [],
        "local_codes": [],
        "sections_to_include": [],
        "cloned_from_configuration_id": None,
        "version": 1,
    }
    defaults.update(kwargs)
    return DbConfiguration(**defaults)


def test_configuration_model_and_aggregate_codes():
    """
    Test Configuration model and code aggregation.
    """

    cond1 = make_condition(
        snomed_codes=[make_db_condition_coding("1111", "SNOMED1")],
        loinc_codes=[make_db_condition_coding("2222", "LOINC1")],
        icd10_codes=[],
        rxnorm_codes=[],
    )
    cond2 = make_condition(
        snomed_codes=[make_db_condition_coding("3333", "SNOMED2")],
        loinc_codes=[],
        icd10_codes=[make_db_condition_coding("I10", "ICD10")],
        rxnorm_codes=[make_db_condition_coding("4444", "RXNORM")],
    )
    config = make_dbconfiguration(
        custom_codes=[
            DbConfigurationCustomCode(code="5555", system="LOINC", name="Custom LOINC")
        ]
    )
    conf_model = Configuration(conditions=[cond1, cond2], configuration=config)

    # test aggregate_codes_from_conditions
    code_set = aggregate_codes_from_conditions([cond1, cond2])
    assert code_set == {"1111", "2222", "3333", "I10", "4444"}

    # test Configuration model holds conditions/configuration as expected
    assert conf_model.conditions == [cond1, cond2]
    assert conf_model.configuration == config


def test_processed_configuration_from_configuration_and_xpath():
    """
    Test that ProcessedConfiguration aggregates codes and builds correct xpath.
    """

    cond1 = make_condition(
        snomed_codes=[make_db_condition_coding("A", "SNOMED")],
        loinc_codes=[],
        icd10_codes=[],
        rxnorm_codes=[],
    )
    config = make_dbconfiguration(
        custom_codes=[
            DbConfigurationCustomCode(code="B", system="LOINC", name="Custom LOINC")
        ]
    )
    conf_model = Configuration(conditions=[cond1], configuration=config)
    processed = ProcessedConfiguration.from_configuration(conf_model)

    # it should aggregate codes from condition and custom codes
    assert processed.codes == {"A", "B"}

    xpath = processed.build_xpath()
    assert '@code="A"' in xpath
    assert '@code="B"' in xpath
    assert ".//hl7:code[" in xpath
    assert " | " in xpath


def test_processed_configuration_empty_codes():
    """
    ProcessedConfiguration with no codes returns empty xpath.
    """

    cond = make_condition(
        snomed_codes=[], loinc_codes=[], icd10_codes=[], rxnorm_codes=[]
    )
    config = make_dbconfiguration(custom_codes=[])
    conf_model = Configuration(conditions=[cond], configuration=config)
    processed = ProcessedConfiguration.from_configuration(conf_model)
    assert processed.codes == set()
    assert processed.build_xpath() == ""


def test_processed_configuration_duplicate_codes():
    """
    Ensure duplicate codes are deduplicated in ProcessedConfiguration.
    """

    cond1 = make_condition(snomed_codes=[make_db_condition_coding("X", "SNOMED")])
    cond2 = make_condition(loinc_codes=[make_db_condition_coding("X", "LOINC")])
    config = make_dbconfiguration(
        custom_codes=[
            DbConfigurationCustomCode(code="X", system="LOINC", name="Custom")
        ]
    )
    conf_model = Configuration(conditions=[cond1, cond2], configuration=config)
    processed = ProcessedConfiguration.from_configuration(conf_model)
    # Only one "X" should be present
    assert processed.codes == {"X"}


def test_aggregate_codes_from_conditions_handles_empty():
    """
    aggregate_codes_from_conditions handles empty input.
    """

    assert aggregate_codes_from_conditions([]) == set()


def test_processed_grouper_creation() -> None:
    """
    Test basic creation of ProcessedGrouper from GrouperRow.
    """

    row = GrouperRow(
        condition="38362002",
        display_name="Test Condition",
        loinc_codes='[{"code": "123", "display": "Test LOINC"}]',
        snomed_codes='[{"code": "456", "display": "Test SNOMED"}]',
        icd10_codes='[{"code": "789", "display": "Test ICD10"}]',
        rxnorm_codes='[{"code": "012", "display": "Test RxNorm"}]',
    )

    processed = ProcessedGrouper.from_grouper_row(row)
    assert processed.condition == "38362002"
    assert processed.display_name == "Test Condition"
    assert processed.codes == {"123", "456", "789", "012"}


def test_processed_grouper_empty_codes() -> None:
    """
    Test ProcessedGrouper creation with empty code arrays.
    """

    row = GrouperRow(
        condition="38362002",
        display_name="Test Condition",
        loinc_codes="[]",
        snomed_codes="[]",
        icd10_codes="[]",
        rxnorm_codes="[]",
    )

    processed = ProcessedGrouper.from_grouper_row(row)
    assert processed.codes == set()


def test_processed_grouper_malformed_json() -> None:
    """
    Test ProcessedGrouper handling of malformed JSON.
    """

    row = GrouperRow(
        condition="38362002",
        display_name="Test Condition",
        loinc_codes='[{"code": "123", "display": "Test"}]',
        snomed_codes="invalid json",  # Malformed JSON
        icd10_codes="[]",
        rxnorm_codes="[]",
    )

    # test that it handles the error gracefully
    processed = ProcessedGrouper.from_grouper_row(row)
    assert "123" in processed.codes  # Should have valid codes
    assert len(processed.codes) == 1  # Should only have valid codes


def test_processed_grouper_json_error_handling() -> None:
    """
    Test ProcessedGrouper handles various JSON errors gracefully.
    """

    test_cases = [
        # malformed JSON
        ("invalid json", set()),
        # empty string
        ("", set()),
        # not an array
        ('{"code": "123"}', set()),
        # array but wrong structure
        ('["not an object"]', set()),
        # valid but missing code field
        ('[{"display": "Test"}]', set()),
        # valid with mixed good/bad entries
        ('[{"code": "123"}, {"display": "bad"}, {"code": "456"}]', {"123", "456"}),
    ]

    for json_str, expected_codes in test_cases:
        row = GrouperRow(
            condition="38362002",
            display_name="Test Condition",
            loinc_codes='[{"code": "789", "display": "Test"}]',  # Always valid
            snomed_codes=json_str,  # Test case
            icd10_codes="[]",
            rxnorm_codes="[]",
        )

        processed = ProcessedGrouper.from_grouper_row(row)
        assert "789" in processed.codes  # Should always have valid code
        test_codes = processed.codes - {"789"}  # Remove known valid code
        assert test_codes == expected_codes, f"Failed for input: {json_str}"


def test_xpath_generation() -> None:
    """
    Test XPath generation with different inputs.
    """

    processed = ProcessedGrouper(
        condition="38362002", display_name="Test Condition", codes={"123", "456"}
    )

    # default search now uses comprehensive "any" search
    xpath = processed.build_xpath()

    # verify it contains the expected patterns (order-independent)
    assert ".//hl7:*[hl7:code[" in xpath
    assert ".//hl7:code[" in xpath
    assert ".//hl7:translation[" in xpath
    assert '@code="123"' in xpath  # Contains both codes
    assert '@code="456"' in xpath
    assert " | " in xpath  # Union operator


def test_xpath_empty_codes() -> None:
    """
    Test XPath generation with no codes.
    """

    processed = ProcessedGrouper(
        condition="38362002", display_name="Test Condition", codes=set()
    )

    assert processed.build_xpath() == ""
