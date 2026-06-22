from unittest.mock import MagicMock, patch
from zipfile import ZipFile

import pytest

from app.core.models.types import XMLFiles
from app.services.assets import get_asset_path
from app.services.ecr.model import JurisdictionReportableConditions
from app.services.pipeline import (
    RefinementContext,
    RefinementException,
    RefinementResult,
    create_augmentation_run_from_xml_files,
    discover_reportable_conditions,
    refine_for_condition,
)
from app.services.terminology import ProcessedConfiguration

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_xml_files() -> XMLFiles:
    """
    Load the mon-mothma two-jurisdiction sample files.
    """
    zip_path = get_asset_path("demo", "mon-mothma-reportable-two-jds.zip")

    with ZipFile(zip_path) as z:
        with z.open("CDA_RR.xml") as f:
            rr_xml = f.read().decode("utf-8")
        with z.open("CDA_eICR.xml") as f:
            eicr_xml = f.read().decode("utf-8")

    return XMLFiles(eicr=eicr_xml, rr=rr_xml)


@pytest.fixture
def minimal_processed_configuration() -> ProcessedConfiguration:
    """
    A minimal ProcessedConfiguration built via from_dict, simulating
    what lambda would produce from an S3 active.json file.
    """
    return ProcessedConfiguration.from_dict(
        {
            "sections": [],
            "included_condition_rsg_codes": ["840539006"],
            "code_system_sets": {
                "loinc": [
                    {
                        "code": "101289-7",
                        "display": "SARS-CoV-2 RNA [Presence] in Throat by NAA with non-probe detection",
                        "system": "2.16.840.1.113883.6.1",
                    }
                ]
            },
        }
    )


# =============================================================================
# STAGE 1: REPORTABILITY DISCOVERY
# =============================================================================


class TestDiscoverReportableConditions:
    """
    Tests for the shared reportability discovery stage.
    """

    def test_returns_jurisdiction_groups(self, sample_xml_files: XMLFiles):
        """
        The mon-mothma sample has two jurisdictions (SDDH and JDDH).
        Discovery should return both.
        """
        groups = discover_reportable_conditions(sample_xml_files)

        assert isinstance(groups, list)
        assert len(groups) > 0

        # Every group should be a JurisdictionReportableConditions
        for group in groups:
            assert isinstance(group, JurisdictionReportableConditions)
            assert group.jurisdiction
            assert len(group.conditions) > 0

    def test_returns_expected_jurisdictions(self, sample_xml_files: XMLFiles):
        """
        Verify the specific jurisdictions from the mon-mothma sample.
        """
        groups = discover_reportable_conditions(sample_xml_files)
        jurisdiction_codes = {g.jurisdiction.upper() for g in groups}

        assert "SDDH" in jurisdiction_codes
        assert "JDDH" in jurisdiction_codes

    def test_returns_expected_conditions(self, sample_xml_files: XMLFiles):
        """
        Verify the specific condition codes from the mon-mothma sample.
        SDDH should have COVID (840539006) and Influenza (772828001).
        """
        groups = discover_reportable_conditions(sample_xml_files)

        sddh_group = next(g for g in groups if g.jurisdiction.upper() == "SDDH")
        sddh_codes = {c.code for c in sddh_group.conditions}

        assert "840539006" in sddh_codes  # COVID
        assert "772828001" in sddh_codes  # Influenza


# =============================================================================
# STAGE 2: REFINEMENT EXECUTION
# =============================================================================


class TestRefineForCondition:
    """
    Tests for the shared refinement execution stage.
    """

    def test_produces_refined_output(
        self,
        sample_xml_files: XMLFiles,
        minimal_processed_configuration: ProcessedConfiguration,
    ):
        """
        Given a valid ProcessedConfiguration, refinement should produce
        both a refined eICR and a refined RR.
        """

        context = RefinementContext(
            jurisdiction_id="SDDH",
            canonical_url="https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64",
            configuration_version=1,
        )
        run = create_augmentation_run_from_xml_files(sample_xml_files)

        result = refine_for_condition(
            xml_files=sample_xml_files,
            processed_configuration=minimal_processed_configuration,
            context=context,
            run=run,
        )

        assert isinstance(result, RefinementResult)
        assert result.documents.eicr
        assert result.documents.rr
        assert len(result.documents.eicr) > 0
        assert len(result.documents.rr) > 0

    def test_trace_records_success(
        self,
        sample_xml_files: XMLFiles,
        minimal_processed_configuration: ProcessedConfiguration,
    ):
        """
        On successful refinement, the trace should be marked as refined
        with configuration_resolved=True and a size reduction percentage.
        """
        context = RefinementContext(
            jurisdiction_id="SDDH",
            canonical_url="https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64",
            configuration_version=1,
        )
        run = create_augmentation_run_from_xml_files(sample_xml_files)

        result = refine_for_condition(
            xml_files=sample_xml_files,
            processed_configuration=minimal_processed_configuration,
            context=context,
            run=run,
        )

        assert result.metrics.eicr.size_reduction_percentage is not None
        assert result.metrics.eicr.size_mib is not None

    def test_trace_records_error_on_failure(self, sample_xml_files: XMLFiles):
        """
        If refinement raises an exception, the trace should capture the
        error before re-raising.
        """
        context = RefinementContext(
            jurisdiction_id="SDDH",
            canonical_url="https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64",
            configuration_version=1,
        )
        run = create_augmentation_run_from_xml_files(sample_xml_files)

        # Create an invalid ProcessedConfiguration that will cause an error
        # by patching the plan creation to raise
        with patch(
            "app.services.pipeline.create_eicr_refinement_plan",
            side_effect=Exception("plan creation failed"),
        ):
            with pytest.raises(
                RefinementException, match="Refinement failed for given condition"
            ) as exc_info:
                refine_for_condition(
                    xml_files=sample_xml_files,
                    processed_configuration=MagicMock(),
                    context=context,
                    run=run,
                )
            assert exc_info.value.detail == "plan creation failed"
