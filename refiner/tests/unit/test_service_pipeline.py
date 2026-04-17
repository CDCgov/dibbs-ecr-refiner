from unittest.mock import MagicMock, patch
from zipfile import ZipFile

import pytest

from app.core.models.types import XMLFiles
from app.services.assets import get_asset_path
from app.services.ecr.model import JurisdictionReportableConditions
from app.services.pipeline import (
    RefinementResult,
    RefinementTrace,
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
            "codes": ["101289-7"],
            "sections": [],
            "included_condition_rsg_codes": ["840539006"],
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
        trace = RefinementTrace(
            jurisdiction_code="SDDH",
            rsg_code="840539006",
            condition_grouper_name="COVID19",
            configuration_version=1,
        )

        result = refine_for_condition(
            xml_files=sample_xml_files,
            processed_configuration=minimal_processed_configuration,
            trace=trace,
        )

        assert isinstance(result, RefinementResult)
        assert result.refined_eicr
        assert result.refined_rr
        assert len(result.refined_eicr) > 0
        assert len(result.refined_rr) > 0

    def test_trace_records_success(
        self,
        sample_xml_files: XMLFiles,
        minimal_processed_configuration: ProcessedConfiguration,
    ):
        """
        On successful refinement, the trace should be marked as refined
        with configuration_resolved=True and a size reduction percentage.
        """
        trace = RefinementTrace(
            jurisdiction_code="SDDH",
            rsg_code="840539006",
            condition_grouper_name="COVID19",
            configuration_version=1,
        )

        result = refine_for_condition(
            xml_files=sample_xml_files,
            processed_configuration=minimal_processed_configuration,
            trace=trace,
        )

        assert result.trace.configuration_resolved is True
        assert result.trace.refinement_outcome == "refined"
        assert result.trace.eicr_size_reduction_percentage is not None
        assert result.trace.error_detail is None

    def test_trace_records_error_on_failure(self, sample_xml_files: XMLFiles):
        """
        If refinement raises an exception, the trace should capture the
        error before re-raising.
        """
        trace = RefinementTrace(
            jurisdiction_code="SDDH",
            rsg_code="840539006",
        )

        # Create an invalid ProcessedConfiguration that will cause an error
        # by patching the plan creation to raise
        with patch(
            "app.services.pipeline.create_eicr_refinement_plan",
            side_effect=Exception("plan creation failed"),
        ):
            with pytest.raises(Exception, match="plan creation failed"):
                refine_for_condition(
                    xml_files=sample_xml_files,
                    processed_configuration=MagicMock(),
                    trace=trace,
                )

        assert trace.refinement_outcome == "error"
        assert trace.error_detail == "plan creation failed"
        assert trace.configuration_resolved is True


# =============================================================================
# TRACE INITIALIZATION
# =============================================================================


class TestRefinementTrace:
    """
    Tests for the RefinementTrace dataclass defaults and behavior.
    """

    def test_default_values(self):
        """
        A newly created trace should have sensible defaults.
        """
        trace = RefinementTrace(
            jurisdiction_code="SDDH",
            rsg_code="840539006",
        )

        assert trace.jurisdiction_code == "SDDH"
        assert trace.rsg_code == "840539006"
        assert trace.condition_grouper_name is None
        assert trace.configuration_version is None
        assert trace.configuration_resolved is False
        assert trace.refinement_outcome == "skipped"
        assert trace.skip_reason is None
        assert trace.eicr_size_reduction_percentage is None
        assert trace.error_detail is None

    def test_skip_trace(self):
        """
        A trace for a skipped condition should capture the reason.
        """
        trace = RefinementTrace(
            jurisdiction_code="SDDH",
            rsg_code="840539006",
            refinement_outcome="skipped",
            skip_reason="no_active_configuration",
        )

        assert trace.refinement_outcome == "skipped"
        assert trace.skip_reason == "no_active_configuration"
        assert trace.configuration_resolved is False
