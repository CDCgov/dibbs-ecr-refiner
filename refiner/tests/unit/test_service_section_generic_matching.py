from lxml import etree
from lxml.etree import _Element

from app.services.ecr.model import HL7_NS
from app.services.ecr.section import get_section_by_code, process_section
from app.services.ecr.section.generic_matching import (
    _find_enclosing_entry,
    _is_mechanics_element,
    _path_from_entry,
    _prune_entry_to_match_paths,
)

# NOTE:
# HELPERS
# =============================================================================


def _build_section(xml: str) -> _Element:
    """
    Parse a raw XML string into a Section element with the HL7 namespace.

    The input string must be a <section> element (or something that
    contains one at its root). The HL7 namespace is applied by the
    caller's xmlns attribute in the input string.

    Returns the parsed section element, ready to be passed to
    process_section.
    """

    return etree.fromstring(xml.encode("utf-8"))


def _local_names_in_order(element: _Element) -> list[str]:
    """
    Walk an element depth-first and return local names of all descendants
    in document order, skipping comments and processing instructions.

    Useful for snapshot-style assertions where we want to say "after
    pruning, the surviving tree should have exactly these elements in
    this order."
    """

    names: list[str] = []
    for el in element.iter():
        if isinstance(el.tag, str):
            names.append(etree.QName(el.tag).localname)
    return names


def _find_one(element: _Element, xpath: str) -> _Element | None:
    """
    Run an XPath query that expects zero or one result and return the
    first hit or None. Raises if XPath returns more than one element,
    which would indicate a bug in the test.
    """

    results = element.xpath(xpath, namespaces=HL7_NS)
    if not isinstance(results, list):
        return None
    if len(results) > 1:
        raise AssertionError(
            f"Expected at most one match for xpath {xpath!r}, found {len(results)}"
        )
    return results[0] if results else None


# NOTE:
# CATEGORY 1: CRITICAL — protect known-correct behavior from regression
# =============================================================================


def test_empty_section_is_stubbed() -> None:
    """
    A section with no entries, when processed with any codes_to_match, should be stubbed with nullFlavor="NI".

    This protects the empty-section short-circuit path. If this test ever
    fails, the matcher has started processing empty sections differently
    than it used to.
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
    A section with real entries, but called with codes_to_match=set(),
    should be stubbed. The no-codes case is the "no configuration"
    guard and the matcher should never preserve content without a
    configured code set.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry>
                <observation>
                    <code code="12345"/>
                </observation>
            </entry>
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
    A section with one entry whose observation/code matches the
    configured set should preserve the entry. Baseline smoke test of
    the "entry with a match survives" path.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry>
                <observation>
                    <code code="MATCH"/>
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
    assert section.get("nullFlavor") != "NI"
    assert _find_one(section, ".//hl7:observation/hl7:code[@code='MATCH']") is not None


def test_nonmatching_code_removes_entry_and_stubs_section() -> None:
    """
    A section whose only entry does not match the configured set
    should have the entry removed and the section stubbed (since
    all entries were pruned, there are no matches at all).
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry>
                <observation>
                    <code code="NOMATCH"/>
                </observation>
            </entry>
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
    The section's own <code> element carries its LOINC identifier, not
    clinical content. Even if a configured code happens to collide with
    the section LOINC, the section's own code should not produce a
    match — it's neutralized during processing so the matcher can't
    see it.

    This protects against false positives where the section LOINC
    happens to appear in a configuration.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry>
                <observation>
                    <code code="NOMATCH"/>
                </observation>
            </entry>
        </section>
        """
    )
    process_section(
        section=section,
        codes_to_match={"30954-2"},  # the section's own loinc
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    # the entry had no matching clinical content, so the section is stubbed
    assert section.get("nullFlavor") == "NI"


def test_cluster_preservation_keeps_sibling_code_when_value_matches() -> None:
    """
    An observation has <code> and <value> as a coding cluster. If the
    match lands on <value>, the sibling <code> should come along via
    cluster preservation so the observation's clinical meaning is
    retained in the output.
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
    # both the matched <value> and its sibling <code> should be preserved
    assert (
        _find_one(section, ".//hl7:observation/hl7:code[@code='TESTCODE']") is not None
    )
    assert _find_one(section, ".//hl7:observation/hl7:value[@code='MATCH']") is not None


def test_cluster_preservation_keeps_sibling_value_when_code_matches() -> None:
    """
    Mirror of the previous test: match on <code>, sibling <value>
    should come along. Cluster preservation should be symmetric
    between code and value.
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


def test_whitespace_in_code_attribute_is_stripped() -> None:
    """
    Some EHRs emit codes with trailing whitespace (e.g. "94310-0 ").
    The matcher should strip whitespace before comparing against the
    configured set so these codes still match. This is the same
    robustness that entry_matching has.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry>
                <observation>
                    <code code="94310-0 "/>
                </observation>
            </entry>
        </section>
        """
    )
    process_section(
        section=section,
        codes_to_match={"94310-0"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )
    assert section.get("nullFlavor") != "NI"


# NOTE:
# CATEGORY 2: MECHANICS EXCLUSION — administrative elements don't trigger matches
# =============================================================================


def test_mechanics_exclusion_ignores_methodCode_matches() -> None:
    """
    Administrative element methodCode does NOT trigger entry preservation.
    A match landing directly on a <methodCode> element's @code should be
    excluded because methodCode is in _EXCLUDED_LOCAL_NAMES.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="47519-4"/>
            <entry>
                <procedure>
                    <code code="PROC"/>
                    <methodCode code="MATCH"/>
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
    # the methodCode match should not count; no other matches; section stubbed
    assert section.get("nullFlavor") == "NI"


def test_mechanics_exclusion_ignores_codes_under_participantRole() -> None:
    """
    Codes nested under participantRole are excluded from matching.
    A <code> element whose parent is <participantRole> should be excluded
    because participantRole is in _EXCLUDED_LOCAL_NAMES and the exclusion
    check walks the parent.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="47519-4"/>
            <entry>
                <procedure>
                    <code code="PROC"/>
                    <participant>
                        <participantRole>
                            <code code="MATCH"/>
                        </participantRole>
                    </participant>
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
    # the match was inside participantRole, which is mechanics; excluded
    assert section.get("nullFlavor") == "NI"


def test_deep_match_under_participant_is_excluded_transitively() -> None:
    """
    Matches deep under participant (participant>participantRole>playingEntity>code)
    are excluded via transitive ancestor checking. The entire administrative chain
    is pruned, not just the immediate parent.

    The match is on playingEntity/code. Its immediate parent is playingEntity,
    which is NOT in _EXCLUDED_LOCAL_NAMES (only playingDevice is). Under simple
    immediate-parent exclusion this would slip through. Transitive ancestor
    checking correctly excludes it.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="47519-4"/>
            <entry>
                <procedure>
                    <code code="PROC"/>
                    <participant>
                        <participantRole>
                            <playingEntity>
                                <code code="MATCH"/>
                            </playingEntity>
                        </participantRole>
                    </participant>
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
    # transitive exclusion: section is stubbed because the only match was
    # inside an administrative container chain
    assert section.get("nullFlavor") == "NI", (
        "match landed deep inside participant; transitive exclusion should "
        "prune the entire administrative chain"
    )


def test_match_inside_specimen_container_is_excluded() -> None:
    """
    Matches under specimen > specimenRole > specimenPlayingEntity are excluded.
    This validates that administrative specimen containers don't trigger
    preservation.

    Note: The <given> element is not code-bearing in the matcher's sense
    (the matcher only looks at <code>, <value>, <translation>), so this
    test documents that behavior rather than testing exclusion transitivity.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="47519-4"/>
            <entry>
                <procedure>
                    <code code="PROC"/>
                    <specimen>
                        <specimenRole>
                            <specimenPlayingEntity>
                                <name>
                                    <given code="MATCH"/>
                                </name>
                            </specimenPlayingEntity>
                        </specimenRole>
                    </specimen>
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
    # <given> elements are not code-bearing, so no match should be found
    assert section.get("nullFlavor") == "NI"


# NOTE:
# CATEGORY 3: STRUCTURAL METADATA PRESERVATION — required CDA elements survive pruning
# =============================================================================
#
# these tests validate that path-based pruning retains structurally-required
# children of preserved ancestors (statusCode, effectiveTime, id, etc.)
# * CDA templates require these children on every clinical statement, and a
# preserved <act> or <procedure> or <observation> that's missing them is
# invalid CDA and will fail the R2 xsl tests


def test_preserved_procedure_retains_statusCode() -> None:
    """
    CDA requires statusCode, id, and effectiveTime on procedures.
    Path-based pruning must preserve these structural metadata elements
    along with the matched code.
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
    assert section.get("nullFlavor") != "NI"
    procedure = _find_one(section, ".//hl7:procedure")
    assert procedure is not None
    assert _find_one(procedure, "hl7:id") is not None
    assert _find_one(procedure, "hl7:statusCode") is not None
    assert _find_one(procedure, "hl7:effectiveTime") is not None


def test_preserved_act_retains_statusCode() -> None:
    """
    CDA Act templates require statusCode, id, and effectiveTime.
    Validates structural metadata preservation for acts.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11450-4"/>
            <entry>
                <act>
                    <id root="xyz"/>
                    <code code="MATCH"/>
                    <statusCode code="active"/>
                    <effectiveTime value="20250101"/>
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
    act = _find_one(section, ".//hl7:act")
    assert act is not None
    assert _find_one(act, "hl7:statusCode") is not None
    assert _find_one(act, "hl7:id") is not None
    assert _find_one(act, "hl7:effectiveTime") is not None


def test_preserved_observation_retains_statusCode_and_effectiveTime() -> None:
    """
    Observations require statusCode and effectiveTime like acts and
    procedures do. Cluster preservation handles code/value/translation
    but must also preserve these structural siblings.
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


def test_preserved_entryRelationship_retains_its_child_clinical_statement() -> None:
    """
    An <entryRelationship> is a wrapper whose XSD content model requires
    at least one clinical statement child (act, observation, procedure,
    organizer, etc.). If the matcher preserves the entryRelationship
    but prunes everything inside it, the output is invalid CDA.

    This validates that when matching inside wrapped content, the wrapper
    keeps its child statement.
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
    # the entryRelationship should be present AND have its observation child
    wrapper = _find_one(section, ".//hl7:entryRelationship")
    assert wrapper is not None, "entryRelationship wrapper was pruned"
    inner_obs = _find_one(wrapper, "hl7:observation")
    assert inner_obs is not None, (
        "entryRelationship preserved as empty shell — XSD content model violated"
    )


# NOTE:
# CATEGORY 4: MULTI-MATCH COMPOSITION — multiple matches in same entry handled correctly
# =============================================================================


def test_two_matches_in_same_entry_preserves_both_paths() -> None:
    """
    When an entry has multiple matches in different sub-structures,
    the union of their paths should be preserved. Neither match should
    interfere with the other.
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
                        <observation>
                            <code code="OBS1"/>
                            <value code="MATCH_A"/>
                        </observation>
                    </entryRelationship>
                    <entryRelationship typeCode="SUBJ">
                        <observation>
                            <code code="OBS2"/>
                            <value code="MATCH_B"/>
                        </observation>
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
    # both wrapper entryRelationships should be preserved
    wrappers = section.xpath(".//hl7:entryRelationship", namespaces=HL7_NS)
    assert len(wrappers) == 2


def test_one_match_in_same_entry_prunes_other_subtree() -> None:
    """
    When an entry has multiple sub-structures but only one matches, the
    matching sub-structure is preserved and the non-matching one is
    pruned — even though both are inside the same preserved entry.

    This is the container-level pruning behavior that the two-diagnosis
    Problem Concern Act case relies on.
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
                        <observation>
                            <value code="MATCH"/>
                        </observation>
                    </entryRelationship>
                    <entryRelationship typeCode="SUBJ">
                        <observation>
                            <value code="OTHER"/>
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
    assert _find_one(section, ".//hl7:value[@code='MATCH']") is not None
    assert _find_one(section, ".//hl7:value[@code='OTHER']") is None


# NOTE:
# CATEGORY 5: REAL-FIXTURE INTEGRATION — validation with production-like data
# =============================================================================


def test_real_v1_1_results_section_matches_loinc(
    structured_body_v1_1: _Element,
) -> None:
    """
    Run the generic matcher against the real v1.1 Results section with
    a known LOINC that should be present (94533-7 based on the existing
    conftest-referenced fixture data).

    Asserts the section is not stubbed and that at least one match
    survives. This is a sanity check that real data behaves sensibly
    in the generic path.
    """

    results = get_section_by_code(structured_body_v1_1, "30954-2")
    assert results is not None, "Results section not found in v1.1 fixture"

    process_section(
        section=results,
        codes_to_match={"94533-7"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )

    assert results.get("nullFlavor") != "NI"
    matched_codes = results.xpath(".//hl7:code[@code='94533-7']", namespaces=HL7_NS)
    assert len(matched_codes) > 0


def test_real_v1_1_results_section_nomatch_stubs(
    structured_body_v1_1: _Element,
) -> None:
    """
    Run the generic matcher against the real v1.1 Results section with
    a code that definitely isn't present. Asserts the section is
    stubbed. This catches cases where the matcher incorrectly preserves
    content when it shouldn't.
    """

    results = get_section_by_code(structured_body_v1_1, "30954-2")
    assert results is not None

    # use a plausibly-looking LOINC that isn't in the fixture
    process_section(
        section=results,
        codes_to_match={"99999-9"},
        namespaces=HL7_NS,
        section_specification=None,
        code_system_sets=None,
    )

    assert results.get("nullFlavor") == "NI"


def test_real_v3_1_1_structured_body_has_sections(
    structured_body_v3_1_1: _Element,
) -> None:
    """
    Smoke test that the v3.1.1 fixture is loaded and parseable by the
    matcher's section traversal. If this fails, it's not a matcher bug,
    it's a fixture-loading problem worth catching early.
    """

    sections = structured_body_v3_1_1.xpath(".//hl7:section", namespaces=HL7_NS)
    assert len(sections) > 0


# NOTE:
# CATEGORY 6: PRUNER UNIT TESTS — direct component testing
# =============================================================================
#
# these call _prune_entry_to_match_paths directly, bypassing the process()
# entry point, so we can assert on pruner behavior without the rest of
# the matching pipeline being involved. Useful for isolating pruning bugs


def test_prune_entry_preserves_match_path_only() -> None:
    """
    Direct test of _prune_entry_to_match_paths. Given an entry with
    several children and a single match deep inside one of them, the
    pruner should preserve just the path from the match to the entry
    root and remove everything else.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry>
                <observation>
                    <code code="TARGET"/>
                    <value code="VALUE"/>
                </observation>
                <performer>
                    <assignedEntity>
                        <id root="unrelated"/>
                    </assignedEntity>
                </performer>
            </entry>
        </section>
        """
    )
    entry = _find_one(section, "hl7:entry")
    assert entry is not None
    target = _find_one(entry, ".//hl7:code[@code='TARGET']")
    assert target is not None

    _prune_entry_to_match_paths(entry, [target])

    # target and its cluster sibling value should survive
    assert _find_one(entry, ".//hl7:code[@code='TARGET']") is not None
    assert _find_one(entry, ".//hl7:value[@code='VALUE']") is not None
    # performer should be gone; it wasn't on any preserve path
    assert _find_one(entry, ".//hl7:performer") is None


def test_is_mechanics_element_direct_cases() -> None:
    """
    Direct unit test of _is_mechanics_element, independent of the
    pruning path. Builds elements whose local name or parent name is
    in the exclusion list and verifies they're identified.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="47519-4"/>
            <entry>
                <procedure>
                    <methodCode code="A"/>
                    <targetSiteCode code="B"/>
                    <participantRole>
                        <code code="C"/>
                    </participantRole>
                    <code code="CLINICAL"/>
                </procedure>
            </entry>
        </section>
        """
    )
    method_code = _find_one(section, ".//hl7:methodCode")
    target_site = _find_one(section, ".//hl7:targetSiteCode")
    role_code = _find_one(section, ".//hl7:participantRole/hl7:code")
    clinical = _find_one(section, ".//hl7:procedure/hl7:code")

    assert method_code is not None
    assert target_site is not None
    assert role_code is not None
    assert clinical is not None

    assert _is_mechanics_element(method_code) is True
    assert _is_mechanics_element(target_site) is True
    assert _is_mechanics_element(role_code) is True
    assert _is_mechanics_element(clinical) is False


def test_find_enclosing_entry_basic() -> None:
    """
    Sanity check that _find_enclosing_entry walks up to the nearest
    <entry> ancestor correctly.
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
    assert entry is not None
    assert deep is not None

    found = _find_enclosing_entry(deep)
    assert found is entry


def test_path_from_entry_builds_correct_string() -> None:
    """
    Sanity check on the _path_from_entry diagnostic helper. Confirms
    that the string representation of a match location is accurate.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="47519-4"/>
            <entry>
                <procedure>
                    <participant>
                        <participantRole>
                            <code code="HERE"/>
                        </participantRole>
                    </participant>
                </procedure>
            </entry>
        </section>
        """
    )
    entry = _find_one(section, "hl7:entry")
    code_el = _find_one(section, ".//hl7:participantRole/hl7:code")
    assert entry is not None
    assert code_el is not None

    path = _path_from_entry(code_el, entry)
    assert path == "procedure/participant/participantRole/code"
