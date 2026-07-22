from lxml import etree
from lxml.etree import _Element

from app.services.ecr.model import HL7_NS
from app.services.ecr.narrative.identifiers import compact_reconstruction_references
from app.services.ecr.narrative.reconstruction import (
    RESULT_FIELDS,
    Block,
    DetailRow,
    FieldSpec,
    extract_fields,
    format_ts,
    reconstruct_immunizations,
    reconstruct_medications,
    reconstruct_narrative,
    reconstruct_problems,
    reconstruct_results,
    render_code_display,
    render_coded_concept,
    render_interpretation,
    render_section_text,
    render_typed_value,
)

# a fixed run stamp so minted row IDs are deterministic in assertions
_RUN_TS = "20240101000000+0000"

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


def test_render_cd_with_xsi_type_surfaces_system_and_code():
    # a CD value is a clinical concept: display (System code), system from OID
    el = _el(
        f'<value {_NSDECL} xsi:type="CD" code="112283007" '
        'codeSystem="2.16.840.1.113883.6.96" displayName="E. coli"/>'
    )
    assert render_typed_value(el) == "E. coli (SNOMED CT 112283007)"


def test_render_cd_without_xsi_type_is_monomorphic_coded():
    # any @code-bearing element routes through the concept renderer; the
    # admin/clinical distinction is made at the field-map kind, not here
    el = _el(f'<interpretationCode {_NSDECL} code="A" displayName="Abnormal"/>')
    assert render_typed_value(el) == "Abnormal (A)"


def test_render_cd_code_only_has_no_redundant_parens():
    # no human display beyond the code → just the code, not "A (A)"
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
    assert render_typed_value(el) == "2024-01-15 to 2024-01-22"


def test_render_ivl_ts_equal_bounds_collapse_to_single_value():
    # an EHR renders a low==high panel time as one timestamp, not "X to X"
    el = _el(
        f'<effectiveTime {_NSDECL} xsi:type="IVL_TS">'
        '<low value="20240115"/><high value="20240115"/></effectiveTime>'
    )
    assert render_typed_value(el) == "2024-01-15"


def test_render_ivl_ts_low_only():
    el = _el(f'<effectiveTime {_NSDECL}><low value="20240115"/></effectiveTime>')
    assert render_typed_value(el) == "2024-01-15"


def test_render_ivl_pq_reference_range_keeps_units():
    # an IVL_PQ reference range: each bound is a PQ, so the unit rides along
    # (format_ts would silently drop it)
    el = _el(
        f'<value {_NSDECL} xsi:type="IVL_PQ">'
        '<low unit="g/dL" value="13.5"/><high unit="g/dL" value="17.5"/></value>'
    )
    assert render_typed_value(el) == "13.5 g/dL to 17.5 g/dL"


def test_render_ivl_pq_high_only_bound():
    el = _el(
        f'<value {_NSDECL} xsi:type="IVL_PQ">'
        '<high inclusive="false" unit="[iU]/mL" value="45"/></value>'
    )
    assert render_typed_value(el) == "45 [iU]/mL"


def test_render_pivl_ts_frequency():
    el = _el(
        f'<effectiveTime {_NSDECL} xsi:type="PIVL_TS">'
        '<period value="8" unit="h"/></effectiveTime>'
    )
    assert render_typed_value(el) == "every 8 h"


def test_render_bare_value():
    el = _el(f'<effectiveTime {_NSDECL} value="20240115"/>')
    assert render_typed_value(el) == "2024-01-15"


# NOTE:
# LAYER 1 — format_ts (human-readable HL7 TS, source precision preserved)
# =============================================================================


def test_format_ts_year_only():
    assert format_ts("2020") == "2020"


def test_format_ts_year_month():
    assert format_ts("202011") == "2020-11"


def test_format_ts_date():
    assert format_ts("20201107") == "2020-11-07"


def test_format_ts_datetime_minutes():
    assert format_ts("202011071159") == "2020-11-07 11:59"


def test_format_ts_datetime_seconds():
    assert format_ts("20201107115930") == "2020-11-07 11:59:30"


def test_format_ts_with_offset():
    assert format_ts("202011071159-0700") == "2020-11-07 11:59 -07:00"


def test_format_ts_date_with_offset_keeps_precision():
    # no fabricated time components when only the date is present
    assert format_ts("20201107+0000") == "2020-11-07 +00:00"


def test_format_ts_empty_and_none():
    assert format_ts("") == ""
    assert format_ts(None) == ""


def test_format_ts_non_ts_passes_through():
    # not a TS (e.g. a nullFlavor token slipping in) → unchanged
    assert format_ts("UNK") == "UNK"


# NOTE:
# LAYER 1 — render_code_display (the real-data display-name fallback chain)
# =============================================================================


def test_code_display_none_is_empty():
    assert render_code_display(None) == ""


def test_code_display_prefers_display_name_attr():
    el = _el(f'<code {_NSDECL} code="60544-4" displayName="Giardia lamblia, NAAT"/>')
    assert render_code_display(el) == "Giardia lamblia, NAAT"


def test_code_display_falls_back_to_original_text():
    # real epic (EHR) shape: no @displayName, label in <originalText> wrapping a
    # <reference> into the narrative; whitespace is normalized
    el = _el(
        f'<code {_NSDECL} code="79381-0">'
        "<originalText>Stool Pathogens,\n   NAAT, Parasite"
        '<reference value="#Result.Comp1Name"/></originalText>'
        "</code>"
    )
    assert render_code_display(el) == "Stool Pathogens, NAAT, Parasite"


def test_code_display_falls_back_to_translation_display_name():
    el = _el(
        f'<code {_NSDECL} code="79381-0">'
        '<translation code="LAB24189" displayName="STOOL PATHOGENS, NAAT, PARASITE"/>'
        "</code>"
    )
    assert render_code_display(el) == "STOOL PATHOGENS, NAAT, PARASITE"


def test_code_display_falls_back_to_bare_code():
    el = _el(f'<code {_NSDECL} code="79381-0"/>')
    assert render_code_display(el) == "79381-0"


def test_code_display_nullflavor_primary_resolves_translation_display():
    # fickle immunization: nullFlavor primary CVX, real vaccine in translation
    el = _el(
        f'<code {_NSDECL} nullFlavor="OTH">'
        '<translation code="207" codeSystem="2.16.840.1.113883.12.292" '
        'displayName="COVID-19 mRNA vaccine"/>'
        "</code>"
    )
    assert render_code_display(el) == "COVID-19 mRNA vaccine"


def test_code_display_nullflavor_primary_falls_back_to_translation_code():
    # translation carries a code but no displayName — better than blank
    el = _el(
        f'<code {_NSDECL} nullFlavor="OTH">'
        '<translation code="207" codeSystem="2.16.840.1.113883.12.292"/>'
        "</code>"
    )
    assert render_code_display(el) == "207"


def test_render_typed_cd_resolves_through_original_text():
    # a CD value with no @displayName resolves its display via originalText,
    # then still surfaces the system + code
    el = _el(
        f'<value {_NSDECL} xsi:type="CD" code="35064005" '
        'codeSystem="2.16.840.1.113883.6.96">'
        "<originalText>Dark stools (finding)</originalText>"
        "</value>"
    )
    assert render_typed_value(el) == "Dark stools (finding) (SNOMED CT 35064005)"


# NOTE:
# LAYER 1 — render_interpretation (HL7 ObservationInterpretation flag display)
# =============================================================================


def test_interpretation_none_is_empty():
    assert render_interpretation(None) == ""


def test_interpretation_maps_bare_code_to_canonical_display():
    # the real-data case: sender gives only @code, no @displayName — "A" reads
    # as noise, so we substitute the canonical flag
    for code, expected in (("A", "Abnormal"), ("H", "High"), ("L", "Low")):
        el = _el(
            f'<interpretationCode {_NSDECL} code="{code}" '
            'codeSystem="2.16.840.1.113883.5.83"/>'
        )
        assert render_interpretation(el) == expected


def test_interpretation_prefers_sender_display_name():
    # when the sender DID label it, we keep their words rather than override
    el = _el(
        f'<interpretationCode {_NSDECL} code="A" '
        'codeSystem="2.16.840.1.113883.5.83" displayName="Abnormal alert"/>'
    )
    assert render_interpretation(el) == "Abnormal alert"


def test_interpretation_unmapped_code_returns_bare_code():
    # never hide an interpretation we do not recognize
    el = _el(
        f'<interpretationCode {_NSDECL} code="ZZZ" '
        'codeSystem="2.16.840.1.113883.5.83"/>'
    )
    assert render_interpretation(el) == "ZZZ"


# NOTE:
# LAYER 1 — render_coded_concept (display + system + code for clinical concepts)
# =============================================================================


def test_coded_concept_code_with_known_system():
    el = _el(
        f'<code {_NSDECL} code="105066-5" codeSystem="2.16.840.1.113883.6.1" '
        'displayName="SARS-CoV-2 Ag"/>'
    )
    assert render_coded_concept(el) == "SARS-CoV-2 Ag (LOINC 105066-5)"


def test_coded_concept_oid_only_resolves_via_oid_not_codesystemname():
    # source carries the OID but NO codeSystemName (or a variant spelling);
    # the system name still resolves canonically from the OID
    el = _el(
        f'<value {_NSDECL} xsi:type="CD" code="1119303003" '
        'codeSystem="2.16.840.1.113883.6.96" '
        'displayName="Post-acute COVID-19 (disorder)"/>'
    )
    assert (
        render_coded_concept(el)
        == "Post-acute COVID-19 (disorder) (SNOMED CT 1119303003)"
    )


def test_coded_concept_unknown_system_omits_system_label():
    el = _el(f'<code {_NSDECL} code="XYZ" codeSystem="9.9.9" displayName="Mystery"/>')
    assert render_coded_concept(el) == "Mystery (XYZ)"


def test_coded_concept_nullflavor_code_is_display_only():
    # nullFlavor primary, real product in a translation → display only, no parens
    el = _el(
        f'<code {_NSDECL} nullFlavor="OTH">'
        '<translation code="207" codeSystem="2.16.840.1.113883.12.292" '
        'displayName="COVID-19 mRNA vaccine"/>'
        "</code>"
    )
    assert render_coded_concept(el) == "COVID-19 mRNA vaccine"


def test_coded_concept_display_only_when_no_code():
    el = _el(f'<code {_NSDECL} displayName="Blood specimen"/>')
    assert render_coded_concept(el) == "Blood specimen"


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
# LAYER 1 — render_section_text (block assembler: tables, IDs, relinking)
# =============================================================================


def _obs(test: str) -> _Element:
    return _el(f'<observation {_NSDECL}><code displayName="{test}"/></observation>')


def test_render_section_text_block_structure_and_provenance_marker():
    obs = _obs("Hemoglobin")
    block = Block(
        context={"Panel": "CBC", "Date(s)": "20240115"},
        columns=["Test", "Outcome"],
        rows=[DetailRow(source=obs, values={"Test": "Hemoglobin", "Outcome": "9.2"})],
    )

    text = render_section_text([block], loinc="30954-2", augmentation_timestamp=_RUN_TS)

    assert text.tag == "{urn:hl7-org:v3}text"

    # block-level machine-derived marker as an XML comment with no double dash
    comments = [c for c in text.iter() if isinstance(c, etree._Comment)]
    assert len(comments) == 1
    assert "machine-derived" in comments[0].text
    assert "--" not in comments[0].text

    # two tables per block: a one-row context table, then the detail table
    tables = text.xpath("hl7:table", namespaces=HL7_NS)
    assert len(tables) == 2

    context_headers = tables[0].xpath(".//hl7:th/text()", namespaces=HL7_NS)
    assert context_headers == ["Panel", "Date(s)"]
    context_cells = tables[0].xpath(
        ".//hl7:tbody/hl7:tr/hl7:td/text()", namespaces=HL7_NS
    )
    assert context_cells == ["CBC", "20240115"]

    detail_headers = tables[1].xpath(".//hl7:th/text()", namespaces=HL7_NS)
    assert detail_headers == ["Test", "Outcome"]


def test_render_section_text_mints_ids_and_relinks_source():
    obs = _obs("Hemoglobin")
    block = Block(
        context={},
        columns=["Test"],
        rows=[DetailRow(source=obs, values={"Test": "Hemoglobin"})],
    )

    text = render_section_text([block], loinc="30954-2", augmentation_timestamp=_RUN_TS)

    # the detail row carries a minted, run-stamped, document-unique xs:ID
    row = text.xpath(".//hl7:tbody/hl7:tr", namespaces=HL7_NS)[0]
    row_id = row.get("ID")
    assert row_id == "ecr-refiner-30954-2-20240101000000-row1"

    # and the source observation is relinked to that row
    ref = obs.xpath("hl7:text/hl7:reference/@value", namespaces=HL7_NS)
    assert ref == [f"#{row_id}"]


# NOTE:
# LAYER 3 — reconstruct_results (per-organizer blocks)
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
      <code code="58410-2" codeSystem="2.16.840.1.113883.6.1" displayName="CBC panel"/>
      <performer>
        <assignedEntity>
          <representedOrganization>
            <name>Acme Reference Lab</name>
          </representedOrganization>
        </assignedEntity>
      </performer>
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
          <referenceRange><observationRange>
            <value xsi:type="IVL_PQ">
              <low unit="g/dL" value="13.5"/><high unit="g/dL" value="17.5"/>
            </value>
          </observationRange></referenceRange>
        </observation>
      </component>
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <code displayName="Bacteria identified"/>
          <effectiveTime value="20240115"/>
          <value xsi:type="CD" code="112283007"
                 codeSystem="2.16.840.1.113883.6.96" displayName="E. coli"/>
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


def test_reconstruct_results_one_block_per_organizer():
    blocks = reconstruct_results(_el(_RESULTS_SECTION))

    # one block per organizer with surviving observations
    assert len(blocks) == 2
    assert blocks[0].columns == [
        "Test",
        "Outcome",
        "Interpretation",
        "Reference Range",
        "Date(s)",
    ]


def test_reconstruct_results_context_is_per_block_not_repeated_on_rows():
    blocks = reconstruct_results(_el(_RESULTS_SECTION))

    # the first organizer's context carries panel + performer + specimen, once.
    # Panel surfaces system + code; Performer is the performing org name reached
    # off the panel; Specimen has no @code so it stays display-only
    assert blocks[0].context == {
        "Panel": "CBC panel (LOINC 58410-2)",
        "Date(s)": "",  # no organizer effectiveTime in the fixture
        "Performer": "Acme Reference Lab",
        "Result Status": "",  # no Laboratory Result Status component
        "Specimen": "Blood specimen",
        "Target Site": "",
    }
    # its two result rows are the detail, with NO context smeared in
    assert len(blocks[0].rows) == 2
    assert blocks[0].rows[0].values == {
        "Test": "Hemoglobin",  # no @code in the fixture → display-only
        "Outcome": "9.2 g/dL",
        "Interpretation": "Low",
        "Reference Range": "13.5 g/dL to 17.5 g/dL",  # IVL_PQ bounds keep units
        "Date(s)": "2024-01-15",
    }
    # the CD result value surfaces its system + code
    assert blocks[0].rows[1].values["Outcome"] == "E. coli (SNOMED CT 112283007)"
    assert blocks[0].rows[1].values["Interpretation"] == ""

    # the second organizer is its own block; no bleed from the first
    assert blocks[1].context["Panel"] == "Glucose panel"
    assert blocks[1].context["Specimen"] == ""  # no procedure in this organizer
    assert blocks[1].rows[0].values["Outcome"] == "105 mg/dL"


# NOTE:
# LAYER 3 — reconstruct_problems (concern act -> problem observations)
# =============================================================================

# one concern act holding two problem observations; the second problem has a
# resolved date (low+high) and resolves its display via originalText
_PROBLEMS_SECTION = f"""
<section {_NSDECL}>
  <code code="11450-4" codeSystem="2.16.840.1.113883.6.1" displayName="Problem List"/>
  <title>Problems</title>
  <text>...original clinician narrative...</text>
  <entry>
    <act classCode="ACT" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
      <statusCode code="active"/>
      <effectiveTime><low value="20251107"/></effectiveTime>
      <entryRelationship typeCode="SUBJ">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
          <code code="75325-1" displayName="Symptom"/>
          <effectiveTime><low value="20251101"/></effectiveTime>
          <value xsi:type="CD" code="35064005"
                 codeSystem="2.16.840.1.113883.6.96" displayName="Dark stools (finding)"/>
        </observation>
      </entryRelationship>
      <entryRelationship typeCode="SUBJ">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
          <code code="75322-8" displayName="Complaint"/>
          <effectiveTime><low value="20251104"/><high value="20251110"/></effectiveTime>
          <value xsi:type="CD" code="409586006"
                 codeSystem="2.16.840.1.113883.6.96">
            <originalText>Paroxysmal cough (finding)</originalText>
          </value>
        </observation>
      </entryRelationship>
    </act>
  </entry>
</section>
"""


def test_reconstruct_problems_one_block_per_concern():
    blocks = reconstruct_problems(_el(_PROBLEMS_SECTION))
    assert len(blocks) == 1
    assert blocks[0].columns == ["Problem Type", "Problem", "Date(s)"]


def test_reconstruct_problems_concern_context_and_problem_rows():
    blocks = reconstruct_problems(_el(_PROBLEMS_SECTION))

    # concern context: status + noted date, rendered once
    assert blocks[0].context == {"Concern Status": "active", "Date(s)": "2025-11-07"}

    # the two problem observations are the detail rows
    assert len(blocks[0].rows) == 2
    # Problem Type (assertion code) is display-only; the Problem surfaces system
    assert blocks[0].rows[0].values == {
        "Problem Type": "Symptom",
        "Problem": "Dark stools (finding) (SNOMED CT 35064005)",
        "Date(s)": "2025-11-01",
    }
    # second problem: display via originalText, resolved range (low to high)
    assert blocks[0].rows[1].values == {
        "Problem Type": "Complaint",
        "Problem": "Paroxysmal cough (finding) (SNOMED CT 409586006)",
        "Date(s)": "2025-11-04 to 2025-11-10",
    }


def test_reconstruct_problems_ignores_priority_preference_refr():
    # a Problem Concern Act permits a Priority Preference (...22.4.143) under
    # entryRelationship[@typeCode='REFR']. it is an <observation>, so an
    # unfiltered row anchor renders it as a phantom problem. only the SUBJ
    # Problem Observation is a real row
    section = _el(
        f"""
    <section {_NSDECL}>
      <code code="11450-4" codeSystem="2.16.840.1.113883.6.1"/>
      <entry>
        <act classCode="ACT" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
          <statusCode code="active"/>
          <entryRelationship typeCode="SUBJ">
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
              <code code="75322-8" displayName="Complaint"/>
              <value xsi:type="CD" code="35064005"
                     codeSystem="2.16.840.1.113883.6.96"
                     displayName="Dark stools (finding)"/>
            </observation>
          </entryRelationship>
          <entryRelationship typeCode="REFR">
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.143"/>
              <code code="63161005" codeSystem="2.16.840.1.113883.6.96"
                    displayName="Principal"/>
            </observation>
          </entryRelationship>
        </act>
      </entry>
    </section>
    """
    )

    blocks = reconstruct_problems(section)
    assert len(blocks) == 1
    problems = [row.values["Problem"] for row in blocks[0].rows]
    assert problems == ["Dark stools (finding) (SNOMED CT 35064005)"], (
        "the Priority Preference REFR observation leaked in as a problem row"
    )


# NOTE:
# LAYER 3 — reconstruct_immunizations (FLAT: one row per substanceAdministration)
# =============================================================================

# two vaccines: the first resolves its display directly; the second is the
# fickle case — nullFlavor primary CVX with the real vaccine in a translation
_IMMUNIZATIONS_SECTION = f"""
<section {_NSDECL}>
  <code code="11369-6" codeSystem="2.16.840.1.113883.6.1" displayName="Immunizations"/>
  <title>Immunizations</title>
  <text>...original clinician narrative...</text>
  <entry>
    <substanceAdministration classCode="SBADM" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
      <id root="00000000-0000-0000-0000-000000000001"/>
      <statusCode code="completed"/>
      <effectiveTime value="20201107"/>
      <consumable>
        <manufacturedProduct>
          <manufacturedMaterial>
            <code code="2563008" codeSystem="2.16.840.1.113883.6.88"
                  displayName="Flucelvax Quadrivalent"/>
          </manufacturedMaterial>
        </manufacturedProduct>
      </consumable>
    </substanceAdministration>
  </entry>
  <entry>
    <substanceAdministration classCode="SBADM" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
      <id root="00000000-0000-0000-0000-000000000002"/>
      <statusCode code="completed"/>
      <effectiveTime value="20201201"/>
      <consumable>
        <manufacturedProduct>
          <manufacturedMaterial>
            <code nullFlavor="OTH">
              <translation code="207" codeSystem="2.16.840.1.113883.12.292"
                           displayName="COVID-19 mRNA vaccine"/>
            </code>
          </manufacturedMaterial>
        </manufacturedProduct>
      </consumable>
    </substanceAdministration>
  </entry>
</section>
"""


def test_reconstruct_immunizations_is_flat_single_block():
    blocks = reconstruct_immunizations(_el(_IMMUNIZATIONS_SECTION))

    # flat: exactly one block, empty context, one row per substanceAdministration
    assert len(blocks) == 1
    assert blocks[0].context == {}
    assert blocks[0].columns == ["Immunization", "Date", "Status"]
    assert len(blocks[0].rows) == 2


def test_reconstruct_immunizations_resolves_vaccine_including_translation():
    blocks = reconstruct_immunizations(_el(_IMMUNIZATIONS_SECTION))
    rows = blocks[0].rows

    assert rows[0].values == {
        "Immunization": "Flucelvax Quadrivalent (RxNorm 2563008)",
        "Date": "2020-11-07",
        "Status": "completed",
    }
    # the fickle one: nullFlavor primary → display-only via the translation
    # (no parenthetical, since the primary @code is absent)
    assert rows[1].values["Immunization"] == "COVID-19 mRNA vaccine"


def test_reconstruct_immunizations_renders_single_table_no_context():
    text = render_section_text(
        reconstruct_immunizations(_el(_IMMUNIZATIONS_SECTION)),
        loinc="11369-6",
        augmentation_timestamp=_RUN_TS,
    )
    # flat section → exactly one table (no context table), two detail rows
    tables = text.xpath("hl7:table", namespaces=HL7_NS)
    assert len(tables) == 1
    rows = text.xpath(".//hl7:tbody/hl7:tr[@ID]", namespaces=HL7_NS)
    assert len(rows) == 2


def test_reconstruct_immunizations_relink_places_text_validly():
    # substanceAdministration has no <code>; the relinked <text> must land
    # after templateId/id (not before templateId, which would be invalid)
    section = _el(_IMMUNIZATIONS_SECTION)
    reconstruct_narrative(section, augmentation_timestamp=_RUN_TS)

    sbadm = section.find("hl7:entry/hl7:substanceAdministration", HL7_NS)
    children = [etree.QName(c).localname for c in sbadm if c.tag is not etree.Comment]
    # <text> sits after templateId and id, before statusCode
    assert children.index("text") > children.index("id")
    assert children.index("text") < children.index("statusCode")
    ref = sbadm.xpath("hl7:text/hl7:reference/@value", namespaces=HL7_NS)
    assert ref == ["#ecr-refiner-11369-6-20240101000000-row1"]


# NOTE:
# LAYER 3 — reconstruct_medications (FLAT, twin of immunizations)
# =============================================================================

# one med carrying BOTH effectiveTimes a Medication Activity may have: an
# IVL_TS administration window and a PIVL_TS dosing frequency. values humanize
# via the typed renderer (dose "1 g", route "ORAL"), matching the v3 convention
_MEDICATIONS_SECTION = f"""
<section {_NSDECL}>
  <code code="29549-3" codeSystem="2.16.840.1.113883.6.1"
        displayName="Medications Administered"/>
  <title>Medications Administered</title>
  <text>...original clinician narrative...</text>
  <entry>
    <substanceAdministration classCode="SBADM" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
      <id root="00000000-0000-0000-0000-0000000000aa"/>
      <statusCode code="completed"/>
      <effectiveTime xsi:type="IVL_TS"><low value="20120318"/></effectiveTime>
      <effectiveTime xsi:type="PIVL_TS"><period value="8" unit="h"/></effectiveTime>
      <routeCode code="C38288" codeSystem="2.16.840.1.113883.3.26.1.1"
                 displayName="ORAL"/>
      <doseQuantity value="1" unit="g"/>
      <consumable>
        <manufacturedProduct>
          <manufacturedMaterial>
            <code code="1115699" codeSystem="2.16.840.1.113883.6.88"
                  displayName="oseltamivir 6 MG/ML [Tamiflu]"/>
          </manufacturedMaterial>
        </manufacturedProduct>
      </consumable>
    </substanceAdministration>
  </entry>
</section>
"""


def test_reconstruct_medications_is_flat_with_convention_columns():
    blocks = reconstruct_medications(_el(_MEDICATIONS_SECTION))

    assert len(blocks) == 1
    assert blocks[0].context == {}
    assert blocks[0].columns == [
        "Medication",
        "Dose",
        "Duration",
        "Frequency",
        "Route",
    ]
    # the two effectiveTimes land in distinct columns: the IVL_TS window as
    # Duration, the PIVL_TS as Frequency (unreachable before the split)
    assert blocks[0].rows[0].values == {
        "Medication": "oseltamivir 6 MG/ML [Tamiflu] (RxNorm 1115699)",
        "Dose": "1 g",
        "Duration": "2012-03-18",
        "Frequency": "every 8 h",
        "Route": "ORAL (NCI Thesaurus C38288)",
    }


# NOTE:
# negationInd — "No Known Medications" (eICR STU 3.1.1 Vol 2 Figure 75)
# =============================================================================
# the ONLY appearance of SNOMED 410942007 in either eICR IG: a Medication
# Activity with @negationInd="true", a nullFlavor="OTH" material code, and the
# generic "drug or medication" carried in a translation. rendered as an ordinary
# row it reads "drug or medication" for a patient who HAS no medications--a
# false clinical assertion. negation is a property of the ROW, so the flag is
# read off the anchor and surfaced in the leading cell

# verbatim from Figure 75 (nullFlavor code + 410942007 translation)
_NO_KNOWN_MEDICATIONS_SECTION = f"""
<section {_NSDECL}>
  <code code="29549-3" codeSystem="2.16.840.1.113883.6.1"
        displayName="Medications Administered"/>
  <text>...original clinician narrative...</text>
  <entry>
    <substanceAdministration classCode="SBADM" moodCode="EVN" negationInd="true">
      <templateId root="2.16.840.1.113883.10.20.22.4.16" extension="2014-06-09"/>
      <id root="072f00fc-4f9d-4516-8d6f-ed00ed523fe0"/>
      <statusCode code="active"/>
      <effectiveTime xsi:type="IVL_TS"><low value="20110103"/></effectiveTime>
      <consumable>
        <manufacturedProduct classCode="MANU">
          <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
          <manufacturedMaterial>
            <code nullFlavor="OTH" codeSystem="2.16.840.1.113883.6.88">
              <translation code="410942007" displayName="drug or medication"
                           codeSystem="2.16.840.1.113883.6.96"
                           codeSystemName="SNOMED CT"/>
            </code>
          </manufacturedMaterial>
        </manufacturedProduct>
      </consumable>
    </substanceAdministration>
  </entry>
</section>
"""


def test_no_known_medications_row_is_flagged_negated():
    blocks = reconstruct_medications(_el(_NO_KNOWN_MEDICATIONS_SECTION))

    assert len(blocks) == 1
    assert blocks[0].rows[0].negated is True


def test_no_known_medications_renders_as_a_negative_not_a_product():
    section = _el(_NO_KNOWN_MEDICATIONS_SECTION)
    text = reconstruct_narrative(section, augmentation_timestamp=_RUN_TS)
    assert text is not None

    cells = [
        td.text for td in text.xpath(".//hl7:tbody/hl7:tr/hl7:td", namespaces=HL7_NS)
    ]
    # the leading cell reads as a negative; the bare "drug or medication" that
    # would falsely assert an administered product never stands alone
    assert cells[0] == "Not administered: drug or medication"
    assert "drug or medication" not in cells[1:]


# NOTE:
# DISPATCH — reconstruct_narrative
# =============================================================================


def test_reconstruct_narrative_results_returns_block_tables():
    text = reconstruct_narrative(_el(_RESULTS_SECTION), augmentation_timestamp=_RUN_TS)
    assert text is not None
    assert text.tag == "{urn:hl7-org:v3}text"
    # one detail row per surviving observation across both organizer blocks
    detail_rows = text.xpath(".//hl7:tbody/hl7:tr[@ID]", namespaces=HL7_NS)
    assert len(detail_rows) == 3


def test_reconstruct_narrative_unknown_loinc_returns_none():
    section = _el(
        f'<section {_NSDECL}><code code="29762-2" displayName="Social History"/>'
        "<entry/></section>"
    )
    assert reconstruct_narrative(section, augmentation_timestamp=_RUN_TS) is None


def test_reconstruct_narrative_relinks_surviving_entries():
    # ADR 0011: reconstruction now MUTATES the section — it strips the stale
    # narrative references and relinks each surviving observation to its row
    section = _el(_RESULTS_SECTION)
    reconstruct_narrative(section, augmentation_timestamp=_RUN_TS)

    # every surviving result observation now references a reconstructed row ID
    refs = section.xpath(
        "hl7:entry/hl7:organizer/hl7:component/hl7:observation"
        "/hl7:text/hl7:reference/@value",
        namespaces=HL7_NS,
    )
    assert len(refs) == 3
    assert all(r.startswith("#ecr-refiner-30954-2-") for r in refs)


def test_reconstruct_narrative_marks_entries_derived():
    # the narrative is rebuilt FROM the entries, so the entry↔narrative
    # relationship is DRIV ("derived from"), not the schema default COMP
    section = _el(_RESULTS_SECTION)
    reconstruct_narrative(section, augmentation_timestamp=_RUN_TS)

    type_codes = section.xpath("hl7:entry/@typeCode", namespaces=HL7_NS)
    assert type_codes == ["DRIV", "DRIV"]


def test_reconstruct_narrative_inlines_coding_originaltext_reference():
    # a surviving value carries its label as originalText-BY-REFERENCE into the
    # narrative. reconstruction strips the stale row-level references, but the
    # coding-level originalText must survive as INLINE text — not be emptied,
    # which would destroy the sender's coding provenance in the shipped data
    section = _el(
        f"""
    <section {_NSDECL}>
      <code code="30954-2" codeSystem="2.16.840.1.113883.6.1"/>
      <text>
        <table><tbody>
          <tr><td><content ID="cough1">Paroxysmal cough (finding)</content></td></tr>
        </tbody></table>
      </text>
      <entry>
        <organizer classCode="BATTERY" moodCode="EVN">
          <code code="58410-2" codeSystem="2.16.840.1.113883.6.1"
                displayName="CBC panel"/>
          <component>
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
              <code code="409586006" codeSystem="2.16.840.1.113883.6.96"
                    displayName="Cough assay"/>
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

    reconstruct_narrative(section, augmentation_timestamp=_RUN_TS)

    original_text = section.xpath(".//hl7:value/hl7:originalText", namespaces=HL7_NS)[0]
    # the by-reference form became by-value: label inlined, <reference> gone
    assert original_text.xpath("normalize-space(.)") == "Paroxysmal cough (finding)"
    assert original_text.find("hl7:reference", HL7_NS) is None


def test_reconstruct_narrative_dangling_coding_reference_leaves_no_reference():
    # an originalText/reference pointing at an id absent from the narrative has
    # nothing to inline; the dangling reference is removed and no text fabricated
    section = _el(
        f"""
    <section {_NSDECL}>
      <code code="30954-2" codeSystem="2.16.840.1.113883.6.1"/>
      <text><table><tbody><tr><td>unrelated</td></tr></tbody></table></text>
      <entry>
        <organizer classCode="BATTERY" moodCode="EVN">
          <code code="58410-2" codeSystem="2.16.840.1.113883.6.1"
                displayName="CBC panel"/>
          <component>
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
              <code code="1" codeSystem="2.16.840.1.113883.6.96"
                    displayName="x"/>
              <value xsi:type="CD" code="1"
                     codeSystem="2.16.840.1.113883.6.96">
                <originalText><reference value="#missing"/></originalText>
              </value>
            </observation>
          </component>
        </organizer>
      </entry>
    </section>
    """
    )

    reconstruct_narrative(section, augmentation_timestamp=_RUN_TS)

    original_text = section.xpath(".//hl7:value/hl7:originalText", namespaces=HL7_NS)[0]
    assert original_text.find("hl7:reference", HL7_NS) is None
    assert original_text.xpath("normalize-space(.)") == ""


def test_reconstruct_narrative_marks_flat_entries_derived():
    # flat sections too: every substanceAdministration entry becomes DRIV
    section = _el(_IMMUNIZATIONS_SECTION)
    reconstruct_narrative(section, augmentation_timestamp=_RUN_TS)

    type_codes = section.xpath("hl7:entry/@typeCode", namespaces=HL7_NS)
    assert type_codes == ["DRIV", "DRIV"]


def test_result_fields_use_the_intended_kinds():
    # guard the design choice: clinical concepts surface system+code, the HL7
    # interpretation flag stays display-only with its canonical map, and the
    # value (and reference range) stay polymorphic
    by_label = {f.label: f for f in RESULT_FIELDS}
    assert by_label["Test"].kind == "concept"  # clinical: display (System code)
    assert by_label["Interpretation"].kind == "interp"  # HL7 flag: display-only
    assert by_label["Outcome"].kind == "typed"  # polymorphic (PQ/CD/ST)
    assert by_label["Reference Range"].kind == "typed"  # IVL_PQ interval


class TestCompactReconstructionReferences:
    """
    The minted entry→narrative reference pointer is a mixed-content
    <reference> and must serialize without surrounding whitespace
    (Boone, The CDA Book, ch. 6). Pretty-printing the whole document
    indents it; this collapses it back, scoped to refiner-minted ids.
    """

    def test_collapses_pretty_printed_reference(self):
        # the shape pretty_print produces over the whole tree
        pretty = (
            "<observation>\n"
            "  <text>\n"
            '    <reference value="#ecr-refiner-30954-2-20260101000000-row1"/>\n'
            "  </text>\n"
            "</observation>\n"
        )
        result = compact_reconstruction_references(pretty)
        assert (
            '<text><reference value="#ecr-refiner-30954-2-20260101000000-row1"/></text>'
            in result
        )
        # no whitespace survives between <text>/<reference>/</text>
        assert "<text>\n" not in result
        assert "/>\n  </text>" not in result

    def test_leaves_author_attested_references_untouched(self):
        # a source-document narrative reference (not refiner-minted) is
        # outside our remit — its whitespace is preserved
        pretty = (
            "<observation>\n"
            "  <text>\n"
            '    <reference value="#Result.1.2.840.Comp1"/>\n'
            "  </text>\n"
            "</observation>\n"
        )
        assert compact_reconstruction_references(pretty) == pretty


# NOTE:
# LAYER 3 — the Trigger Code Result Organizer's three permitted components
# =============================================================================
# CONF:4527-441/442 (Result Observation), 4527-443/444 (Laboratory Result
# Status ...4.418), 4527-450/451 (Specimen Collection Procedure ...4.415). the
# prune carve-out keeps all three alive; reconstruction must place each in the
# right part of the block, and only the first becomes a table row


_THREE_COMPONENT_ORGANIZER = f"""
<section {_NSDECL}>
  <code code="30954-2" codeSystem="2.16.840.1.113883.6.1"/>
  <entry>
    <organizer classCode="BATTERY" moodCode="EVN">
      <code code="58410-2" codeSystem="2.16.840.1.113883.6.1"
            displayName="CBC panel"/>
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
          <code code="718-7" codeSystem="2.16.840.1.113883.6.1"
                displayName="Hemoglobin"/>
          <value xsi:type="PQ" value="13.2" unit="g/dL"/>
        </observation>
      </component>
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.418"
                      extension="2018-06-11"/>
          <code code="92235-1" codeSystem="2.16.840.1.113883.6.1"
                displayName="Lab order result status"/>
          <value xsi:type="CD" code="final"
                 codeSystem="2.16.840.1.113883.5.83" displayName="Final"/>
        </observation>
      </component>
      <component>
        <procedure classCode="PROC" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.415"
                      extension="2018-09-01"/>
          <code code="17636008" codeSystem="2.16.840.1.113883.6.96"/>
          <targetSiteCode code="368208006"
                          codeSystem="2.16.840.1.113883.6.96"
                          displayName="Left upper arm structure"/>
        </procedure>
      </component>
    </organizer>
  </entry>
</section>
"""


def test_lab_result_status_is_context_not_a_result_row():
    """
    Laboratory Result Status (...4.418) must not render as a result row.

    It is an <observation> under organizer/component, exactly like a real
    result, and the shared-context prune carve-out deliberately keeps it
    alive. Unfiltered it renders a row reading "Lab order result status" beside
    the actual analytes. It belongs in the block context.
    """

    blocks = reconstruct_results(_el(_THREE_COMPONENT_ORGANIZER))
    assert len(blocks) == 1

    rows = [row.values["Test"] for row in blocks[0].rows]
    assert rows == ["Hemoglobin (LOINC 718-7)"], (
        "Laboratory Result Status leaked into the result table as a row"
    )

    assert blocks[0].context["Result Status"] == "Final"
    # and the specimen procedure still lands in context, not as a row
    assert blocks[0].context["Target Site"] == (
        "Left upper arm structure (SNOMED CT 368208006)"
    )


def test_result_row_without_a_templateid_still_renders():
    """
    A result observation missing its templateId is still a row.

    The row filter excludes the known non-result template rather than
    requireing the Result Observation V3 one. Requiring it would blank the whole
    table for any sender that omits the templateId, which would make the DRIV
    assertion ("narrative is clinically equivalent to the entries") false--a
    worse failure than one spurious row.
    """

    section = _el(
        _THREE_COMPONENT_ORGANIZER.replace(
            '<templateId root="2.16.840.1.113883.10.20.22.4.2"/>', ""
        )
    )
    blocks = reconstruct_results(section)

    assert len(blocks) == 1
    assert [row.values["Test"] for row in blocks[0].rows] == [
        "Hemoglobin (LOINC 718-7)"
    ], "a result observation with no templateId was dropped from the table"
