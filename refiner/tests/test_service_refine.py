from lxml import etree

from app.core.models.types import XMLFiles
from app.db.conditions.model import DbCondition, DbConditionCoding
from app.db.configurations.model import DbConfiguration
from app.services.ecr.models import RefinementPlan
from app.services.ecr.refine import refine_eicr, refine_rr
from app.services.terminology import ConfigurationPayload, ProcessedConfiguration

from .conftest import NAMESPACES

# NOTE:
# LOCAL TEST HELPER FUNCTIONS - v1.1
# =============================================================================


def _make_condition_v1_1(**kwargs) -> DbCondition:
    """
    Creates a DbCondition model for v1.1 testing.
    """

    defaults = {
        "id": "fake-condition-id-v1-1",
        "display_name": "Test Condition v1.1",
        "canonical_url": "http://example.com/condition/v1.1",
        "version": "1.1",
        "child_rsg_snomed_codes": [],
        "snomed_codes": [],
        "loinc_codes": [],
        "icd10_codes": [],
        "rxnorm_codes": [],
    }
    defaults.update(kwargs)
    return DbCondition(**defaults)


def _make_db_configuration_v1_1(**kwargs) -> DbConfiguration:
    """
    Creates a DbConfiguration model for v1.1 testing.
    """

    defaults = {
        "id": "fake-config-id-v1-1",
        "name": "Test Config v1.1",
        "jurisdiction_id": "SDDH",
        "condition_id": "fake-condition-id-v1-1",
        "status": "active",
        "version": 1,
        "included_conditions": [],
        "custom_codes": [],
        "local_codes": [],
        "section_processing": [],
        "last_activated_at": None,
        "last_activated_by": None,
        "condition_canonical_url": "http://example.com/condition/v1.1",
        "created_by": "fake-config-id-v1-1",
        "tes_version": "1.0.0",
    }
    defaults.update(kwargs)
    return DbConfiguration(**defaults)


# NOTE:
# LOCAL TEST HELPER FUNCTIONS - v3.1.1
# =============================================================================


def _make_condition_v3_1_1(**kwargs) -> DbCondition:
    """
    Creates a DbCondition model for v3.1.1 testing.
    """

    defaults = {
        "id": "fake-condition-id-v3-1-1",
        "display_name": "Test Condition v3.1.1",
        "canonical_url": "http://example.com/condition/v3.1.1",
        "version": "3.1.1",
        "child_rsg_snomed_codes": [],
        "snomed_codes": [],
        "loinc_codes": [],
        "icd10_codes": [],
        "rxnorm_codes": [],
    }
    defaults.update(kwargs)
    return DbCondition(**defaults)


def _make_db_configuration_v3_1_1(**kwargs) -> DbConfiguration:
    """
    Creates a DbConfiguration model for v3.1.1 testing.
    """

    defaults = {
        "id": "fake-config-id-v3-1-1",
        "name": "Test Config v3.1.1",
        "jurisdiction_id": "SDDH",
        "condition_id": "fake-condition-id-v3-1-1",
        "status": "active",
        "version": 1,
        "included_conditions": [],
        "custom_codes": [],
        "local_codes": [],
        "section_processing": [],
        "last_activated_at": None,
        "last_activated_by": None,
        "condition_canonical_url": "http://example.com/condition/v3.1.1",
        "created_by": "fake-config-id-v1-1",
        "tes_version": "1.0.0",
    }
    defaults.update(kwargs)
    return DbConfiguration(**defaults)


# NOTE:
# EICR REFINEMENT TESTS
# =============================================================================


def test_retain_action_v1_1(covid_influenza_v1_1_files: XMLFiles):
    """
    Tests the 'retain' action, which should not modify the section.
    """

    plan = RefinementPlan(xpath="", section_instructions={"29762-2": "retain"})
    refined_xml = refine_eicr(xml_files=covid_influenza_v1_1_files, plan=plan)

    doc_refined = etree.fromstring(refined_xml.encode("utf-8"))
    section_refined = doc_refined.xpath(
        './/hl7:section[hl7:code[@code="29762-2"]]', namespaces=NAMESPACES
    )[0]

    original_doc = etree.fromstring(covid_influenza_v1_1_files.eicr.encode("utf-8"))
    section_original = original_doc.xpath(
        './/hl7:section[hl7:code[@code="29762-2"]]', namespaces=NAMESPACES
    )[0]

    assert etree.tostring(section_refined) == etree.tostring(section_original)


def test_refine_action_with_no_matches_v1_1(covid_influenza_v1_1_files: XMLFiles):
    """
    Tests 'refine' with a non-matching XPath, which should create a minimal section.
    """

    plan = RefinementPlan(
        xpath=".//hl7:code[@code='NON_EXISTENT_CODE']",
        section_instructions={"11450-4": "refine"},
    )
    refined_xml = refine_eicr(xml_files=covid_influenza_v1_1_files, plan=plan)
    doc = etree.fromstring(refined_xml.encode("utf-8"))
    problems_section = doc.xpath(
        './/hl7:section[hl7:code[@code="11450-4"]]', namespaces=NAMESPACES
    )[0]
    assert problems_section.get("nullFlavor") == "NI"


def test_refine_action_with_matches_v1_1(covid_influenza_v1_1_files: XMLFiles):
    """
    Tests the 'refine' action for v1.1, ensuring it correctly uses the
    terminology pipeline to build an XPath and filter a section.
    """

    condition = _make_condition_v1_1(
        loinc_codes=[DbConditionCoding(code="94310-0", display="")]
    )
    config = _make_db_configuration_v1_1()
    payload = ConfigurationPayload(conditions=[condition], configuration=config)

    processed_config = ProcessedConfiguration.from_payload(payload)
    xpath = processed_config.build_xpath()

    plan = RefinementPlan(xpath=xpath, section_instructions={"30954-2": "refine"})
    refined_xml = refine_eicr(xml_files=covid_influenza_v1_1_files, plan=plan)

    doc = etree.fromstring(refined_xml.encode("utf-8"))
    results_section = doc.xpath(
        './/hl7:section[hl7:code[@code="30954-2"]]', namespaces=NAMESPACES
    )[0]
    section_text = etree.tostring(results_section, encoding="unicode")
    assert "94310-0" in section_text


# NOTE:
# RR REFINEMENT TESTS
# =============================================================================


def test_refine_rr_by_condition_v1_1(covid_influenza_v1_1_files: XMLFiles):
    """
    Tests RR refinement for v1.1: keeps ONLY the observations for conditions
    specified in the configuration.
    """

    covid_condition = _make_condition_v1_1(child_rsg_snomed_codes=["840539006"])
    config = _make_db_configuration_v1_1()
    payload = ConfigurationPayload(conditions=[covid_condition], configuration=config)

    refined_xml = refine_rr(
        jurisdiction_id="SDDH", xml_files=covid_influenza_v1_1_files, payload=payload
    )
    doc_string = etree.tostring(
        etree.fromstring(refined_xml.encode("utf-8")), encoding="unicode"
    )

    assert "840539006" in doc_string
    assert "49727002" not in doc_string


def test_refine_rr_by_jurisdiction_v1_1(covid_influenza_v1_1_files: XMLFiles):
    """
    Tests RR refinement for v1.1: removes observations not for the given jurisdiction.
    """

    covid_condition = _make_condition_v1_1(child_rsg_snomed_codes=["840539006"])
    config = _make_db_configuration_v1_1()
    payload = ConfigurationPayload(conditions=[covid_condition], configuration=config)

    refined_xml = refine_rr(
        jurisdiction_id="SOME_OTHER_JD",
        xml_files=covid_influenza_v1_1_files,
        payload=payload,
    )
    doc_string = etree.tostring(
        etree.fromstring(refined_xml.encode("utf-8")), encoding="unicode"
    )

    assert "840539006" not in doc_string


def test_refine_rr_by_condition_v3_1_1(zika_v3_1_1_files: XMLFiles):
    """
    Tests RR refinement on the Zika file: confirms the Zika observation is kept.
    """

    zika_condition = _make_condition_v3_1_1(child_rsg_snomed_codes=["3928002"])
    config = _make_db_configuration_v3_1_1()
    payload = ConfigurationPayload(conditions=[zika_condition], configuration=config)

    refined_xml = refine_rr(
        jurisdiction_id="SDDH", xml_files=zika_v3_1_1_files, payload=payload
    )
    doc_string = etree.tostring(
        etree.fromstring(refined_xml.encode("utf-8")), encoding="unicode"
    )

    assert "3928002" in doc_string


def test_refine_rr_by_jurisdiction_v3_1_1(zika_v3_1_1_files: XMLFiles):
    """
    Tests RR refinement on the Zika file: confirms the Zika observation is
    removed when the jurisdiction does not match.
    """

    zika_condition = _make_condition_v3_1_1(child_rsg_snomed_codes=["3928002"])
    config = _make_db_configuration_v3_1_1()
    payload = ConfigurationPayload(conditions=[zika_condition], configuration=config)

    refined_xml = refine_rr(
        jurisdiction_id="SOME_OTHER_JD", xml_files=zika_v3_1_1_files, payload=payload
    )
    doc_string = etree.tostring(
        etree.fromstring(refined_xml.encode("utf-8")), encoding="unicode"
    )

    assert "3928002" not in doc_string
