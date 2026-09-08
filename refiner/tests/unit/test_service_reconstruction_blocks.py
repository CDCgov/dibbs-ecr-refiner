from lxml import etree
from lxml.etree import _Element

from app.services.ecr.model import HL7_NS
from app.services.ecr.narrative.reconstruction import (
    Block,
    DetailRow,
    render_section_text,
)
from tests.unit.conftest import NSDECL, RUN_TS, parse_element

# NOTE:
# LAYER 1 — render_section_text (block assembler: tables, IDs, relinking)
# =============================================================================


def _obs(test: str) -> _Element:
    return parse_element(
        f'<observation {NSDECL}><code displayName="{test}"/></observation>'
    )


def test_render_section_text_block_structure_and_provenance_marker():
    obs = _obs("Hemoglobin")
    block = Block(
        context={"Panel": "CBC", "Date(s)": "20240115"},
        columns=["Test", "Outcome"],
        rows=[DetailRow(source=obs, values={"Test": "Hemoglobin", "Outcome": "9.2"})],
    )

    text = render_section_text([block], loinc="30954-2", augmentation_timestamp=RUN_TS)

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

    text = render_section_text([block], loinc="30954-2", augmentation_timestamp=RUN_TS)

    # the detail row carries a minted, run-stamped, document-unique xs:ID
    row = text.xpath(".//hl7:tbody/hl7:tr", namespaces=HL7_NS)[0]
    row_id = row.get("ID")
    assert row_id == "ecr-refiner-30954-2-20240101000000-row1"

    # and the source observation is relinked to that row
    ref = obs.xpath("hl7:text/hl7:reference/@value", namespaces=HL7_NS)
    assert ref == [f"#{row_id}"]
