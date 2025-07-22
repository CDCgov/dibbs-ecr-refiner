import pytest

from pipeline.fetch_api_data import dynamic_classify_valueset


@pytest.mark.parametrize(
    "valueset, expected_category",
    [
        # test case 1: reporting specification grouper
        (
            {
                "id": "vsm-latest-reporting-spec",
                "version": "20241008",
                "meta": {
                    "profile": [
                        "http://aims.org/fhir/StructureDefinition/vsm-reportingspecificationgroupervalueset"
                    ]
                },
            },
            "reporting_spec_grouper_20241008",
        ),
        # test case 2: condition grouper
        (
            {
                "id": "vsm-latest-condition",
                "version": "1.0.0",
                "meta": {
                    "profile": [
                        "http://aims.org/fhir/StructureDefinition/vsm-conditiongroupervalueset"
                    ]
                },
            },
            "condition_grouper_1.0.0",
        ),
        # test case 3: additional context grouper (numeric ID, no profile)
        (
            {
                "id": "12345",
                "version": "2.0.0",
                "meta": {},  # No profile
            },
            "additional_context_grouper_2.0.0",
        ),
        # test case 4: triggering ValueSet (should be ignored)
        (
            {
                "id": "some-trigger",
                "version": "3.0.0",
                "meta": {
                    "profile": [
                        "http://hl7.org/fhir/us/ph-library/StructureDefinition/us-ph-triggering-valueset"
                    ]
                },
            },
            None,
        ),
        # test case 5: unclassified (has profile, but not one we care about)
        (
            {
                "id": "other-valueset",
                "version": "1.1.1",
                "meta": {"profile": ["http://example.com/some-other-profile"]},
            },
            "unclassified_1.1.1",
        ),
        # test case 6: robustness--missing version
        (
            {
                "id": "vsm-latest-condition",
                "meta": {
                    "profile": [
                        "http://aims.org/fhir/StructureDefinition/vsm-conditiongroupervalueset"
                    ]
                },
            },
            "condition_grouper_unknown_version",
        ),
    ],
)
def test_dynamic_classify_valueset(valueset, expected_category):
    """
    Tests that the dynamic_classify_valueset function correctly categorizes different types of ValueSet resources.
    """

    assert dynamic_classify_valueset(valueset) == expected_category
