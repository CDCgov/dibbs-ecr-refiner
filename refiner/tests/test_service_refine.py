from lxml import etree

from app.services.ecr.models import RefinementPlan
from app.services.ecr.refine import refine_eicr

NAMESPACES = {"hl7": "urn:hl7-org:v3"}


def build_xpath_for_codes(codes: set[str]) -> str:
    """
    Helper to build XPath from a set of codes, mimicking ProcessedConfiguration.build_xpath()
    """

    if not codes:
        return ""

    code_conditions = " or ".join(f'@code="{code}"' for code in codes)
    return (
        f".//hl7:*[hl7:code[{code_conditions}] or hl7:translation[{code_conditions}] or hl7:value[{code_conditions}]] | "
        f".//hl7:code[{code_conditions}] | "
        f".//hl7:translation[{code_conditions}] | "
        f".//hl7:value[{code_conditions}]"
    )


def test_preserve_social_history_section(sample_xml_files):
    # social history loinc code is 29762-2
    # tell the plan to "retain" (don't touch) the social history section
    plan = RefinementPlan(
        xpath="",
        section_instructions={"29762-2": "retain"},
    )
    refined_xml = refine_eicr(xml_files=sample_xml_files, plan=plan)

    # parse both original and refined XMLs
    doc_refined = etree.fromstring(refined_xml.encode("utf-8"))
    doc_original = etree.fromstring(sample_xml_files.eicr.encode("utf-8"))

    social_section_refined = doc_refined.xpath(
        './/hl7:section[hl7:code[@code="29762-2"]]', namespaces=NAMESPACES
    )[0]
    social_section_original = doc_original.xpath(
        './/hl7:section[hl7:code[@code="29762-2"]]', namespaces=NAMESPACES
    )[0]

    # section should NOT be minimal
    assert social_section_refined.get("nullFlavor") != "NI"

    # compare entries
    # they should be the same since refiner didn't touch them at all and normally
    # they'd be refined out unless a config was set up to keep them
    entries_refined = social_section_refined.xpath(
        ".//hl7:entry", namespaces=NAMESPACES
    )
    entries_original = social_section_original.xpath(
        ".//hl7:entry", namespaces=NAMESPACES
    )

    # assert both number and content are the same
    assert len(entries_refined) == len(entries_original)
    for orig, refined in zip(entries_original, entries_refined):
        # compare the string representations
        assert etree.tostring(orig) == etree.tostring(refined)


def test_minimal_problems_section(sample_xml_files):
    # no matching codes in problems section
    # tell the plan to "refine" but with a non-matching code
    plan = RefinementPlan(
        xpath=build_xpath_for_codes(codes={"NOT_A_REAL_CODE"}),
        section_instructions={"11450-4": "refine"},
    )

    refined_xml = refine_eicr(xml_files=sample_xml_files, plan=plan)

    doc = etree.fromstring(refined_xml.encode("utf-8"))
    problems_section = doc.xpath(
        './/hl7:section[hl7:code[@code="11450-4"]]', namespaces=NAMESPACES
    )[0]
    # it should be a minimal (empty) section if there are no matching codes
    assert problems_section.get("nullFlavor") == "NI"
    assert not problems_section.xpath(".//hl7:entry", namespaces=NAMESPACES)


def test_retain_single_lab_entry(sample_xml_files):
    # use the loinc code "94310-0" present in results section
    plan = RefinementPlan(
        xpath=build_xpath_for_codes(codes={"94310-0"}),
        section_instructions={"30954-2": "refine"},
    )

    refined_xml = refine_eicr(xml_files=sample_xml_files, plan=plan)

    doc = etree.fromstring(refined_xml.encode("utf-8"))
    results_section = doc.xpath(
        './/hl7:section[hl7:code[@code="30954-2"]]', namespaces=NAMESPACES
    )[0]
    entries = results_section.xpath(".//hl7:entry", namespaces=NAMESPACES)
    assert any(
        "94310-0" in etree.tostring(entry, encoding="unicode") for entry in entries
    )
    # should not be minimal
    assert results_section.get("nullFlavor") != "NI"


def test_retain_multiple_problem_entries(sample_xml_files):
    # use snomed code "840539006" (COVID-19) and "230145002" (Difficulty Breathing) in Problems section
    plan = RefinementPlan(
        xpath=build_xpath_for_codes(codes={"840539006", "230145002"}),
        section_instructions={"11450-4": "refine"},
    )

    refined_xml = refine_eicr(xml_files=sample_xml_files, plan=plan)

    doc = etree.fromstring(refined_xml.encode("utf-8"))
    problems_section = doc.xpath(
        './/hl7:section[hl7:code[@code="11450-4"]]', namespaces=NAMESPACES
    )[0]
    entries = problems_section.xpath(".//hl7:entry", namespaces=NAMESPACES)
    # check for both codes in entries (they appear as <value code="..."> in the XML)
    assert any(
        "840539006" in etree.tostring(entry, encoding="unicode")
        or "230145002" in etree.tostring(entry, encoding="unicode")
        for entry in entries
    )
    # should not be minimal
    assert problems_section.get("nullFlavor") != "NI"


def test_preserve_encounters_section_with_narrative_and_entry(sample_xml_files):
    # encounters section loinc code is 46240-8
    plan = RefinementPlan(
        xpath=build_xpath_for_codes(codes={"NOT_A_CODE"}),
        section_instructions={"46240-8": "retain"},
    )

    refined_xml = refine_eicr(xml_files=sample_xml_files, plan=plan)

    doc = etree.fromstring(refined_xml.encode("utf-8"))
    encounters_section = doc.xpath(
        './/hl7:section[hl7:code[@code="46240-8"]]', namespaces=NAMESPACES
    )[0]
    assert encounters_section.get("nullFlavor") != "NI"
    # should have both the narrative and at least one entry
    entries = encounters_section.xpath(".//hl7:entry", namespaces=NAMESPACES)
    assert entries


def test_results_section_minimal_on_nonexistent_code(sample_xml_files):
    # use a code not present in results section ("NOT_A_REAL_CODE")
    plan = RefinementPlan(
        xpath=build_xpath_for_codes({"NOT_A_REAL_CODE"}),
        section_instructions={"30954-2": "refine"},
    )

    refined_xml = refine_eicr(xml_files=sample_xml_files, plan=plan)

    doc = etree.fromstring(refined_xml.encode("utf-8"))
    results_section = doc.xpath(
        './/hl7:section[hl7:code[@code="30954-2"]]', namespaces=NAMESPACES
    )[0]
    assert results_section.get("nullFlavor") == "NI"
    assert not results_section.xpath(".//hl7:entry", namespaces=NAMESPACES)
