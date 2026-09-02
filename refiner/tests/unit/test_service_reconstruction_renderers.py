import pytest

from app.services.ecr.narrative.reconstruction import (
    format_ts,
    render_code_display,
    render_coded_concept,
    render_interpretation,
    render_performer,
    render_performer_org,
    render_typed_value,
)
from tests.unit.conftest import NSDECL, parse_element

# NOTE:
# LAYER 1 — render_typed_value (the closed CDA data-type set)
# =============================================================================


def test_render_none_is_empty():
    assert render_typed_value(None) == ""


def test_render_cd_with_xsi_type_surfaces_system_and_code():
    # a CD value is a clinical concept: display (System code), system from OID
    el = parse_element(
        f'<value {NSDECL} xsi:type="CD" code="112283007" '
        'codeSystem="2.16.840.1.113883.6.96" displayName="E. coli"/>'
    )
    assert render_typed_value(el) == "E. coli (SNOMED CT 112283007)"


def test_render_cd_without_xsi_type_is_monomorphic_coded():
    # any @code-bearing element routes through the concept renderer; the
    # admin/clinical distinction is made at the field-map kind, not here
    el = parse_element(
        f'<interpretationCode {NSDECL} code="A" displayName="Abnormal"/>'
    )
    assert render_typed_value(el) == "Abnormal (A)"


def test_render_cd_code_only_has_no_redundant_parens():
    # no human display beyond the code → just the code, not "A (A)"
    el = parse_element(f'<value {NSDECL} xsi:type="CD" code="A"/>')
    assert render_typed_value(el) == "A"


def test_render_pq_with_xsi_type():
    el = parse_element(f'<value {NSDECL} xsi:type="PQ" value="9.2" unit="g/dL"/>')
    assert render_typed_value(el) == "9.2 g/dL"


def test_render_pq_monomorphic_dose_quantity():
    # doseQuantity is PQ by the CDA model — no xsi:type
    el = parse_element(f'<doseQuantity {NSDECL} value="1" unit="tablet"/>')
    assert render_typed_value(el) == "1 tablet"


def test_render_st():
    el = parse_element(f'<value {NSDECL} xsi:type="ST">free text</value>')
    assert render_typed_value(el) == "free text"


def test_render_ivl_ts_low_and_high():
    el = parse_element(
        f'<effectiveTime {NSDECL} xsi:type="IVL_TS">'
        '<low value="20240115"/><high value="20240122"/></effectiveTime>'
    )
    assert render_typed_value(el) == "2024-01-15 to 2024-01-22"


def test_render_ivl_ts_equal_bounds_collapse_to_single_value():
    # an EHR renders a low==high panel time as one timestamp, not "X to X"
    el = parse_element(
        f'<effectiveTime {NSDECL} xsi:type="IVL_TS">'
        '<low value="20240115"/><high value="20240115"/></effectiveTime>'
    )
    assert render_typed_value(el) == "2024-01-15"


def test_render_ivl_ts_low_only():
    # an interval open at the high end says the end was not recorded, which a
    # bare "2024-01-15" would hide behind something that reads as a point
    el = parse_element(
        f'<effectiveTime {NSDECL}><low value="20240115"/></effectiveTime>'
    )
    assert render_typed_value(el) == "2024-01-15 onward"


def test_render_ivl_pq_reference_range_keeps_units():
    # an IVL_PQ reference range: each bound is a PQ, so the unit rides along
    # (format_ts would silently drop it)
    el = parse_element(
        f'<value {NSDECL} xsi:type="IVL_PQ">'
        '<low unit="g/dL" value="13.5"/><high unit="g/dL" value="17.5"/></value>'
    )
    assert render_typed_value(el) == "13.5 g/dL to 17.5 g/dL"


def test_render_ivl_pq_high_only_bound():
    # a one-sided reference range is a comparison, not a value: "45 [iU]/mL"
    # read as though the whole range were 45. this bound is explicitly
    # exclusive, so it earns "<" rather than the default inclusive symbol
    el = parse_element(
        f'<value {NSDECL} xsi:type="IVL_PQ">'
        '<high inclusive="false" unit="[iU]/mL" value="45"/></value>'
    )
    assert render_typed_value(el) == "< 45 [iU]/mL"


def test_render_pivl_ts_frequency():
    el = parse_element(
        f'<effectiveTime {NSDECL} xsi:type="PIVL_TS">'
        '<period value="8" unit="h"/></effectiveTime>'
    )
    assert render_typed_value(el) == "every 8 h"


def test_render_bare_value():
    el = parse_element(f'<effectiveTime {NSDECL} value="20240115"/>')
    assert render_typed_value(el) == "2024-01-15"


# NOTE:
# LAYER 1 — format_ts (human-readable HL7 TS, source precision preserved)
# =============================================================================
# an HL7 V3 TS carries its own precision: "2020" and "20201107115930" are both
# well-formed and mean different things. The renderer must never fabricate the
# components a sender did not send, so the cases below ARE the specification --
# each row is one precision, and the table reads as the contract


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2020", "2020"),
        ("202011", "2020-11"),
        ("20201107", "2020-11-07"),
        ("202011071159", "2020-11-07 11:59"),
        ("20201107115930", "2020-11-07 11:59:30"),
        ("202011071159-0700", "2020-11-07 11:59 -07:00"),
        # an offset does not imply a time: a date keeps its precision
        ("20201107+0000", "2020-11-07 +00:00"),
    ],
    ids=lambda v: v,
)
def test_format_ts_preserves_the_precision_the_sender_sent(raw, expected):
    assert format_ts(raw) == expected


@pytest.mark.parametrize("raw", ["", None])
def test_format_ts_empty_input_renders_nothing(raw):
    assert format_ts(raw) == ""


def test_format_ts_non_ts_passes_through():
    # not a TS (e.g. a nullFlavor token slipping in) → unchanged
    assert format_ts("UNK") == "UNK"


# NOTE:
# LAYER 1 — render_code_display (the real-data display-name fallback chain)
# =============================================================================


def test_code_display_none_is_empty():
    assert render_code_display(None) == ""


def test_code_display_prefers_display_name_attr():
    el = parse_element(
        f'<code {NSDECL} code="60544-4" displayName="Giardia lamblia, NAAT"/>'
    )
    assert render_code_display(el) == "Giardia lamblia, NAAT"


def test_code_display_falls_back_to_original_text():
    # real epic (EHR) shape: no @displayName, label in <originalText> wrapping a
    # <reference> into the narrative; whitespace is normalized
    el = parse_element(
        f'<code {NSDECL} code="79381-0">'
        "<originalText>Stool Pathogens,\n   NAAT, Parasite"
        '<reference value="#Result.Comp1Name"/></originalText>'
        "</code>"
    )
    assert render_code_display(el) == "Stool Pathogens, NAAT, Parasite"


def test_code_display_falls_back_to_translation_display_name():
    el = parse_element(
        f'<code {NSDECL} code="79381-0">'
        '<translation code="LAB24189" displayName="STOOL PATHOGENS, NAAT, PARASITE"/>'
        "</code>"
    )
    assert render_code_display(el) == "STOOL PATHOGENS, NAAT, PARASITE"


def test_code_display_falls_back_to_bare_code():
    el = parse_element(f'<code {NSDECL} code="79381-0"/>')
    assert render_code_display(el) == "79381-0"


def test_code_display_nullflavor_primary_resolves_translation_display():
    # fickle immunization: nullFlavor primary CVX, real vaccine in translation
    el = parse_element(
        f'<code {NSDECL} nullFlavor="OTH">'
        '<translation code="207" codeSystem="2.16.840.1.113883.12.292" '
        'displayName="COVID-19 mRNA vaccine"/>'
        "</code>"
    )
    assert render_code_display(el) == "COVID-19 mRNA vaccine"


def test_code_display_nullflavor_primary_falls_back_to_translation_code():
    # translation carries a code but no displayName — better than blank
    el = parse_element(
        f'<code {NSDECL} nullFlavor="OTH">'
        '<translation code="207" codeSystem="2.16.840.1.113883.12.292"/>'
        "</code>"
    )
    assert render_code_display(el) == "207"


def test_render_typed_cd_resolves_through_original_text():
    # a CD value with no @displayName resolves its display via originalText,
    # then still surfaces the system + code
    el = parse_element(
        f'<value {NSDECL} xsi:type="CD" code="35064005" '
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
        el = parse_element(
            f'<interpretationCode {NSDECL} code="{code}" '
            'codeSystem="2.16.840.1.113883.5.83"/>'
        )
        assert render_interpretation(el) == expected


def test_interpretation_prefers_sender_display_name():
    # when the sender DID label it, we keep their words rather than override
    el = parse_element(
        f'<interpretationCode {NSDECL} code="A" '
        'codeSystem="2.16.840.1.113883.5.83" displayName="Abnormal alert"/>'
    )
    assert render_interpretation(el) == "Abnormal alert"


def test_interpretation_unmapped_code_returns_bare_code():
    # never hide an interpretation we do not recognize
    el = parse_element(
        f'<interpretationCode {NSDECL} code="ZZZ" codeSystem="2.16.840.1.113883.5.83"/>'
    )
    assert render_interpretation(el) == "ZZZ"


# NOTE:
# LAYER 1 — render_coded_concept (display + system + code for clinical concepts)
# =============================================================================


def test_coded_concept_code_with_known_system():
    el = parse_element(
        f'<code {NSDECL} code="105066-5" codeSystem="2.16.840.1.113883.6.1" '
        'displayName="SARS-CoV-2 Ag"/>'
    )
    assert render_coded_concept(el) == "SARS-CoV-2 Ag (LOINC 105066-5)"


def test_coded_concept_oid_only_resolves_via_oid_not_codesystemname():
    # source carries the OID but NO codeSystemName (or a variant spelling);
    # the system name still resolves canonically from the OID
    el = parse_element(
        f'<value {NSDECL} xsi:type="CD" code="1119303003" '
        'codeSystem="2.16.840.1.113883.6.96" '
        'displayName="Post-acute COVID-19 (disorder)"/>'
    )
    assert (
        render_coded_concept(el)
        == "Post-acute COVID-19 (disorder) (SNOMED CT 1119303003)"
    )


def test_coded_concept_unknown_system_omits_system_label():
    el = parse_element(
        f'<code {NSDECL} code="XYZ" codeSystem="9.9.9" displayName="Mystery"/>'
    )
    assert render_coded_concept(el) == "Mystery (XYZ)"


def test_coded_concept_nullflavor_code_is_display_only():
    # nullFlavor primary, real product in a translation → display only, no parens
    el = parse_element(
        f'<code {NSDECL} nullFlavor="OTH">'
        '<translation code="207" codeSystem="2.16.840.1.113883.12.292" '
        'displayName="COVID-19 mRNA vaccine"/>'
        "</code>"
    )
    assert render_coded_concept(el) == "COVID-19 mRNA vaccine"


def test_coded_concept_display_only_when_no_code():
    el = parse_element(f'<code {NSDECL} displayName="Blood specimen"/>')
    assert render_coded_concept(el) == "Blood specimen"


# NOTE:
# LAYER 1 — render_performer (the person-or-organization shape)
# =============================================================================


def test_performer_none_is_empty():
    assert render_performer(None) == ""


def test_performer_prefers_the_assigned_person():
    """
    A person and an organization on the same performer: the person wins.

    A planned act's intended performer is the clinician; the organization
    is the coarser answer to the same question.
    """

    performer = parse_element(f"""
    <performer {NSDECL}>
      <assignedEntity>
        <assignedPerson>
          <name><given>Patricia</given><family>Primary</family></name>
        </assignedPerson>
        <representedOrganization>
          <name>The DoctorsTogether Physician Group</name>
        </representedOrganization>
      </assignedEntity>
    </performer>
    """)

    assert render_performer(performer) == "Patricia Primary"


def test_performer_falls_back_to_the_organization():
    performer = parse_element(f"""
    <performer {NSDECL}>
      <assignedEntity>
        <representedOrganization>
          <name>Community Health and Hospitals</name>
        </representedOrganization>
      </assignedEntity>
    </performer>
    """)

    assert render_performer(performer) == "Community Health and Hospitals"


def test_performer_name_parts_join_without_source_whitespace():
    """
    A compactly serialized name must not run its parts together.

    The parts are CHILDREN of <name>, so taking the element's string-value
    would render "JaneDoe" for a document with no whitespace between the
    tags -- and senders do emit that.
    """

    performer = parse_element(
        f"<performer {NSDECL}><assignedEntity><assignedPerson>"
        "<name><given>Jane</given><family>Doe</family></name>"
        "</assignedPerson></assignedEntity></performer>"
    )

    assert render_performer(performer) == "Jane Doe"


def test_performer_drops_the_call_me_given_name():
    """
    qualifier="CL" is a nickname ALONGSIDE the legal given name.

    Rendering it inline turns Patricia Primary into "Patricia Patty Primary".
    """

    performer = parse_element(f"""
    <performer {NSDECL}>
      <assignedEntity>
        <assignedPerson>
          <name>
            <given>Patricia</given>
            <given qualifier="CL">Patty</given>
            <family>Primary</family>
            <suffix qualifier="AC">M.D.</suffix>
          </name>
        </assignedPerson>
      </assignedEntity>
    </performer>
    """)

    assert render_performer(performer) == "Patricia Primary M.D."


def test_performer_with_no_resolvable_name_is_empty():
    performer = parse_element(
        f"<performer {NSDECL}><assignedEntity>"
        '<id root="2.16.840.1.113883.19"/></assignedEntity></performer>'
    )

    assert render_performer(performer) == ""


# NOTE:
# PHA REVIEW FEEDBACK — the shapes real Epic/Meditech data ships
# =============================================================================
# each of these pins a case a public health reviewer reported reading wrong in
# refined output, with the source XML they pointed at


def test_reference_range_reads_a_nullflavored_bound_via_its_translation():
    # Epic parks the number in a <translation> when the unit is not UCUM-codable;
    # reading only the bound's own @value rendered the whole range blank
    value = parse_element(
        f"""
        <value {NSDECL} xsi:type="IVL_PQ">
          <low nullFlavor="OTH">
            <translation nullFlavor="OTH" value="49">
              <originalText>IU/L</originalText>
            </translation>
          </low>
          <high nullFlavor="OTH">
            <translation nullFlavor="OTH" value="135">
              <originalText>IU/L</originalText>
            </translation>
          </high>
        </value>
        """
    )
    assert render_typed_value(value) == "49 IU/L to 135 IU/L"


def test_performer_org_falls_back_to_the_person_when_no_organization():
    performer = parse_element(
        f"""
        <performer {NSDECL}><assignedEntity>
          <assignedPerson><name><given>Jane</given><family>Doe</family></name></assignedPerson>
        </assignedEntity></performer>
        """
    )
    assert render_performer_org(performer) == "Jane Doe"
    # the person-preferring renderer is unchanged
    assert render_performer(performer) == "Jane Doe"


def test_code_display_prefers_original_text_over_display_name():
    # a lab codes AST with the full LOINC name on @displayName and "AST" in
    # originalText; the short form is the one a PHA recognizes at a glance
    code = parse_element(
        f"""
        <code {NSDECL} code="1920-8" codeSystem="2.16.840.1.113883.6.1"
              displayName="Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma">
          <originalText>AST</originalText>
        </code>
        """
    )
    assert render_code_display(code) == "AST"
    # the verifiable half is still rendered alongside
    assert render_coded_concept(code) == "AST (LOINC 1920-8)"


def test_unknown_code_system_falls_back_to_the_senders_system_name():
    # Epic proprietary result-type enum: "16" alone told the reviewer nothing
    value = parse_element(
        f"""
        <value {NSDECL} xsi:type="CD" code="16"
               codeSystem="1.2.840.114350.1.72.1.5007" codeSystemName="Epic.Result.Type"/>
        """
    )
    assert render_coded_concept(value) == "Epic.Result.Type 16"


def test_ucum_pure_annotation_unit_renders_without_braces():
    quantity = parse_element(f'<quantity {NSDECL} unit="{{tbl}}" value="60.0"/>')
    assert render_typed_value(quantity) == "60.0 tbl"
    # a real unit carrying a trailing annotation is left alone
    annotated = parse_element(f'<quantity {NSDECL} unit="mg{{total}}" value="5"/>')
    assert render_typed_value(annotated) == "5 mg{total}"


# NOTE:
# INTERVALS — the shape that cannot be rendered honestly by accident
# =============================================================================
# a bare bound reads as a point in time. "started then, no end recorded" and
# "ended then" are different clinical facts, and on Problems the first is the
# difference between an active condition and a one-off note.
#
# the wording also splits on WHAT is bounded, because the same IVL branch
# serves reference ranges and "onward" is meaningless on a quantity. an HL7 V3
# bound is inclusive unless it says otherwise, so the inclusive symbols are the
# default and @inclusive="false" earns the strict ones.
#
# one table rather than nine functions: the shapes are only meaningful next to
# each other. what makes "2026-08-03 onward" the right answer is that a closed
# interval and a point in time render differently, which you can only see by
# reading the rows together


def _interval(body: str, xsi_type: str = "") -> str:
    attr = f' xsi:type="{xsi_type}"' if xsi_type else ""
    return f"<value {NSDECL}{attr}>{body}</value>"


@pytest.mark.parametrize(
    ("body", "xsi_type", "expected"),
    [
        pytest.param(
            '<low value="20260803"/><high value="20260810"/>',
            "IVL_TS",
            "2026-08-03 to 2026-08-10",
            id="closed interval",
        ),
        pytest.param(
            '<low value="20260803"/><high value="20260803"/>',
            "IVL_TS",
            "2026-08-03",
            id="zero width",
        ),
        pytest.param(
            '<low value="20260803"/>',
            "IVL_TS",
            "2026-08-03 onward",
            id="time low only",
        ),
        pytest.param(
            '<low value="20260803"/><high nullFlavor="UNK"/>',
            "IVL_TS",
            "2026-08-03 onward",
            id="time nullflavored high",
        ),
        pytest.param(
            '<high value="20260810"/>',
            "IVL_TS",
            "until 2026-08-10",
            id="time high only",
        ),
        pytest.param(
            '<high unit="mg/dL" value="1.2"/>',
            "IVL_PQ",
            "≤ 1.2 mg/dL",
            id="quantity high only",
        ),
        pytest.param(
            '<low unit="mg/dL" value="60"/>',
            "IVL_PQ",
            "≥ 60 mg/dL",
            id="quantity low only",
        ),
        pytest.param(
            '<high unit="mg/dL" value="1.2" inclusive="false"/>',
            "IVL_PQ",
            "< 1.2 mg/dL",
            id="quantity exclusive",
        ),
        pytest.param(
            '<high unit="mg/dL" value="1.2"/>',
            "",
            "≤ 1.2 mg/dL",
            id="untyped quantity",
        ),
    ],
)
def test_interval_rendering_names_the_side_that_is_open(body, xsi_type, expected):
    assert render_typed_value(parse_element(_interval(body, xsi_type))) == expected


def test_open_interval_never_claims_the_interval_is_ongoing():
    # "onward" says the end was not recorded; "to present" would assert a fact
    # the source never stated
    rendered = render_typed_value(
        parse_element(_interval('<low value="20260803"/>', "IVL_TS"))
    )
    assert "present" not in rendered
    assert "ongoing" not in rendered


def test_a_flat_timestamp_gains_no_interval_wording():
    rendered = render_typed_value(
        parse_element(f'<effectiveTime {NSDECL} value="20260803"/>')
    )
    assert rendered == "2026-08-03"
