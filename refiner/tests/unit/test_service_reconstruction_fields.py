from app.services.ecr.narrative.reconstruction import (
    PANEL_FIELDS,
    RESULT_FIELDS,
    FieldSpec,
    extract_fields,
)
from tests.unit.conftest import NSDECL, parse_element

# NOTE:
# LAYER 1 — extract_fields
# =============================================================================


def test_extract_fields_attr_typed_and_missing():
    obs = parse_element(
        f"<observation {NSDECL}>"
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


def test_result_fields_use_the_intended_kinds():
    # guard the design choice: clinical concepts surface system+code, the HL7
    # interpretation flag stays display-only with its canonical map, and the
    # value (and reference range) stay polymorphic
    by_label = {f.label: f for f in RESULT_FIELDS}
    assert by_label["Test"].kind == "concept"  # clinical: display (System code)
    assert by_label["Interpretation"].kind == "interp"  # HL7 flag: display-only
    assert by_label["Result value"].kind == "typed"  # polymorphic (PQ/CD/ST)
    assert by_label["Reference Range"].kind == "typed"  # IVL_PQ interval


def test_reference_range_falls_back_to_the_senders_own_text():
    # nothing structured to render: the sender's spelled-out range beats a blank
    observation = parse_element(
        f"""
        <observation {NSDECL}>
          <referenceRange><observationRange>
            <text>0 - 35 IU/L</text>
            <value xsi:type="IVL_PQ"><low nullFlavor="OTH"/><high nullFlavor="OTH"/></value>
          </observationRange></referenceRange>
        </observation>
        """
    )
    fields = extract_fields(observation, RESULT_FIELDS)
    assert fields["Reference Range"] == "0 - 35 IU/L"


def test_result_status_falls_back_to_the_organizer_status_code():
    # the Laboratory Result Status template is a MAY almost nobody sends; the
    # answer the reviewer wanted was on the organizer's own statusCode
    organizer = parse_element(
        f"""
        <organizer {NSDECL}>
          <code code="58410-2" codeSystem="2.16.840.1.113883.6.1"/>
          <statusCode code="completed"/>
        </organizer>
        """
    )
    assert extract_fields(organizer, PANEL_FIELDS)["Result Status"] == "completed"


def test_result_status_prefers_the_ig_template_over_the_organizer_status():
    organizer = parse_element(
        f"""
        <organizer {NSDECL}>
          <code code="58410-2" codeSystem="2.16.840.1.113883.6.1"/>
          <statusCode code="completed"/>
          <component>
            <observation>
              <templateId root="2.16.840.1.113883.10.20.22.4.418"/>
              <value displayName="Final"/>
            </observation>
          </component>
        </organizer>
        """
    )
    assert extract_fields(organizer, PANEL_FIELDS)["Result Status"] == "Final"


def test_panel_performer_is_the_organization_not_the_person():
    # "which laboratory ran this?" — the verifying technologist is noise on a
    # results table, and naming them discloses a clinician the PHA did not need
    organizer = parse_element(
        f"""
        <organizer {NSDECL}>
          <performer><assignedEntity>
            <assignedPerson><name><given>Jane</given><family>Doe</family></name></assignedPerson>
            <representedOrganization><name>Acme Reference Lab</name></representedOrganization>
          </assignedEntity></performer>
        </organizer>
        """
    )
    assert extract_fields(organizer, PANEL_FIELDS)["Performer"] == "Acme Reference Lab"
