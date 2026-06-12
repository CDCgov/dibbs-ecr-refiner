from app.api.v1.configurations.model import SectionUpdateInput
from app.api.v1.configurations.sections import _build_section_update
from app.db.configurations.model import DbConfigurationSectionProcessing
from app.services.configurations import (
    clone_section_processing_instructions,
    get_default_sections,
)
from app.services.ecr.policy import NARRATIVE_ONLY_SECTIONS, SECTION_PROCESSING_SKIP
from app.services.ecr.specification import load_spec


class TestGetDefaultSections:
    def test_narrative_only_sections_default_to_retain(self):
        """
        Tests that narrative-only sections (has_match_rules=False) default to action="retain".
        """
        sections = get_default_sections()
        section_map = {s.code: s for s in sections}

        for code in NARRATIVE_ONLY_SECTIONS:
            assert code in section_map, (
                f"Narrative-only section {code} not found in defaults"
            )
            assert section_map[code].action == "retain", (
                f"Narrative-only section {code} should default to 'retain', got '{section_map[code].action}'"
            )

    def test_disabled_sections_default_to_retain(self):
        """
        Tests that disabled sections (SECTION_PROCESSING_SKIP) default to action="retain".
        """
        sections = get_default_sections()
        section_map = {s.code: s for s in sections}

        for code in SECTION_PROCESSING_SKIP:
            assert code in section_map, f"Disabled section {code} not found in defaults"
            assert section_map[code].action == "retain", (
                f"Disabled section {code} should default to 'retain', got '{section_map[code].action}'"
            )

    def test_refinable_sections_default_to_refine(self):
        """
        Tests that sections with match rules and not in skip list default to action="refine".
        """
        sections = get_default_sections()
        spec = load_spec("3.1.1")

        for section in sections:
            spec_entry = spec.sections.get(section.code)
            if (
                spec_entry
                and spec_entry.has_match_rules
                and section.code not in SECTION_PROCESSING_SKIP
            ):
                assert section.action == "refine", (
                    f"Refinable section {section.code} should default to 'refine', got '{section.action}'"
                )

    def test_no_narrative_only_section_defaults_to_refine(self):
        """
        Tests that no narrative-only section accidentally defaults to action="refine".
        """
        sections = get_default_sections()
        spec = load_spec("3.1.1")

        for section in sections:
            spec_entry = spec.sections.get(section.code)
            if spec_entry and not spec_entry.has_match_rules:
                assert section.action != "refine", (
                    f"Narrative-only section {section.code} must not default to 'refine'"
                )


class TestCloneSectionProcessingInstructions:
    def test_clone_preserves_narrative_only_retain_action(self):
        """
        Tests that cloning preserves action="retain" for narrative-only sections,
        even if the source had action="refine".
        """
        narrative_only_code = NARRATIVE_ONLY_SECTIONS[0]

        clone_from = [
            DbConfigurationSectionProcessing(
                code=narrative_only_code,
                name="Test Section",
                action="refine",
                include=True,
                narrative="retain",
                versions=["1.1"],
                section_type="standard",
            )
        ]

        clone_to = [
            DbConfigurationSectionProcessing(
                code=narrative_only_code,
                name="Test Section",
                action="retain",
                include=True,
                narrative="retain",
                versions=["1.1"],
                section_type="standard",
            )
        ]

        result = clone_section_processing_instructions(clone_from, clone_to)

        assert len(result) == 1
        assert result[0].code == narrative_only_code
        assert result[0].action == "retain", (
            f"Narrative-only section should remain 'retain' after cloning, got '{result[0].action}'"
        )

    def test_clone_preserves_refine_action_for_refinable_sections(self):
        """
        Tests that cloning preserves action="refine" for sections with match rules.
        """
        refinable_code = "11450-4"

        clone_from = [
            DbConfigurationSectionProcessing(
                code=refinable_code,
                name="Problem Section",
                action="refine",
                include=True,
                narrative="remove",
                versions=["1.1"],
                section_type="standard",
            )
        ]

        clone_to = [
            DbConfigurationSectionProcessing(
                code=refinable_code,
                name="Problem Section",
                action="retain",
                include=True,
                narrative="retain",
                versions=["1.1"],
                section_type="standard",
            )
        ]

        result = clone_section_processing_instructions(clone_from, clone_to)

        assert len(result) == 1
        assert result[0].code == refinable_code
        assert result[0].action == "refine", (
            f"Refinable section should keep 'refine' action after cloning, got '{result[0].action}'"
        )

    def test_clone_handles_custom_sections(self):
        """
        Tests that custom sections are copied directly from clone_from.
        """
        custom_code = "custom-123"

        clone_from = [
            DbConfigurationSectionProcessing(
                code=custom_code,
                name="Custom Section",
                action="refine",
                include=True,
                narrative="remove",
                versions=[],
                section_type="custom",
            )
        ]

        clone_to = []

        result = clone_section_processing_instructions(clone_from, clone_to)

        assert len(result) == 1
        assert result[0].code == custom_code
        assert result[0].section_type == "custom"
        assert result[0].action == "refine"

    def test_clone_mixed_sections(self):
        """
        Tests cloning with a mix of narrative-only, refinable, and custom sections.
        """
        narrative_code = NARRATIVE_ONLY_SECTIONS[0]
        refinable_code = "11450-4"
        custom_code = "custom-456"

        clone_from = [
            DbConfigurationSectionProcessing(
                code=narrative_code,
                name="Narrative Section",
                action="refine",
                include=True,
                narrative="retain",
                versions=["1.1"],
                section_type="standard",
            ),
            DbConfigurationSectionProcessing(
                code=refinable_code,
                name="Problem Section",
                action="refine",
                include=False,
                narrative="remove",
                versions=["1.1"],
                section_type="standard",
            ),
            DbConfigurationSectionProcessing(
                code=custom_code,
                name="Custom Section",
                action="retain",
                include=True,
                narrative="retain",
                versions=[],
                section_type="custom",
            ),
        ]

        clone_to = [
            DbConfigurationSectionProcessing(
                code=narrative_code,
                name="Narrative Section",
                action="retain",
                include=True,
                narrative="retain",
                versions=["3.1.1"],
                section_type="standard",
            ),
            DbConfigurationSectionProcessing(
                code=refinable_code,
                name="Problem Section",
                action="retain",
                include=True,
                narrative="retain",
                versions=["3.1.1"],
                section_type="standard",
            ),
        ]

        result = clone_section_processing_instructions(clone_from, clone_to)

        assert len(result) == 3

        result_map = {s.code: s for s in result}

        assert result_map[narrative_code].action == "retain"
        assert result_map[refinable_code].action == "refine"
        assert result_map[refinable_code].include is False
        assert result_map[custom_code].section_type == "custom"


class TestBuildSectionUpdateNormalization:
    def test_narrative_only_standard_section_normalized_to_retain(self):
        """
        Tests that standard sections with narrative-only codes are normalized to action="retain"
        even when action="refine" is requested (handles legacy DB rows).
        """
        narrative_code = NARRATIVE_ONLY_SECTIONS[0]

        prev_section = DbConfigurationSectionProcessing(
            code=narrative_code,
            name="Chief Complaint",
            action="refine",  # Legacy value from before narrative refinement PR
            include=True,
            narrative="retain",
            versions=["1.1"],
            section_type="standard",
        )

        section_input = SectionUpdateInput(
            current_code=narrative_code,
            action="refine",  # Attempting to set to refine
        )

        result = _build_section_update(prev_section, section_input)

        assert result.code == narrative_code
        assert result.action == "retain", (
            f"Narrative-only standard section should be normalized to 'retain', got '{result.action}'"
        )
        assert result.section_type == "standard"

    def test_narrative_only_custom_section_not_normalized(self):
        """
        Tests that custom sections with narrative-only codes are NOT normalized,
        allowing them to keep their requested action.
        """
        narrative_code = NARRATIVE_ONLY_SECTIONS[0]

        prev_section = DbConfigurationSectionProcessing(
            code=narrative_code,
            name="Custom Narrative Section",
            action="refine",
            include=True,
            narrative="retain",
            versions=[],
            section_type="custom",
        )

        section_input = SectionUpdateInput(
            current_code=narrative_code,
            action="refine",
        )

        result = _build_section_update(prev_section, section_input)

        assert result.code == narrative_code
        assert result.action == "refine", (
            f"Custom section should keep 'refine' action, got '{result.action}'"
        )
        assert result.section_type == "custom"

    def test_refinable_standard_section_keeps_refine_action(self):
        """
        Tests that standard sections with match rules keep action="refine" when requested.
        """
        refinable_code = "11450-4"  # Problem Section

        prev_section = DbConfigurationSectionProcessing(
            code=refinable_code,
            name="Problem Section",
            action="retain",
            include=True,
            narrative="remove",
            versions=["1.1"],
            section_type="standard",
        )

        section_input = SectionUpdateInput(
            current_code=refinable_code,
            action="refine",
        )

        result = _build_section_update(prev_section, section_input)

        assert result.code == refinable_code
        assert result.action == "refine", (
            f"Refinable standard section should keep 'refine' action, got '{result.action}'"
        )
        assert result.section_type == "standard"
