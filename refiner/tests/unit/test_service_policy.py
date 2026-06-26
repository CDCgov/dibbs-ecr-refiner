from app.services.ecr.policy import (
    NARRATIVE_ONLY_SECTIONS,
    RECONSTRUCTABLE_SECTIONS,
    SECTION_PROCESSING_SKIP,
    NarrativeOnlySection,
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
