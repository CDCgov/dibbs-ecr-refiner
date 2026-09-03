from app.services.ecr.narrative.reconstruction import SECTION_RECONSTRUCTORS
from app.services.ecr.policy import (
    NARRATIVE_ACTION_REQUIRES_REFINE,
    NARRATIVE_ONLY_SECTIONS,
    RECONSTRUCTABLE_SECTIONS,
    SECTION_PROCESSING_SKIP,
    TRIGGER_CODE_SECTIONS,
    NarrativeOnlySection,
    is_disabled_section,
    is_narrative_only_section,
    is_reconstructable_section,
    is_trigger_code_section,
    narrative_requires_refine,
    normalize_section_processing,
)
from app.services.ecr.specification import get_trigger_code_sections, load_spec


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
        expected = ["30954-2", "11450-4", "11369-6", "29549-3", "18776-5"]
        assert RECONSTRUCTABLE_SECTIONS == expected

    def test_every_reconstructable_section_has_a_reconstructor(self):
        """
        The policy gate and the dispatch table must not drift.

        `is_reconstructable_section` is what the API lets a jurisdiction
        configure; SECTION_RECONSTRUCTORS is what actually runs. A code in
        the first but not the second silently degrades to the retained
        narrative at refinement time.
        """

        assert set(RECONSTRUCTABLE_SECTIONS) == set(SECTION_RECONSTRUCTORS)


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


class TestTriggerCodeSectionSync:
    def test_enum_matches_specification_union(self):
        """
        TriggerCodeSection must equal the union of sections carrying
        trigger code templates across every supported eICR version.
        """

        assert set(TRIGGER_CODE_SECTIONS) == get_trigger_code_sections()

    def test_every_enum_value_has_trigger_codes_in_some_version(self):
        """
        Every code in the enum must carry trigger codes in at least one
        supported version of the spec.
        """

        versions = ("1.1", "3.1", "3.1.1")
        for code in TRIGGER_CODE_SECTIONS:
            assert any(
                (section := load_spec(v).sections.get(code)) is not None
                and section.has_trigger_codes
                for v in versions
            ), f"{code} is in TriggerCodeSection but carries no trigger codes"

    def test_no_overlap_with_disabled_or_narrative_only(self):
        """
        Trigger code sections must not collide with the other policy
        lists — a section cannot be both always-removed and never-removed.
        """

        trigger = set(TRIGGER_CODE_SECTIONS)
        assert trigger & set(SECTION_PROCESSING_SKIP) == set()
        assert trigger & set(NARRATIVE_ONLY_SECTIONS) == set()

    def test_is_trigger_code_section(self):
        assert is_trigger_code_section("30954-2") is True
        assert is_trigger_code_section("29762-2") is False


class TestNormalizeSectionProcessing:
    def test_valid_combo_is_passthrough(self):
        include, action, narrative, notes = normalize_section_processing(
            code="11450-4",
            include=True,
            section_action="refine",
            narrative_action="remove",
        )
        assert include is True
        assert action == "refine"
        assert narrative == "remove"
        assert notes == []

    def test_narrative_only_action_coerced_to_retain(self):
        _include, action, _narrative, notes = normalize_section_processing(
            code="29299-5",  # Reason for Visit (narrative-only)
            include=True,
            section_action="refine",
            narrative_action="retain",
        )
        assert action == "retain"
        assert any("narrative-only" in n for n in notes)

    def test_disabled_section_action_coerced_to_retain(self):
        _include, action, _narrative, notes = normalize_section_processing(
            code="83910-0",  # Emergency Outbreak (disabled)
            include=True,
            section_action="refine",
            narrative_action="retain",
        )
        assert action == "retain"
        assert any("system-skipped" in n for n in notes)

    def test_trigger_code_section_include_coerced_to_true(self):
        include, action, narrative, notes = normalize_section_processing(
            code="47519-4",  # Procedures — trigger codes in 3.x
            include=False,
            section_action="refine",
            narrative_action="remove",
        )
        assert include is True
        assert any("can carry a trigger code" in n for n in notes)

        # removal is the only thing forced; everything else survives
        assert action == "refine"
        assert narrative == "remove"

    def test_non_trigger_section_may_be_removed(self):
        include, _action, _narrative, notes = normalize_section_processing(
            code="29762-2",  # Social History — no trigger codes
            include=False,
            section_action="refine",
            narrative_action="retain",
        )
        assert include is False
        assert notes == []

    def test_narrative_requires_refine_coerces_to_retain(self):
        _include, action, narrative, notes = normalize_section_processing(
            code="11450-4",
            include=True,
            section_action="retain",
            narrative_action="keep_on_match",
        )
        assert action == "retain"
        assert narrative == "retain"
        assert any("requires action='refine'" in n for n in notes)

    def test_reconstruct_on_non_reconstructable_coerces_to_retain(self):
        _include, action, narrative, notes = normalize_section_processing(
            code="29762-2",  # Social History — not in ReconstructableSection
            include=True,
            section_action="refine",
            narrative_action="reconstruct",
        )
        assert action == "refine"
        assert narrative == "retain"
        assert any("does not support narrative reconstruction" in n for n in notes)

    def test_reconstruct_on_results_is_valid(self):
        _include, action, narrative, notes = normalize_section_processing(
            code="30954-2",  # Results
            include=True,
            section_action="refine",
            narrative_action="reconstruct",
        )
        assert action == "refine"
        assert narrative == "reconstruct"
        assert notes == []

    def test_idempotent(self):
        """Normalizing already-coerced output should be a no-op."""

        include1, action1, narrative1, _notes1 = normalize_section_processing(
            code="29299-5",
            include=True,
            section_action="refine",
            narrative_action="keep_on_match",
        )
        include2, action2, narrative2, notes2 = normalize_section_processing(
            code="29299-5",
            include=include1,
            section_action=action1,
            narrative_action=narrative1,
        )
        assert include1 == include2
        assert action1 == action2
        assert narrative1 == narrative2
        assert notes2 == []

    def test_idempotent_for_trigger_section(self):
        include1, action1, narrative1, _notes1 = normalize_section_processing(
            code="46240-8",
            include=False,
            section_action="refine",
            narrative_action="keep_on_match",
        )
        include2, action2, narrative2, notes2 = normalize_section_processing(
            code="46240-8",
            include=include1,
            section_action=action1,
            narrative_action=narrative1,
        )
        assert include1 == include2
        assert action1 == action2
        assert narrative1 == narrative2
        assert notes2 == []
