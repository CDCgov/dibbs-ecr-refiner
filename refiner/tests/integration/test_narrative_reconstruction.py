from pathlib import Path

import pytest
from lxml import etree
from lxml.etree import _Element

from app.services.ecr.model import HL7_NS, SectionRunResult
from app.services.ecr.narrative.constants import RECONSTRUCTED_EMPTY_MESSAGE
from app.services.ecr.narrative.reconstruction import (
    ReconstructedNarrative,
    reconstruct_narrative,
)
from app.services.ecr.section.entry_matching import process as refine_section
from app.services.ecr.specification import load_spec
from app.services.terminology import CodeSystemSets

from ..fixtures.loader import load_fixture_str

_RUN_TS = "20260101000000+0000"


def _refine_with_no_matches(section: _Element, loinc: str) -> SectionRunResult:
    """
    Refine one section with `narrative="reconstruct"` and nothing to match.

    An empty `CodeSystemSets` is a configuration that cannot match anything,
    which is the only way to reach the no-match branch without authoring an
    eICR whose codes were chosen to miss. Mutates `section` in place and
    returns what the engine reported.
    """

    return refine_section(
        section=section,
        code_system_sets=CodeSystemSets(),
        section_specification=load_spec("1.1").sections[loinc],
        namespaces=HL7_NS,
        narrative_action="reconstruct",
        augmentation_timestamp=_RUN_TS,
    )


# NOTE:
# CDA-VALIDITY OF RECONSTRUCTED NARRATIVE
# =============================================================================
# the previous reconstruction attempt was disconnected because its output
# failed CDA R2 XSD validation (it emitted bare HTML). these tests retest that
# exact failure mode: take a known-valid eICR, swap the Results section's
# <text> for reconstruct_narrative's output, and validate the WHOLE document;
# a reconstructed <text> must be at least as valid as the narrative it
# replaces--it may not introduce new XSD or schematron errors

_RESULTS_LOINC = "30954-2"


def _eicr_with_reconstructed_results(fixtures_path: Path) -> tuple[str, str]:
    """
    Return (original_xml, reconstructed_xml) for the all-sections eICR.
    """

    src = fixtures_path / "eicr_v3_1_1" / "all_sections_test_files" / "CDA_eICR.xml"
    root = etree.parse(str(src)).getroot()
    original_xml = etree.tostring(root, encoding="unicode")

    section = root.xpath(
        f"//hl7:section[hl7:code/@code='{_RESULTS_LOINC}']", namespaces=HL7_NS
    )[0]
    rebuilt = reconstruct_narrative(
        section, augmentation_timestamp="20260101000000+0000"
    )
    assert isinstance(rebuilt, ReconstructedNarrative), (
        "expected a reconstructed <text> for Results"
    )

    existing_text = section.find("hl7:text", HL7_NS)
    assert existing_text is not None
    section.replace(existing_text, rebuilt.text)

    reconstructed_xml = etree.tostring(root, encoding="unicode")
    return original_xml, reconstructed_xml


def test_reconstructed_results_is_xsd_valid(fixtures_path, validate_xml_string_xsd):
    original_xml, reconstructed_xml = _eicr_with_reconstructed_results(fixtures_path)

    original = validate_xml_string_xsd(original_xml)
    reconstructed = validate_xml_string_xsd(reconstructed_xml)

    # the reconstructed document must not introduce XSD errors
    assert reconstructed["errors"] <= original["errors"], reconstructed["details"]


def test_reconstructed_results_is_schematron_valid(fixtures_path, validate_xml_string):
    original_xml, reconstructed_xml = _eicr_with_reconstructed_results(fixtures_path)

    original = validate_xml_string(original_xml, "eicr")
    reconstructed = validate_xml_string(reconstructed_xml, "eicr")

    # swapping in the reconstructed narrative must not add schematron errors
    assert reconstructed["errors"] <= original["errors"], reconstructed["details"]


def test_reconstructed_text_actually_replaced_the_narrative(fixtures_path):
    _, reconstructed_xml = _eicr_with_reconstructed_results(fixtures_path)

    # the machine-derived provenance marker proves the swap took effect
    assert "machine-derived" in reconstructed_xml
    # and a panel displayName from the fixture's Results organizer is present
    assert "SARS-CoV" in reconstructed_xml


# NOTE:
# CDA-VALIDITY OF THE *EMPTY* RECONSTRUCTION
# =============================================================================
# the no-match branch reconstructs over zero surviving entries. that output has
# its own failure mode: CDA R2 has no empty table -- StrucDoc.Table requires a
# <tbody>, which requires a <tr>, which requires a cell -- so rendering the
# section's tables "but empty" produces a document that does not validate.
# these pin that the empty reconstruction stays inside the schema


def _eicr_with_unmatched_results(fixtures_path: Path) -> tuple[str, str]:
    """
    Return (original_xml, refined_xml) after refining Results against a
    configuration that matches nothing.

    Drives the real entry-matching engine rather than pruning by hand, so
    what gets validated is the document the no-match branch actually
    produces: entries pruned, nullFlavor="NI" set, and the narrative
    replaced by the empty reconstruction.
    """

    src = fixtures_path / "eicr_v3_1_1" / "all_sections_test_files" / "CDA_eICR.xml"
    root = etree.parse(str(src)).getroot()
    original_xml = etree.tostring(root, encoding="unicode")

    section = root.xpath(
        f"//hl7:section[hl7:code/@code='{_RESULTS_LOINC}']", namespaces=HL7_NS
    )[0]
    result = _refine_with_no_matches(section, _RESULTS_LOINC)
    assert result.narrative_disposition == "reconstructed_empty"

    return original_xml, etree.tostring(root, encoding="unicode")


def test_empty_reconstruction_is_xsd_valid(fixtures_path, validate_xml_string_xsd):
    original_xml, refined_xml = _eicr_with_unmatched_results(fixtures_path)

    original = validate_xml_string_xsd(original_xml)
    refined = validate_xml_string_xsd(refined_xml)

    assert refined["errors"] <= original["errors"], refined["details"]


def test_empty_reconstruction_is_schematron_valid(fixtures_path, validate_xml_string):
    original_xml, refined_xml = _eicr_with_unmatched_results(fixtures_path)

    original = validate_xml_string(original_xml, "eicr")
    refined = validate_xml_string(refined_xml, "eicr")

    assert refined["errors"] <= original["errors"], refined["details"]


def test_empty_reconstruction_emits_no_table_and_says_so(fixtures_path):
    _, refined_xml = _eicr_with_unmatched_results(fixtures_path)

    section = etree.fromstring(refined_xml.encode()).xpath(
        f"//hl7:section[hl7:code/@code='{_RESULTS_LOINC}']", namespaces=HL7_NS
    )[0]
    section_text = section.find("hl7:text", HL7_NS)
    rendered = etree.tostring(section_text, encoding="unicode")

    # the engine took the no-match branch
    assert section.findall("hl7:entry", HL7_NS) == []
    assert section.get("nullFlavor") == "NI"

    # still reconstruction output: the marker is what the footnote's
    # "reconstructed" claim refers to
    assert "machine-derived" in rendered
    assert RECONSTRUCTED_EMPTY_MESSAGE in rendered
    # no table at all, rather than a table with nothing in it -- StrucDoc
    # cannot express the latter
    assert section_text.findall("hl7:table", HL7_NS) == []
    # and none of the pruned results survived into the narrative
    assert "SARS-CoV" not in rendered


# NOTE:
# EVERY RECONSTRUCTABLE SECTION, REFINED AGAINST A CONFIGURATION THAT MATCHES
# NOTHING
# =============================================================================
# the scenario harness cannot reach this case: every reconstructable section in
# the committed eICR pairs matches under both COVID and Influenza, so there is
# no jurisdiction configuration that leaves one of them empty. the committed
# section fixtures get there directly -- refine each one against an empty code
# set and the no-match branch is the only branch available.
#
# per section rather than once for Results because the branch dispatches into
# reconstruct_narrative, which dispatches AGAIN on the section's LOINC. a
# section whose reconstructor was never registered falls out as
# "reconstruct_unavailable" and quietly keeps its original narrative, which is
# exactly the regression these would catch


_RECONSTRUCTABLE_FIXTURES: list[tuple[str, str]] = [
    ("results_two_panels", "30954-2"),
    ("problems_concern_with_two_observations", "11450-4"),
    ("immunizations_flat", "11369-6"),
    ("medications_administered", "29549-3"),
    ("plan_of_treatment_all_kinds", "18776-5"),
]


@pytest.mark.parametrize(("fixture_name", "loinc"), _RECONSTRUCTABLE_FIXTURES)
def test_every_reconstructable_section_reconstructs_empty_on_no_match(
    fixture_name: str, loinc: str
) -> None:
    section = etree.fromstring(
        load_fixture_str(f"sections/{fixture_name}.xml").encode()
    )
    original = etree.tostring(section, encoding="unicode")

    result = _refine_with_no_matches(section, loinc)

    assert result.matches_found is False
    assert result.narrative_disposition == "reconstructed_empty", (
        f"{fixture_name} did not reconstruct on the no-match branch"
    )

    assert section.findall("hl7:entry", HL7_NS) == []
    assert section.get("nullFlavor") == "NI"

    section_text = section.find("hl7:text", HL7_NS)
    assert section_text is not None
    paragraphs = section_text.findall("hl7:paragraph", HL7_NS)
    assert [p.text for p in paragraphs] == [RECONSTRUCTED_EMPTY_MESSAGE]
    assert section_text.findall("hl7:table", HL7_NS) == [], (
        "CDA R2 has no rowless table; the empty reconstruction must be prose"
    )

    # nothing the configuration excluded came back through the narrative
    assert original != etree.tostring(section, encoding="unicode")


@pytest.mark.parametrize(("fixture_name", "loinc"), _RECONSTRUCTABLE_FIXTURES)
def test_empty_reconstruction_of_each_section_is_xsd_valid(
    fixture_name: str,
    loinc: str,
    fixtures_path,
    validate_xml_string_xsd,
) -> None:
    """
    Swap each emptied section into a real eICR and validate the whole document.

    The section fixtures are bare <section> elements, so schema validity is
    only meaningful once one is sitting where a section actually goes.
    """

    src = fixtures_path / "eicr_v3_1_1" / "all_sections_test_files" / "CDA_eICR.xml"
    root = etree.parse(str(src)).getroot()
    original_xml = etree.tostring(root, encoding="unicode")

    target = root.xpath(f"//hl7:section[hl7:code/@code='{loinc}']", namespaces=HL7_NS)[
        0
    ]
    replacement = etree.fromstring(
        load_fixture_str(f"sections/{fixture_name}.xml").encode()
    )
    _refine_with_no_matches(replacement, loinc)
    target.getparent().replace(target, replacement)

    original = validate_xml_string_xsd(original_xml)
    refined = validate_xml_string_xsd(etree.tostring(root, encoding="unicode"))

    assert refined["errors"] <= original["errors"], refined["details"]
