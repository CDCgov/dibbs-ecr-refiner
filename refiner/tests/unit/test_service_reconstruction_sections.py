from lxml import etree

from app.services.ecr.model import HL7_NS
from app.services.ecr.narrative.reconstruction import (
    reconstruct_immunizations,
    reconstruct_medications,
    reconstruct_narrative,
    reconstruct_plan_of_treatment,
    reconstruct_problems,
    reconstruct_results,
    render_section_text,
)
from tests.unit.conftest import NSDECL, RUN_TS, load_section, parse_element

# NOTE:
# LAYER 3 — reconstruct_results (per-organizer blocks)
# =============================================================================

_RESULTS_SECTION = load_section("results_two_panels")


def test_reconstruct_results_one_block_per_organizer():
    blocks = reconstruct_results(parse_element(_RESULTS_SECTION))

    # one block per organizer with surviving observations
    assert len(blocks) == 2
    assert blocks[0].columns == [
        "Test",
        "Result value",
        "Interpretation",
        "Reference Range",
        "Date(s)",
    ]


def test_reconstruct_results_context_is_per_block_not_repeated_on_rows():
    blocks = reconstruct_results(parse_element(_RESULTS_SECTION))

    # the first organizer's context carries panel + performer + specimen, once.
    # Panel surfaces system + code; Performer is the performing org name reached
    # off the panel; Specimen has no @code so it stays display-only
    assert blocks[0].context == {
        "Panel name": "CBC panel (LOINC 58410-2)",
        "Date(s)": "",  # no organizer effectiveTime in the fixture
        "Performer": "Acme Reference Lab",
        # no Laboratory Result Status component; falls back to organizer statusCode
        "Result Status": "completed",
        "Specimen": "Blood specimen",
        "Target Site": "",
    }
    # its two result rows are the detail, with NO context smeared in
    assert len(blocks[0].rows) == 2
    assert blocks[0].rows[0].values == {
        "Test": "Hemoglobin",  # no @code in the fixture → display-only
        "Result value": "9.2 g/dL",
        "Interpretation": "Low",
        "Reference Range": "13.5 g/dL to 17.5 g/dL",  # IVL_PQ bounds keep units
        "Date(s)": "2024-01-15",
    }
    # the CD result value surfaces its system + code
    assert blocks[0].rows[1].values["Result value"] == "E. coli (SNOMED CT 112283007)"
    assert blocks[0].rows[1].values["Interpretation"] == ""

    # the second organizer is its own block; no bleed from the first
    assert blocks[1].context["Panel name"] == "Glucose panel"
    assert blocks[1].context["Specimen"] == ""  # no procedure in this organizer
    assert blocks[1].rows[0].values["Result value"] == "105 mg/dL"


# NOTE:
# LAYER 3 — reconstruct_problems (concern act -> problem observations)
# =============================================================================

_PROBLEMS_SECTION = load_section("problems_concern_with_two_observations")


def test_reconstruct_problems_one_block_per_concern():
    blocks = reconstruct_problems(parse_element(_PROBLEMS_SECTION))
    assert len(blocks) == 1
    assert blocks[0].columns == ["Problem Type", "Problem", "Date(s)"]


def test_reconstruct_problems_concern_context_and_problem_rows():
    blocks = reconstruct_problems(parse_element(_PROBLEMS_SECTION))

    # concern context: status + noted date, rendered once. the concern is
    # ACTIVE with an onset and no resolution, so its interval is open at the
    # high end — "2025-11-07" alone read as a single-day concern
    assert blocks[0].context == {
        "Concern Status": "active",
        "Date(s)": "2025-11-07 onward",
    }

    # the two problem observations are the detail rows
    assert len(blocks[0].rows) == 2
    # Problem Type (assertion code) is display-only; the Problem surfaces system
    assert blocks[0].rows[0].values == {
        "Problem Type": "Symptom",
        "Problem": "Dark stools (finding) (SNOMED CT 35064005)",
        # onset recorded, never resolved
        "Date(s)": "2025-11-01 onward",
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
    section = parse_element(
        f"""
    <section {NSDECL}>
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

_IMMUNIZATIONS_SECTION = load_section("immunizations_flat")


def test_reconstruct_immunizations_is_flat_single_block():
    blocks = reconstruct_immunizations(parse_element(_IMMUNIZATIONS_SECTION))

    # flat: exactly one block, empty context, one row per substanceAdministration
    assert len(blocks) == 1
    assert blocks[0].context == {}
    assert blocks[0].columns == ["Immunization", "Date", "Status"]
    assert len(blocks[0].rows) == 2


def test_reconstruct_immunizations_resolves_vaccine_including_translation():
    blocks = reconstruct_immunizations(parse_element(_IMMUNIZATIONS_SECTION))
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
        reconstruct_immunizations(parse_element(_IMMUNIZATIONS_SECTION)),
        loinc="11369-6",
        augmentation_timestamp=RUN_TS,
    )
    # flat section → exactly one table (no context table), two detail rows
    tables = text.xpath("hl7:table", namespaces=HL7_NS)
    assert len(tables) == 1
    rows = text.xpath(".//hl7:tbody/hl7:tr[@ID]", namespaces=HL7_NS)
    assert len(rows) == 2


def test_reconstruct_immunizations_relink_places_text_validly():
    # substanceAdministration has no <code>; the relinked <text> must land
    # after templateId/id (not before templateId, which would be invalid)
    section = parse_element(_IMMUNIZATIONS_SECTION)
    reconstruct_narrative(section, augmentation_timestamp=RUN_TS)

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

_MEDICATIONS_SECTION = load_section("medications_administered")


def test_reconstruct_medications_is_flat_with_convention_columns():
    blocks = reconstruct_medications(parse_element(_MEDICATIONS_SECTION))

    assert len(blocks) == 1
    assert blocks[0].context == {}
    assert blocks[0].columns == [
        "Medication",
        "Dose",
        "Quantity",
        "Date administered",
        "Frequency",
        "Route",
        "Status",
    ]
    # the two effectiveTimes land in distinct columns: the IVL_TS window
    # contributes its low bound as Date administered, the PIVL_TS as Frequency
    # (unreachable before the split)
    assert blocks[0].rows[0].values == {
        "Medication": "oseltamivir 6 MG/ML [Tamiflu] (RxNorm 1115699)",
        "Dose": "1 g",
        "Quantity": "",
        "Date administered": "2012-03-18",
        "Frequency": "every 8 h",
        "Route": "ORAL (NCI Thesaurus C38288)",
        "Status": "completed",
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

_NO_KNOWN_MEDICATIONS_SECTION = load_section("medications_no_known_negated")


def test_no_known_medications_row_is_flagged_negated():
    blocks = reconstruct_medications(parse_element(_NO_KNOWN_MEDICATIONS_SECTION))

    assert len(blocks) == 1
    assert blocks[0].rows[0].negated is True


def test_no_known_medications_renders_as_a_negative_not_a_product():
    section = parse_element(_NO_KNOWN_MEDICATIONS_SECTION)
    text = reconstruct_narrative(section, augmentation_timestamp=RUN_TS).text
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
    text = reconstruct_narrative(
        parse_element(_RESULTS_SECTION), augmentation_timestamp=RUN_TS
    ).text
    assert text is not None
    assert text.tag == "{urn:hl7-org:v3}text"
    # one detail row per surviving observation across both organizer blocks
    detail_rows = text.xpath(".//hl7:tbody/hl7:tr[@ID]", namespaces=HL7_NS)
    assert len(detail_rows) == 3


def test_reconstruct_narrative_unknown_loinc_produces_no_narrative():
    section = parse_element(
        f'<section {NSDECL}><code code="29762-2" displayName="Social History"/>'
        "<entry/></section>"
    )
    assert reconstruct_narrative(section, augmentation_timestamp=RUN_TS) is None


def test_reconstruct_narrative_relinks_surviving_entries():
    # ADR 0011: reconstruction now MUTATES the section — it strips the stale
    # narrative references and relinks each surviving observation to its row
    section = parse_element(_RESULTS_SECTION)
    reconstruct_narrative(section, augmentation_timestamp=RUN_TS)

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
    section = parse_element(_RESULTS_SECTION)
    reconstruct_narrative(section, augmentation_timestamp=RUN_TS)

    type_codes = section.xpath("hl7:entry/@typeCode", namespaces=HL7_NS)
    assert type_codes == ["DRIV", "DRIV"]


def test_reconstruct_narrative_inlines_coding_originaltext_reference():
    # a surviving value carries its label as originalText-BY-REFERENCE into the
    # narrative. reconstruction strips the stale row-level references, but the
    # coding-level originalText must survive as INLINE text — not be emptied,
    # which would destroy the sender's coding provenance in the shipped data
    section = parse_element(
        f"""
    <section {NSDECL}>
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

    reconstruct_narrative(section, augmentation_timestamp=RUN_TS)

    original_text = section.xpath(".//hl7:value/hl7:originalText", namespaces=HL7_NS)[0]
    # the by-reference form became by-value: label inlined, <reference> gone
    assert original_text.xpath("normalize-space(.)") == "Paroxysmal cough (finding)"
    assert original_text.find("hl7:reference", HL7_NS) is None


def test_reconstruct_narrative_dangling_coding_reference_leaves_no_reference():
    # an originalText/reference pointing at an id absent from the narrative has
    # nothing to inline; the dangling reference is removed and no text fabricated
    section = parse_element(
        f"""
    <section {NSDECL}>
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

    reconstruct_narrative(section, augmentation_timestamp=RUN_TS)

    original_text = section.xpath(".//hl7:value/hl7:originalText", namespaces=HL7_NS)[0]
    assert original_text.find("hl7:reference", HL7_NS) is None
    assert original_text.xpath("normalize-space(.)") == ""


def test_reconstruct_narrative_marks_flat_entries_derived():
    # flat sections too: every substanceAdministration entry becomes DRIV
    section = parse_element(_IMMUNIZATIONS_SECTION)
    reconstruct_narrative(section, augmentation_timestamp=RUN_TS)

    type_codes = section.xpath("hl7:entry/@typeCode", namespaces=HL7_NS)
    assert type_codes == ["DRIV", "DRIV"]


# NOTE:
# LAYER 3 — the Trigger Code Result Organizer's three permitted components
# =============================================================================
# the prune carve-out keeps all three component kinds alive, so reconstruction
# has to place each in the right part of the block: only the Result Observation
# becomes a table row, the other two are organizer-scoped context


_THREE_COMPONENT_ORGANIZER = load_section("results_organizer_three_components")


def test_lab_result_status_is_context_not_a_result_row():
    """
    Laboratory Result Status (...4.418) must not render as a result row.

    It is an <observation> under organizer/component, exactly like a real
    result, and the shared-context prune carve-out deliberately keeps it
    alive. Unfiltered it renders a row reading "Lab order result status" beside
    the actual analytes. It belongs in the block context.
    """

    blocks = reconstruct_results(parse_element(_THREE_COMPONENT_ORGANIZER))
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

    section = parse_element(
        _THREE_COMPONENT_ORGANIZER.replace(
            '<templateId root="2.16.840.1.113883.10.20.22.4.2"/>', ""
        )
    )
    blocks = reconstruct_results(section)

    assert len(blocks) == 1
    assert [row.values["Test"] for row in blocks[0].rows] == [
        "Hemoglobin (LOINC 718-7)"
    ], "a result observation with no templateId was dropped from the table"


# NOTE:
# PLAN OF TREATMENT — the heterogeneous section
# =============================================================================

_PLAN_OF_TREATMENT = load_section("plan_of_treatment_all_kinds")


def test_plan_of_treatment_emits_one_captioned_block_per_entry_kind():
    """
    Five unlike clinical statements share this section; each gets its own
    table, captioned, in spreadsheet order rather than document order.
    """

    blocks = reconstruct_plan_of_treatment(parse_element(_PLAN_OF_TREATMENT))

    assert [block.caption for block in blocks] == [
        "Planned Observations",
        "Planned Procedures",
        "Planned Activities",
        "Planned Medications",
        "Planned Immunizations",
    ]
    assert all(len(block.rows) == 1 for block in blocks)
    # unlike shapes are never collapsed into a shared grid
    assert blocks[0].columns != blocks[1].columns


def test_plan_of_treatment_splits_substance_administration_by_template():
    """
    Medication and immunization are the SAME element; only the templateId
    tells them apart -- mirroring how the section's match rules discriminate.
    """

    blocks = reconstruct_plan_of_treatment(parse_element(_PLAN_OF_TREATMENT))
    medications, immunizations = blocks[3], blocks[4]

    assert medications.rows[0].values["Planned Medication"] == (
        "Azithromycin 500 MG Oral Tablet (RxNorm 248656)"
    )
    assert medications.rows[0].values["Dose"] == "1 g"
    assert medications.rows[0].values["Route"] == "ORAL (NCI Thesaurus C38288)"

    assert immunizations.rows[0].values["Planned Immunization"] == (
        "COVID-19 mRNA vaccine (CVX 207)"
    )
    assert immunizations.rows[0].values["Lot"] == "LOT-1234"
    assert immunizations.rows[0].values["Manufacturer"] == "Moderna"


def test_plan_of_treatment_unknown_substance_administration_reads_as_medication():
    """
    A substanceAdministration bearing neither immunization template still
    renders. Dropping it would leave a surviving entry with no narrative
    row, making the section's typeCode="DRIV" a lie.
    """

    section = parse_element(
        _PLAN_OF_TREATMENT.replace(
            '<templateId root="2.16.840.1.113883.10.20.22.4.120"/>', ""
        )
    )
    blocks = reconstruct_plan_of_treatment(section)

    captions = [block.caption for block in blocks]
    assert "Planned Immunizations" not in captions
    assert len(blocks[-1].rows) == 2, (
        "the untemplated substanceAdministration was dropped instead of "
        "falling back to the medication table"
    )


def test_plan_of_treatment_renders_procedure_site_and_method():
    blocks = reconstruct_plan_of_treatment(parse_element(_PLAN_OF_TREATMENT))
    procedure = blocks[1].rows[0].values

    assert procedure["Planned Procedure"] == (
        "Extracorporeal membrane oxygenation (SNOMED CT 233573008)"
    )
    assert procedure["Target Site"] == "Abdomen and pelvis (SNOMED CT 416949008)"
    assert procedure["Method"] == "Diagnostic ultrasonography (SNOMED CT 16310003)"
    assert procedure["Date"] == "2020-11-08"
    assert procedure["Status"] == "active"


def test_plan_of_treatment_carries_performer_per_row():
    blocks = reconstruct_plan_of_treatment(parse_element(_PLAN_OF_TREATMENT))

    assert blocks[0].rows[0].values["Performer"] == "Community Health"
    # a planned item with no performer leaves the cell empty rather than
    # reaching for the author, who is not the responsible party
    assert blocks[1].rows[0].values["Performer"] == ""


def test_plan_of_treatment_empty_section_reconstructs_to_nothing():
    """
    Nothing survived pruning -> no blocks, so reconstruct_narrative returns
    None and the caller falls back to retaining the original narrative.
    """

    section = parse_element(
        '<section xmlns="urn:hl7-org:v3">'
        '<code code="18776-5" codeSystem="2.16.840.1.113883.6.1"/>'
        "</section>"
    )

    assert reconstruct_plan_of_treatment(section) == []
    # a section with no entries at all is the one case that still produces no
    # narrative; the reduced-form sweep covers every other shape
    assert reconstruct_narrative(section, augmentation_timestamp=RUN_TS) is None


def test_plan_of_treatment_dispatches_and_renders_captioned_tables():
    """
    End to end through the public entry: the section LOINC dispatches to the
    heterogeneous reconstructor and <caption> lands FIRST inside <table>,
    where StrucDoc.Table requires it.
    """

    section = parse_element(_PLAN_OF_TREATMENT)
    text = reconstruct_narrative(section, augmentation_timestamp=RUN_TS).text

    assert text is not None
    tables = text.findall("hl7:table", HL7_NS)
    assert len(tables) == 5
    for table in tables:
        assert etree.QName(table[0]).localname == "caption"

    captions = [table.find("hl7:caption", HL7_NS).text for table in tables]
    assert captions[0] == "Planned Observations"


def test_plan_of_treatment_relinks_every_surviving_entry():
    """
    Each planned entry points at the row that represents it, and the stale
    narrative references are gone.
    """

    section = parse_element(_PLAN_OF_TREATMENT)
    reconstruct_narrative(section, augmentation_timestamp=RUN_TS)

    references = section.xpath(".//hl7:entry//hl7:reference/@value", namespaces=HL7_NS)
    assert len(references) == 5
    assert all(str(ref).startswith("#ecr-refiner-18776-5-") for ref in references)
    assert all(
        entry.get("typeCode") == "DRIV"
        for entry in section.findall("hl7:entry", HL7_NS)
    )


def test_negated_planned_entry_reads_as_not_planned():
    """
    Negation wording follows moodCode: an EVN statement that did not happen
    was "Not administered"; a planned one that will not happen is "Not
    planned" -- a contraindication or cancelled order, not a missing dose.
    """

    section = parse_element(_PLAN_OF_TREATMENT)
    vaccine = section.findall("hl7:entry/hl7:substanceAdministration", HL7_NS)[-1]
    vaccine.set("negationInd", "true")

    text = reconstruct_narrative(section, augmentation_timestamp=RUN_TS).text

    assert text is not None
    rendered = etree.tostring(text, encoding="unicode")
    assert "Not planned: COVID-19 mRNA vaccine (CVX 207)" in rendered
    assert "Not administered:" not in rendered


def test_medication_row_carries_supply_quantity_and_single_administration_date():
    section = parse_element(
        f"""
        <section {NSDECL}>
          <code code="29549-3"/>
          <entry><substanceAdministration classCode="SBADM" moodCode="EVN">
            <statusCode code="completed"/>
            <effectiveTime xsi:type="IVL_TS">
              <low value="20260803190000+0000"/><high value="20260803192700+0000"/>
            </effectiveTime>
            <consumable><manufacturedProduct><manufacturedMaterial>
              <code displayName="ceftriaxone sodium"/>
            </manufacturedMaterial></manufacturedProduct></consumable>
            <entryRelationship typeCode="REFR">
              <supply classCode="SPLY" moodCode="INT">
                <quantity unit="{{tbl}}" value="60.0"/>
              </supply>
            </entryRelationship>
          </substanceAdministration></entry>
        </section>
        """
    )
    row = reconstruct_medications(section)[0].rows[0].values
    # the high bound (the moment the infusion ended) is dropped: an
    # administration happened at a time, not over a clinically meaningful window
    assert row["Date administered"] == "2026-08-03 19:00:00 +00:00"
    assert row["Quantity"] == "60.0 tbl"
    assert row["Status"] == "completed"


def test_medication_date_falls_back_to_a_flat_effective_time():
    section = parse_element(
        f"""
        <section {NSDECL}>
          <code code="29549-3"/>
          <entry><substanceAdministration classCode="SBADM" moodCode="EVN">
            <effectiveTime value="20260803"/>
            <consumable><manufacturedProduct><manufacturedMaterial>
              <code displayName="ceftriaxone sodium"/>
            </manufacturedMaterial></manufacturedProduct></consumable>
          </substanceAdministration></entry>
        </section>
        """
    )
    row = reconstruct_medications(section)[0].rows[0].values
    assert row["Date administered"] == "2026-08-03"


def test_periodic_interval_without_a_period_is_a_date_not_a_frequency():
    # senders ship `xsi:type="PIVL_TS"` on what is really a plain timestamp;
    # splitting on the type alone filed that date under "Frequency"
    section = parse_element(
        f"""
        <section {NSDECL}>
          <code code="29549-3"/>
          <entry><substanceAdministration classCode="SBADM" moodCode="EVN">
            <effectiveTime xsi:type="PIVL_TS" operator="A" value="202011071159-0700"/>
            <consumable><manufacturedProduct><manufacturedMaterial>
              <code displayName="oseltamivir"/>
            </manufacturedMaterial></manufacturedProduct></consumable>
          </substanceAdministration></entry>
        </section>
        """
    )
    row = reconstruct_medications(section)[0].rows[0].values
    assert row["Date administered"] == "2020-11-07 11:59 -07:00"
    assert row["Frequency"] == ""


def test_a_real_periodic_interval_still_renders_as_frequency():
    section = parse_element(
        f"""
        <section {NSDECL}>
          <code code="29549-3"/>
          <entry><substanceAdministration classCode="SBADM" moodCode="EVN">
            <effectiveTime xsi:type="IVL_TS"><low value="20201107"/></effectiveTime>
            <effectiveTime xsi:type="PIVL_TS" operator="A">
              <period value="8" unit="h"/>
            </effectiveTime>
            <consumable><manufacturedProduct><manufacturedMaterial>
              <code displayName="oseltamivir"/>
            </manufacturedMaterial></manufacturedProduct></consumable>
          </substanceAdministration></entry>
        </section>
        """
    )
    row = reconstruct_medications(section)[0].rows[0].values
    assert row["Date administered"] == "2020-11-07"
    assert row["Frequency"] == "every 8 h"


def test_results_detail_table_is_captioned_and_marked_subordinate():
    # StrucDoc.Td forbids a nested <table>, so containment is carried by the
    # caption naming the parent panel plus an indent styleCode
    blocks = reconstruct_results(parse_element(_RESULTS_SECTION))
    assert blocks[0].caption == "Tests in panel: CBC panel"

    text = render_section_text(
        blocks, loinc="30954-2", augmentation_timestamp="20260101000000"
    )
    tables = text.findall("hl7:table", HL7_NS)
    # per block: a context table (plain) then a detail table (subordinate)
    assert tables[0].get("styleCode") is None
    assert tables[1].get("styleCode") == "xallIndent"
    assert tables[1].find("hl7:caption", HL7_NS).text == "Tests in panel: CBC panel"


def test_flat_section_tables_are_not_marked_subordinate():
    # a flat block has no context table above it, so there is nothing to indent
    # under — Immunizations rows are not members of anything
    blocks = reconstruct_immunizations(parse_element(_IMMUNIZATIONS_SECTION))
    text = render_section_text(
        blocks, loinc="11369-6", augmentation_timestamp="20260101000000"
    )
    assert text.find("hl7:table", HL7_NS).get("styleCode") is None


def test_medication_date_administered_is_unaffected_by_interval_wording():
    # the column reads effectiveTime/low directly, so it renders a bound, not
    # an interval — an administration date must never read "onward"
    section = parse_element(
        f"""
        <section {NSDECL}>
          <code code="29549-3"/>
          <entry><substanceAdministration classCode="SBADM" moodCode="EVN">
            <effectiveTime xsi:type="IVL_TS"><low value="20260803"/></effectiveTime>
            <consumable><manufacturedProduct><manufacturedMaterial>
              <code displayName="drug"/>
            </manufacturedMaterial></manufacturedProduct></consumable>
          </substanceAdministration></entry>
        </section>
        """
    )
    assert (
        reconstruct_medications(section)[0].rows[0].values["Date administered"]
        == "2026-08-03"
    )


# NOTE:
# THE GENERIC FALLBACK — no surviving entry goes unrepresented
# =============================================================================
# a per-section reconstructor anchors on the arrangement the IG describes, so
# an entry arranged differently matches, survives pruning, and renders nothing.
# the PARTIAL case is the dangerous one: the section reports a clean
# "reconstructed", every entry is stamped typeCode="DRIV", and one of them is
# simply missing from the narrative that claims to derive from it


_PARTIAL_RESULTS_SECTION = load_section("results_partial_reconstruction")


def test_an_entry_the_reconstructor_cannot_cover_still_gets_a_row():
    section = parse_element(_PARTIAL_RESULTS_SECTION)

    rebuilt = reconstruct_narrative(section, augmentation_timestamp=RUN_TS)

    assert rebuilt.reduced_entry_count == 1
    rendered = etree.tostring(rebuilt.text, encoding="unicode")
    # the covered entry keeps its full per-section rendering
    assert "COVID (LOINC 94533-7)" in rendered
    # the uncovered one is present rather than silently dropped
    assert "Bare result (LOINC 94533-7)" in rendered


def test_the_reduced_block_is_captioned_so_a_thin_table_explains_itself():
    section = parse_element(_PARTIAL_RESULTS_SECTION)

    rebuilt = reconstruct_narrative(section, augmentation_timestamp=RUN_TS)

    captions = [
        c.text for c in rebuilt.text.findall(".//hl7:caption", HL7_NS) if c.text
    ]
    assert any("reduced form" in c for c in captions)


def test_every_surviving_entry_is_relinked_to_a_row():
    # typeCode="DRIV" asserts the narrative is derived from these entries; an
    # entry with no row makes that assertion false
    section = parse_element(_PARTIAL_RESULTS_SECTION)

    reconstruct_narrative(section, augmentation_timestamp=RUN_TS)

    for entry in section.findall("hl7:entry", HL7_NS):
        assert entry.get("typeCode") == "DRIV"
        refs = entry.xpath(".//hl7:text/hl7:reference/@value", namespaces=HL7_NS)
        assert refs, "a surviving entry was left with no narrative row"


def test_a_fully_covered_section_reports_no_reduced_entries():
    # the fallback must not fire when the section's own reconstructor
    # covered everything — otherwise the outcome label cries wolf
    rebuilt = reconstruct_narrative(
        parse_element(_RESULTS_SECTION), augmentation_timestamp=RUN_TS
    )

    assert rebuilt.reduced_entry_count == 0
    captions = [
        c.text for c in rebuilt.text.findall(".//hl7:caption", HL7_NS) if c.text
    ]
    assert not any("reduced form" in c for c in captions)


def test_reduced_rows_render_a_substance_administration_product():
    # a substanceAdministration carries no <code> of its own; the concept
    # lives on the consumable, which is why render_entry_concept searches
    section = parse_element(
        f"""
        <section {NSDECL}>
          <code code="11450-4"/>
          <text>Original.</text>
          <entry><substanceAdministration classCode="SBADM" moodCode="EVN">
            <statusCode code="completed"/>
            <effectiveTime value="20260803"/>
            <consumable><manufacturedProduct><manufacturedMaterial>
              <code code="1115699" codeSystem="2.16.840.1.113883.6.88"
                    displayName="oseltamivir"/>
            </manufacturedMaterial></manufacturedProduct></consumable>
          </substanceAdministration></entry>
        </section>
        """
    )

    rebuilt = reconstruct_narrative(section, augmentation_timestamp=RUN_TS)

    assert rebuilt.reduced_entry_count == 1
    rendered = etree.tostring(rebuilt.text, encoding="unicode")
    assert "oseltamivir (RxNorm 1115699)" in rendered
    assert "2026-08-03" in rendered
    assert "completed" in rendered
