import pytest
from lxml import etree
from lxml.etree import _Element

from app.services.ecr.model import HL7_NS, EntryMatchRule, SectionSpecification
from app.services.ecr.section import get_section_by_code
from app.services.ecr.section.entry_matching import process
from app.services.ecr.specification import load_spec
from app.services.terminology import CodeSystemSets

# NOTE:
# HELPERS
# =============================================================================

SNOMED_OID = "2.16.840.1.113883.6.96"
ICD10_OID = "2.16.840.1.113883.6.90"
LOINC_OID = "2.16.840.1.113883.6.1"
RXNORM_OID = "2.16.840.1.113883.6.88"
CVX_OID = "2.16.840.1.113883.12.292"


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


def _make_code_system_sets(codes_by_system: dict[str, list[str]]) -> CodeSystemSets:
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
    return SectionSpecification(
        loinc_code=loinc,
        display_name="Test Section",
        template_id=template_id,
        entry_match_rules=rules,
    )


@pytest.fixture(scope="session")
def spec_v1_1():
    return load_spec("1.1")


@pytest.fixture(scope="session")
def spec_v3_1_1():
    return load_spec("3.1.1")


# NOTE:
# CATEGORY 1: CRITICAL — protect known-correct behavior from regression
# =============================================================================


def test_empty_section_is_stubbed_when_no_entries(spec_v1_1) -> None:
    """
    Section with no entries at all should be stubbed.
    """

    section = _build_section(
        '<section xmlns="urn:hl7-org:v3"><code code="11450-4"/></section>'
    )
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["1234"]}),
        section_specification=spec_v1_1.sections["11450-4"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is False
    assert section.get("nullFlavor") == "NI"


def test_nonmatching_entries_stub_section(spec_v1_1) -> None:
    """
    Entries that don't match the configured set should cause stubbing.
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
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=spec_v1_1.sections["11450-4"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is False
    assert section.get("nullFlavor") == "NI"


def test_matching_entry_is_preserved(spec_v1_1) -> None:
    """
    Matching entry survives; section is not stubbed.
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
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=spec_v1_1.sections["11450-4"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True
    assert section.get("nullFlavor") != "NI"
    assert _find_one(section, ".//hl7:value[@code='840539006']") is not None


def test_enrichment_populates_displayName(spec_v1_1) -> None:
    """
    After matching, displayName is populated from the CodeSystemSets.
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
    process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=spec_v1_1.sections["11450-4"],
        namespaces=HL7_NS,
    )
    val = _find_one(section, ".//hl7:value[@code='840539006']")
    assert val is not None
    assert val.get("displayName") == "SNOMED 840539006 display"


def test_narrative_retention_when_include_narrative_true(spec_v1_1) -> None:
    """
    include_narrative=True leaves the original <text> intact.
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
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=spec_v1_1.sections["11450-4"],
        namespaces=HL7_NS,
        include_narrative=True,
    )
    assert result.narrative_disposition == "retained"
    text = _find_one(section, "hl7:text")
    assert text is not None and "Original narrative" in (text.text or "")


def test_narrative_removal_when_include_narrative_false(spec_v1_1) -> None:
    """
    include_narrative=False replaces the narrative with a removal notice.
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
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=spec_v1_1.sections["11450-4"],
        namespaces=HL7_NS,
        include_narrative=False,
    )
    assert result.narrative_disposition == "removed"
    text = _find_one(section, "hl7:text")
    assert text is not None
    assert "Original narrative" not in etree.tostring(text, encoding="unicode")


# NOTE:
# CATEGORY 2: PER-RULE — exercise each section's specific rules
# =============================================================================


def test_problems_rule_matches_snomed_on_value(spec_v1_1) -> None:
    """
    Problems T1: SNOMED code on Problem Observation value (CONF:1098-31526).
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
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=spec_v1_1.sections["11450-4"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_problems_icd10_primary_is_blocked_by_t1_structural_precedence(
    spec_v1_1,
) -> None:
    """
    Structural precedence means the T1 rule (SNOMED) claims the entry as
    soon as it finds the Problem Observation value element — regardless
    of the actual code system on that element. The T3 heuristic (ICD-10)
    rule is never evaluated.

    An entry with ICD-10 as primary does NOT match unless the ICD-10 code
    has also been placed in the SNOMED dict (cross-system match via the
    configured code set). This is the correct behavior — it prevents T3
    from silently overriding T1's structural claim.
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
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"icd10": ["U07.1"]}),
        section_specification=spec_v1_1.sections["11450-4"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is False


def test_problems_rule_matches_code_in_translation(spec_v1_1) -> None:
    """
    Problems translation path: configured ICD-10 code in value/translation.
    Primary value element has an unconfigured SNOMED code; the ICD-10
    translation carries the match. The rule's translation_code_system_oid
    is ICD10_OID, so the translation branch matches ICD-10 codes.
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
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"icd10": ["U07.1"]}),
        section_specification=spec_v1_1.sections["11450-4"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_immunizations_rule_matches_cvx_as_primary(spec_v1_1) -> None:
    """
    Immunizations: CVX on manufacturedMaterial/code — IG-conformant shape.
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
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"cvx": ["207"]}),
        section_specification=spec_v1_1.sections["11369-6"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_immunizations_rule_matches_rxnorm_as_primary(spec_v1_1) -> None:
    """
    Immunizations: RxNorm as the primary vaccine code — no nullFlavor,
    no CVX translation. This is the non-conformant pattern that was the
    root cause of the immunizations matching failure.

    Fix: code_system_oid=None on the rule. The structural location
    (manufacturedMaterial/code) is unambiguous; the configured code set
    provides the semantic constraint.

    If this test fails, the CVX_OID restriction has been reintroduced.
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
                                <code code="2563008" codeSystem="2.16.840.1.113883.6.88"/>
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
        code_system_sets=_make_code_system_sets({"rxnorm": ["2563008"]}),
        section_specification=spec_v1_1.sections["11369-6"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_immunizations_nullFlavor_primary_with_translation(spec_v1_1) -> None:
    """
    Immunizations nullFlavor pattern: primary has nullFlavor="NA",
    actual vaccine code is in a <translation>. Primary loop skips
    the nullFlavor'd element; translation branch matches.
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
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"rxnorm": ["798302"]}),
        section_specification=spec_v1_1.sections["11369-6"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_results_rule_matches_loinc_on_code(spec_v1_1) -> None:
    """
    Results T1: LOINC on Result Observation code (CONF:1098-7133).
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
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"loinc": ["94533-7"]}),
        section_specification=spec_v1_1.sections["30954-2"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_results_rule_matches_snomed_on_value(spec_v1_1) -> None:
    """
    Results T2 (rule 3): SNOMED on Result Observation value[@xsi:type='CD'].
    This rule requires sdtc:valueSet on the value element — it targets
    organism/substance trigger codes (CONF:4527-443), which always carry
    sdtc:valueSet from the RCTC. The entry has no observation/code element
    so T1 and T2 find no candidates and do not claim, allowing rule 3 to
    evaluate the value element.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xmlns:sdtc="urn:hl7-org:sdtc">
            <code code="30954-2"/>
            <entry>
                <organizer classCode="BATTERY" moodCode="EVN">
                    <component>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                            <value xsi:type="CD" code="260373001"
                                   codeSystem="2.16.840.1.113883.6.96"
                                   sdtc:valueSet="2.16.840.1.113762.1.4.1146.1105"/>
                        </observation>
                    </component>
                </organizer>
            </entry>
        </section>
        """
    )
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["260373001"]}),
        section_specification=spec_v1_1.sections["30954-2"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_rule_with_candidates_claims_entry_blocking_subsequent_rules() -> None:
    """
    Structural precedence: the first rule that finds any code-bearing
    element at its xpath claims the entry. Subsequent rules are skipped
    even if they would have matched.

    Both rules target the SAME xpath. Rule 1 finds a candidate but no
    match. Rule 1 claims. Rule 2 never runs. Section is stubbed.

    If this returns True, structural precedence is broken.
    """

    custom_spec = _make_spec_with_rules(
        rules=[
            EntryMatchRule(
                code_xpath=".//hl7:observation/hl7:code", code_system_oid=None
            ),
            EntryMatchRule(
                code_xpath=".//hl7:observation/hl7:code", code_system_oid=None
            ),
        ],
    )
    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="TEST"/>
            <entry>
                <observation classCode="OBS" moodCode="EVN">
                    <code code="UNCONFIGURED"/>
                </observation>
            </entry>
        </section>
        """
    )
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["CONFIGURED"]}),
        section_specification=custom_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is False


def test_rule_with_no_candidates_does_not_claim_entry() -> None:
    """
    A rule whose xpath finds NO elements does not claim the entry.
    The next rule gets to evaluate.

    Rule 1 targets observation/code — element absent, no candidates.
    Rule 2 targets observation/value — finds and matches.
    """

    custom_spec = _make_spec_with_rules(
        rules=[
            EntryMatchRule(
                code_xpath=".//hl7:observation/hl7:code", code_system_oid=None
            ),
            EntryMatchRule(
                code_xpath=".//hl7:observation/hl7:value", code_system_oid=None
            ),
        ],
    )
    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="TEST"/>
            <entry>
                <observation classCode="OBS" moodCode="EVN">
                    <value code="CONFIGURED"/>
                </observation>
            </entry>
        </section>
        """
    )
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["CONFIGURED"]}),
        section_specification=custom_spec,
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


# NOTE:
# CATEGORY 4: ROBUSTNESS — edge cases in code matching
# =============================================================================


def test_whitespace_in_code_is_stripped_before_match() -> None:
    """
    Trailing whitespace on @code is stripped before comparing.
    """

    custom_spec = _make_spec_with_rules(
        rules=[
            EntryMatchRule(
                code_xpath=".//hl7:observation/hl7:code", code_system_oid=None
            )
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


def test_nullFlavor_primary_falls_through_to_translation() -> None:
    """
    Element with @nullFlavor and no @code is skipped by the primary loop.
    Translation branch fires and matches the translation element.
    This is the immunization nullFlavor mechanism at the unit level.
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
# CATEGORY 5: CONTAINER-LEVEL PRUNING
# =============================================================================


def test_container_pruning_preserves_only_matching_container(spec_v1_1) -> None:
    """
    Problem Concern Act with two Problem Observations. Only one matches.
    Matching entryRelationship survives; non-matching one is pruned.
    Concern act wrapper is kept.
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
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=spec_v1_1.sections["11450-4"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True
    assert _find_one(section, ".//hl7:value[@code='840539006']") is not None
    assert _find_one(section, ".//hl7:value[@code='99999999']") is None
    assert _find_one(section, ".//hl7:act") is not None


def test_container_pruning_removes_nonmatching_components(spec_v1_1) -> None:
    """
    Results organizer: matching component survives, non-matching pruned.
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
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"loinc": ["94533-7"]}),
        section_specification=spec_v1_1.sections["30954-2"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True
    assert _find_one(section, ".//hl7:code[@code='94533-7']") is not None
    assert _find_one(section, ".//hl7:code[@code='OTHER']") is None


def test_two_matching_containers_both_survive(spec_v1_1) -> None:
    """
    Multiple matching containers in one entry all survive (union pruning).
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
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"loinc": ["94533-7", "94534-5"]}),
        section_specification=spec_v1_1.sections["30954-2"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True
    assert _find_one(section, ".//hl7:code[@code='94533-7']") is not None
    assert _find_one(section, ".//hl7:code[@code='94534-5']") is not None
    assert _find_one(section, ".//hl7:code[@code='NONMATCH']") is None


# NOTE:
# CATEGORY 6: PRESERVE WHOLE ENTRY
# =============================================================================


def test_preserve_whole_entry_keeps_reaction_chain(spec_v1_1) -> None:
    """
    Rules with preserve_whole_entry=True keep the entire matched entry
    intact — including entryRelationship chains carrying unconfigured codes.

    This is the fix that keeps ECMO reaction chains, vaccine adverse event
    observations, and medication entryRelationships intact.

    If this fails, preserve_whole_entry is not being honored.
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
                            <manufacturedMaterial>
                                <code code="2563008" codeSystem="2.16.840.1.113883.6.88"/>
                            </manufacturedMaterial>
                        </manufacturedProduct>
                    </consumable>
                    <entryRelationship typeCode="RSON">
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.9"/>
                            <code code="ASSERTION"/>
                            <value code="REACTION_CODE"/>
                        </observation>
                    </entryRelationship>
                </substanceAdministration>
            </entry>
        </section>
        """
    )
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"rxnorm": ["2563008"]}),
        section_specification=spec_v1_1.sections["11369-6"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True
    assert (
        _find_one(section, ".//hl7:entryRelationship[@typeCode='RSON']") is not None
    ), "Reaction entryRelationship was pruned — preserve_whole_entry not honored"


def test_preserve_whole_entry_scope_does_not_protect_sibling_entries(spec_v1_1) -> None:
    """
    preserve_whole_entry=True applies to the matched entry only.
    Non-matching sibling entries are still removed normally.
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
                            <manufacturedMaterial>
                                <code code="2563008" codeSystem="2.16.840.1.113883.6.88"/>
                            </manufacturedMaterial>
                        </manufacturedProduct>
                    </consumable>
                    <entryRelationship typeCode="RSON">
                        <observation classCode="OBS" moodCode="EVN">
                            <code code="ASSERTION"/>
                        </observation>
                    </entryRelationship>
                </substanceAdministration>
            </entry>
            <entry>
                <substanceAdministration classCode="SBADM" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
                    <consumable>
                        <manufacturedProduct>
                            <manufacturedMaterial>
                                <code code="UNCONFIGURED" codeSystem="2.16.840.1.113883.6.88"/>
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
        code_system_sets=_make_code_system_sets({"rxnorm": ["2563008"]}),
        section_specification=spec_v1_1.sections["11369-6"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True
    assert _find_one(section, ".//hl7:code[@code='2563008']") is not None
    assert _find_one(section, ".//hl7:entryRelationship[@typeCode='RSON']") is not None
    assert _find_one(section, ".//hl7:code[@code='UNCONFIGURED']") is None
    assert len(section.findall("{urn:hl7-org:v3}entry")) == 1


# NOTE:
# CATEGORY 7: PROVENANCE COMMENTS
# =============================================================================


def test_provenance_comment_injected_with_rule_and_code(spec_v1_1) -> None:
    """
    Provenance comment injected after matching, citing rule tier and code.
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
    process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=spec_v1_1.sections["11450-4"],
        namespaces=HL7_NS,
    )
    comments = _get_refiner_comments(section)
    assert len(comments) == 1
    assert "840539006" in comments[0]
    assert "(T1)" in comments[0]


def test_source_comments_stripped_before_matching(spec_v1_1) -> None:
    """
    Pre-existing eCR Refiner comments are stripped at STEP 1.
    Output contains only the new comment, preventing accumulation
    across multiple refinement passes.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="11450-4"/>
            <!--eCR Refiner matched: value[OLDCODE] 'stale' (SNOMED) Entry match fired for: rule 1 (T1) [hl7:value]-->
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
    process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=spec_v1_1.sections["11450-4"],
        namespaces=HL7_NS,
    )
    comments = _get_refiner_comments(section)
    assert len(comments) == 1
    assert "OLDCODE" not in comments[0]
    assert "840539006" in comments[0]


# NOTE:
# CATEGORY 8: REAL-FIXTURE INTEGRATION
# =============================================================================


def test_real_v1_1_problems_section_matches_covid(
    structured_body_v1_1: _Element, spec_v1_1
) -> None:
    """
    COVID code 840539006 found in real v1.1 Problems fixture.
    """

    problems = get_section_by_code(structured_body_v1_1, "11450-4")
    assert problems is not None
    result = process(
        section=problems,
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
        section_specification=spec_v1_1.sections["11450-4"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True
    assert _find_one(problems, ".//hl7:value[@code='840539006']") is not None


def test_real_v1_1_results_section_with_no_matches_stubs(
    structured_body_v1_1: _Element, spec_v1_1
) -> None:
    """
    Absent LOINC code on real fixture stubs the Results section.
    """

    results = get_section_by_code(structured_body_v1_1, "30954-2")
    assert results is not None
    result = process(
        section=results,
        code_system_sets=_make_code_system_sets({"loinc": ["99999-9"]}),
        section_specification=spec_v1_1.sections["30954-2"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is False
    assert results.get("nullFlavor") == "NI"


def test_real_v3_1_1_problems_section_is_processable(
    structured_body_v3_1_1: _Element, spec_v3_1_1
) -> None:
    """
    v3.1.1 Problems section processes without raising.
    """

    problems = get_section_by_code(structured_body_v3_1_1, "11450-4")
    if problems is None:
        pytest.skip("v3.1.1 fixture does not contain Problems section")
    result = process(
        section=problems,
        code_system_sets=_make_code_system_sets({"snomed": ["NONEXISTENT"]}),
        section_specification=spec_v3_1_1.sections["11450-4"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is False
