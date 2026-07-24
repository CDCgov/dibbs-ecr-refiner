from lxml import etree
from lxml.etree import _Element

from app.services.ecr.model import HL7_NS
from app.services.ecr.narrative.reconstruction import reconstruct_narrative
from app.services.ecr.section.utils import (
    _index_narrative_display_ids,
    _resolve_reference_display,
    enrich_surviving_entries,
)
from app.services.ecr.specification.constants import SNOMED_OID
from app.services.terminology import CodeSystemSets, Coding

_NSDECL = 'xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'


def _el(xml: str) -> _Element:
    return etree.fromstring(xml.encode("utf-8"))


def _empty_sets() -> CodeSystemSets:
    # no code will ever match -> every element falls through to the narrative
    return CodeSystemSets()


def _sets_with(code: str, display: str, oid: str = SNOMED_OID) -> CodeSystemSets:
    return CodeSystemSets(
        oid_to_system_map={oid: "snomed"},
        system_to_code_maps={"snomed": {code: Coding(code, display, oid)}},
    )


# a section whose narrative parks the human label in a cell, and whose surviving
# value points at that cell through <originalText><reference/></originalText>
# with no @displayName of its own (a raw SNOMED value)
def _section_with_reference(
    *,
    ref_value: str = "#cough1",
    display_name: str | None = None,
    with_original_text: bool = True,
) -> _Element:
    dn = f' displayName="{display_name}"' if display_name is not None else ""
    original_text = (
        f"<originalText><reference value={ref_value!r}/></originalText>"
        if with_original_text
        else ""
    )
    return _el(
        f"""
    <section {_NSDECL}>
      <code code="30954-2" codeSystem="2.16.840.1.113883.6.1" displayName="Results"/>
      <text>
        <table><tbody>
          <tr><td><content ID="cough1">Paroxysmal cough (finding)</content></td></tr>
        </tbody></table>
      </text>
      <entry>
        <observation classCode="OBS" moodCode="EVN">
          <code displayName="Finding"/>
          <value xsi:type="CD" code="409586006"
                 codeSystem="2.16.840.1.113883.6.96"{dn}>
            {original_text}
          </value>
        </observation>
      </entry>
    </section>
    """
    )


def _value(section: _Element) -> _Element:
    return section.xpath(".//hl7:value", namespaces=HL7_NS)[0]


# NOTE:
# narrative-reference fallback in enrich_surviving_entries
# =============================================================================


def test_enrich_recovers_value_display_from_narrative_reference():
    # empty code sets -> the only display available is the narrative cell the
    # value references; enrichment stamps it onto @displayName
    section = _section_with_reference()
    enrich_surviving_entries(section, _empty_sets(), HL7_NS)
    assert _value(section).get("displayName") == "Paroxysmal cough (finding)"


def test_enrich_recovers_code_display_from_narrative_reference():
    # the same fallback applies to a <code> (not just <value>)
    section = _el(
        f"""
    <section {_NSDECL}>
      <text><content ID="p1">Colonic polypectomy</content></text>
      <entry>
        <procedure classCode="PROC" moodCode="EVN">
          <code code="274025005" codeSystem="2.16.840.1.113883.6.96">
            <originalText><reference value="#p1"/></originalText>
          </code>
        </procedure>
      </entry>
    </section>
    """
    )
    enrich_surviving_entries(section, _empty_sets(), HL7_NS)
    code = section.xpath(".//hl7:procedure/hl7:code", namespaces=HL7_NS)[0]
    assert code.get("displayName") == "Colonic polypectomy"


def test_enrich_code_sets_take_precedence_over_narrative():
    # when the jurisdiction code sets carry a display, that authoritative label
    # wins; the narrative fallback only fills what the code sets could not
    section = _section_with_reference()
    sets = _sets_with("409586006", "Cough (code set)")
    enrich_surviving_entries(section, sets, HL7_NS)
    assert _value(section).get("displayName") == "Cough (code set)"


def test_enrich_leaves_existing_display_name_untouched():
    # a value that already carries a display is never overwritten
    section = _section_with_reference(display_name="Sender label")
    enrich_surviving_entries(section, _empty_sets(), HL7_NS)
    assert _value(section).get("displayName") == "Sender label"


def test_enrich_dangling_reference_is_noop():
    # a reference to an id that is not in the narrative resolves to nothing;
    # no displayName is fabricated (render falls back to the bare code later)
    section = _section_with_reference(ref_value="#missing")
    enrich_surviving_entries(section, _empty_sets(), HL7_NS)
    assert _value(section).get("displayName") is None


def test_enrich_no_reference_is_noop():
    # a value with neither a code-set match nor a narrative reference is left
    # as-is
    section = _section_with_reference(with_original_text=False)
    enrich_surviving_entries(section, _empty_sets(), HL7_NS)
    assert _value(section).get("displayName") is None


# NOTE:
# enrich -> reconstruct handoff (the whole point: reconstruction needs no
# change; a label recovered at enrichment time flows through render_code_display)
# =============================================================================


def test_recovered_label_flows_into_reconstructed_narrative():
    # a Results section whose one result value is a raw SNOMED code with no
    # display of its own, only a narrative reference. after enrichment the
    # reconstructed table renders the recovered concept, not the bare code
    section = _el(
        f"""
    <section {_NSDECL}>
      <code code="30954-2" codeSystem="2.16.840.1.113883.6.1" displayName="Results"/>
      <text>
        <table><tbody>
          <tr><td><content ID="cough1">Paroxysmal cough (finding)</content></td></tr>
        </tbody></table>
      </text>
      <entry>
        <organizer classCode="BATTERY" moodCode="EVN">
          <code displayName="Respiratory panel"/>
          <component>
            <observation classCode="OBS" moodCode="EVN">
              <code displayName="Cough assay"/>
              <value xsi:type="CD" code="409586006"
                     codeSystem="2.16.840.1.113883.6.96">
                <originalText><reference value="#cough1"/></originalText>
              </value>
            </observation>
          </component>
        </organizer>
      </entry>
    </section>
    """
    )

    enrich_surviving_entries(section, _empty_sets(), HL7_NS)
    text = reconstruct_narrative(section, augmentation_timestamp="20240101000000+0000")

    assert text is not None
    outcome = text.xpath(".//hl7:tbody/hl7:tr/hl7:td", namespaces=HL7_NS)
    rendered = [td.text for td in outcome]
    assert "Paroxysmal cough (finding) (SNOMED CT 409586006)" in rendered


# NOTE:
# helpers
# =============================================================================


def test_index_narrative_display_ids_collapses_whitespace():
    section = _el(
        f"""
    <section {_NSDECL}>
      <text>
        <content ID="a">  Multi
            line   label </content>
        <paragraph>no id here</paragraph>
      </text>
    </section>
    """
    )
    index = _index_narrative_display_ids(section, HL7_NS)
    assert index == {"a": "Multi line label"}


def test_index_narrative_display_ids_no_text_returns_empty():
    section = _el(f'<section {_NSDECL}><code code="x"/></section>')
    assert _index_narrative_display_ids(section, HL7_NS) == {}


def test_resolve_reference_display_non_fragment_is_none():
    # a reference @value that is not a "#id" fragment pointer is ignored
    el = _el(
        f'<value {_NSDECL} code="1" codeSystem="x">'
        '<originalText><reference value="http://example/x"/></originalText></value>'
    )
    assert _resolve_reference_display(el, {"x": "unused"}, HL7_NS) is None


def test_resolve_reference_display_no_original_text_is_none():
    el = _el(f'<value {_NSDECL} code="1" codeSystem="x"/>')
    assert _resolve_reference_display(el, {"x": "unused"}, HL7_NS) is None
