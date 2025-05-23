from app.db.models import GrouperRow
from app.services.terminology import ProcessedGrouper


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

    # default search_in
    xpath = processed.build_xpath()
    assert xpath.startswith("//hl7:section//hl7:code")
    assert '@code="123"' in xpath
    assert '@code="456"' in xpath

    # custom search_in
    custom_xpath = processed.build_xpath(search_in="custom")
    assert custom_xpath.startswith("//hl7:custom//hl7:code")


def test_xpath_empty_codes() -> None:
    """
    Test XPath generation with no codes.
    """

    processed = ProcessedGrouper(
        condition="38362002", display_name="Test Condition", codes=set()
    )

    assert processed.build_xpath() == ""
