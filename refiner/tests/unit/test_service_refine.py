from unittest.mock import AsyncMock

import pytest
from lxml import etree

from app.db.conditions.model import DbCondition, DbConditionCoding
from app.db.configurations.model import (
    DbConfiguration,
    DbConfigurationSectionInstructions,
)
from app.services.ecr.model import (
    HL7_NS,
    EICRRefinementPlan,
    SectionOutcome,
    SectionProvenanceRecord,
    SectionSource,
)
from app.services.ecr.narrative.constants import (
    PROVENANCE_OUTCOME_NOTES,
    REMOVE_NARRATIVE_MESSAGE,
)
from app.services.ecr.refine import create_rr_refinement_plan, refine_eicr, refine_rr
from app.services.ecr.specification import load_spec
from app.services.terminology import ProcessedConfiguration
from tests.unit.helpers.configuration import create_processed_config

# NOTE:
# TEST CONSTANTS
# =============================================================================
# placeholder values for the EICRRefinementPlan fields that the tests in
# this file don't actually exercise. refine_eicr only reads
# augmentation_timestamp when it appends a provenance footnote, and only
# appends a footnote when section_provenance has an entry for the section
# being processed. an empty section_provenance dict means no footnotes
# get rendered, so the timestamp is never read and the placeholder is
# safe — the tests focus on refinement behavior (filtering, pruning,
# enrichment) rather than provenance footnote contents

_PLACEHOLDER_AUGMENTATION_TIMESTAMP = "19700101000000+0000"

# ProcessedConfiguration must contain at least one code or otherwise is considered
# to be invalid. We are using a code that definitely will not appear in a real code set.
_MOCK_CONDITION_CODES = [DbConditionCoding(code="fake-code-0!", display="")]

# NOTE:
# LOCAL TEST HELPER FUNCTIONS - v1.1
# =============================================================================


def _make_condition_v1_1(**kwargs) -> DbCondition:
    """
    Creates a DbCondition model for v1.1 testing.
    """

    defaults = {
        "id": "fake-condition-id-v1-1",
        "display_name": "Test Condition v1.1",
        "canonical_url": "http://example.com/condition/v1.1",
        "version": "1.1",
        "child_rsg_snomed_codes": [],
        "snomed_codes": [],
        "loinc_codes": [],
        "icd10_codes": [],
        "rxnorm_codes": [],
        "cvx_codes": [],
    }
    defaults.update(kwargs)
    return DbCondition(**defaults)


def _make_db_configuration_v1_1(**kwargs) -> DbConfiguration:
    """
    Creates a DbConfiguration model for v1.1 testing.
    """

    defaults = {
        "id": "fake-config-id-v1-1",
        "name": "Test Config v1.1",
        "jurisdiction_id": "SDDH",
        "condition_id": "fake-condition-id-v1-1",
        "status": "active",
        "version": 1,
        "included_conditions": [],
        "custom_codes": [],
        "section_processing": [],
        "last_activated_at": None,
        "last_activated_by": None,
        "created_by": "fake-config-id-v1-1",
        "s3_url": [],
    }
    defaults.update(kwargs)
    return DbConfiguration(**defaults)


# NOTE:
# LOCAL TEST HELPER FUNCTIONS - v3.1.1
# =============================================================================


def _make_condition_v3_1_1(**kwargs) -> DbCondition:
    """
    Creates a DbCondition model for v3.1.1 testing.
    """

    defaults = {
        "id": "fake-condition-id-v3-1-1",
        "display_name": "Test Condition v3.1.1",
        "canonical_url": "http://example.com/condition/v3.1.1",
        "version": "3.1.1",
        "child_rsg_snomed_codes": [],
        "snomed_codes": [],
        "loinc_codes": [],
        "icd10_codes": [],
        "rxnorm_codes": [],
        "cvx_codes": [],
    }
    defaults.update(kwargs)
    return DbCondition(**defaults)


def _make_db_configuration_v3_1_1(**kwargs) -> DbConfiguration:
    """
    Creates a DbConfiguration model for v3.1.1 testing.
    """

    defaults = {
        "id": "fake-config-id-v3-1-1",
        "name": "Test Config v3.1.1",
        "jurisdiction_id": "SDDH",
        "condition_id": "fake-condition-id-v3-1-1",
        "status": "active",
        "version": 1,
        "included_conditions": [],
        "custom_codes": [],
        "section_processing": [],
        "last_activated_at": None,
        "last_activated_by": None,
        "created_by": "fake-config-id-v1-1",
        "s3_url": "",
    }
    defaults.update(kwargs)
    return DbConfiguration(**defaults)


# NOTE:
# LOCAL TEST HELPER FUNCTIONS - shared
# =============================================================================


async def _make_empty_processed_config() -> ProcessedConfiguration:
    """
    Creates a ProcessedConfiguration with no codes.

    Used by tests that need a valid code_system_sets but don't
    care about matching (e.g., retain, no-match tests).
    """

    condition = _make_condition_v1_1(cvx_codes=_MOCK_CONDITION_CODES)
    config = _make_db_configuration_v1_1()
    return await create_processed_config(config=config, conditions=[condition])


async def _make_processed_config_v1_1(**condition_kwargs) -> ProcessedConfiguration:
    """
    Creates a ProcessedConfiguration from a v1.1 condition with the given codes.

    Convenience helper to reduce boilerplate in tests that need real
    code_system_sets for section-aware matching.
    """

    condition = _make_condition_v1_1(**condition_kwargs)
    config = _make_db_configuration_v1_1()

    return await create_processed_config(config=config, conditions=[condition])


def _make_plan(
    processed_config: ProcessedConfiguration,
    sections: dict[str, str],
) -> EICRRefinementPlan:
    """
    Creates an EICRRefinementPlan from a ProcessedConfiguration and a dict
    of section_code -> action.

    The plan is built with empty section_provenance and a placeholder
    augmentation_timestamp. The tests in this file exercise refinement
    behavior, not provenance footnote rendering, so the empty provenance
    dict means no footnotes get rendered and the timestamp is never read.

    Args:
        processed_config: The processed configuration with codes and code_system_sets.
        sections: Dict mapping section LOINC codes to actions ("refine", "retain", "remove").
    """

    return EICRRefinementPlan(
        codes_to_check=processed_config.codes,
        code_system_sets=processed_config.code_system_sets,
        section_instructions={
            code: DbConfigurationSectionInstructions(
                action=action, include=True, narrative="remove"
            )
            for code, action in sections.items()
        },
        section_provenance={},
        specification=load_spec("1.1"),
        augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
    )


# NOTE:
# EICR REFINEMENT TESTS — existing (fixed)
# =============================================================================


@pytest.fixture(autouse=True)
def mock_db_functions(monkeypatch, mock_all_systems):
    """
    Mock return values of the `_db` functions called by the routes.
    """
    monkeypatch.setattr(
        "app.services.code_systems.get_all_code_systems_db",
        AsyncMock(return_value={m.id: m for m in mock_all_systems}),
    )

    monkeypatch.setattr(
        "app.services.configurations.get_code_system_by_key_db",
        AsyncMock(
            side_effect=lambda key, db: next(
                m for m in mock_all_systems if m.key == key
            ),
        ),
    )


@pytest.mark.asyncio
class TestRefiningService:
    async def test_retain_action_v1_1(
        self, eicr_root_v1_1: etree._Element, original_eicr_root_v1_1: etree._Element
    ):
        """
        Tests the 'retain' action, which should not modify the section.
        """

        empty_config = await _make_empty_processed_config()

        plan = EICRRefinementPlan(
            codes_to_check=set(),
            code_system_sets=empty_config.code_system_sets,
            section_instructions={
                "29762-2": DbConfigurationSectionInstructions(
                    action="retain", include=True, narrative="retain"
                )
            },
            section_provenance={},
            specification=load_spec("1.1"),
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
        )

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        section_refined = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="29762-2"]]', namespaces=HL7_NS
        )[0]

        section_original = original_eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="29762-2"]]', namespaces=HL7_NS
        )[0]

        assert etree.tostring(section_refined) == etree.tostring(section_original)

    async def test_refine_action_with_no_matches_v1_1(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Tests 'refine' + narrative='remove' with a non-matching code.

        With the keep-on-match work, the hard-coded "stub the section
        when nothing matches" policy is gone. The engine now prunes
        every <entry> and honors the configured narrative: with
        narrative='remove', the section's <text> is replaced with the
        removal notice and the section is NOT marked nullFlavor='NI'.
        """

        empty_config = await _make_empty_processed_config()

        plan = EICRRefinementPlan(
            codes_to_check={"NON_EXISTENT_CODE"},
            code_system_sets=empty_config.code_system_sets,
            section_instructions={
                "11450-4": DbConfigurationSectionInstructions(
                    action="refine", include=True, narrative="remove"
                )
            },
            section_provenance={},
            specification=load_spec("1.1"),
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
        )

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        problems_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="11450-4"]]', namespaces=HL7_NS
        )[0]

        # nullFlavor='NI' is still applied so the document remains
        # CDA schematron-conformant on sections that require at least
        # one entry; narrative removal is driven by the narrative setting
        assert problems_section.get("nullFlavor") == "NI"

        # entries should be pruned and the narrative replaced with the
        # removal notice
        assert problems_section.findall("hl7:entry", namespaces=HL7_NS) == []
        rendered = etree.tostring(problems_section, encoding="unicode")
        assert REMOVE_NARRATIVE_MESSAGE in rendered

    async def test_refine_no_matches_narrative_retain_v1_1(
        self,
        eicr_root_v1_1: etree._Element,
        original_eicr_root_v1_1: etree._Element,
    ):
        """
        Scenario: Retain Original — coded data=refine, narrative=retain,
        no matches. The narrative should be preserved untouched.
        """

        empty_config = await _make_empty_processed_config()

        plan = EICRRefinementPlan(
            codes_to_check={"NON_EXISTENT_CODE"},
            code_system_sets=empty_config.code_system_sets,
            section_instructions={
                "11450-4": DbConfigurationSectionInstructions(
                    action="refine", include=True, narrative="retain"
                )
            },
            section_provenance={
                "11450-4": SectionProvenanceRecord(
                    loinc_code="11450-4",
                    display_name="Problems",
                    include=True,
                    action="refine",
                    narrative="retain",
                    config_version=1,
                    source=SectionSource.CONFIGURED,
                )
            },
            specification=load_spec("1.1"),
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
        )

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        problems_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="11450-4"]]', namespaces=HL7_NS
        )[0]
        original_section = original_eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="11450-4"]]', namespaces=HL7_NS
        )[0]

        # nullFlavor='NI' applied for schematron compliance
        assert problems_section.get("nullFlavor") == "NI"
        # entries pruned (none matched)
        assert problems_section.findall("hl7:entry", namespaces=HL7_NS) == []
        # narrative removal notice should NOT appear (narrative preserved)
        rendered = etree.tostring(problems_section, encoding="unicode")
        assert REMOVE_NARRATIVE_MESSAGE not in rendered
        # original narrative table rows preserved — we check that
        # every <td> cell content from the original narrative table
        # also appears in the refined narrative. byte-for-byte
        # equality is too strict (entry_matching strips XML comments
        # as part of pre-matching cleanup), but the clinical content
        # the reviewer reads should be intact.
        original_cells = [
            (td.text or "").strip()
            for td in original_section.xpath("hl7:text//hl7:td", namespaces=HL7_NS)
            if (td.text or "").strip()
        ]
        for cell_text in original_cells:
            assert cell_text in rendered
        # the rendered footnote should carry the retained-on-no-match outcome
        assert (
            PROVENANCE_OUTCOME_NOTES[
                SectionOutcome.REFINED_NO_MATCHES_NARRATIVE_RETAINED
            ]
            in rendered
        )

    async def test_refine_keep_on_match_with_matches_v1_1(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Scenario: Keep on Match (Positive) — coded data=refine,
        narrative=keep_on_match, matches found. Narrative preserved.
        """

        processed_config = await _make_processed_config_v1_1(
            loinc_codes=[
                DbConditionCoding(code="94533-7", display="SARS-CoV-2 N gene"),
            ],
        )

        plan = EICRRefinementPlan(
            codes_to_check=processed_config.codes,
            code_system_sets=processed_config.code_system_sets,
            section_instructions={
                "30954-2": DbConfigurationSectionInstructions(
                    action="refine", include=True, narrative="keep_on_match"
                )
            },
            section_provenance={
                "30954-2": SectionProvenanceRecord(
                    loinc_code="30954-2",
                    display_name="Results",
                    include=True,
                    action="refine",
                    narrative="keep_on_match",
                    config_version=1,
                    source=SectionSource.CONFIGURED,
                )
            },
            specification=load_spec("1.1"),
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
        )

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        results_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="30954-2"]]', namespaces=HL7_NS
        )[0]
        rendered = etree.tostring(results_section, encoding="unicode")

        # matched entry survived
        assert "94533-7" in rendered
        # narrative retained — removal notice should NOT appear
        assert REMOVE_NARRATIVE_MESSAGE not in rendered
        # footnote shows refined-with-matches outcome
        assert PROVENANCE_OUTCOME_NOTES[SectionOutcome.REFINED_WITH_MATCHES] in rendered

    async def test_refine_keep_on_match_no_matches_v1_1(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Scenario: Keep on Match (Negative) — coded data=refine,
        narrative=keep_on_match, no matches. Narrative removed.
        """

        empty_config = await _make_empty_processed_config()

        plan = EICRRefinementPlan(
            codes_to_check={"NON_EXISTENT_CODE"},
            code_system_sets=empty_config.code_system_sets,
            section_instructions={
                "11450-4": DbConfigurationSectionInstructions(
                    action="refine", include=True, narrative="keep_on_match"
                )
            },
            section_provenance={
                "11450-4": SectionProvenanceRecord(
                    loinc_code="11450-4",
                    display_name="Problems",
                    include=True,
                    action="refine",
                    narrative="keep_on_match",
                    config_version=1,
                    source=SectionSource.CONFIGURED,
                )
            },
            specification=load_spec("1.1"),
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
        )

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        problems_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="11450-4"]]', namespaces=HL7_NS
        )[0]
        rendered = etree.tostring(problems_section, encoding="unicode")

        # nullFlavor='NI' applied for schematron compliance
        assert problems_section.get("nullFlavor") == "NI"
        # entries pruned
        assert problems_section.findall("hl7:entry", namespaces=HL7_NS) == []
        # narrative replaced with removal notice
        assert REMOVE_NARRATIVE_MESSAGE in rendered
        # footnote shows the negative branch outcome
        assert (
            PROVENANCE_OUTCOME_NOTES[
                SectionOutcome.REFINED_NO_MATCHES_NARRATIVE_REMOVED
            ]
            in rendered
        )

    async def test_refine_reconstruct_no_matches_falls_back_to_retain_v1_1(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        narrative='reconstruct' + no matches: the engine can't rebuild
        from anything, so it falls back to retaining the original
        narrative rather than swapping in a removal notice. Outcome
        is REFINED_RECONSTRUCT_FALLBACK_RETAINED.
        """

        empty_config = await _make_empty_processed_config()

        plan = EICRRefinementPlan(
            codes_to_check={"NON_EXISTENT_CODE"},
            code_system_sets=empty_config.code_system_sets,
            section_instructions={
                "30954-2": DbConfigurationSectionInstructions(
                    action="refine", include=True, narrative="reconstruct"
                )
            },
            section_provenance={
                "30954-2": SectionProvenanceRecord(
                    loinc_code="30954-2",
                    display_name="Results",
                    include=True,
                    action="refine",
                    narrative="reconstruct",
                    config_version=1,
                    source=SectionSource.CONFIGURED,
                )
            },
            specification=load_spec("1.1"),
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
        )

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        results_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="30954-2"]]', namespaces=HL7_NS
        )[0]
        rendered = etree.tostring(results_section, encoding="unicode")

        # nullFlavor='NI' applied for schematron compliance
        assert results_section.get("nullFlavor") == "NI"
        # entries pruned
        assert results_section.findall("hl7:entry", namespaces=HL7_NS) == []
        # narrative NOT replaced with removal notice
        assert REMOVE_NARRATIVE_MESSAGE not in rendered
        # footnote shows reconstruct-fallback outcome
        assert (
            PROVENANCE_OUTCOME_NOTES[
                SectionOutcome.REFINED_RECONSTRUCT_FALLBACK_RETAINED
            ]
            in rendered
        )

    async def test_refine_reconstruct_unregistered_falls_back_to_retain_v1_1(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        narrative='reconstruct' on a section with matches but no
        registered reconstructor: the engine falls back to retaining
        the original narrative. Encounters (46240-8) is refinable but
        has no reconstructor in ReconstructableSection.

        Outcome is REFINED_RECONSTRUCT_FALLBACK_RETAINED.
        """

        processed_config = await _make_processed_config_v1_1(
            snomed_codes=[
                DbConditionCoding(
                    code="840539006", display="Disease caused by SARS-CoV-2"
                ),
            ],
        )

        plan = EICRRefinementPlan(
            codes_to_check=processed_config.codes,
            code_system_sets=processed_config.code_system_sets,
            section_instructions={
                "46240-8": DbConfigurationSectionInstructions(
                    action="refine", include=True, narrative="reconstruct"
                )
            },
            section_provenance={
                "46240-8": SectionProvenanceRecord(
                    loinc_code="46240-8",
                    display_name="Encounters",
                    include=True,
                    action="refine",
                    narrative="reconstruct",
                    config_version=1,
                    source=SectionSource.CONFIGURED,
                )
            },
            specification=load_spec("1.1"),
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
        )

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        encounters_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="46240-8"]]', namespaces=HL7_NS
        )[0]
        rendered = etree.tostring(encounters_section, encoding="unicode")

        # matches found → section has surviving entries, not stubbed
        assert encounters_section.get("nullFlavor") is None
        assert len(encounters_section.findall("hl7:entry", namespaces=HL7_NS)) > 0
        # narrative NOT replaced with removal notice (fallback to retain)
        assert REMOVE_NARRATIVE_MESSAGE not in rendered
        # footnote shows reconstruct-fallback outcome
        assert (
            PROVENANCE_OUTCOME_NOTES[
                SectionOutcome.REFINED_RECONSTRUCT_FALLBACK_RETAINED
            ]
            in rendered
        )

    async def test_refine_action_with_matches_v1_1(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Tests the 'refine' action for v1.1, ensuring it correctly uses the
        terminology pipeline to build codes and filter a section.
        """

        processed_config = await _make_processed_config_v1_1(
            loinc_codes=[DbConditionCoding(code="94533-7", display="")]
        )

        plan = EICRRefinementPlan(
            codes_to_check=processed_config.codes,
            code_system_sets=processed_config.code_system_sets,
            section_instructions={
                "30954-2": DbConfigurationSectionInstructions(
                    action="refine", include=True, narrative="remove"
                )
            },
            section_provenance={},
            specification=load_spec("1.1"),
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
        )

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        results_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="30954-2"]]', namespaces=HL7_NS
        )[0]
        section_text = etree.tostring(results_section, encoding="unicode")
        assert "94533-7" in section_text

    async def test_refine_action_on_narrative_only_section_v1_1(
        self, eicr_root_v1_1: etree._Element, original_eicr_root_v1_1: etree._Element
    ):
        """
        Tests that 'refine' action on a narrative-only section (e.g., Reason for Visit)
        is treated as 'retain' and does NOT result in a stubbed section (nullFlavor NI),
        even if no matching codes are provided.

        Also asserts that the rendered provenance footnote uses the
        NARRATIVE_ONLY_RETAINED outcome — distinct from the configured
        retain outcomes (RETAINED / RETAINED_NARRATIVE_REMOVED) because
        the section had no entry match rules to begin with.
        """

        empty_config = await _make_empty_processed_config()

        # Using '29299-5' (Reason for Visit) which is narrative-only
        plan = EICRRefinementPlan(
            codes_to_check=set(),
            code_system_sets=empty_config.code_system_sets,
            section_instructions={
                "29299-5": DbConfigurationSectionInstructions(
                    action="refine", include=True, narrative="retain"
                )
            },
            section_provenance={
                "29299-5": SectionProvenanceRecord(
                    loinc_code="29299-5",
                    display_name="Reason for Visit",
                    include=True,
                    action="refine",
                    narrative="retain",
                    config_version=1,
                    source=SectionSource.CONFIGURED,
                )
            },
            specification=load_spec("1.1"),
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
        )

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        section_refined = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="29299-5"]]', namespaces=HL7_NS
        )[0]

        # It should NOT be stubbed (nullFlavor should be None)
        assert section_refined.get("nullFlavor") is None

        # the provenance footnote should render the narrative-only outcome,
        # not a generic RETAINED or REFINED_* outcome
        rendered = etree.tostring(section_refined, encoding="unicode")
        assert (
            PROVENANCE_OUTCOME_NOTES[SectionOutcome.NARRATIVE_ONLY_RETAINED] in rendered
        )
        assert PROVENANCE_OUTCOME_NOTES[SectionOutcome.RETAINED] not in rendered

    async def test_narrative_removed_on_narrative_only_section_v1_1(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Tests narrative removal on a narrative-only section.

        With narrative="remove", the section's <text> should be replaced
        with the removal notice and the rendered provenance footnote
        should carry the NARRATIVE_ONLY_REMOVED outcome — distinct from
        the configured RETAINED_NARRATIVE_REMOVED because the section
        had no entry match rules to begin with.
        """

        empty_config = await _make_empty_processed_config()

        plan = EICRRefinementPlan(
            codes_to_check=set(),
            code_system_sets=empty_config.code_system_sets,
            section_instructions={
                "29299-5": DbConfigurationSectionInstructions(
                    action="retain", include=True, narrative="remove"
                )
            },
            section_provenance={
                "29299-5": SectionProvenanceRecord(
                    loinc_code="29299-5",
                    display_name="Reason for Visit",
                    include=True,
                    action="retain",
                    narrative="remove",
                    config_version=1,
                    source=SectionSource.CONFIGURED,
                )
            },
            specification=load_spec("1.1"),
            augmentation_timestamp=_PLACEHOLDER_AUGMENTATION_TIMESTAMP,
        )

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        section_refined = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="29299-5"]]', namespaces=HL7_NS
        )[0]
        rendered = etree.tostring(section_refined, encoding="unicode")

        assert (
            PROVENANCE_OUTCOME_NOTES[SectionOutcome.NARRATIVE_ONLY_REMOVED] in rendered
        )
        assert (
            PROVENANCE_OUTCOME_NOTES[SectionOutcome.RETAINED_NARRATIVE_REMOVED]
            not in rendered
        )

    # NOTE:
    # EICR REFINEMENT TESTS — section-aware path
    # =============================================================================
    # * these tests exercise the full refine_eicr pipeline with real
    # ProcessedConfiguration objects so that the section-aware match rules,
    # component-level pruning, and displayName enrichment all fire
    # * they assert on the shape of the refined XML output rather than testing
    # internal functions, making them resilient to internal refactoring

    async def test_section_aware_results_filtering_v1_1(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Tests that the section-aware path correctly filters the Results section:
        keeps entries with LOINC codes in the condition grouper and removes entries
        with LOINC codes not in the condition grouper.
        """

        processed_config = await _make_processed_config_v1_1(
            loinc_codes=[
                DbConditionCoding(code="94533-7", display="SARS-CoV-2 N gene"),
                DbConditionCoding(code="94558-4", display="SARS-CoV-2 Ag Rapid"),
            ],
        )
        plan = _make_plan(processed_config, {"30954-2": "refine"})

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        results_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="30954-2"]]', namespaces=HL7_NS
        )[0]

        # matching COVID tests should survive
        organizer_codes = results_section.xpath(
            ".//hl7:organizer/hl7:code/@code", namespaces=HL7_NS
        )
        assert "94533-7" in organizer_codes
        assert "94558-4" in organizer_codes

        # non-matching entries should be removed
        section_text = etree.tostring(results_section, encoding="unicode")
        assert "34487-9" not in section_text  # influenza
        assert "51990-0" not in section_text  # BMP
        assert "48065-7" not in section_text  # D-dimer
        assert "30746-2" not in section_text  # chest X-ray

    async def test_section_aware_problems_component_pruning_v1_1(
        self,
        eicr_root_v1_1: etree._Element,
    ):
        """
        Tests that the Problems section prunes individual problem observations
        within a Problem Concern Act while keeping the act wrapper intact.
        """

        processed_config = await _make_processed_config_v1_1(
            snomed_codes=[
                DbConditionCoding(
                    code="840539006", display="Disease caused by SARS-CoV-2"
                ),
                DbConditionCoding(code="186747009", display="Coronavirus infection"),
                DbConditionCoding(code="230145002", display="Difficulty Breathing"),
            ],
        )
        plan = _make_plan(processed_config, {"11450-4": "refine"})

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        problems_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="11450-4"]]', namespaces=HL7_NS
        )[0]

        # section should NOT be NI — we have matches
        assert problems_section.get("nullFlavor") is None

        # the Problem Concern Act wrapper should still be present
        concern_acts = problems_section.xpath(
            ".//hl7:act[hl7:code[@code='CONC']]", namespaces=HL7_NS
        )
        assert len(concern_acts) == 1

        # matching problem observations should survive
        surviving_values = problems_section.xpath(
            ".//hl7:observation/hl7:value/@code", namespaces=HL7_NS
        )
        assert "840539006" in surviving_values
        assert "186747009" in surviving_values
        assert "230145002" in surviving_values

        # non-matching observations should be pruned
        section_text = etree.tostring(problems_section, encoding="unicode")
        assert "719865001" not in section_text  # influenza
        assert "59621000" not in section_text  # hypertension
        assert "44054006" not in section_text  # diabetes

    async def test_display_name_enrichment_v1_1(self, eicr_root_v1_1: etree._Element):
        """
        Tests that missing displayName attributes are filled in from the condition
        grouper, both at match time (observation code) and during the post-prune
        enrichment pass (organizer code, result value).
        """

        processed_config = await _make_processed_config_v1_1(
            loinc_codes=[
                DbConditionCoding(
                    code="94759-8",
                    display="SARS-CoV-2 (COVID-19) RNA [Presence] in Nasopharynx by NAA with probe detection",
                ),
            ],
            snomed_codes=[
                DbConditionCoding(
                    code="260373001", display="Detected (qualifier value)"
                ),
            ],
        )
        plan = _make_plan(processed_config, {"30954-2": "refine"})

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        results_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="30954-2"]]', namespaces=HL7_NS
        )[0]

        # observation code should be enriched (match-time)
        obs_codes = results_section.xpath(
            ".//hl7:observation/hl7:code[@code='94759-8']", namespaces=HL7_NS
        )
        assert len(obs_codes) > 0
        assert obs_codes[0].get("displayName") is not None
        assert "Nasopharynx" in obs_codes[0].get("displayName", "")

        # organizer code should be enriched (post-prune _enrich_surviving_entries)
        organizer_codes = results_section.xpath(
            ".//hl7:organizer/hl7:code[@code='94759-8']", namespaces=HL7_NS
        )
        assert len(organizer_codes) > 0
        assert organizer_codes[0].get("displayName") is not None
        assert "Nasopharynx" in organizer_codes[0].get("displayName", "")

        # result value should be enriched (post-prune _enrich_surviving_entries)
        detected_values = results_section.xpath(
            ".//hl7:value[@code='260373001']", namespaces=HL7_NS
        )
        assert len(detected_values) > 0
        assert detected_values[0].get("displayName") is not None
        assert "Detected" in detected_values[0].get("displayName", "")

    async def test_plan_of_treatment_heterogeneous_entries_v1_1(
        self,
        eicr_root_v1_1: etree._Element,
    ):
        """
        Tests that Plan of Treatment correctly handles heterogeneous entry types:
        keeps matching lab orders (LOINC) and medications (RxNorm), removes
        non-matching entries.
        """

        processed_config = await _make_processed_config_v1_1(
            loinc_codes=[
                DbConditionCoding(code="94500-6", display="SARS-CoV-2 RNA panel"),
            ],
            rxnorm_codes=[
                DbConditionCoding(
                    code="2284960", display="remdesivir 100 MG Injection"
                ),
            ],
        )
        plan = _make_plan(processed_config, {"18776-5": "refine"})

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        pot_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="18776-5"]]', namespaces=HL7_NS
        )[0]
        section_text = etree.tostring(pot_section, encoding="unicode")

        # matching lab order and medication should survive
        assert "94500-6" in section_text
        assert "2284960" in section_text

        # non-matching entries should be removed
        assert "25836-8" not in section_text  # influenza lab order
        assert "261315" not in section_text  # oseltamivir
        assert "314076" not in section_text  # lisinopril
        assert "861007" not in section_text  # metformin
        assert "270427003" not in section_text  # follow-up encounter

    async def test_encounters_diagnosis_pruning_v1_1(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Tests that the Encounters section prunes non-matching diagnoses at the
        component level while keeping the encounter wrapper and matching diagnoses.
        """

        processed_config = await _make_processed_config_v1_1(
            snomed_codes=[
                DbConditionCoding(
                    code="840539006", display="Disease caused by SARS-CoV-2"
                ),
            ],
        )
        plan = _make_plan(processed_config, {"46240-8": "refine"})

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        enc_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="46240-8"]]', namespaces=HL7_NS
        )[0]

        # only encounters with matching diagnoses should survive
        entries = enc_section.xpath(".//hl7:entry", namespaces=HL7_NS)
        assert len(entries) == 1

        # covid diagnosis should be kept
        surviving_values = enc_section.xpath(
            ".//hl7:observation/hl7:value/@code", namespaces=HL7_NS
        )
        assert "840539006" in surviving_values

        # influenza diagnosis should be pruned from within the encounter
        section_text = etree.tostring(enc_section, encoding="unicode")
        assert "772828001" not in section_text

    async def test_non_matching_section_no_longer_stubbed_v1_1(
        self, eicr_root_v1_1: etree._Element
    ):
        """
        Tests that a section with entries but no matching codes has all
        entries removed and the narrative replaced with the removal
        notice (narrative='remove' is the _make_plan default).
        nullFlavor='NI' is retained for CDA schematron compliance, but
        the narrative is now driven by the narrative setting (no more
        hard-coded stub table overwriting <text>).
        """

        processed_config = await _make_processed_config_v1_1(
            snomed_codes=[
                DbConditionCoding(
                    code="840539006", display="Disease caused by SARS-CoV-2"
                ),
            ],
        )
        plan = _make_plan(processed_config, {"11369-6": "refine"})

        refine_eicr(eicr_root=eicr_root_v1_1, plan=plan)

        imm_section = eicr_root_v1_1.xpath(
            './/hl7:section[hl7:code[@code="11369-6"]]', namespaces=HL7_NS
        )[0]

        # nullFlavor='NI' applied for schematron compliance
        assert imm_section.get("nullFlavor") == "NI"

        # entries should be removed
        entries = imm_section.xpath(".//hl7:entry", namespaces=HL7_NS)
        assert len(entries) == 0

        # narrative replaced with the removal notice
        rendered = etree.tostring(imm_section, encoding="unicode")
        assert REMOVE_NARRATIVE_MESSAGE in rendered

    # NOTE:
    # RR REFINEMENT TESTS
    # =============================================================================

    async def test_refine_rr_by_condition_v1_1(self, rr_root_v1_1: etree._Element):
        """
        Tests RR refinement for v1.1: keeps ONLY the observations for conditions
        specified in the configuration.
        """

        covid_condition = _make_condition_v1_1(
            child_rsg_snomed_codes=["840539006"], rxnorm_codes=_MOCK_CONDITION_CODES
        )
        config = _make_db_configuration_v1_1()

        processed_configuration = await create_processed_config(
            config=config, conditions=[covid_condition]
        )

        rr_refinement_plan = create_rr_refinement_plan(
            processed_configuration=processed_configuration
        )

        refine_rr(rr_root=rr_root_v1_1, plan=rr_refinement_plan)

        doc_string = etree.tostring(rr_root_v1_1, encoding="unicode")

        assert "840539006" in doc_string
        assert "49727002" not in doc_string

    async def test_refine_rr_by_jurisdiction_v1_1(self, rr_root_v1_1: etree._Element):
        """
        Tests RR refinement for v1.1: doesn't touch observations not for the given jurisdiction.
        """

        covid_condition = _make_condition_v1_1(
            child_rsg_snomed_codes=["840539006"], snomed_codes=_MOCK_CONDITION_CODES
        )
        config = _make_db_configuration_v1_1(jurisdiction_id="SOME-OTHER-JD")

        processed_configuration = await create_processed_config(
            config=config, conditions=[covid_condition]
        )
        rr_refinement_plan = create_rr_refinement_plan(
            processed_configuration=processed_configuration
        )

        refine_rr(rr_root=rr_root_v1_1, plan=rr_refinement_plan)

        doc_string = etree.tostring(rr_root_v1_1, encoding="unicode")

        assert "840539006" in doc_string

    async def test_refine_rr_by_condition_v3_1_1(self, rr_root_v3_1_1: etree._Element):
        """
        Tests RR refinement on the Zika file: confirms the Zika observation is kept
        even if config is for another jurisdiction.
        """

        zika_condition = _make_condition_v3_1_1(
            child_rsg_snomed_codes=["3928002"], loinc_codes=_MOCK_CONDITION_CODES
        )
        config = _make_db_configuration_v3_1_1()

        processed_configuration = await create_processed_config(
            config=config, conditions=[zika_condition]
        )
        rr_refinement_plan = create_rr_refinement_plan(
            processed_configuration=processed_configuration
        )

        refine_rr(rr_root=rr_root_v3_1_1, plan=rr_refinement_plan)

        doc_string = etree.tostring(rr_root_v3_1_1, encoding="unicode")

        assert "3928002" in doc_string

    async def test_refine_rr_by_jurisdiction_v3_1_1(
        self, rr_root_v3_1_1: etree._Element
    ):
        """
        Tests RR refinement on the Zika file: confirms the Zika observation is still
        present even when jurisdiction is different.
        """

        zika_condition = _make_condition_v3_1_1(
            child_rsg_snomed_codes=["3928002"], icd10_codes=_MOCK_CONDITION_CODES
        )
        config = _make_db_configuration_v3_1_1(jurisdiction_id="SOME-OTHER-JD")

        processed_configuration = await create_processed_config(
            config=config, conditions=[zika_condition]
        )
        rr_refinement_plan = create_rr_refinement_plan(
            processed_configuration=processed_configuration
        )

        refine_rr(rr_root=rr_root_v3_1_1, plan=rr_refinement_plan)

        doc_string = etree.tostring(rr_root_v3_1_1, encoding="unicode")

        assert "3928002" in doc_string
