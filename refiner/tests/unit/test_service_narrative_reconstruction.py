from lxml import etree
from lxml.etree import _Element

from app.services.ecr.model import HL7_NS
from app.services.ecr.narrative.reconstruction import (
    RESULT_FIELDS,
    FieldSpec,
    build_table,
    extract_fields,
    reconstruct_narrative,
    reconstruct_results,
    render_typed_value,
)

# NOTE:
# HELPERS
# =============================================================================


def _el(xml: str) -> _Element:
    return etree.fromstring(xml.encode("utf-8"))


_NSDECL = 'xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'


# NOTE:
# LAYER 1 — render_typed_value (the closed CDA data-type set)
# =============================================================================


def test_render_none_is_empty():
    assert render_typed_value(None) == ""


def test_render_cd_with_xsi_type():
    el = _el(f'<value {_NSDECL} xsi:type="CD" code="112283007" displayName="E. coli"/>')
    assert render_typed_value(el) == "E. coli (112283007)"


def test_render_cd_without_xsi_type_is_monomorphic_coded():
    # interpretationCode carries @code with no xsi:type — still coded
    el = _el(f'<interpretationCode {_NSDECL} code="A" displayName="Abnormal"/>')
    assert render_typed_value(el) == "Abnormal (A)"


def test_render_cd_code_only_falls_back_to_code():
    el = _el(f'<value {_NSDECL} xsi:type="CD" code="A"/>')
    assert render_typed_value(el) == "A"


def test_render_pq_with_xsi_type():
    el = _el(f'<value {_NSDECL} xsi:type="PQ" value="9.2" unit="g/dL"/>')
    assert render_typed_value(el) == "9.2 g/dL"


def test_render_pq_monomorphic_dose_quantity():
    # doseQuantity is PQ by the CDA model — no xsi:type
    el = _el(f'<doseQuantity {_NSDECL} value="1" unit="tablet"/>')
    assert render_typed_value(el) == "1 tablet"


def test_render_st():
    el = _el(f'<value {_NSDECL} xsi:type="ST">free text</value>')
    assert render_typed_value(el) == "free text"


def test_render_ivl_ts_low_and_high():
    el = _el(
        f'<effectiveTime {_NSDECL} xsi:type="IVL_TS">'
        '<low value="20240115"/><high value="20240122"/></effectiveTime>'
    )
    assert render_typed_value(el) == "20240115 to 20240122"


def test_render_ivl_ts_low_only():
    el = _el(f'<effectiveTime {_NSDECL}><low value="20240115"/></effectiveTime>')
    assert render_typed_value(el) == "20240115"


def test_render_pivl_ts_frequency():
    el = _el(
        f'<effectiveTime {_NSDECL} xsi:type="PIVL_TS">'
        '<period value="8" unit="h"/></effectiveTime>'
    )
    assert render_typed_value(el) == "every 8 h"


def test_render_bare_value():
    el = _el(f'<effectiveTime {_NSDECL} value="20240115"/>')
    assert render_typed_value(el) == "20240115"


# NOTE:
# LAYER 1 — extract_fields
# =============================================================================


def test_extract_fields_attr_typed_and_missing():
    obs = _el(
        f"<observation {_NSDECL}>"
        '<code displayName="Hemoglobin"/>'
        '<value xsi:type="PQ" value="9.2" unit="g/dL"/>'
        "</observation>"
    )
    fields = [
        FieldSpec("Test", "hl7:code/@displayName", "attr"),
        FieldSpec("Result", "hl7:value", "typed"),
        FieldSpec("Missing", "hl7:interpretationCode/@code", "attr"),
    ]
    assert extract_fields(obs, fields) == {
        "Test": "Hemoglobin",
        "Result": "9.2 g/dL",
        "Missing": "",
    }


# NOTE:
# LAYER 1 — build_table
# =============================================================================


def test_build_table_structure_and_provenance_marker():
    text = build_table(["A", "B"], [{"A": "1", "B": "2"}, {"A": "3", "B": ""}])

    # namespace-qualified <text>
    assert text.tag == "{urn:hl7-org:v3}text"

    # block-level machine-derived marker as an XML comment with no double dash
    comments = [c for c in text.iter() if isinstance(c, etree._Comment)]
    assert len(comments) == 1
    assert "machine-derived" in comments[0].text
    assert "--" not in comments[0].text

    headers = text.xpath(".//hl7:thead/hl7:tr/hl7:th/text()", namespaces=HL7_NS)
    assert headers == ["A", "B"]

    body_rows = text.xpath(".//hl7:tbody/hl7:tr", namespaces=HL7_NS)
    assert len(body_rows) == 2
    first_cells = body_rows[0].xpath("hl7:td/text()", namespaces=HL7_NS)
    assert first_cells == ["1", "2"]


# NOTE:
# LAYER 3 — reconstruct_results (the join)
# =============================================================================

# two organizers; the first holds TWO result observations so the panel and
# specimen context must fan out across both rows without bleeding into the
# second organizer's row
_RESULTS_SECTION = f"""
<section {_NSDECL}>
  <code code="30954-2" codeSystem="2.16.840.1.113883.6.1" displayName="Results"/>
  <title>Results</title>
  <text>...original clinician narrative...</text>
  <entry>
    <organizer classCode="BATTERY" moodCode="EVN">
      <code displayName="CBC panel"/>
      <component>
        <procedure classCode="PROC" moodCode="EVN">
          <participant typeCode="SBJ"><participantRole><playingEntity>
            <code displayName="Blood specimen"/>
          </playingEntity></participantRole></participant>
        </procedure>
      </component>
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <code displayName="Hemoglobin"/>
          <effectiveTime value="20240115"/>
          <value xsi:type="PQ" value="9.2" unit="g/dL"/>
          <interpretationCode code="L" displayName="Low"/>
        </observation>
      </component>
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <code displayName="Bacteria identified"/>
          <effectiveTime value="20240115"/>
          <value xsi:type="CD" code="112283007" displayName="E. coli"/>
        </observation>
      </component>
    </organizer>
  </entry>
  <entry>
    <organizer classCode="BATTERY" moodCode="EVN">
      <code displayName="Glucose panel"/>
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <code displayName="Glucose"/>
          <effectiveTime value="20240116"/>
          <value xsi:type="PQ" value="105" unit="mg/dL"/>
        </observation>
      </component>
    </organizer>
  </entry>
</section>
"""


def test_reconstruct_results_columns():
    columns, _ = reconstruct_results(_el(_RESULTS_SECTION))
    assert columns == ["Panel", "Specimen", "Test", "Result", "Interpretation", "Date"]


def test_reconstruct_results_fans_context_across_rows_without_bleed():
    _, rows = reconstruct_results(_el(_RESULTS_SECTION))

    assert len(rows) == 3

    # both rows of the first organizer share its panel + specimen context
    assert rows[0] == {
        "Panel": "CBC panel",
        "Specimen": "Blood specimen",
        "Test": "Hemoglobin",
        "Result": "9.2 g/dL",
        "Interpretation": "Low (L)",
        "Date": "20240115",
    }
    assert rows[1]["Panel"] == "CBC panel"
    assert rows[1]["Specimen"] == "Blood specimen"
    assert rows[1]["Result"] == "E. coli (112283007)"
    assert rows[1]["Interpretation"] == ""  # no interpretationCode on this obs

    # the second organizer's row does NOT inherit the first's context
    assert rows[2]["Panel"] == "Glucose panel"
    assert rows[2]["Specimen"] == ""  # no procedure in this organizer
    assert rows[2]["Result"] == "105 mg/dL"


# NOTE:
# DISPATCH — reconstruct_narrative
# =============================================================================


def test_reconstruct_narrative_results_returns_text_table():
    text = reconstruct_narrative(_el(_RESULTS_SECTION))
    assert text is not None
    assert text.tag == "{urn:hl7-org:v3}text"
    body_rows = text.xpath(".//hl7:tbody/hl7:tr", namespaces=HL7_NS)
    assert len(body_rows) == 3


def test_reconstruct_narrative_unknown_loinc_returns_none():
    section = _el(
        f'<section {_NSDECL}><code code="29762-2" displayName="Social History"/>'
        "<entry/></section>"
    )
    assert reconstruct_narrative(section) is None


def test_reconstruct_narrative_does_not_mutate_section():
    section = _el(_RESULTS_SECTION)
    before = etree.tostring(section)
    reconstruct_narrative(section)
    assert etree.tostring(section) == before


def test_result_fields_use_typed_interpretation():
    # guard the design choice: interpretation renders via the typed renderer
    # so it humanizes (Low (L)) with graceful fallback, not a bare code
    spec = {f.label: f for f in RESULT_FIELDS}["Interpretation"]
    assert spec.kind == "typed"
    assert spec.xpath == "hl7:interpretationCode"
