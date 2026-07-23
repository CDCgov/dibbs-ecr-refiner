"""
Tests for zero-code-set (passthrough) configuration behavior.

This module verifies that when a configuration has no primary condition
(`condition_id=None`), the refiner:
1. Skips mapping loops without raising 400 errors
2. Produces a valid eICR (not empty or corrupted)
3. Sets SectionProvenanceRecord source to UNCONFIGURED for all sections
4. Preserves the original data (no condition-specific mappings applied)
5. Applies RSG fallback logic when included conditions have RSG codes
"""

from unittest.mock import AsyncMock, patch

import pytest
from lxml import etree

from app.db.code_systems.db import DbCodeSystem
from app.db.conditions.model import DbCondition
from app.db.configurations.model import DbConfiguration
from app.services.ecr.model import (
    HL7_NS,
    SectionSource,
)
from app.services.ecr.refine import (
    create_eicr_refinement_plan,
    refine_eicr,
    refine_rr,
)
from app.services.terminology import ProcessedConfiguration
from tests.unit.helpers.configuration import create_processed_config

# NOTE:
# TEST CONSTANTS
# =============================================================================

_PLACEHOLDER_AUGMENTATION_TIMESTAMP = "19700101000000+0000"

# Placeholder codes that won't match anything in test fixtures
_PLACEHOLDER_CODE = "fake-zero-code-set-placeholder"


# NOTE:
# TEST HELPER FUNCTIONS
# =============================================================================


def _make_zero_code_set_condition() -> DbCondition:
    """
    Creates a DbCondition with no codes (zero-code-set).
    """

    return DbCondition(
        id="zero-code-condition-id",
        display_name="Zero Code Set Condition",
        canonical_url="http://example.com/condition/zero-code-set",
        version="1.0.0",
        child_rsg_snomed_codes=[],
        snomed_codes=[],
        loinc_codes=[],
        icd10_codes=[],
        rxnorm_codes=[],
        cvx_codes=[],
    )


def _make_zero_code_set_db_config() -> DbConfiguration:
    """
    Creates a DbConfiguration with condition_id=None (zero-code-set).
    """

    return DbConfiguration(
        id="zero-code-config-id",
        name="Zero Code Set Config",
        jurisdiction_id="SDDH",
        primary_condition_id=None,  # This is the key: no primary condition
        original_condition_id=None,  # Zero-code-set has no original condition
        included_conditions=[],
        custom_codes=[],
        section_processing=[],
        version=1,
        status="active",
        last_activated_at=None,
        last_activated_by=None,
        created_by="fake-user-id",
        s3_url="",
    )


def _make_mock_code_systems() -> dict[str, DbCodeSystem]:
    """
    Creates mock code systems for testing.
    """

    from uuid import uuid4

    return {
        "snomed": DbCodeSystem(
            id=uuid4(),
            oid="2.16.840.1.113883.6.96",
            display_name="SNOMED",
            key="snomed",
        ),
        "loinc": DbCodeSystem(
            id=uuid4(),
            oid="2.16.840.1.113883.6.1",
            display_name="LOINC",
            key="loinc",
        ),
        "icd10": DbCodeSystem(
            id=uuid4(),
            oid="2.16.840.1.113883.6.90",
            display_name="ICD-10",
            key="icd10",
        ),
        "rxnorm": DbCodeSystem(
            id=uuid4(),
            oid="2.16.840.1.113883.6.88",
            display_name="RxNorm",
            key="rxnorm",
        ),
        "cvx": DbCodeSystem(
            id=uuid4(),
            oid="2.16.840.1.113883.12.292",
            display_name="CVX",
            key="cvx",
        ),
    }


@pytest.fixture(autouse=True)
def mock_db_functions(monkeypatch, mock_all_systems):
    """
    Mock return values of the `_db` functions called by the routes.
    """

    monkeypatch.setattr(
        "app.services.code_systems.get_all_code_systems_db",
        AsyncMock(return_value=mock_all_systems),
    )

    monkeypatch.setattr(
        "app.services.configurations.get_code_system_by_key_db",
        AsyncMock(
            side_effect=lambda key, db: mock_all_systems[key],
        ),
    )


async def _make_zero_code_set_processed_config() -> ProcessedConfiguration:
    """
    Creates a ProcessedConfiguration from a zero-code-set configuration.
    """

    condition = _make_zero_code_set_condition()
    config = _make_zero_code_set_db_config()

    return await create_processed_config(config=config, conditions=[condition])


# NOTE:
# EICR REFINEMENT PASSTHROUGH TESTS
# =============================================================================


@pytest.mark.asyncio
class TestZeroCodeSetPassthrough:
    """
    Tests for passthrough behavior when condition_id=None.
    """

    async def test_refine_eicr_zero_code_set_no_exception(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Tests that refining an eICR with a zero-code-set configuration
        completes without raising a 400 or any exception.
        """

        processed_config = await _make_zero_code_set_processed_config()

        plan = create_eicr_refinement_plan(
            processed_configuration=processed_config,
            eicr_root=eicr_root_v1_1,
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
            config_version=1,
        )

        # Should not raise any exception
        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        # Verify the document is still valid XML
        assert eicr_root_v1_1 is not None
        assert eicr_root_v1_1.tag == "{urn:hl7-org:v3}ClinicalDocument"

    async def test_refine_eicr_zero_code_set_valid_eicr_output(
        self, eicr_root_v1_1: etree._Element, original_eicr_root_v1_1: etree._Element
    ):
        """
        Tests that the output XML is still a valid eICR (not empty or corrupted).
        """

        processed_config = await _make_zero_code_set_processed_config()

        plan = create_eicr_refinement_plan(
            processed_configuration=processed_config,
            eicr_root=eicr_root_v1_1,
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
            config_version=1,
        )

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        # Serialize and verify it's valid XML
        output_xml = etree.tostring(eicr_root_v1_1, encoding="unicode")

        # Should not be empty
        assert output_xml and len(output_xml) > 0

        # Should contain the original clinical data (no filtering)
        # Check that COVID and influenza data are still present
        assert "840539006" in output_xml  # COVID
        assert "719865001" in output_xml  # Influenza

        # Should still be well-formed
        parsed = etree.fromstring(output_xml.encode("utf-8"))
        assert parsed.tag == "{urn:hl7-org:v3}ClinicalDocument"

    async def test_refine_eicr_zero_code_set_provenance_unconfigured(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Tests that SectionProvenanceRecord for sections reflects UNCONFIGURED source.
        """

        processed_config = await _make_zero_code_set_processed_config()

        plan = create_eicr_refinement_plan(
            processed_configuration=processed_config,
            eicr_root=eicr_root_v1_1,
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
            config_version=1,
        )

        # Verify all sections have UNCONFIGURED source
        for section_code, provenance in plan.section_provenance.items():
            assert provenance.source == SectionSource.UNCONFIGURED, (
                f"Section {section_code} should have UNCONFIGURED source, "
                f"got {provenance.source}"
            )

        # Run refinement
        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        # Verify provenance records still exist and have correct source
        for section_code, provenance in plan.section_provenance.items():
            assert provenance.source == SectionSource.UNCONFIGURED

    async def test_refine_eicr_zero_code_set_no_condition_mappings_applied(
        self, eicr_root_v1_1: etree._Element, original_eicr_root_v1_1: etree._Element
    ):
        """
        Tests that no condition-specific mappings were applied (data remains as-is).
        """

        processed_config = await _make_zero_code_set_processed_config()

        plan = create_eicr_refinement_plan(
            processed_configuration=processed_config,
            eicr_root=eicr_root_v1_1,
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
            config_version=1,
        )

        # Verify codes_to_check is empty (no codes to match)
        assert plan.codes_to_check == set(), (
            "Zero-code-set config should have empty codes_to_check"
        )

        # Store original section content for comparison
        original_eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="11450-4"]]', namespaces=HL7_NS
        )[0]

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        # Verify all original entries are still present (no filtering)
        problems_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="11450-4"]]', namespaces=HL7_NS
        )[0]

        # All original SNOMED codes should still be present
        original_snomed_codes = [
            "840539006",  # COVID
            "719865001",  # Influenza
            "59621000",  # Hypertension
            "44054006",  # Diabetes
        ]

        for code in original_snomed_codes:
            assert code in etree.tostring(problems_section, encoding="unicode"), (
                f"Original code {code} should still be present"
            )

    async def test_refine_eicr_zero_code_set_all_sections_present(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Tests that all sections from the original eICR are still present.
        """

        processed_config = await _make_zero_code_set_processed_config()

        plan = create_eicr_refinement_plan(
            processed_configuration=processed_config,
            eicr_root=eicr_root_v1_1,
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
            config_version=1,
        )

        # Get all section codes from the plan
        section_codes = list(plan.section_instructions.keys())

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        # Verify all sections are still present in the output
        for section_code in section_codes:
            section = eicr_root_v1_1.xpath(
                f'.//hl7:section[hl7:code[@code="{section_code}"]]', namespaces=HL7_NS
            )
            assert len(section) == 1, (
                f"Section {section_code} should be present in output"
            )

    async def test_refine_eicr_zero_code_set_narrative_only_sections(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Tests that narrative-only sections are handled correctly.
        """

        processed_config = await _make_zero_code_set_processed_config()

        plan = create_eicr_refinement_plan(
            processed_configuration=processed_config,
            eicr_root=eicr_root_v1_1,
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
            config_version=1,
        )

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        # Check a narrative-only section (Reason for Visit - 29299-5)
        reason_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="29299-5"]]', namespaces=HL7_NS
        )[0]

        # Should not be stubbed (nullFlavor should be None)
        assert reason_section.get("nullFlavor") is None

        # Should have provenance footnote (footnote ID, not "Provenance" text)
        rendered = etree.tostring(reason_section, encoding="unicode")
        assert "footnote" in rendered.lower()
        assert "ecr-refiner-29299-5" in rendered

    async def test_refine_eicr_zero_code_set_provenance_footnotes_rendered(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Tests that provenance footnotes are rendered for all sections.
        """

        processed_config = await _make_zero_code_set_processed_config()

        plan = create_eicr_refinement_plan(
            processed_configuration=processed_config,
            eicr_root=eicr_root_v1_1,
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
            config_version=1,
        )

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        # Check that footnotes are rendered for narrative-only sections
        # (Reason for Visit - 29299-5) - these always get footnotes
        reason_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="29299-5"]]', namespaces=HL7_NS
        )[0]

        rendered = etree.tostring(reason_section, encoding="unicode")

        # Should have provenance footnote (footnote ID, not "Provenance" text)
        assert "footnote" in rendered.lower()
        assert "ecr-refiner-29299-5" in rendered
        # Should have unconfigured source in the footnote (text says "Not in jurisdiction configuration")
        assert "not in jurisdiction configuration" in rendered.lower()

    async def test_refine_rr_zero_code_set_no_exception(
        self, rr_root_v1_1: etree._Element
    ):
        """
        Tests that refining an RR with a zero-code-set configuration
        completes without raising an exception.
        """

        processed_config = await _make_zero_code_set_processed_config()

        create_eicr_refinement_plan(
            processed_configuration=processed_config,
            eicr_root=etree.fromstring(
                etree.tostring(rr_root_v1_1, encoding="unicode").encode("utf-8")
            ),
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
            config_version=1,
        )

        # Create RR refinement plan
        from app.services.ecr.refine import create_rr_refinement_plan

        rr_plan = create_rr_refinement_plan(processed_configuration=processed_config)

        # Should not raise any exception
        refine_rr(rr_root=rr_root_v1_1, plan=rr_plan)

        # Verify the document is still valid XML
        assert rr_root_v1_1 is not None
        assert rr_root_v1_1.tag == "{urn:hl7-org:v3}ClinicalDocument"

    async def test_refine_rr_zero_code_set_valid_rr_output(
        self, rr_root_v1_1: etree._Element
    ):
        """
        Tests that the RR output is still valid (not empty or corrupted).
        """

        processed_config = await _make_zero_code_set_processed_config()

        from app.services.ecr.refine import create_rr_refinement_plan

        rr_plan = create_rr_refinement_plan(processed_configuration=processed_config)

        refine_rr(rr_root=rr_root_v1_1, plan=rr_plan)

        # Serialize and verify it's valid XML
        output_xml = etree.tostring(rr_root_v1_1, encoding="unicode")

        # Should not be empty
        assert output_xml and len(output_xml) > 0

        # Should still be well-formed
        parsed = etree.fromstring(output_xml.encode("utf-8"))
        assert parsed.tag == "{urn:hl7-org:v3}ClinicalDocument"

    async def test_refine_eicr_zero_code_set_empty_codes_to_check(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Tests that codes_to_check is empty for zero-code-set configurations.
        """

        processed_config = await _make_zero_code_set_processed_config()

        plan = create_eicr_refinement_plan(
            processed_configuration=processed_config,
            eicr_root=eicr_root_v1_1,
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
            config_version=1,
        )

        # Verify codes_to_check is empty
        assert plan.codes_to_check == set()

        # Verify code_system_sets has empty code maps (but not None)
        assert plan.code_system_sets.system_to_code_maps == {
            "loinc": {},
            "snomed": {},
            "rxnorm": {},
            "icd10": {},
            "cvx": {},
            "other": {},
        }

    async def test_refine_eicr_zero_code_set_provenance_config_version(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Tests that config_version is correctly set in provenance records.
        """

        processed_config = await _make_zero_code_set_processed_config()

        plan = create_eicr_refinement_plan(
            processed_configuration=processed_config,
            eicr_root=eicr_root_v1_1,
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
            config_version=5,  # Use a specific version
        )

        # Verify all provenance records have the correct config_version
        for provenance in plan.section_provenance.values():
            assert provenance.config_version == 5

    async def test_refine_eicr_zero_code_set_retain_action_on_unconfigured(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Tests that unconfigured sections use retain action (SKIP_SECTION_INSTRUCTIONS).
        """

        processed_config = await _make_zero_code_set_processed_config()

        plan = create_eicr_refinement_plan(
            processed_configuration=processed_config,
            eicr_root=eicr_root_v1_1,
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
            config_version=1,
        )

        # Verify unconfigured sections have retain action
        for section_code, instructions in plan.section_instructions.items():
            # Unconfigured sections should default to retain action
            assert instructions.action == "retain", (
                f"Unconfigured section {section_code} should have retain action"
            )
            assert instructions.include is True
            assert instructions.narrative == "retain"

    async def test_refine_eicr_zero_code_set_rsg_fallback_applied(
        self,
        eicr_root_v1_1: etree._Element,
        original_eicr_root_v1_1: etree._Element,
        rr_root_v1_1: etree._Element,
    ):
        """
        Tests that RSG fallback mappings are applied even when condition_id=None.

        When a configuration has no primary condition (condition_id=None) but has
        included conditions with RSG codes, the RSG-based processing should still
        occur. This verifies that the RSG fallback logic remains active without
        a primary condition.
        """

        # Create a condition with RSG codes but no primary codes
        from app.db.conditions.model import DbCondition

        rsg_condition = DbCondition(
            id="rsg-condition-id",
            display_name="RSG Condition",
            canonical_url="http://example.com/condition/rsg",
            version="1.0.0",
            child_rsg_snomed_codes=["840539006"],  # COVID RSG code
            snomed_codes=[],  # No primary codes
            loinc_codes=[],
            icd10_codes=[],
            rxnorm_codes=[],
            cvx_codes=[],
        )

        # Create a config with condition_id=None but with the RSG condition included
        zero_code_config = DbConfiguration(
            id="zero-code-config-with-rsg-id",
            name="Zero Code Set Config with RSG",
            jurisdiction_id="SDDH",
            primary_condition_id=None,  # No primary condition
            original_condition_id=None,  # Zero-code-set has no original condition
            included_conditions=[
                "rsg-condition-id"
            ],  # But has included condition with RSG
            custom_codes=[],
            section_processing=[],
            version=1,
            status="active",
            last_activated_at=None,
            last_activated_by=None,
            created_by="fake-user-id",
            s3_url="",
        )

        # Mock the get_included_conditions_db to return our RSG condition
        with patch(
            "app.services.configurations.get_included_conditions_db",
            return_value=[rsg_condition],
        ):
            processed_config = await create_processed_config(
                config=zero_code_config, conditions=[rsg_condition]
            )

        # Verify the processed config has RSG codes but no primary codes
        assert processed_config.codes == set(), (
            "Zero-code-set config should have empty codes set"
        )
        assert processed_config.included_condition_rsg_codes == {"840539006"}, (
            "RSG codes should be populated from included conditions"
        )

        # Create refinement plan
        plan = create_eicr_refinement_plan(
            processed_configuration=processed_config,
            eicr_root=eicr_root_v1_1,
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
            config_version=1,
        )

        # Verify codes_to_check is empty (no primary condition codes)
        assert plan.codes_to_check == set(), (
            "codes_to_check should be empty for zero-code-set config"
        )

        # Verify RSG codes are available for RR refinement
        from app.services.ecr.refine import create_rr_refinement_plan

        rr_plan = create_rr_refinement_plan(processed_configuration=processed_config)
        assert (
            "840539006" in rr_plan.included_condition_child_rsg_snomed_codes_to_retain
        ), "RSG codes should be available for RR refinement"

        # Run eICR refinement
        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        # Verify the eICR still contains the COVID data (RSG-based processing)
        output_xml = etree.tostring(eicr_root_v1_1, encoding="unicode")
        assert "840539006" in output_xml, (
            "COVID RSG code should be retained in eICR output"
        )

        # Run RR refinement
        from app.services.ecr.refine import refine_rr

        refine_rr(rr_root=rr_root_v1_1, plan=rr_plan)

        # Verify RR output contains the COVID RSG code
        rr_output_xml = etree.tostring(rr_root_v1_1, encoding="unicode")
        assert "840539006" in rr_output_xml, (
            "COVID RSG code should be retained in RR output"
        )


# NOTE:
# INTEGRATION TESTS (using harness)
# =============================================================================


@pytest.mark.asyncio
class TestZeroCodeSetIntegration:
    """
    Integration tests for zero-code-set passthrough using the refinement pipeline.
    """

    async def test_pipeline_refine_for_condition_zero_code_set(
        self,
        covid_influenza_v1_1_files,
    ):
        """
        Tests the full refine_for_condition pipeline with a zero-code-set config.
        """

        from app.services.pipeline import (
            RefinementContext,
            create_augmentation_run_from_xml_files,
            refine_for_condition,
        )

        processed_config = await _make_zero_code_set_processed_config()

        run = create_augmentation_run_from_xml_files(covid_influenza_v1_1_files)

        context = RefinementContext(
            jurisdiction_id="SDDH",
            canonical_url="http://example.com/api/fhir/ValueSet/123e4567-e89b-42d3-a456-426614174000",
            configuration_version=1,
        )

        # Should not raise any exception
        result = refine_for_condition(
            xml_files=covid_influenza_v1_1_files,
            processed_configuration=processed_config,
            context=context,
            run=run,
        )

        # Verify output is valid
        assert result.documents.eicr is not None
        assert len(result.documents.eicr) > 0
        assert result.documents.rr is not None
        assert len(result.documents.rr) > 0

        # Verify eICR is well-formed
        parsed = etree.fromstring(result.documents.eicr.encode("utf-8"))
        assert parsed.tag == "{urn:hl7-org:v3}ClinicalDocument"

        # Verify eICR contains provenance footnotes
        assert "footnote" in result.documents.eicr.lower()
        # Verify eICR contains unconfigured source text
        assert "not in jurisdiction configuration" in result.documents.eicr.lower()

    async def test_pipeline_zero_code_set_preserves_original_data(
        self,
        covid_influenza_v1_1_files,
    ):
        """
        Tests that zero-code-set configuration preserves all original data.
        """

        from app.services.pipeline import (
            RefinementContext,
            create_augmentation_run_from_xml_files,
            refine_for_condition,
        )

        processed_config = await _make_zero_code_set_processed_config()

        run = create_augmentation_run_from_xml_files(covid_influenza_v1_1_files)

        context = RefinementContext(
            jurisdiction_id="SDDH",
            canonical_url="http://example.com/api/fhir/ValueSet/123e4567-e89b-42d3-a456-426614174000",
            configuration_version=1,
        )

        result = refine_for_condition(
            xml_files=covid_influenza_v1_1_files,
            processed_configuration=processed_config,
            context=context,
            run=run,
        )

        # Verify original clinical data is preserved
        assert "840539006" in result.documents.eicr  # COVID
        assert "719865001" in result.documents.eicr  # Influenza
        assert "59621000" in result.documents.eicr  # Hypertension
        assert "44054006" in result.documents.eicr  # Diabetes

        # Verify eICR contains provenance footnotes
        assert "footnote" in result.documents.eicr.lower()
        # Verify eICR contains unconfigured source text
        assert "not in jurisdiction configuration" in result.documents.eicr.lower()
