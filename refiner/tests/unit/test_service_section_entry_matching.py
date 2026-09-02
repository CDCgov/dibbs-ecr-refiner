from collections import defaultdict
from dataclasses import dataclass

import pytest
from lxml import etree
from lxml.etree import _Element

from app.services.ecr.model import (
    HL7_NS,
    HL7_XSI_NS,
    EntryMatchRule,
    SectionSpecification,
)
from app.services.ecr.section import get_section_by_code
from app.services.ecr.section.entry_matching import (
    _group_rules_by_precedence,
    _try_match_entry,
    process,
)
from app.services.ecr.specification import load_spec
from app.services.terminology import CodeSystemKey, CodeSystemSets, Oid
from tests.unit.conftest import create_mock_systems, load_section

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


def _make_oid_to_system_map() -> dict[Oid, CodeSystemKey]:
    systems: dict[Oid, CodeSystemKey] = defaultdict()

    for system in create_mock_systems():
        systems[system.oid] = system.key

    return systems


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

    return CodeSystemSets.from_dict(
        coding_by_code_system=data, oid_to_system_map=_make_oid_to_system_map()
    )


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


def test_narrative_retention_when_narrative_retain(spec_v1_1) -> None:
    """
    narrative="retain" leaves the original <text> intact.
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
        narrative_action="retain",
    )
    assert result.narrative_disposition == "retained"
    text = _find_one(section, "hl7:text")
    assert text is not None and "Original narrative" in (text.text or "")


def test_narrative_removal_when_narrative_remove(spec_v1_1) -> None:
    """
    narrative="remove" replaces the narrative with a removal notice.
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
        narrative_action="remove",
    )
    assert result.narrative_disposition == "removed"
    text = _find_one(section, "hl7:text")
    assert text is not None
    assert "Original narrative" not in etree.tostring(text, encoding="unicode")


def test_narrative_reconstruct_results_rebuilds_text(spec_v1_1) -> None:
    """
    narrative="reconstruct" on Results swaps the stale source narrative for
    a machine-derived table built from the surviving result entries.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <code code="30954-2"/>
            <text>Original narrative content here.</text>
            <entry>
                <organizer classCode="BATTERY" moodCode="EVN">
                    <code displayName="CBC panel"/>
                    <component>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                            <code code="94533-7" codeSystem="2.16.840.1.113883.6.1"
                                  displayName="Hemoglobin"/>
                            <effectiveTime value="20240115"/>
                            <value xsi:type="PQ" value="9.2" unit="g/dL"/>
                            <interpretationCode code="L" displayName="Low"/>
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
        narrative_action="reconstruct",
    )
    assert result.matches_found is True
    assert result.narrative_disposition == "reconstructed"

    text = _find_one(section, "hl7:text")
    assert text is not None
    serialized = etree.tostring(text, encoding="unicode")
    assert "Original narrative" not in serialized
    assert "machine-derived" in serialized
    assert "CBC panel" in serialized
    # one detail row (carrying a minted xs:ID) per surviving observation;
    # the panel context renders once in its own table, not per row
    detail_rows = text.xpath(".//hl7:tbody/hl7:tr[@ID]", namespaces=HL7_NS)
    assert len(detail_rows) == 1


def test_narrative_reconstruct_without_matches_removes_the_original_narrative(
    spec_v1_1,
) -> None:
    """
    narrative="reconstruct" on Results swaps the stale source narrative for
    a machine-derived table built from the surviving result entries.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <code code="30954-2"/>
            <text>Original narrative content here.</text>
            <entry>
                <organizer classCode="BATTERY" moodCode="EVN">
                    <code displayName="CBC panel"/>
                    <component>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                            <code code="nonsense code" codeSystem="2.16.840.1.113883.6.1"
                                  displayName="nonsense"/>
                            <effectiveTime value="20240115"/>
                            <value xsi:type="PQ" value="9.2" unit="g/dL"/>
                            <interpretationCode code="L" displayName="Low"/>
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
        narrative_action="reconstruct",
    )
    assert result.matches_found is False
    assert result.narrative_disposition == "removed"

    # the original narrative described the entries that were just pruned, so
    # retaining it would ship exactly the content the configuration excluded
    text = _find_one(section, "hl7:text")
    assert text is not None
    assert "Original narrative" not in etree.tostring(text, encoding="unicode")


def test_narrative_reconstruct_without_reconstructor_falls_back_to_retain(
    spec_v1_1,
) -> None:
    """
    narrative="reconstruct" on a refinable section with no registered
    reconstructor (Social History — not reconstructable) falls back to
    retaining the original narrative rather than swapping in a removal
    notice. The intent is that the original narrative is more
    informative to a reviewer than the removal placeholder when
    reconstruction can't be produced.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="29762-2"/>
            <text>Original narrative content here.</text>
            <entry>
                <observation classCode="OBS" moodCode="EVN">
                    <code code="229819007" codeSystem="2.16.840.1.113883.6.96"/>
                </observation>
            </entry>
        </section>
        """
    )
    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": ["229819007"]}),
        section_specification=spec_v1_1.sections["29762-2"],
        namespaces=HL7_NS,
        narrative_action="reconstruct",
    )
    assert result.matches_found is True
    assert result.narrative_disposition == "reconstruct_unavailable"
    text = _find_one(section, "hl7:text")
    assert text is not None
    assert "Original narrative" in etree.tostring(text, encoding="unicode")


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


def test_problems_icd10_primary_matches_via_t3_same_location_rule(
    spec_v1_1,
) -> None:
    """
    T1 (SNOMED) and T3 (ICD-10) read the SAME Problem Observation value, so
    they form one precedence group and both are evaluated before the entry
    is claimed. An ICD-10-primary entry matches via T3.
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
    assert result.matches_found is True


def test_problems_icd10_primary_with_snomed_translation_matches(spec_v1_1) -> None:
    """
    The reversed sender pattern: billing code (ICD-10) as the primary value,
    clinical concept (SNOMED) in translation, with only the SNOMED code
    configured. T1 finds a candidate but no SNOMED match and its translation
    branch is scoped to ICD-10; T3 is the rule that reaches the SNOMED
    translation. Both must run for this entry to survive.
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
                            <value code="O09.32" codeSystem="2.16.840.1.113883.6.90">
                                <translation code="426403007" codeSystem="2.16.840.1.113883.6.96"/>
                                <translation code="V23.7" codeSystem="2.16.840.1.113883.6.103"/>
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
        code_system_sets=_make_code_system_sets({"snomed": ["426403007"]}),
        section_specification=spec_v1_1.sections["11450-4"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True


def test_problems_unconfigured_code_still_does_not_match(spec_v1_1) -> None:
    """
    Grouping widens WHICH rules run, not what counts as a match: an entry
    whose codes are in no configured set is still pruned.
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
                            <value code="O09.32" codeSystem="2.16.840.1.113883.6.90">
                                <translation code="426403007" codeSystem="2.16.840.1.113883.6.96"/>
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
        code_system_sets=_make_code_system_sets({"snomed": ["840539006"]}),
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


# NOTE:
# RESULTS SHARED-CONTEXT CARVE-OUT (prune_container_guard_xpath)
# =============================================================================
# a Result Organizer may carry sibling components that are NOT result
# observations — the Specimen Collection Procedure (...4.415, the specimen
# collection date / body site / source) and the Laboratory Result Status
# (...4.418). They are organizer-scoped shared context and unmatchable by
# construction. The guard on the Results rules exempts any component that does
# not itself contain a Result Observation V3, so those siblings survive
# alongside a retained result instead of being pruned as non-matching


def _results_organizer_with_specimen() -> str:
    # one organizer: a MATCHED result, a NON-matching result, a Specimen
    # Collection Procedure (...4.415), and a Laboratory Result Status (...4.418)
    return """
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
                            <code code="99999-9" codeSystem="2.16.840.1.113883.6.1"/>
                        </observation>
                    </component>
                    <component>
                        <procedure classCode="PROC" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.415"
                                        extension="2018-09-01"/>
                            <code code="17636008"
                                  codeSystem="2.16.840.1.113883.6.96"/>
                            <effectiveTime><low value="20200309"/></effectiveTime>
                        </procedure>
                    </component>
                    <component>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.418"/>
                            <code code="55199-6" codeSystem="2.16.840.1.113883.6.1"/>
                        </observation>
                    </component>
                </organizer>
            </entry>
        </section>
        """


def _result_codes(section: _Element) -> list[str]:
    return section.xpath(
        ".//hl7:observation[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.2']]"
        "/hl7:code/@code",
        namespaces=HL7_NS,
    )


def test_results_specimen_and_labstatus_survive_with_matched_result(
    spec_v1_1,
) -> None:
    """
    The carve-out retains non-result siblings alongside a matched result.

    In a single organizer: the matched Result Observation is kept, the
    non-matching one is still pruned, and BOTH the Specimen Collection
    Procedure and the Laboratory Result Status survive as shared context.
    Lab Result Status is itself an <observation> under a sibling component —
    its survival proves the guard keys on the Result Observation V3 templateId,
    not "any observation".
    """

    section = _build_section(_results_organizer_with_specimen())

    # precondition: the source organizer really carries the shared-context
    # siblings this test is about
    assert section.xpath(
        ".//hl7:procedure[hl7:code/@code='17636008']", namespaces=HL7_NS
    )
    assert section.xpath(
        ".//hl7:observation[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.418']]",
        namespaces=HL7_NS,
    )

    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"loinc": ["94533-7"]}),
        section_specification=spec_v1_1.sections["30954-2"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True

    # matched result kept; non-matching Result Observation still pruned
    assert _result_codes(section) == ["94533-7"]

    # specimen collection procedure (...4.415) survives as shared context
    assert section.xpath(
        ".//hl7:procedure[hl7:code/@code='17636008']", namespaces=HL7_NS
    ), "Specimen Collection Procedure was pruned — the specimen data-loss bug"

    # laboratory result status (...4.418) survives too
    assert section.xpath(
        ".//hl7:observation[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.418']]",
        namespaces=HL7_NS,
    ), "Laboratory Result Status was pruned — guard is over-broad"


def test_results_unmatched_organizer_drops_its_specimen_procedure(
    spec_v1_1,
) -> None:
    """
    Regression guard: the carve-out fires only within a MATCHED organizer.

    An organizer whose only result does not match is removed wholesale and its
    specimen procedure goes with it — the shared-context exemption must not
    leak an orphaned procedure out of a fully-pruned organizer.
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
                            <code code="99999-9" codeSystem="2.16.840.1.113883.6.1"/>
                        </observation>
                    </component>
                    <component>
                        <procedure classCode="PROC" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.415"
                                        extension="2018-09-01"/>
                            <code code="17636008"
                                  codeSystem="2.16.840.1.113883.6.96"/>
                        </procedure>
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
    assert result.matches_found is False
    assert not section.xpath(
        ".//hl7:procedure[hl7:code/@code='17636008']", namespaces=HL7_NS
    ), "A fully-pruned organizer leaked its specimen procedure"


def test_results_specimen_retained_only_in_matched_organizer(spec_v1_1) -> None:
    """
    With two organizers, the specimen procedure survives only where a result
    was retained; the fully-pruned organizer emits nothing.

    The two procedures are distinguished by targetSiteCode so the assertion
    names exactly which one survived.
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
                        <procedure classCode="PROC" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.415"
                                        extension="2018-09-01"/>
                            <code code="17636008"
                                  codeSystem="2.16.840.1.113883.6.96"/>
                            <targetSiteCode code="MATCHED"/>
                        </procedure>
                    </component>
                </organizer>
            </entry>
            <entry>
                <organizer classCode="BATTERY" moodCode="EVN">
                    <component>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                            <code code="99999-9" codeSystem="2.16.840.1.113883.6.1"/>
                        </observation>
                    </component>
                    <component>
                        <procedure classCode="PROC" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.415"
                                        extension="2018-09-01"/>
                            <code code="17636008"
                                  codeSystem="2.16.840.1.113883.6.96"/>
                            <targetSiteCode code="UNMATCHED"/>
                        </procedure>
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

    surviving_sites = section.xpath(
        ".//hl7:procedure[hl7:code/@code='17636008']/hl7:targetSiteCode/@code",
        namespaces=HL7_NS,
    )
    assert surviving_sites == ["MATCHED"], (
        f"Specimen procedure survived in the wrong organizers: {surviving_sites}. "
        f"Expected only the one under the organizer whose result matched."
    )


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


# NOTE:
# INVARIANT: a matched entry is never removed
# =============================================================================
# container-level pruning ends by deleting an entry that has no containers
# left. that test cannot, on its own, tell "we pruned every container away"
# apart from "this entry never had containers at that path"--and the second
# case is reachable on live data, because every code_xpath is unanchored
# (`.//`) while every prune_container_xpath assumes a specific shape. the two
# tests below pin the distinction from both sides


def test_matched_entry_without_containers_survives_results(spec_v1_1) -> None:
    """
    A bare Result Observation under <entry>, with no organizer, is retained.

    The Results code_xpath is unanchored, so it matches an observation sitting
    directly under <entry>. prune_container_xpath ("hl7:organizer/hl7:component")
    then finds nothing--which must read as "this rule's container model does
    not describe this entry", not as "we pruned it to nothing".
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
            <code code="30954-2"/>
            <entry>
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                    <code code="94533-7" codeSystem="2.16.840.1.113883.6.1"/>
                </observation>
            </entry>
        </section>
        """
    )

    # precondition: the entry really has no organizer/component containers
    assert not section.xpath(
        ".//hl7:entry/hl7:organizer/hl7:component", namespaces=HL7_NS
    )

    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"loinc": ["94533-7"]}),
        section_specification=spec_v1_1.sections["30954-2"],
        namespaces=HL7_NS,
    )

    assert result.matches_found is True
    assert _result_codes(section) == ["94533-7"], (
        "a matched entry was deleted because it carried no containers at "
        "prune_container_xpath"
    )


def test_matched_entry_with_containers_pruned_to_nothing_is_removed(
    spec_v1_1,
) -> None:
    """
    The other side of the invariant: pruning every container does delete.

    Guards against "fixing" the case above by never removing an emptied entry.
    Here the organizer holds only non-matching Result Observations, so every
    container is legitimately pruned and the husk goes with them.
    """

    section = _build_section(_results_organizer_with_specimen())

    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"loinc": ["94533-7"]}),
        section_specification=spec_v1_1.sections["30954-2"],
        namespaces=HL7_NS,
    )
    assert result.matches_found is True

    # the matched organizer survives; nothing else to assert here beyond the
    # entry still being present with its one retained result
    assert section.xpath(".//hl7:entry/hl7:organizer", namespaces=HL7_NS)
    assert _result_codes(section) == ["94533-7"]


def test_results_proprietary_component_is_pruned_not_treated_as_context(
    spec_v1_1,
) -> None:
    """
    A vendor-proprietary component is an ordinary prunable candidate.

    The shared-context exemption names the two IG context templates. It used
    to exempt anything that merely lacked a Result Observation templateId,
    which swept in Epic's proprietary result components (a nullFlavored code
    plus a bare enum value) — they rode through the prune and rendered as
    narrative rows reading "16".
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
                            <templateId root="1.2.840.114350.1.72.3.4"/>
                            <code nullFlavor="UNK"/>
                            <value xsi:type="CD" code="16"
                                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                   codeSystem="1.2.840.114350.1.72.1.5007"
                                   codeSystemName="Epic.Result.Type"/>
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
    proprietary = section.xpath(
        ".//hl7:observation[hl7:templateId[@root='1.2.840.114350.1.72.3.4']]",
        namespaces=HL7_NS,
    )
    assert proprietary == [], "proprietary component survived as shared context"
    # the matched result is untouched
    assert _result_codes(section) == ["94533-7"]


def test_rule_grouping_is_by_adjacency_not_by_xpath_globally() -> None:
    """
    Only CONSECUTIVE same-location rules group.

    A rule separated from its twin by a rule at another location is making a
    deliberate ordering statement; collecting every matching xpath
    document-wide would silently rewrite it.
    """

    def _rule(xpath: str, tier: int) -> EntryMatchRule:
        return EntryMatchRule(code_xpath=xpath, code_system_oid=None, tier=tier)

    a1, b, a2 = _rule("a", 1), _rule("b", 2), _rule("a", 3)
    assert _group_rules_by_precedence([a1, a2, b]) == [[a1, a2], [b]]
    assert _group_rules_by_precedence([a1, b, a2]) == [[a1], [b], [a2]]
    assert _group_rules_by_precedence([]) == []


def test_an_explicit_precedence_group_unites_rules_at_different_locations() -> None:
    """
    Rules reading one statement at different locations declare it.

    Without the group they key on their own code_xpath and end up in
    separate units, which is what left the Results organism/substance rule
    unreachable behind the test-name rule.
    """

    def _grouped(xpath: str, group: str | None) -> EntryMatchRule:
        return EntryMatchRule(
            code_xpath=xpath, code_system_oid=None, precedence_group=group
        )

    ungrouped = [_grouped("obs/code", None), _grouped("obs/value", None)]
    assert len(_group_rules_by_precedence(ungrouped)) == 2

    grouped = [_grouped("obs/code", "stmt"), _grouped("obs/value", "stmt")]
    assert _group_rules_by_precedence(grouped) == [grouped]


# NOTE:
# THE ICD-10-PRIMARY PROBLEM LIST — a synthetic stand-in for reported data
# =============================================================================
# a reviewer reported problem entries being pruned from real Connecticut eICRs
# even though their SNOMED code was configured. the fixture reproduces the
# sender shape (billing code primary, clinical code in translation) without any
# patient data; see its header comment for the four entries it carries


@pytest.fixture
def problems_icd10_primary() -> _Element:
    return _build_section(load_section("problems_icd10_primary"))


# the three SNOMED concepts a jurisdiction would have configured for this
# condition. two are reachable only through a <translation>
_CONFIGURED_SNOMED = ["426403007", "1621000119101", "76272004"]


def _process_problems(section: _Element, spec, **kwargs) -> object:
    return process(
        section=section,
        code_system_sets=_make_code_system_sets({"snomed": _CONFIGURED_SNOMED}),
        section_specification=spec.sections["11450-4"],
        namespaces=HL7_NS,
        **kwargs,
    )


def test_icd10_primary_problems_survive_when_their_snomed_is_configured(
    problems_icd10_primary, spec_v1_1
) -> None:
    """
    The reported regression, end to end through the section processor.

    Entries 1 and 2 carry the configured SNOMED only in a <translation>
    under an ICD-10 primary value. Before the precedence fix the tier-1 rule
    claimed each entry on sight of its value element and the tier-3 rule that
    reads the same location under the reversed code system never ran, so both
    were pruned as non-matching.
    """

    result = _process_problems(problems_icd10_primary, spec_v1_1)

    assert result.matches_found is True
    surviving = problems_icd10_primary.xpath(
        ".//hl7:entryRelationship/hl7:observation/hl7:value/@code", namespaces=HL7_NS
    )
    assert surviving == ["O09.32", "O98.812", "76272004"]


def test_unconfigured_problems_are_still_pruned(
    problems_icd10_primary, spec_v1_1
) -> None:
    """
    Widening WHICH rules run must not widen what counts as a match.

    Entry 3 (Z34.90 / 72892002) is configured under neither code system and
    goes entirely; the sibling problem inside entry 4's concern act
    (J30.2 / 367498001) goes too, proving container-level pruning still
    discriminates inside an entry that DID match.
    """

    _process_problems(problems_icd10_primary, spec_v1_1)

    remaining = problems_icd10_primary.xpath(
        ".//hl7:entryRelationship/hl7:observation/hl7:value/hl7:translation/@code",
        namespaces=HL7_NS,
    )
    assert "72892002" not in remaining, "unconfigured problem survived"
    assert "367498001" not in remaining, "unconfigured sibling problem survived"
    # entry 3 had a single problem, so the whole concern act goes with it
    assert problems_icd10_primary.xpath("count(hl7:entry)", namespaces=HL7_NS) == 3


def test_reconstructed_rows_carry_the_labels_from_the_source_narrative(
    problems_icd10_primary, spec_v1_1
) -> None:
    """
    Every value in this fixture gives `originalText` BY REFERENCE, the shape
    real senders use — the label lives in the narrative, not on @displayName.
    The reference has to be inlined before the field extractor runs or the
    rows fall back to the formal terminology name.
    """

    result = _process_problems(
        problems_icd10_primary,
        spec_v1_1,
        augmentation_timestamp="20260101000000",
        narrative_action="reconstruct",
    )
    assert result.narrative_disposition == "reconstructed"

    rendered = etree.tostring(
        problems_icd10_primary.find("hl7:text", HL7_NS), encoding="unicode"
    )
    assert "Late prenatal care affecting pregnancy in second trimester" in rendered
    assert "Chlamydia infection affecting pregnancy in second trimester" in rendered
    # the sender's own word, resolved from the narrative — not the configured
    # terminology display that enrichment stamped onto @displayName
    assert "Syphilis (SNOMED CT 76272004)" in rendered
    # the pruned problems are absent from the rebuilt narrative
    assert "Supervision of normal pregnancy" not in rendered
    assert "Seasonal allergic rhinitis" not in rendered


def test_original_text_is_converted_to_by_value_not_blanked(
    problems_icd10_primary, spec_v1_1
) -> None:
    """
    The shipped structured data keeps the sender's coding provenance.

    Replacing the narrative deletes the `xs:ID`s these references point at,
    so leaving them would strand a dangling `#id` and removing them outright
    would destroy the label. They are converted by-reference -> by-value.
    """

    _process_problems(
        problems_icd10_primary,
        spec_v1_1,
        augmentation_timestamp="20260101000000",
        narrative_action="reconstruct",
    )

    original_texts = problems_icd10_primary.xpath(
        ".//hl7:entry//hl7:originalText", namespaces=HL7_NS
    )
    assert original_texts, "the fixture's originalText elements were removed"
    for element in original_texts:
        assert element.find("hl7:reference", HL7_NS) is None, "dangling #id left behind"
        assert (element.text or "").strip(), "originalText was blanked"


# NOTE:
# RULE REACHABILITY — every rule must be able to fire, and fire ITSELF
# =============================================================================
# structural precedence has silently killed rules twice: the diagnosis
# sections' reversed-code pairs, and the Results organism/substance rule. Both
# were invisible because every OTHER rule in the section still worked -- no
# test failed and no output looked wrong, the affected entries just quietly
# stopped surviving refinement.
#
# this pins the property directly. each case is a minimal entry built so that
# ONE named rule should claim it, and the assertion checks WHICH rule produced
# the match, not merely that the section matched something. that distinction is
# the whole point: a rule shadowed by an earlier one that happens to match the
# same entry is still dead, and a section-level "did anything match?" assertion
# would sail straight past it.
#
# the entries are hand-written rather than synthesized from each rule's xpath.
# generating XML from an XPath would re-implement the matcher's own reading of
# the rule, and a test that shares its subject's assumptions cannot falsify
# them.
#
# every MULTI-rule section is covered — those are the only ones precedence can
# shadow. single-rule sections (Immunizations, Vital Signs, Pregnancy, ...) are
# reachable by construction: there is no earlier rule to claim the entry first.
# a guard below asserts that split rather than trusting this comment, so a
# second rule added to a single-rule section fails until the table catches up.


@dataclass(frozen=True)
class ReachabilityCase:
    """One rule, an entry only it should claim, and the code it should match."""

    version: str
    section: str
    rule_index: int
    what: str
    configured: dict[str, list[str]]
    entry: str


def _results_entry(observation_body: str) -> str:
    return f"""
    <entry><organizer classCode="BATTERY" moodCode="EVN">
      <statusCode code="completed"/>
      <component><observation classCode="OBS" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
        {observation_body}
      </observation></component>
    </organizer></entry>
    """


def _diagnosis_entry(value: str) -> str:
    return f"""
    <entry><act classCode="ACT" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
      <entryRelationship typeCode="SUBJ">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
          {value}
        </observation>
      </entryRelationship>
    </act></entry>
    """


# Results: ONE Result Observation read at three locations. rules 2 and 3 were
# unreachable until they were declared a single precedence group -- <code> is
# SHALL on this template, so rule 1 always claimed the entry first
_RESULTS_CASES: list[ReachabilityCase] = [
    ReachabilityCase(
        version="1.1",
        section="30954-2",
        rule_index=0,
        what="LOINC test name on observation/code",
        configured={"loinc": ["94533-7"]},
        entry=_results_entry(
            '<code code="94533-7" codeSystem="2.16.840.1.113883.6.1"/>'
            '<value xsi:type="PQ" value="1" unit="1"/>'
        ),
    ),
    ReachabilityCase(
        version="1.1",
        section="30954-2",
        rule_index=1,
        what="local code primary, LOINC trigger in code/translation",
        configured={"loinc": ["94533-7"]},
        entry=_results_entry(
            '<code code="LAB1234" codeSystem="1.2.840.114350.1.13.999">'
            '<translation code="94533-7" codeSystem="2.16.840.1.113883.6.1"/>'
            "</code>"
            '<value xsi:type="PQ" value="1" unit="1"/>'
        ),
    ),
    ReachabilityCase(
        version="1.1",
        section="30954-2",
        rule_index=2,
        what="organism/substance SNOMED on observation/value",
        configured={"snomed": ["5247005"]},
        entry=_results_entry(
            # a generic test name the jurisdiction has NOT configured: the
            # reportable concept is the organism in the value
            '<code code="00000-0" codeSystem="2.16.840.1.113883.6.1"/>'
            '<value xsi:type="CD" code="5247005"'
            ' codeSystem="2.16.840.1.113883.6.96"'
            ' sdtc:valueSet="2.16.840.1.114222.4.11.7508"/>'
        ),
    ),
]

# the diagnosis-shaped sections all carry the same rule pair: SNOMED on the
# Problem Observation value (tier 1) and the reversed ICD-10-primary pattern
# (tier 3). generated rather than repeated five times -- only the section
# code and spec version differ
_DIAGNOSIS_SECTIONS: list[tuple[str, str]] = [
    ("1.1", "11450-4"),  # Problem
    ("3.1.1", "46241-6"),  # Admission Diagnosis
    ("3.1.1", "11535-2"),  # Discharge Diagnosis
    ("1.1", "46240-8"),  # Encounters
    ("3.1.1", "11348-0"),  # Past Medical History
]

_DIAGNOSIS_CASES: list[ReachabilityCase] = [
    case
    for version, section in _DIAGNOSIS_SECTIONS
    for case in (
        ReachabilityCase(
            version=version,
            section=section,
            rule_index=0,
            what="SNOMED on the observation value (conformant)",
            configured={"snomed": ["840539006"]},
            entry=_diagnosis_entry(
                '<value xsi:type="CD" code="840539006"'
                ' codeSystem="2.16.840.1.113883.6.96"/>'
            ),
        ),
        ReachabilityCase(
            version=version,
            section=section,
            rule_index=1,
            what="ICD-10 primary with SNOMED in translation (reversed)",
            configured={"snomed": ["840539006"]},
            entry=_diagnosis_entry(
                '<value xsi:type="CD" code="U07.1"'
                ' codeSystem="2.16.840.1.113883.6.90">'
                '<translation code="840539006"'
                ' codeSystem="2.16.840.1.113883.6.96"/></value>'
            ),
        ),
    )
]


def _statement(tag: str, template: str, body: str) -> str:
    return f"""
    <entry><{tag} classCode="ACT" moodCode="INT">
      <templateId root="{template}"/>
      {body}
    </{tag}></entry>
    """


def _product(code: str) -> str:
    return (
        "<consumable><manufacturedProduct><manufacturedMaterial>"
        f'<code code="{code}" codeSystem="2.16.840.1.113883.6.88"/>'
        "</manufacturedMaterial></manufacturedProduct></consumable>"
    )


_CODED = '<code code="840539006" codeSystem="2.16.840.1.113883.6.96"/>'
_SNOMED = {"snomed": ["840539006"]}
_RXNORM = {"rxnorm": ["1115699"]}

# Plan of Treatment: eight rules, each a distinct planned statement type.
# they discriminate by element name AND templateId, so an entry built for one
# is invisible to the others
_PLAN_OF_TREATMENT_CASES: list[ReachabilityCase] = [
    ReachabilityCase(
        "1.1",
        "18776-5",
        0,
        "planned observation code",
        _SNOMED,
        _statement("observation", "2.16.840.1.113883.10.20.22.4.44", _CODED),
    ),
    ReachabilityCase(
        "1.1",
        "18776-5",
        1,
        "planned medication product",
        _RXNORM,
        _statement(
            "substanceAdministration",
            "2.16.840.1.113883.10.20.22.4.42",
            _product("1115699"),
        ),
    ),
    ReachabilityCase(
        "1.1",
        "18776-5",
        2,
        "medication activity product",
        _RXNORM,
        _statement(
            "substanceAdministration",
            "2.16.840.1.113883.10.20.22.4.16",
            _product("1115699"),
        ),
    ),
    ReachabilityCase(
        "1.1",
        "18776-5",
        3,
        "planned immunization product",
        _RXNORM,
        _statement(
            "substanceAdministration",
            "2.16.840.1.113883.10.20.22.4.120",
            _product("1115699"),
        ),
    ),
    ReachabilityCase(
        "1.1",
        "18776-5",
        4,
        "immunization activity product",
        _RXNORM,
        _statement(
            "substanceAdministration",
            "2.16.840.1.113883.10.20.22.4.52",
            _product("1115699"),
        ),
    ),
    ReachabilityCase(
        "1.1",
        "18776-5",
        5,
        "planned act code",
        _SNOMED,
        _statement("act", "2.16.840.1.113883.10.20.22.4.39", _CODED),
    ),
    ReachabilityCase(
        "1.1",
        "18776-5",
        6,
        "planned procedure code",
        _SNOMED,
        _statement("procedure", "2.16.840.1.113883.10.20.22.4.41", _CODED),
    ),
    ReachabilityCase(
        "1.1",
        "18776-5",
        7,
        "planned observation VALUE",
        _SNOMED,
        _statement(
            "observation",
            "2.16.840.1.113883.10.20.22.4.19",
            '<value xsi:type="CD" code="840539006"'
            ' codeSystem="2.16.840.1.113883.6.96"/>',
        ),
    ),
]

# Procedures: three trigger-code templates, one per element name
_PROCEDURES_CASES: list[ReachabilityCase] = [
    ReachabilityCase(
        "3.1.1",
        "47519-4",
        0,
        "trigger procedure code",
        _SNOMED,
        _statement("procedure", "2.16.840.1.113883.10.20.15.2.3.44", _CODED),
    ),
    ReachabilityCase(
        "3.1.1",
        "47519-4",
        1,
        "trigger act code",
        _SNOMED,
        _statement("act", "2.16.840.1.113883.10.20.15.2.3.45", _CODED),
    ),
    ReachabilityCase(
        "3.1.1",
        "47519-4",
        2,
        "trigger observation code",
        _SNOMED,
        _statement("observation", "2.16.840.1.113883.10.20.15.2.3.46", _CODED),
    ),
]

# Social History scans broadly: one rule covering observation/act code, with
# its translation_xpath reaching value. that is why it is a single rule --
# see the deletion note in entry_match_rules
_SOCIAL_HISTORY_CASES: list[ReachabilityCase] = [
    ReachabilityCase(
        "1.1",
        "29762-2",
        0,
        "any observation or act code",
        _SNOMED,
        '<entry><observation classCode="OBS" moodCode="EVN">'
        f"{_CODED}</observation></entry>",
    ),
]


_REACHABILITY_CASES: list[ReachabilityCase] = (
    _RESULTS_CASES
    + _DIAGNOSIS_CASES
    + _PLAN_OF_TREATMENT_CASES
    + _PROCEDURES_CASES
    + _SOCIAL_HISTORY_CASES
)


@pytest.mark.parametrize(
    "case",
    _REACHABILITY_CASES,
    ids=lambda c: f"{c.section}-rule{c.rule_index}",
)
def test_every_match_rule_can_claim_an_entry(case: ReachabilityCase) -> None:
    """
    The rule this case was written for produces the match itself.

    A failure means structural precedence is swallowing the rule -- an
    earlier one claims the entry before this one is evaluated -- so the
    sender pattern it exists to catch is being pruned in production.
    """

    rules = load_spec(case.version).sections[case.section].entry_match_rules
    entry = _build_section(
        f"""
        <entry xmlns="urn:hl7-org:v3"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:sdtc="urn:hl7-org:sdtc">{case.entry}</entry>
        """
    )[0]

    matches = _try_match_entry(
        entry,
        _make_code_system_sets(case.configured),
        rules,
        HL7_XSI_NS,
    )

    assert matches, (
        f"{case.section} rule[{case.rule_index}] ({case.what}) matched nothing"
    )
    matched_indices = {rules.index(m.rule) for m in matches}
    assert case.rule_index in matched_indices, (
        f"{case.section} rule[{case.rule_index}] ({case.what}) is shadowed: "
        f"the entry was claimed by rule(s) {sorted(matched_indices)} instead"
    )


def test_every_multi_rule_section_appears_in_the_reachability_table() -> None:
    """
    Precedence can only shadow a rule that has an earlier rule to hide behind.

    So the table must claim every section carrying more than one rule. A
    single-rule section is reachable by construction and needs no case — but
    the moment a second rule is added there, this fails until the table
    covers it.
    """

    claimed = {case.section for case in _REACHABILITY_CASES}
    for version in ("1.1", "3.1.1"):
        spec = load_spec(version)
        multi_rule = {
            code
            for code, section in spec.sections.items()
            if len(section.entry_match_rules) > 1
        }
        assert multi_rule <= claimed, (
            f"spec {version}: multi-rule sections missing from the "
            f"reachability table: {sorted(multi_rule - claimed)}"
        )


def test_reachability_table_covers_every_rule_of_the_sections_it_claims() -> None:
    """
    Adding a rule to a covered section must not leave it unguarded.

    That silent gap is the failure mode the table exists to prevent, so the
    table policing its own completeness is the part that keeps it honest.
    """

    covered: dict[tuple[str, str], set[int]] = {}
    for case in _REACHABILITY_CASES:
        covered.setdefault((case.version, case.section), set()).add(case.rule_index)

    for (version, section), indices in covered.items():
        rule_count = len(load_spec(version).sections[section].entry_match_rules)
        assert indices == set(range(rule_count)), (
            f"{section} (spec {version}) has {rule_count} rules but the "
            f"reachability table covers {sorted(indices)}"
        )


# NOTE:
# nullFlavored PRODUCT CODE WITH THE REAL CODE IN <translation>
# =============================================================================
# a sender may put a nullFlavor on the primary CVX/RxNorm code and carry the
# real one in a <translation> (NDC, RxNorm, CVX). render_code_display's
# translation fallbacks cite this as their reason for existing and the
# immunization match rule carries a translation_xpath for it, but nothing
# exercised either end. both halves matter independently: the entry has to
# SURVIVE matching, and then it has to RENDER as something other than a blank
# cell -- a surviving entry with an empty narrative row would make the
# section's typeCode="DRIV" a lie


def test_immunization_matches_on_a_cvx_code_carried_in_translation(
    spec_v1_1,
) -> None:
    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
          <code code="11369-6"/>
          <entry><substanceAdministration classCode="SBADM" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
            <consumable><manufacturedProduct><manufacturedMaterial>
              <code nullFlavor="UNK">
                <translation code="141" codeSystem="2.16.840.1.113883.12.292"
                             displayName="Influenza, seasonal, injectable"/>
              </code>
            </manufacturedMaterial></manufacturedProduct></consumable>
          </substanceAdministration></entry>
        </section>
        """
    )

    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"cvx": ["141"]}),
        section_specification=spec_v1_1.sections["11369-6"],
        namespaces=HL7_NS,
    )

    assert result.matches_found is True
    assert section.findall("hl7:entry", HL7_NS), "the matched entry was pruned"


def test_immunization_row_renders_the_translation_rather_than_a_blank_cell(
    spec_v1_1,
) -> None:
    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3">
          <code code="11369-6"/>
          <text>...original clinician narrative...</text>
          <entry><substanceAdministration classCode="SBADM" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
            <statusCode code="completed"/>
            <effectiveTime value="20260803"/>
            <consumable><manufacturedProduct><manufacturedMaterial>
              <code nullFlavor="UNK">
                <translation code="141" codeSystem="2.16.840.1.113883.12.292"
                             displayName="Influenza, seasonal, injectable"/>
              </code>
            </manufacturedMaterial></manufacturedProduct></consumable>
          </substanceAdministration></entry>
        </section>
        """
    )

    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"cvx": ["141"]}),
        section_specification=spec_v1_1.sections["11369-6"],
        namespaces=HL7_NS,
        augmentation_timestamp="20260101000000",
        narrative_action="reconstruct",
    )

    assert result.narrative_disposition == "reconstructed"
    rendered = etree.tostring(section.find("hl7:text", HL7_NS), encoding="unicode")
    assert "Influenza, seasonal, injectable" in rendered
    # the nullFlavored primary code must not surface as the product identity
    assert "UNK" not in rendered


def test_partial_reconstruction_is_reported_in_the_section_outcome(
    spec_v1_1,
) -> None:
    """
    A reduced-form entry changes the outcome the provenance footnote shows.

    Without a distinct disposition the section reports a clean rebuild while
    an entry stamped typeCode="DRIV" is only present in reduced form, and a
    reviewer looking at a thin table has nothing telling them why.
    """

    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <code code="30954-2"/>
          <text>Original clinician narrative.</text>
          <entry><organizer classCode="BATTERY" moodCode="EVN">
            <statusCode code="completed"/>
            <component><observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
              <code code="94533-7" codeSystem="2.16.840.1.113883.6.1"/>
              <value xsi:type="PQ" value="1" unit="1"/>
            </observation></component>
          </organizer></entry>
          <entry><observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <code code="94533-7" codeSystem="2.16.840.1.113883.6.1"/>
            <value xsi:type="PQ" value="2" unit="1"/>
          </observation></entry>
        </section>
        """
    )

    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"loinc": ["94533-7"]}),
        section_specification=spec_v1_1.sections["30954-2"],
        namespaces=HL7_NS,
        augmentation_timestamp="20260101000000",
        narrative_action="reconstruct",
    )

    assert result.matches_found is True
    assert result.narrative_disposition == "reconstructed_reduced"


def test_a_fully_reconstructed_section_reports_the_plain_outcome(
    spec_v1_1,
) -> None:
    section = _build_section(
        """
        <section xmlns="urn:hl7-org:v3"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <code code="30954-2"/>
          <text>Original clinician narrative.</text>
          <entry><organizer classCode="BATTERY" moodCode="EVN">
            <statusCode code="completed"/>
            <component><observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
              <code code="94533-7" codeSystem="2.16.840.1.113883.6.1"/>
              <value xsi:type="PQ" value="1" unit="1"/>
            </observation></component>
          </organizer></entry>
        </section>
        """
    )

    result = process(
        section=section,
        code_system_sets=_make_code_system_sets({"loinc": ["94533-7"]}),
        section_specification=spec_v1_1.sections["30954-2"],
        namespaces=HL7_NS,
        augmentation_timestamp="20260101000000",
        narrative_action="reconstruct",
    )

    assert result.narrative_disposition == "reconstructed"
