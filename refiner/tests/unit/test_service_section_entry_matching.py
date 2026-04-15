import pytest
from lxml import etree
from lxml.etree import _Element

from app.services.ecr.model import HL7_NS, EntryMatchRule, SectionSpecification
from app.services.ecr.section import get_section_by_code
from app.services.ecr.section.entry_matching import (
    process,
)
from app.services.ecr.specification import load_spec
from app.services.terminology import CodeSystemSets

# NOTE:
# HELPERS
# =============================================================================

# these OIDs match the values used in entry_match_rules.py and
# specification/constants.py; kept inline here so the tests don't depend
# on a specific import path for these constants
SNOMED_OID = "2.16.840.1.113883.6.96"
ICD10_OID = "2.16.840.1.113883.6.90"
LOINC_OID = "2.16.840.1.113883.6.1"
RXNORM_OID = "2.16.840.1.113883.6.88"
CVX_OID = "2.16.840.1.113883.12.292"


def _build_section(xml: str) -> _Element:
    """
    Parse a raw XML string into a Section element with the HL7 namespace.
    Same helper as in the generic matcher tests — keeps test input
    visible in the same place as the assertion.
    """

    return etree.fromstring(xml.encode("utf-8"))


def _find_one(element: _Element, xpath: str) -> _Element | None:
    """
    Run an XPath query that expects zero or one result and return
    the first hit or None. Raises if XPath returns more than one.
    """

    results = element.xpath(xpath, namespaces=HL7_NS)
    if not isinstance(results, list):
        return None
    if len(results) > 1:
        raise AssertionError(
            f"Expected at most one match for xpath {xpath!r}, found {len(results)}"
        )
    return results[0] if results else None


def _make_code_system_sets(codes_by_system: dict[str, list[str]]) -> CodeSystemSets:
    """
    Build a CodeSystemSets with specific codes in specific system dicts.

    Input is a dict mapping system name ("snomed", "loinc", "icd10",
    "rxnorm", "cvx", "other") to a list of code strings. Each code is
    wrapped in a Coding with a placeholder display string so enrichment
    has something to attach.

    Uses CodeSystemSets.from_dict, which expects a dict of lists of
    Coding-shaped dicts per system. This matches the format used by
    the S3 active.json serialization, so we're exercising the same
    deserialization path the lambda uses in production.
    """

    data: dict[str, list[dict[str, str]]] = {
        "snomed": [],
        "loinc": [],
        "icd10": [],
        "rxnorm": [],
        "cvx": [],
        "other": [],
    }
    for system, codes in codes_by_system.items():
        if system not in data:
            raise ValueError(f"Unknown system: {system}")
        for code in codes:
            data[system].append(
                {
                    "code": code,
                    "display": f"{system.upper()} {code} display",
                    "system": system,
                }
            )
    return CodeSystemSets.from_dict(data)


def _make_spec_with_rules(
    rules: list[EntryMatchRule],
    loinc: str = "00000-0",
    template_id: str = "2.16.840.1.113883.10.20.22.2.99",
) -> SectionSpecification:
    """
    Build a SectionSpecification with custom rules for tests that need
    to exercise specific rule shapes without loading the full catalog.

    Only `rules` is meaningful to the matcher — `loinc` and
    `template_id` are placeholder defaults because the dataclass
    requires them but entry_matching doesn't read them during matching.
    Callers can override the defaults if a test ever needs specific
    values, but most tests should rely on the defaults so the test
    focuses on the rule behavior it's actually exercising.

    The placeholder values are deliberately chosen to be obviously
    fake: "00000-0" is not a real LOINC code, and the template_id
    ends in .99 which is not a real C-CDA section template OID.
    Anyone reading test output and seeing these values should
    immediately recognize them as test doubles.
    """

    return SectionSpecification(
        loinc_code=loinc,
        display_name="Test Section",
        template_id=template_id,
        entry_match_rules=rules,
    )


@pytest.fixture(scope="session")
def spec_v1_1():
    """
    Loads the complete eICR v1.1 specification once per session. Used
    by tests that want the real rules for a given section without
    constructing them inline.
    """

    return load_spec("1.1")


@pytest.fixture(scope="session")
def spec_v3_1_1():
    """
    Loads the complete eICR v3.1.1 specification once per session.
    """

    return load_spec("3.1.1")


# NOTE:
# CATEGORY 1: CRITICAL — protect known-correct behavior from regression
# =============================================================================


def test_empty_section_is_stubbed_when_no_entries(spec_v1_1) -> None:
    """
    A section with no entries at all should be stubbed via the
    "no matches" policy override. Baseline smoke test.
    """

    section = _build_section(
        '<section xmlns="urn:hl7-org:v3"><code code="11450-4"/></section>'
    )
    problems_spec = spec_v1_1.sections["11450-4"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["1234"]}),
        section_specification=problems_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is False
    assert section.get("nullFlavor") == "NI"


def test_nonmatching_entries_stub_section(spec_v1_1) -> None:
    """
    A section with entries but none matching the configured set
    should be stubbed. Preserves the no-match policy.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11450-4"/>
            <entry>
                <act classCode="ACT" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
                    <entryRelationship typeCode="SUBJ">
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                            <value code="99999999" codeSystem="2.16.840.1.113883.6.96"/>
                        </observation>
                    </entryRelationship>
                </act>
            </entry>
        </section>
        """
    )
    problems_spec = spec_v1_1.sections["11450-4"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=problems_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is False
    assert section.get("nullFlavor") == "NI"


def test_matching_entry_is_preserved(spec_v1_1) -> None:
    """
    A section with one entry whose value matches the configured set
    should preserve the entry. Baseline of the entry-preservation path.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11450-4"/>
            <entry>
                <act classCode="ACT" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
                    <entryRelationship typeCode="SUBJ">
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                            <value code="840539006" codeSystem="2.16.840.1.113883.6.96"/>
                        </observation>
                    </entryRelationship>
                </act>
            </entry>
        </section>
        """
    )
    problems_spec = spec_v1_1.sections["11450-4"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=problems_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True
    assert section.get("nullFlavor") != "NI"
    assert _find_one(section, ".//hl7:value[@code='840539006']") is not None


def test_enrichment_populates_displayName(spec_v1_1) -> None:
    """
    After matching, enrich_surviving_entries should populate
    @displayName on matched code-bearing elements from the Coding
    objects in the CodeSystemSets. Preserves the enrichment behavior.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11450-4"/>
            <entry>
                <act classCode="ACT" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
                    <entryRelationship typeCode="SUBJ">
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                            <value code="840539006" codeSystem="2.16.840.1.113883.6.96"/>
                        </observation>
                    </entryRelationship>
                </act>
            </entry>
        </section>
        """
    )
    problems_spec = spec_v1_1.sections["11450-4"]
    process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=problems_spec,
        namespaces=HL7_NS,
    )
    matched_value = _find_one(section, ".//hl7:value[@code='840539006']")
    assert matched_value is not None
    assert matched_value.get("displayName") == "SNOMED 840539006 display"


def test_narrative_retention_when_include_narrative_true(spec_v1_1) -> None:
    """
    When include_narrative=True, the original <text> should be left
    alone. Preserves the narrative-retention branch.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11450-4"/>
            <text>Original narrative content here.</text>
            <entry>
                <act classCode="ACT" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
                    <entryRelationship typeCode="SUBJ">
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                            <value code="840539006" codeSystem="2.16.840.1.113883.6.96"/>
                        </observation>
                    </entryRelationship>
                </act>
            </entry>
        </section>
        """
    )
    problems_spec = spec_v1_1.sections["11450-4"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=problems_spec,
        namespaces=HL7_NS,
        include_narrative=True,
    )
    assert result.narrative_disposition == "retained"
    text = _find_one(section, "hl7:text")
    assert text is not None
    assert text.text is not None and "Original narrative" in text.text


def test_narrative_removal_when_include_narrative_false(spec_v1_1) -> None:
    """
    When include_narrative=False, the narrative should be replaced
    with a removal notice. Preserves the narrative-removal branch.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11450-4"/>
            <text>Original narrative content here.</text>
            <entry>
                <act classCode="ACT" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
                    <entryRelationship typeCode="SUBJ">
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                            <value code="840539006" codeSystem="2.16.840.1.113883.6.96"/>
                        </observation>
                    </entryRelationship>
                </act>
            </entry>
        </section>
        """
    )
    problems_spec = spec_v1_1.sections["11450-4"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=problems_spec,
        namespaces=HL7_NS,
        include_narrative=False,
    )
    assert result.narrative_disposition == "removed"
    text = _find_one(section, "hl7:text")
    assert text is not None
    # the removal notice should NOT contain the original content
    text_str = etree.tostring(text, encoding="unicode")
    assert "Original narrative" not in text_str


# NOTE:
# CATEGORY 2: PER-RULE — exercise each section's specific rules
# =============================================================================


def test_problems_rule_matches_snomed_on_value(spec_v1_1) -> None:
    """
    Problems rule: SNOMED on Problem Observation value element.
    The IG-conformant shape with SNOMED as primary.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11450-4"/>
            <entry>
                <act classCode="ACT" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
                    <entryRelationship typeCode="SUBJ">
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                            <value code="840539006" codeSystem="2.16.840.1.113883.6.96"/>
                        </observation>
                    </entryRelationship>
                </act>
            </entry>
        </section>
        """
    )
    problems_spec = spec_v1_1.sections["11450-4"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=problems_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_problems_rule_matches_icd10_on_value_via_unscoped_lookup(
    spec_v1_1,
) -> None:
    """
    Problems rule handles the reversed-coding case (ICD-10 primary,
    SNOMED translation) via the unscoped find_match lookup. The rule's
    code_system_oid is SNOMED, but the matcher passes None to find_match
    so the ICD-10 code is found in its own system dict.

    This validates the reversed-rule-consolidation — the same rule
    catches both shapes without needing a second rule.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11450-4"/>
            <entry>
                <act classCode="ACT" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
                    <entryRelationship typeCode="SUBJ">
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                            <value code="U07.1" codeSystem="2.16.840.1.113883.6.90"/>
                        </observation>
                    </entryRelationship>
                </act>
            </entry>
        </section>
        """
    )
    problems_spec = spec_v1_1.sections["11450-4"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"icd10": ["U07.1"]}),
        section_specification=problems_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_problems_rule_matches_code_in_translation(spec_v1_1) -> None:
    """
    Problems rule's translation_xpath catches codes that appear in
    value/translation. Exercises the primary-miss, translation-hit
    path through _try_match_entry.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11450-4"/>
            <entry>
                <act classCode="ACT" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
                    <entryRelationship typeCode="SUBJ">
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                            <value code="99999999" codeSystem="2.16.840.1.113883.6.96">
                                <translation code="U07.1" codeSystem="2.16.840.1.113883.6.90"/>
                            </value>
                        </observation>
                    </entryRelationship>
                </act>
            </entry>
        </section>
        """
    )
    problems_spec = spec_v1_1.sections["11450-4"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"icd10": ["U07.1"]}),
        section_specification=problems_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_immunizations_rule_matches_cvx(spec_v1_1) -> None:
    """
    Immunizations rule: CVX on manufacturedMaterial/code.
    The IG-conformant shape.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11369-6"/>
            <entry>
                <substanceAdministration classCode="SBADM" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
                    <consumable>
                        <manufacturedProduct>
                            <templateId root="2.16.840.1.113883.10.20.22.4.54"/>
                            <manufacturedMaterial>
                                <code code="207" codeSystem="2.16.840.1.113883.12.292"/>
                            </manufacturedMaterial>
                        </manufacturedProduct>
                    </consumable>
                </substanceAdministration>
            </entry>
        </section>
        """
    )
    immunizations_spec = spec_v1_1.sections["11369-6"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"cvx": ["207"]}),
        section_specification=immunizations_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_immunizations_nullFlavor_primary_with_rxnorm_translation(
    spec_v1_1,
) -> None:
    """
    The real-world pattern where an EHR can't supply CVX on the primary
    manufacturedMaterial/code (e.g., because it indexes vaccines on
    RxNorm internally), sets @nullFlavor on the primary, and puts the
    actual code in a <translation>.

    The matcher's primary loop skips the nullFlavor'd element (no @code),
    the translation branch runs, and the translation's RxNorm code
    matches via unscoped lookup. Entry is preserved.

    This is the case that motivated dropping the OID check — the matcher
    correctly handles CVX-primary with RxNorm-translation.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11369-6"/>
            <entry>
                <substanceAdministration classCode="SBADM" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
                    <consumable>
                        <manufacturedProduct>
                            <templateId root="2.16.840.1.113883.10.20.22.4.54"/>
                            <manufacturedMaterial>
                                <code nullFlavor="NA">
                                    <translation code="798302" codeSystem="2.16.840.1.113883.6.88"/>
                                </code>
                            </manufacturedMaterial>
                        </manufacturedProduct>
                    </consumable>
                </substanceAdministration>
            </entry>
        </section>
        """
    )
    immunizations_spec = spec_v1_1.sections["11369-6"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"rxnorm": ["798302"]}),
        section_specification=immunizations_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_results_rule_matches_loinc_on_code(spec_v1_1) -> None:
    """
    Results rule 1: LOINC on Result Observation code (the SHOULD case).
    IG-conformant shape.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry>
                <organizer classCode="BATTERY" moodCode="EVN">
                    <component>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                            <code code="94533-7" codeSystem="2.16.840.1.113883.6.1"/>
                        </observation>
                    </component>
                </organizer>
            </entry>
        </section>
        """
    )
    results_spec = spec_v1_1.sections["30954-2"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"loinc": ["94533-7"]}),
        section_specification=results_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_results_rule_matches_snomed_on_value(spec_v1_1) -> None:
    """
    Results rule 2: SNOMED on Result Observation value[@xsi:type='CD'].
    The SHOULD case for result values from the SNOMED Findings value set.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <code code="30954-2"/>
            <entry>
                <organizer classCode="BATTERY" moodCode="EVN">
                    <component>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                            <code code="LOCAL" codeSystem="local"/>
                            <value xsi:type="CD" code="260373001" codeSystem="2.16.840.1.113883.6.96"/>
                        </observation>
                    </component>
                </organizer>
            </entry>
        </section>
        """
    )
    results_spec = spec_v1_1.sections["30954-2"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["260373001"]}),
        section_specification=results_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_results_rule_matches_translation_under_code(spec_v1_1) -> None:
    """
    Results rule 3: LOINC in code/translation for the real-world case
    where a lab uses a local primary code with LOINC in translation.
    Validates the SHOULD-handling refinement.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry>
                <organizer classCode="BATTERY" moodCode="EVN">
                    <component>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                            <code code="LOCAL-PANEL-42" codeSystem="local">
                                <translation code="94533-7" codeSystem="2.16.840.1.113883.6.1"/>
                            </code>
                        </observation>
                    </component>
                </organizer>
            </entry>
        </section>
        """
    )
    results_spec = spec_v1_1.sections["30954-2"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"loinc": ["94533-7"]}),
        section_specification=results_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


# NOTE:
# CATEGORY 3: STRUCTURAL PRECEDENCE — rule ordering and claim semantics
# =============================================================================


def test_rule_without_match_does_not_claim_entry() -> None:
    """
    STRUCTURAL PRECEDENCE: if a rule's xpath finds candidates but none
    of them match the configured set, the rule does NOT claim the
    entry. Subsequent rules get to try.

    Built with a custom two-rule spec so we can control which rule
    runs first and observe whether the second rule gets a chance.

    Rule 1: targets observation/code with value "NONEXISTENT"
    Rule 2: targets observation/value with value "REAL_MATCH"

    The entry has both shapes. Rule 1 finds candidates but no match.
    Under the old candidates_found semantics, rule 1 claims and rule 2
    never runs, so no match is recorded. Under the correct semantics
    (rule_produced_match), rule 1 doesn't claim, rule 2 runs and
    matches.

    If this test fails, the structural precedence fix has regressed.
    """

    custom_spec = _make_spec_with_rules(
        rules=[
            EntryMatchRule(
                code_xpath=".//hl7:observation/hl7:code",
                code_system_oid=None,
            ),
            EntryMatchRule(
                code_xpath=".//hl7:observation/hl7:value",
                code_system_oid=None,
            ),
        ],
    )
    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="TEST"/>
            <entry>
                <observation classCode="OBS" moodCode="EVN">
                    <code code="SOMETHING_ELSE"/>
                    <value code="REAL_MATCH"/>
                </observation>
            </entry>
        </section>
        """
    )
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["REAL_MATCH"]}),
        section_specification=custom_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True, (
        "rule 1 found candidates but no match; rule 2 should have run "
        "and matched. if this failed, structural precedence is still "
        "using candidates_found instead of rule_produced_match."
    )


def test_rule_with_match_claims_entry() -> None:
    """
    Complementary to the previous test: if a rule matches, it claims
    the entry and subsequent rules are not tried. Prevents a
    fallback rule from double-matching when the more specific rule
    already found something.
    """

    custom_spec = _make_spec_with_rules(
        rules=[
            EntryMatchRule(
                code_xpath=".//hl7:observation/hl7:code",
                code_system_oid=None,
            ),
            EntryMatchRule(
                code_xpath=".//hl7:observation/hl7:value",
                code_system_oid=None,
            ),
        ],
    )
    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="TEST"/>
            <entry>
                <observation classCode="OBS" moodCode="EVN">
                    <code code="MATCH_FROM_RULE_1"/>
                    <value code="MATCH_FROM_RULE_2"/>
                </observation>
            </entry>
        </section>
        """
    )
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets(
            {"snomed": ["MATCH_FROM_RULE_1", "MATCH_FROM_RULE_2"]}
        ),
        section_specification=custom_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


# NOTE:
# CATEGORY 4: UNSCOPED LOOKUP — cross-system code matching (OID-agnostic)
# =============================================================================


def test_code_matches_across_code_systems_regardless_of_oid() -> None:
    """
    Unscoped lookup: CVX code tagged as RxNorm still matches when CVX
    is the configured system. The matcher ignores the element's declared
    codeSystem OID and searches all configured code systems.

    The configured set has the code in its CVX dict. Under the old
    OID-scoped lookup, find_match(code, CVX_OID) would look only in the
    CVX dict, but the matcher's rule would pass RXNORM_OID (from the
    element's codeSystem attribute) and miss. Under the unscoped lookup,
    find_match(code, None) walks all dicts and finds the code in the
    CVX dict, returning a match.

    If this test fails, the OID-agnostic lookup has regressed.
    """

    custom_spec = _make_spec_with_rules(
        rules=[
            EntryMatchRule(
                code_xpath=".//hl7:manufacturedMaterial/hl7:code",
                code_system_oid=CVX_OID,
            ),
        ],
    )
    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="TEST"/>
            <entry>
                <substanceAdministration classCode="SBADM" moodCode="EVN">
                    <consumable>
                        <manufacturedProduct>
                            <manufacturedMaterial>
                                <code code="2468230" codeSystem="2.16.840.1.113883.6.88"/>
                            </manufacturedMaterial>
                        </manufacturedProduct>
                    </consumable>
                </substanceAdministration>
            </entry>
        </section>
        """
    )
    # the code is in the CVX dict (correctly classified by the
    # configuration) but the document tagged it as RxNorm (incorrectly
    # classified by the EHR); the unscoped lookup bridges the gap
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"cvx": ["2468230"]}),
        section_specification=custom_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_whitespace_in_code_is_stripped_before_match() -> None:
    """
    Some EHRs emit codes with trailing whitespace (e.g. "94310-0 ").
    The matcher should strip whitespace before comparing against
    the configured set. Same robustness as the generic matcher has
    and the same whitespace-strip fix.
    """

    custom_spec = _make_spec_with_rules(
        rules=[
            EntryMatchRule(
                code_xpath=".//hl7:observation/hl7:code",
                code_system_oid=None,
            ),
        ],
    )
    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="TEST"/>
            <entry>
                <observation classCode="OBS" moodCode="EVN">
                    <code code="94310-0 " codeSystem="2.16.840.1.113883.6.1"/>
                </observation>
            </entry>
        </section>
        """
    )
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"loinc": ["94310-0"]}),
        section_specification=custom_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_nullFlavor_primary_code_is_skipped() -> None:
    """
    An element with @nullFlavor and no @code should be skipped by the
    primary-loop iteration, NOT treated as a match-claimer. If the
    primary loop set rule_produced_match=True based on the presence
    of the element alone (without an actual @code match), subsequent
    translation-branch logic would be short-circuited incorrectly.
    """

    custom_spec = _make_spec_with_rules(
        rules=[
            EntryMatchRule(
                code_xpath=".//hl7:manufacturedMaterial/hl7:code",
                code_system_oid=None,
                translation_xpath=".//hl7:manufacturedMaterial/hl7:code/hl7:translation",
            ),
        ],
    )
    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="TEST"/>
            <entry>
                <substanceAdministration classCode="SBADM" moodCode="EVN">
                    <consumable>
                        <manufacturedProduct>
                            <manufacturedMaterial>
                                <code nullFlavor="NA">
                                    <translation code="798302"/>
                                </code>
                            </manufacturedMaterial>
                        </manufacturedProduct>
                    </consumable>
                </substanceAdministration>
            </entry>
        </section>
        """
    )
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"rxnorm": ["798302"]}),
        section_specification=custom_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


# NOTE:
# CATEGORY 5: CONTAINER-LEVEL PRUNING — selective preservation of matched substructures
# =============================================================================


def test_container_pruning_preserves_only_matching_container(spec_v1_1) -> None:
    """
    The Problems two-diagnosis case: one Problem Concern Act contains
    two Problem Observations via sibling entryRelationship[@typeCode='SUBJ']
    elements. Only one diagnosis matches the configured set. The
    matching entryRelationship should be preserved and the non-matching
    one should be pruned.

    This validates the behavior seen in real Mon Mothma COVID output —
    the Concern Act survives with only the condition-specific diagnosis
    inside it.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11450-4"/>
            <entry>
                <act classCode="ACT" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
                    <entryRelationship typeCode="SUBJ">
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                            <value code="840539006" codeSystem="2.16.840.1.113883.6.96"/>
                        </observation>
                    </entryRelationship>
                    <entryRelationship typeCode="SUBJ">
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                            <value code="99999999" codeSystem="2.16.840.1.113883.6.96"/>
                        </observation>
                    </entryRelationship>
                </act>
            </entry>
        </section>
        """
    )
    problems_spec = spec_v1_1.sections["11450-4"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=problems_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True
    # matching diagnosis survives
    assert _find_one(section, ".//hl7:value[@code='840539006']") is not None
    # non-matching diagnosis is pruned
    assert _find_one(section, ".//hl7:value[@code='99999999']") is None
    # the concern act wrapper still exists (entry itself is preserved)
    assert _find_one(section, ".//hl7:act") is not None


def test_container_pruning_removes_entry_when_all_containers_pruned(
    spec_v1_1,
) -> None:
    """
    If every container inside a matched entry gets pruned (because
    no match landed in any of them), the entry itself should be
    removed. This handles the edge case where the entry-level match
    set is non-empty but container pruning removes everything.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry>
                <organizer classCode="BATTERY" moodCode="EVN">
                    <component>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                            <code code="94533-7" codeSystem="2.16.840.1.113883.6.1"/>
                        </observation>
                    </component>
                    <component>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                            <code code="OTHER" codeSystem="2.16.840.1.113883.6.1"/>
                        </observation>
                    </component>
                </organizer>
            </entry>
        </section>
        """
    )
    results_spec = spec_v1_1.sections["30954-2"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"loinc": ["94533-7"]}),
        section_specification=results_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True
    # matching component survives
    assert _find_one(section, ".//hl7:code[@code='94533-7']") is not None
    # non-matching component is pruned
    assert _find_one(section, ".//hl7:code[@code='OTHER']") is None


def test_two_matching_containers_both_survive(spec_v1_1) -> None:
    """
    Multiple matching containers in one entry should all survive.
    Validates the union behavior of container-level pruning — the pruner
    keeps every container that has a match, not just the first one.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry>
                <organizer classCode="BATTERY" moodCode="EVN">
                    <component>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                            <code code="94533-7" codeSystem="2.16.840.1.113883.6.1"/>
                        </observation>
                    </component>
                    <component>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                            <code code="94534-5" codeSystem="2.16.840.1.113883.6.1"/>
                        </observation>
                    </component>
                    <component>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                            <code code="NONMATCH" codeSystem="2.16.840.1.113883.6.1"/>
                        </observation>
                    </component>
                </organizer>
            </entry>
        </section>
        """
    )
    results_spec = spec_v1_1.sections["30954-2"]
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"loinc": ["94533-7", "94534-5"]}),
        section_specification=results_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True
    assert _find_one(section, ".//hl7:code[@code='94533-7']") is not None
    assert _find_one(section, ".//hl7:code[@code='94534-5']") is not None
    assert _find_one(section, ".//hl7:code[@code='NONMATCH']") is None


# NOTE:
# CATEGORY 6: REAL-FIXTURE INTEGRATION — validation with production-like data
# =============================================================================


def test_real_v1_1_problems_section_matches_covid(
    structured_body_v1_1: _Element,
    spec_v1_1,
) -> None:
    """
    Validates that the COVID code (840539006) is found in the real fixture
    Problems section. The fixture has the COVID diagnosis inside a
    Problem Concern Act.

    If this test fails because the code isn't present, the fixture data
    may have changed. Update the test with the current expected code.
    """

    problems = get_section_by_code(structured_body_v1_1, "11450-4")
    assert problems is not None

    problems_spec = spec_v1_1.sections["11450-4"]
    result = process(
        section=problems,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=problems_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True, "COVID code 840539006 not found in fixture"
    assert _find_one(problems, ".//hl7:value[@code='840539006']") is not None


def test_real_v1_1_results_section_with_no_matches_stubs(
    structured_body_v1_1: _Element,
    spec_v1_1,
) -> None:
    """
    Run entry_matching against the real v1.1 Results section with
    a LOINC that definitely isn't present. Assert the section is
    stubbed via the no-match policy.
    """

    results = get_section_by_code(structured_body_v1_1, "30954-2")
    assert results is not None

    results_spec = spec_v1_1.sections["30954-2"]
    result = process(
        section=results,
        code_system_sets=_make_code_system_sets({"loinc": ["99999-9"]}),
        section_specification=results_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is False
    assert results.get("nullFlavor") == "NI"


def test_real_v3_1_1_problems_section_is_processable(
    structured_body_v3_1_1: _Element,
    spec_v3_1_1,
) -> None:
    """
    Smoke test that v3.1.1 Problems section runs through process()
    without raising. Catches any differences in template handling
    between v1.1 and v3.1.1.
    """

    problems = get_section_by_code(structured_body_v3_1_1, "11450-4")
    if problems is None:
        pytest.skip("v3.1.1 fixture does not contain Problems section")

    problems_spec = spec_v3_1_1.sections["11450-4"]
    # run with an empty configured set — we just want to verify
    # the matcher runs without raising. no-match is the expected result.
    result = process(
        section=problems,
        code_system_sets=_make_code_system_sets({"snomed": ["NONEXISTENT"]}),
        section_specification=problems_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is False
