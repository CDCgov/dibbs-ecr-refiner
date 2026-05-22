from app.services.ecr.policy import (
    DISABLED_SECTIONS,
    NARRATIVE_ONLY_SECTIONS,
    SECTION_PROCESSING_SKIP,
)
from app.services.ecr.specification import load_spec


def test_disabled_sections_match_skip_set():
    """
    The Literal-typed tuple shipped to the frontend must be the single
    source of truth for the runtime skip set.
    """

    assert set(DISABLED_SECTIONS) == SECTION_PROCESSING_SKIP


def test_narrative_only_sections_match_spec_catalog():
    """
    Every code declared as narrative-only here must have
    has_match_rules=False in the spec, and every section in the spec
    with has_match_rules=False must be listed here.

    This guards against drift between the literal-typed tuple shipped to
    the frontend and the IG-derived spec catalog. If a new narrative-only
    section is added to the catalog, this test fails until the tuple is
    updated.
    """

    spec = load_spec("3.1.1")
    spec_narrative_only = {
        code for code, section in spec.sections.items() if not section.has_match_rules
    }

    # narrative-only catalog codes that are also operationally disabled
    # (e.g. reportability response) are surfaced via DISABLED_SECTIONS
    # instead — narrative-only behavior in the UI is for sections that
    # are otherwise refinable
    expected = spec_narrative_only - set(DISABLED_SECTIONS)

    assert set(NARRATIVE_ONLY_SECTIONS) == expected
