import pytest
from lxml import etree
from lxml.etree import _Element

from app.services.ecr.model import HL7_NS
from app.services.ecr.narrative.constants import (
    MINIMAL_SECTION_MESSAGE,
    NARRATIVE_REMOVED_MESSAGE,
    REFINER_OUTPUT_TITLE,
    REMOVE_NARRATIVE_MESSAGE,
    REMOVE_SECTION_MESSAGE,
)
from app.services.ecr.narrative.writers import (
    create_minimal_section,
    replace_narrative_with_removal_notice,
)

# NOTE:
# MINIMAL SECTION STUB — what a PHA sees for a section they switched off
# =============================================================================
# create_minimal_section is live on the "removed by configuration" path
# (refine._process_sections BRANCH 1) and had no test at all. it is the only
# content a reviewer gets for that section, and it has to leave the section
# schema-valid: entries gone, nullFlavor="NI" set, and the stub table built
# with real <thead>/<th> header semantics rather than the HTML-invalid
# <thead><tr><td> shape an earlier implementation emitted


def _stub_section(body: str = "") -> _Element:
    return etree.fromstring(
        f"""
        <section xmlns="urn:hl7-org:v3">
          <code code="10164-2" codeSystem="2.16.840.1.113883.6.1"/>
          <title>HISTORY OF PRESENT ILLNESS</title>
          <text><paragraph>Original clinician narrative.</paragraph></text>
          {body}
        </section>
        """.encode()
    )


_STUB_ENTRY = """
  <entry><observation classCode="OBS" moodCode="EVN">
    <code code="1234-5" codeSystem="2.16.840.1.113883.6.1"/>
  </observation></entry>
"""


@pytest.mark.parametrize(
    ("reason", "expected_message"),
    [
        ("configured", REMOVE_SECTION_MESSAGE),
        ("no_match", MINIMAL_SECTION_MESSAGE),
    ],
)
def test_minimal_section_states_why_the_section_is_empty(
    reason, expected_message
) -> None:
    section = _stub_section(_STUB_ENTRY)

    create_minimal_section(section=section, removal_reason=reason)

    cells = section.xpath(".//hl7:text//hl7:td/text()", namespaces=HL7_NS)
    assert cells == [expected_message]
    caption = section.xpath(".//hl7:text//hl7:caption/text()", namespaces=HL7_NS)
    assert caption == [REFINER_OUTPUT_TITLE]


def test_minimal_section_drops_entries_and_marks_the_section_null() -> None:
    section = _stub_section(_STUB_ENTRY + _STUB_ENTRY)

    create_minimal_section(section=section, removal_reason="configured")

    assert section.findall("hl7:entry", HL7_NS) == []
    # schematron requires refinable sections to declare the absence rather
    # than simply ship empty
    assert section.get("nullFlavor") == "NI"


def test_minimal_section_replaces_the_original_narrative() -> None:
    section = _stub_section(_STUB_ENTRY)

    create_minimal_section(section=section, removal_reason="configured")

    rendered = etree.tostring(section, encoding="unicode")
    assert "Original clinician narrative" not in rendered
    # exactly one <text>, still in its xs:sequence position after <title>
    assert len(section.findall("hl7:text", HL7_NS)) == 1
    order = [etree.QName(c).localname for c in section if isinstance(c.tag, str)]
    assert order == ["code", "title", "text"]


def test_minimal_section_uses_real_table_header_semantics() -> None:
    # <thead><tr><th>, not the HTML-invalid <thead><tr><td> an earlier
    # implementation emitted
    section = _stub_section()

    create_minimal_section(section=section, removal_reason="configured")

    assert section.xpath(".//hl7:thead/hl7:tr/hl7:th/text()", namespaces=HL7_NS) == [
        "Status"
    ]
    assert section.xpath(".//hl7:thead//hl7:td", namespaces=HL7_NS) == []
    assert section.xpath(".//hl7:tbody/hl7:tr/hl7:td", namespaces=HL7_NS)


def test_minimal_section_builds_a_narrative_when_the_section_had_none() -> None:
    # a section whose <text> was already stripped still gets a stub, inserted
    # after <title> per the CDA R2 section sequence
    section = etree.fromstring(
        b"""
        <section xmlns="urn:hl7-org:v3">
          <code code="10164-2" codeSystem="2.16.840.1.113883.6.1"/>
          <title>HISTORY OF PRESENT ILLNESS</title>
        </section>
        """
    )

    create_minimal_section(section=section, removal_reason="configured")

    order = [etree.QName(c).localname for c in section if isinstance(c.tag, str)]
    assert order == ["code", "title", "text"]


# NOTE:
# THE REMOVAL NOTICE MAKES A CLAIM ABOUT ENTRIES
# =============================================================================
# "Clinical entries are preserved for machine processing" is only true when the
# entries actually survived. A review of real refined output caught sections
# carrying nullFlavor="NI" and zero entries while telling PHAs exactly that, so
# the two situations now carry different text


def test_configured_removal_says_the_entries_are_still_there() -> None:
    section = _stub_section(_STUB_ENTRY)

    replace_narrative_with_removal_notice(section, removal_reason="configured")

    rendered = etree.tostring(section, encoding="unicode")
    assert REMOVE_NARRATIVE_MESSAGE in rendered
    # and they are: this path does not prune
    assert section.findall("hl7:entry", HL7_NS)


def test_configured_removal_on_a_section_with_no_entries_makes_no_claim() -> None:
    # a narrative-only section (Chief Complaint, Reason for Visit, ...) has no
    # coded entries by definition. "removed as configured" is the whole story;
    # there is nothing preserved to mention
    section = _stub_section()

    replace_narrative_with_removal_notice(section, removal_reason="configured")

    rendered = etree.tostring(section, encoding="unicode")
    assert NARRATIVE_REMOVED_MESSAGE in rendered
    assert "preserved for machine processing" not in rendered


def test_no_match_removal_does_not_claim_preserved_entries() -> None:
    # the caller has already pruned every entry by the time it reaches here
    section = _stub_section()

    replace_narrative_with_removal_notice(section, removal_reason="no_match")

    rendered = etree.tostring(section, encoding="unicode")
    assert MINIMAL_SECTION_MESSAGE in rendered
    assert "preserved for machine processing" not in rendered


def test_the_two_notices_are_not_the_same_text() -> None:
    # they were one string, which is how the false claim reached production
    assert MINIMAL_SECTION_MESSAGE != REMOVE_NARRATIVE_MESSAGE
