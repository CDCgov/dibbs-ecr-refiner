import pytest
from lxml import etree
from lxml.etree import _Element

from app.core.models.types import XMLFiles
from app.services.ecr.process_eicr import _get_section_by_code
from app.services.ecr.refine import refine


@pytest.fixture(autouse=True)
def mock_db_conditions(monkeypatch):
    """
    Monkeypatch the function as imported by refine.py so it does not try to use the DB.
    """

    from app.db.conditions.model import DbCondition

    async def fake_get_conditions_by_child_rsg_snomed_codes(db, codes):
        return [
            DbCondition(
                id="fake-id",
                display_name="Test Condition",
                canonical_url="http://example.com",
                version="1.0.0",
                child_rsg_snomed_codes=["840539006"],
                snomed_codes=[],
                loinc_codes=[],
                icd10_codes=[],
                rxnorm_codes=[],
            )
        ]

    # patch the imported name in refine.py; not the original module
    monkeypatch.setattr(
        "app.services.ecr.refine.get_conditions_by_child_rsg_snomed_codes",
        fake_get_conditions_by_child_rsg_snomed_codes,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sections_to_include,expected_in_results",
    [
        (None, True),
        (["29762-2"], True),
        (["30954-2"], True),
    ],
)
async def test_refine_eicr(
    sample_xml_files: XMLFiles, sections_to_include, expected_in_results
):
    jurisdiction_id = "TEST"
    refined_output = await refine(
        original_xml=sample_xml_files,
        # the value doesn't matter, it's ignored by the mock
        db=None,
        jurisdiction_id=jurisdiction_id,
        sections_to_include=sections_to_include,
    )

    assert len(refined_output) == 1
    refined_doc: _Element = etree.fromstring(refined_output[0].refined_eicr)
    refined_structured_body: _Element | None = refined_doc.find(
        path=".//{urn:hl7-org:v3}structuredBody", namespaces={"hl7": "urn:hl7-org:v3"}
    )
    refined_results_section = _get_section_by_code(refined_structured_body, "30954-2")
    xpath_query = ".//hl7:code"
    result: bool = bool(
        refined_results_section.xpath(
            _path=xpath_query, namespaces={"hl7": "urn:hl7-org:v3"}
        )
    )
    assert result == expected_in_results
