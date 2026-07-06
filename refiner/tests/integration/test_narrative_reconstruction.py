from pathlib import Path

from lxml import etree

from app.services.ecr.model import HL7_NS
from app.services.ecr.narrative.reconstruction import reconstruct_narrative

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

    src = fixtures_path / "eicr_v3_1_1" / "all_sections_CDA_eICR.xml"
    root = etree.parse(str(src)).getroot()
    original_xml = etree.tostring(root, encoding="unicode")

    section = root.xpath(
        f"//hl7:section[hl7:code/@code='{_RESULTS_LOINC}']", namespaces=HL7_NS
    )[0]
    new_text = reconstruct_narrative(
        section, augmentation_timestamp="20260101000000+0000"
    )
    assert new_text is not None, "expected a reconstructed <text> for Results"

    existing_text = section.find("hl7:text", HL7_NS)
    assert existing_text is not None
    section.replace(existing_text, new_text)

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
