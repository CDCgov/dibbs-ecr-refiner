from app.services.ecr.policy import (
    NARRATIVE_ACTION_REQUIRES_REFINE,
    NARRATIVE_ONLY_SECTIONS,
    RECONSTRUCTABLE_SECTIONS,
    SECTION_PROCESSING_SKIP,
    NarrativeOnlySection,
    is_disabled_section,
    is_narrative_only_section,
    is_reconstructable_section,
    narrative_requires_refine,
    normalize_section_narrative,
)
from app.services.ecr.specification import load_spec


class TestNarrativeOnlySectionSync:
    def test_every_enum_value_is_narrative_only_in_spec(self):
        """
        Every code in NarrativeOnlySection must have has_match_rules=False
        in the eICR specification catalog.
        """
        spec = load_spec("3.1.1")

        for section in NarrativeOnlySection:
            spec_entry = spec.sections.get(section.value)
            assert spec_entry is not None, (
                f"NarrativeOnlySection code {section.value} ({section.name}) "
                f"not found in the eICR specification catalog"
            )
            assert not spec_entry.has_match_rules, (
                f"NarrativeOnlySection code {section.value} ({section.name}) "
                f"has has_match_rules=True in the spec — it should be False"
            )

    def test_every_narrative_only_spec_section_is_in_enum(self):
        """
        Every spec section with has_match_rules=False must be listed in
        NarrativeOnlySection (unless it's in SECTION_PROCESSING_SKIP).
        This prevents new narrative-only sections from silently bypassing
        the policy constant.
        """
        spec = load_spec("3.1.1")
        narrative_only_codes = set(NARRATIVE_ONLY_SECTIONS)
        disabled_codes = set(SECTION_PROCESSING_SKIP)

        for loinc_code, spec_entry in spec.sections.items():
            if not spec_entry.has_match_rules and loinc_code not in disabled_codes:
                assert loinc_code in narrative_only_codes, (
                    f"Spec section {loinc_code} ({spec_entry.display_name}) "
                    f"has has_match_rules=False but is not in NarrativeOnlySection"
                )


class TestReconstructableSections:
    def test_active_reconstructable_sections(self):
        """
        Ensure only the intended LOINCs are active for reconstruction.
        TODO: Update this list when more LOINCs are uncommented in policy.py
        """
        expected = ["30954-2", "11450-4", "11369-6", "29549-3"]
        assert RECONSTRUCTABLE_SECTIONS == expected


class TestPolicyPredicates:
    def test_is_disabled_section(self):
        assert is_disabled_section("83910-0") is True
        assert is_disabled_section("88085-6") is True
        assert is_disabled_section("11450-4") is False

    def test_is_narrative_only_section(self):
        assert is_narrative_only_section("29299-5") is True
        assert is_narrative_only_section("11450-4") is False

    def test_is_reconstructable_section(self):
        assert is_reconstructable_section("30954-2") is True
        assert is_reconstructable_section("29762-2") is False

    def test_narrative_requires_refine(self):
        assert narrative_requires_refine("reconstruct") is True
        assert narrative_requires_refine("keep_on_match") is True
        assert narrative_requires_refine("retain") is False
        assert narrative_requires_refine("remove") is False

    def test_narrative_requires_refine_contents(self):
        assert NARRATIVE_ACTION_REQUIRES_REFINE == frozenset(
            {"reconstruct", "keep_on_match"}
        )


class TestNormalizeSectionNarrative:
    def test_valid_combo_is_passthrough(self):
        action, narrative, notes = normalize_section_narrative(
            code="11450-4", section_action="refine", narrative_action="remove"
        )
        assert action == "refine"
        assert narrative == "remove"
        assert notes == []

    def test_narrative_only_action_coerced_to_retain(self):
        action, _narrative, notes = normalize_section_narrative(
            code="29299-5",  # Reason for Visit (narrative-only)
            section_action="refine",
            narrative_action="retain",
        )
        assert action == "retain"
        assert any("narrative-only" in n for n in notes)

    def test_disabled_section_action_coerced_to_retain(self):
        action, _narrative, notes = normalize_section_narrative(
            code="83910-0",  # Emergency Outbreak (disabled)
            section_action="refine",
            narrative_action="retain",
        )
        assert action == "retain"
        assert any("system-skipped" in n for n in notes)

    def test_narrative_requires_refine_coerces_to_retain(self):
        action, narrative, notes = normalize_section_narrative(
            code="11450-4", section_action="retain", narrative_action="keep_on_match"
        )
        assert action == "retain"
        assert narrative == "retain"
        assert any("requires action='refine'" in n for n in notes)

    def test_reconstruct_on_non_reconstructable_coerces_to_retain(self):
        action, narrative, notes = normalize_section_narrative(
            code="29762-2",  # Social History — not in ReconstructableSection
            section_action="refine",
            narrative_action="reconstruct",
        )
        assert action == "refine"
        assert narrative == "retain"
        assert any("does not support narrative reconstruction" in n for n in notes)

    def test_reconstruct_on_results_is_valid(self):
        action, narrative, notes = normalize_section_narrative(
            code="30954-2",  # Results
            section_action="refine",
            narrative_action="reconstruct",
        )
        assert action == "refine"
        assert narrative == "reconstruct"
        assert notes == []

    def test_idempotent(self):
        """Normalizing already-coerced output should be a no-op."""

        action1, narrative1, _notes1 = normalize_section_narrative(
            code="29299-5", section_action="refine", narrative_action="keep_on_match"
        )
        action2, narrative2, notes2 = normalize_section_narrative(
            code="29299-5", section_action=action1, narrative_action=narrative1
        )
        assert action1 == action2
        assert narrative1 == narrative2
        assert notes2 == []
