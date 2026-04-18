from lxml import etree
from lxml.etree import _Element

from app.services.ecr.model import HL7_NS
from app.services.ecr.section import get_section_by_code, process_section
from app.services.ecr.section.generic_matching import (
    _find_path_to_entry,
)

# NOTE:
# HELPERS
# =============================================================================


def _build_section(xml: str) -> _Element:
    return etree.fromstring(xml.encode("utf-8"))


def _find_one(element: _Element, xpath: str) -> _Element | None:
    results = element.xpath(xpath, namespaces=HL7_NS)
    if not isinstance(results, list):
        return None
    if len(results) > 1:
        raise AssertionError(
            f"Expected at most one match for {xpath!r}, got {len(results)}"
        )
    return results[0] if results else None


def _get_refiner_comments(section: _Element) -> list[str]:
    return [
        item.text.strip()
        for item in section.iter()
        if isinstance(item, etree._Comment)
        and item.text is not None
        and "eCR Refiner" in item.text
    ]


# NOTE:
# CATEGORY 1: CRITICAL — protect known-correct behavior from regression
# =============================================================================


def test_empty_section_is_stubbed() -> None:
    """
    Section with no entries and any code set should be stubbed.
    """

    section = _build_section(
        '<section xmlns="urn:hl7-org:v3"><code code="30954-2"/></section>'
    )
    process_section(
        section=section,
        codes_to_match={"ANYTHING"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    assert section.get("nullFlavor") == "NI"


def test_empty_codes_to_match_stubs_section() -> None:
    """
    codes_to_match=set() with real entries stubs the section — no config guard.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry><observation><code code="12345"/></observation></entry>
        </section>
        """
    )
    process_section(
        section=section,
        codes_to_match=set(),
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    assert section.get("nullFlavor") == "NI"


def test_matching_code_preserves_entry() -> None:
    """
    Entry whose code matches the configured set survives.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry><observation><code code="MATCH"/></observation></entry>
        </section>
        """
    )
    process_section(
        section=section,
        codes_to_match={"MATCH"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    assert section.get("nullFlavor") != "NI"
    assert _find_one(section, ".//hl7:observation/hl7:code[@code='MATCH']") is not None


def test_nonmatching_code_removes_entry_and_stubs_section() -> None:
    """
    Entry with no matching code is removed; section stubbed.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry><observation><code code="NOMATCH"/></observation></entry>
        </section>
        """
    )
    process_section(
        section=section,
        codes_to_match={"DIFFERENT"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    assert section.get("nullFlavor") == "NI"


def test_section_own_code_does_not_match() -> None:
    """
    The section's own <code> LOINC identifier is neutralized before
    matching. Even if that code appears in codes_to_match, it does not
    produce a match — preventing false positives when a section LOINC
    happens to be in a jurisdiction's configuration.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry><observation><code code="NOMATCH"/></observation></entry>
        </section>
        """
    )
    process_section(
        section=section,
        codes_to_match={"30954-2"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    assert section.get("nullFlavor") == "NI"


def test_cluster_preservation_keeps_sibling_code_when_value_matches() -> None:
    """
    Match on <value> — sibling <code> travels with it via cluster
    preservation. The observation's test name is kept alongside its result.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry>
                <observation>
                    <code code="TESTCODE"/>
                    <value code="MATCH"/>
                </observation>
            </entry>
        </section>
        """
    )
    process_section(
        section=section,
        codes_to_match={"MATCH"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    assert (
        _find_one(section, ".//hl7:observation/hl7:code[@code='TESTCODE']") is not None
    )
    assert _find_one(section, ".//hl7:observation/hl7:value[@code='MATCH']") is not None


def test_cluster_preservation_keeps_sibling_value_when_code_matches() -> None:
    """
    Mirror: match on <code>, sibling <value> travels with it.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry>
                <observation>
                    <code code="MATCH"/>
                    <value code="RESULT"/>
                </observation>
            </entry>
        </section>
        """
    )
    process_section(
        section=section,
        codes_to_match={"MATCH"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    assert _find_one(section, ".//hl7:observation/hl7:code[@code='MATCH']") is not None
    assert (
        _find_one(section, ".//hl7:observation/hl7:value[@code='RESULT']") is not None
    )


def test_preserved_procedure_retains_structural_metadata() -> None:
    """
    CDA procedures require id, statusCode, and effectiveTime. Path-based
    pruning must keep these structural siblings alongside the matched code.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="47519-4"/>
            <entry>
                <procedure>
                    <id root="abc"/>
                    <code code="MATCH"/>
                    <statusCode code="completed"/>
                    <effectiveTime value="20250101"/>
                </procedure>
            </entry>
        </section>
        """
    )
    process_section(
        section=section,
        codes_to_match={"MATCH"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    proc = _find_one(section, ".//hl7:procedure")
    assert proc is not None
    assert _find_one(proc, "hl7:id") is not None
    assert _find_one(proc, "hl7:statusCode") is not None
    assert _find_one(proc, "hl7:effectiveTime") is not None


def test_preserved_observation_retains_structural_metadata() -> None:
    """
    Observations require statusCode and effectiveTime — same constraint.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry>
                <observation>
                    <id root="obs1"/>
                    <code code="MATCH"/>
                    <statusCode code="completed"/>
                    <effectiveTime value="20250101"/>
                </observation>
            </entry>
        </section>
        """
    )
    process_section(
        section=section,
        codes_to_match={"MATCH"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    obs = _find_one(section, ".//hl7:observation")
    assert obs is not None
    assert _find_one(obs, "hl7:statusCode") is not None
    assert _find_one(obs, "hl7:effectiveTime") is not None
    assert _find_one(obs, "hl7:id") is not None


def test_preserved_entryRelationship_retains_child_clinical_statement() -> None:
    """
    An entryRelationship's XSD content model requires at least one clinical
    statement child. A preserved entryRelationship that loses its child
    is invalid CDA. Pruning must never leave an empty ER shell.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11450-4"/>
            <entry>
                <act>
                    <id root="wrapper"/>
                    <code code="CONC"/>
                    <statusCode code="active"/>
                    <entryRelationship typeCode="SUBJ">
                        <observation>
                            <id root="inner"/>
                            <code code="OBSCODE"/>
                            <statusCode code="completed"/>
                            <value code="MATCH"/>
                        </observation>
                    </entryRelationship>
                </act>
            </entry>
        </section>
        """
    )
    process_section(
        section=section,
        codes_to_match={"MATCH"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    wrapper = _find_one(section, ".//hl7:entryRelationship")
    assert wrapper is not None, "entryRelationship was pruned"
    inner_obs = _find_one(wrapper, "hl7:observation")
    assert inner_obs is not None, "entryRelationship preserved as empty shell"


# NOTE:
# CATEGORY 3: MULTI-MATCH COMPOSITION
# =============================================================================


def test_two_matches_in_same_entry_preserves_both_paths() -> None:
    """
    Both matching sub-structures survive — union path behavior.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11450-4"/>
            <entry>
                <act>
                    <code code="CONC"/>
                    <statusCode code="active"/>
                    <entryRelationship typeCode="SUBJ">
                        <observation><value code="MATCH_A"/></observation>
                    </entryRelationship>
                    <entryRelationship typeCode="SUBJ">
                        <observation><value code="MATCH_B"/></observation>
                    </entryRelationship>
                </act>
            </entry>
        </section>
        """
    )
    process_section(
        section=section,
        codes_to_match={"MATCH_A", "MATCH_B"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    assert _find_one(section, ".//hl7:value[@code='MATCH_A']") is not None
    assert _find_one(section, ".//hl7:value[@code='MATCH_B']") is not None
    assert len(section.xpath(".//hl7:entryRelationship", namespaces=HL7_NS)) == 2


def test_nonmatching_entry_removed_matching_entry_kept() -> None:
    """
    Generic matching prunes at the ENTRY level only — entire non-matching
    entries are removed. Sub-trees within a surviving entry are NOT pruned.

    Two entries: one matches, one does not. The matching entry survives
    intact; the non-matching entry is removed entirely.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11450-4"/>
            <entry>
                <observation><value code="MATCH"/></observation>
            </entry>
            <entry>
                <observation><value code="OTHER"/></observation>
            </entry>
        </section>
        """
    )
    process_section(
        section=section,
        codes_to_match={"MATCH"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    assert _find_one(section, ".//hl7:value[@code='MATCH']") is not None
    assert _find_one(section, ".//hl7:value[@code='OTHER']") is None
    assert len(section.findall("{urn:hl7-org:v3}entry")) == 1


# NOTE:
# CATEGORY 4: PROVENANCE COMMENTS
# =============================================================================


def test_generic_match_comment_injected_above_surviving_entry() -> None:
    """
    After matching, a 'generic match' provenance comment is injected
    immediately before each surviving entry, identifying the matched code.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry><observation><value code="MATCH"/></observation></entry>
        </section>
        """
    )
    process_section(
        section=section,
        codes_to_match={"MATCH"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    comments = _get_refiner_comments(section)
    assert len(comments) == 1
    assert "generic match" in comments[0]
    assert "MATCH" in comments[0]


def test_source_comments_stripped_before_matching() -> None:
    """
    Pre-existing eCR Refiner comments are stripped at STEP 1.
    Output contains only the new comment from this run.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <!--eCR Refiner: generic match — value[OLDCODE] "" at observation/value-->
            <entry><observation><value code="MATCH"/></observation></entry>
        </section>
        """
    )
    process_section(
        section=section,
        codes_to_match={"MATCH"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    comments = _get_refiner_comments(section)
    assert len(comments) == 1
    assert "OLDCODE" not in comments[0]
    assert "MATCH" in comments[0]


# NOTE:
# CATEGORY 5: REAL-FIXTURE INTEGRATION
# =============================================================================


def test_real_v1_1_results_section_matches_loinc(
    structured_body_v1_1: _Element,
) -> None:
    """
    Known LOINC code found in real v1.1 Results fixture; section not stubbed.
    """

    results = get_section_by_code(structured_body_v1_1, "30954-2")
    assert results is not None

    process_section(
        section=results,
        codes_to_match={"94533-7"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    assert results.get("nullFlavor") != "NI"
    assert len(results.xpath(".//hl7:code[@code='94533-7']", namespaces=HL7_NS)) > 0


def test_real_v1_1_results_section_nomatch_stubs(
    structured_body_v1_1: _Element,
) -> None:
    """
    Absent code on real fixture stubs the Results section.
    """

    results = get_section_by_code(structured_body_v1_1, "30954-2")
    assert results is not None

    process_section(
        section=results,
        codes_to_match={"99999-9"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    assert results.get("nullFlavor") == "NI"


# NOTE:
# CATEGORY 6: INTERNAL HELPER UNIT TESTS
# =============================================================================


def test_find_path_to_entry_returns_enclosing_entry() -> None:
    """
    _find_path_to_entry walks up from a deep element and returns the
    nearest <entry> ancestor. Core to the entry-preservation mapping.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11450-4"/>
            <entry>
                <act>
                    <entryRelationship>
                        <observation>
                            <value code="DEEP"/>
                        </observation>
                    </entryRelationship>
                </act>
            </entry>
        </section>
        """
    )
    entry = _find_one(section, "hl7:entry")
    deep = _find_one(section, ".//hl7:value[@code='DEEP']")
    assert entry is not None and deep is not None
    assert _find_path_to_entry(deep) is entry
