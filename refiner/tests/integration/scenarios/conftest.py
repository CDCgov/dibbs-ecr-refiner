import pytest

from ..conftest import (
    assert_schematron_valid,
    assert_xsd_valid,
    validate_refined_xml,
)


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Update the snapshot files we check against.
    """

    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help=(
            "Regenerate scenario snapshots from current refinement output "
            "instead of comparing against committed files. Use when "
            "refinement behavior legitimately changes."
        ),
    )


@pytest.fixture
def update_snapshots(request: pytest.FixtureRequest) -> bool:
    """
    Whether the test run requested snapshot regeneration.
    """

    return bool(request.config.getoption("--update-snapshots"))


# NOTE:
# COMPOSED VALIDATION FIXTURE
# =============================================================================
# composes the three validation steps an integration test would run on a
# refined document into one call per (xml, doc_kind) pair. the underlying
# validators (validate_xml_string, validate_xml_string_xsd) and their
# session-cached xsd_schema are inherited from the parent integration
# conftest -- this suite is now a subdirectory of tests/integration/, so
# pytest applies that conftest's fixtures here by injection.


@pytest.fixture
def validate_refined_document(
    validate_xml_string,
    validate_xml_string_xsd,
):
    """
    Returns a callable that runs full validation on one refined document.

    Scenarios call this twice (once for the refined eICR, once for the
    refined RR) before snapshot operations so:

      - In compare mode, an invalid document fails the test with a
        clear validation error rather than as an opaque XML diff.
      - In --update-snapshots mode, an invalid document fails the test
        BEFORE the snapshot is overwritten, preventing invalid snapshots
        from being committed.

    Args (on the returned callable):
        xml_string: the refined document as a UTF-8 string.
        doc_kind: "eICR" or "RR" - used only for human-readable labels
            in failure messages; the actual document type is detected
            from the root template OID.
        scenario_name: included in failure messages and labels.
    """

    def _validate(
        xml_string: str,
        doc_kind: str,
        scenario_name: str,
    ) -> None:
        label = f"{scenario_name} {doc_kind}"

        # well-formedness + correct CDA ClinicalDocument root
        validate_refined_xml(xml_string, doc_kind, label, scenario_name)

        # CDA R2 XSD: schema is session-cached
        xsd_result = validate_xml_string_xsd(xml_string)
        assert_xsd_valid(xsd_result, label, scenario_name)

        # schematron - the XSLT is compiled per call
        schematron_result = validate_xml_string(xml_string, doc_kind.lower())
        assert_schematron_valid(schematron_result, label, scenario_name)

    return _validate
