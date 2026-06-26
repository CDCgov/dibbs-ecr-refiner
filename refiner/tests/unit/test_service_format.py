import pytest
from fastapi import HTTPException, status
from lxml import etree

from app.api.validation.file_validation import format_xml_document_for_display_or_raise
from app.services.format import format_xml_document_for_display

HL7 = "urn:hl7-org:v3"


class TestFormatXmlDocumentForDisplay:
    """
    Direct tests for the formatter. Behavior we care about:

      - It pretty-prints output with consistent indentation
      - It preserves content unchanged (no whitespace collapse, no
        comment stripping, no element reordering)
      - It is idempotent
      - It rejects bad input loudly
    """

    def test_returns_string_for_valid_input(self):
        result = format_xml_document_for_display("<root><child>text</child></root>")
        assert "<root>" in result
        assert "<child>text</child>" in result

    def test_handles_xml_declaration(self):
        xml = '<?xml version="1.0" encoding="UTF-8"?><root><child>text</child></root>'
        result = format_xml_document_for_display(xml)
        assert "<root>" in result

    def test_pretty_prints_output(self):
        # serialized as a flat string; formatter should add indentation
        flat = "<root><parent><child>text</child></parent></root>"
        result = format_xml_document_for_display(flat)
        # multiple lines and indentation appear
        assert "\n" in result
        assert "  <parent>" in result
        assert "    <child>text</child>" in result

    def test_preserves_element_order(self):
        result = format_xml_document_for_display("<root><x>1</x><y>2</y></root>")
        assert result.find("<x>1</x>") < result.find("<y>2</y>")

    def test_preserves_comments(self):
        """
        Comments are part of the eCR Refiner audit trail (provenance).
        The formatter must never strip them.
        """
        xml = "<root><!-- provenance: matched grouper --><child/></root>"
        result = format_xml_document_for_display(xml)
        assert "provenance: matched grouper" in result

    def test_preserves_multiple_comments(self):
        xml = """<root>
        <!-- a comment -->
        <child>Text</child>
        <!-- another comment -->
        </root>"""
        result = format_xml_document_for_display(xml)
        assert "a comment" in result
        assert "another comment" in result

    def test_does_not_collapse_narrative_whitespace(self):
        """
        CDA narrative <text> is mixed-content with semantically meaningful
        whitespace. The formatter must NOT collapse internal whitespace
        — that was the dangerous behavior we removed from the old
        _normalize_xml.
        """

        xml = (
            '<paragraph xmlns="urn:hl7-org:v3">'
            "Patient has    multiple   spaces.</paragraph>"
        )
        result = format_xml_document_for_display(xml)
        assert "multiple   spaces" in result, (
            "narrative whitespace was collapsed — content was mutated"
        )

    def test_does_not_collapse_text_inside_table_cells(self):
        """
        Whitespace inside <td> cells is part of the rendered narrative.
        The old formatter collapsed this; the new one must not.
        """

        xml = "<root><table><tr><td>   spaced    out   text   </td></tr></table></root>"
        result = format_xml_document_for_display(xml)

        # original spacing inside the cell preserved (formatter only normalizes
        # inter-element whitespace, never intra-element text)
        assert "   spaced    out   text   " in result

    def test_preserves_mixed_content(self):
        """
        Mixed content like '<paragraph>foo <content>bar</content> baz</paragraph>'
        is fragile under tail-whitespace mutation. The inline element and
        its surrounding text must remain whole.
        """

        xml = (
            '<paragraph xmlns="urn:hl7-org:v3">'
            'before <content styleCode="Bold">bold</content> after</paragraph>'
        )
        result = format_xml_document_for_display(xml)
        assert "before " in result
        assert '<content styleCode="Bold">bold</content>' in result
        assert " after" in result

    def test_idempotent(self):
        """
        Formatting an already-formatted document must be a no-op.
        """

        xml = "<root><parent><child>text</child></parent></root>"
        once = format_xml_document_for_display(xml)
        twice = format_xml_document_for_display(once)
        assert once == twice

    @pytest.mark.parametrize(
        "bad_xml",
        [
            "",
            "<root><unclosed></root>",
            "<root><child></root>",
            "not xml at all",
        ],
    )
    def test_invalid_xml_raises_xml_syntax_error(self, bad_xml):
        with pytest.raises(etree.XMLSyntaxError):
            format_xml_document_for_display(bad_xml)


class TestFormatXmlDocumentForDisplayOrRaise:
    """
    Tests for the FastAPI wrapper. The wrapper's only job is to convert
    XMLSyntaxError into an HTTP 422 — everything else delegates.
    """

    def test_passes_through_valid_xml(self):
        result = format_xml_document_for_display_or_raise(
            "<root><child>text</child></root>"
        )
        assert "<root>" in result
        assert "<child>text</child>" in result

    def test_raises_422_for_invalid_xml(self):
        with pytest.raises(HTTPException) as exc_info:
            format_xml_document_for_display_or_raise("<unclosed>")
        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert "Invalid XML" in exc_info.value.detail

    def test_preserves_comments_through_wrapper(self):
        """
        Confirms the wrapper does not strip comments — they are part of
        the audit trail and must reach the API response intact.
        """

        xml = "<root><!-- provenance --><child/></root>"
        result = format_xml_document_for_display_or_raise(xml)
        assert "provenance" in result


class TestRegressionLxmlPrettyPrintGotcha:
    """
    Regression tests for the lxml whitespace gotcha.

    Background: etree.tostring(root, pretty_print=True) does NOT
    indent subtrees that were added via SubElement to a tree parsed
    WITHOUT remove_blank_text=True. The new subtree's parent already
    has whitespace text/tail content from the source document, and
    lxml interprets that as 'meaningful — hands off.'

    This is the bug that caused refined eICR footnotes to render as
    single 1800-character lines in the downloaded zip even though
    pretty_print=True was set on the tostring call. The fix is the
    formatter's parse-with-remove_blank_text + pretty_print round-trip.

    These tests model the exact pipeline.py flow and fail if the
    formatter ever stops doing the round-trip correctly. Don't delete
    them without understanding why they exist.
    """

    def _build_eicr_with_subelement_footnote(self) -> str:
        """
        Replicate the pipeline.py + narrative.py flow:
          1. Parse a CDA-shaped document WITHOUT remove_blank_text
             (matches XMLFiles.parse_eicr())
          2. Add a footnote subtree via SubElement (matches
             append_section_provenance_footnote in narrative.py)
          3. Serialize via tostring (matches the pipeline's
             etree.tostring(eicr_root, encoding='unicode'))

        The resulting string has the flat-footnote symptom that
        format_xml_document_for_display must fix.
        """

        source = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
<component>
    <section>
    <code code="11450-4"/>
    <text>
        <table border="1">
        <tbody><tr><td>existing</td></tr></tbody>
        </table>
    </text>
    </section>
</component>
</ClinicalDocument>"""

        # parse without remove_blank_text — exactly like the pipeline
        parser = etree.XMLParser()
        root = etree.fromstring(source.encode("utf-8"), parser=parser)

        # build a footnote via SubElement — exactly like narrative.py
        ns = {"hl7": HL7}
        text_el = root.find(".//hl7:section/hl7:text", ns)
        footnote = etree.SubElement(
            text_el, f"{{{HL7}}}footnote", ID="ecr-refiner-test"
        )
        para = etree.SubElement(footnote, f"{{{HL7}}}paragraph")
        content = etree.SubElement(para, f"{{{HL7}}}content", styleCode="Bold")
        content.text = "eCR Refiner — Jurisdiction Configuration"
        table = etree.SubElement(footnote, f"{{{HL7}}}table", border="1")
        thead = etree.SubElement(table, f"{{{HL7}}}thead")
        tr = etree.SubElement(thead, f"{{{HL7}}}tr")
        for header in ["Section (LOINC)", "Outcome"]:
            th = etree.SubElement(tr, f"{{{HL7}}}th")
            th.text = header

        return etree.tostring(root, encoding="unicode")

    def test_subelement_footnote_renders_flat_without_formatter(self):
        """
        Sanity check: confirm we can reproduce the bug. If this test
        fails, lxml's behavior has changed and the rest of the
        regression suite needs revisiting.
        """

        raw = self._build_eicr_with_subelement_footnote()

        # the footnote's children should be packed onto one line;
        # this is the lxml gotcha at work
        assert "<footnote" in raw

        # all four constructed elements appear without intervening newlines
        assert "<paragraph><content" in raw or "<paragraph >" in raw

        # no newline between footnote-internal elements
        footnote_section = raw[raw.index("<footnote") : raw.index("</footnote>")]
        assert "\n" not in footnote_section, (
            "expected flat footnote subtree as the bug repro — "
            "if this fails, the lxml whitespace behavior may have changed"
        )

    def test_formatter_indents_subelement_footnote(self):
        """
        The fix: format_xml_document_for_display must indent the
        footnote subtree even though it was built with SubElement on
        a tree parsed without remove_blank_text.
        """

        raw = self._build_eicr_with_subelement_footnote()
        formatted = format_xml_document_for_display(raw)

        # each major footnote child should be on its own line with
        # indentation; the formatter normalizes whitespace via
        # remove_blank_text + pretty_print, so the entire tree: including
        # the new subtree that gets indented uniformly
        assert "<footnote ID=" in formatted
        assert "<paragraph>" in formatted
        assert "<content " in formatted
        assert "<table border=" in formatted

        # find the footnote block and confirm it has line breaks now
        footnote_start = formatted.index("<footnote")
        footnote_end = formatted.index("</footnote>")
        footnote_section = formatted[footnote_start:footnote_end]
        assert footnote_section.count("\n") >= 4, (
            "footnote subtree was not pretty-printed — formatter is "
            "no longer doing the remove_blank_text + pretty_print "
            "round-trip"
        )

    def test_plain_pretty_print_does_not_fix_the_gotcha(self):
        """
        Document why tostring(pretty_print=True) alone is not enough.

        This test exists to capture the diagnosis. If a future
        contributor 'simplifies' the formatter to just call
        tostring(pretty_print=True), this test will fail and
        explain why.
        """

        raw = self._build_eicr_with_subelement_footnote()

        # re-parse and apply pretty_print=True without remove_blank_text;
        # this is what someone might try as a 'simpler' fix
        parser = etree.XMLParser()
        root = etree.fromstring(raw.encode("utf-8"), parser=parser)
        naive_attempt = etree.tostring(root, encoding="unicode", pretty_print=True)

        # confirm the naive approach still produces flat footnotes
        footnote_start = naive_attempt.index("<footnote")
        footnote_end = naive_attempt.index("</footnote>")
        footnote_section = naive_attempt[footnote_start:footnote_end]
        assert "\n" not in footnote_section, (
            "if this passes, lxml's pretty_print behavior changed — "
            "the formatter may no longer need the remove_blank_text "
            "round-trip"
        )


class TestRegressionContentNotMutated:
    """
    Regression tests for the content-mutation behavior we deliberately
    removed.

    Background: the old format.py walked every element with
    `for el in root.iter()` and collapsed whitespace inside text and
    tail content. For CDA narrative <text> blocks (mixed content with
    inline elements), this could merge words, strip semantically
    meaningful indentation, and change what a clinician sees in a
    rendered document.

    These tests ensure we never reintroduce that behavior. Don't
    delete them without understanding the CDA narrative model.
    """

    def test_narrative_paragraph_internal_whitespace_unchanged(self):
        original = (
            '<paragraph xmlns="urn:hl7-org:v3">'
            "Patient has    multiple    spaces.</paragraph>"
        )
        result = format_xml_document_for_display(original)
        assert "multiple    spaces" in result

    def test_narrative_mixed_content_tail_whitespace_unchanged(self):
        """
        Tail whitespace between an inline element and the surrounding
        text matters in mixed content — it's the space between words.
        """

        original = (
            '<paragraph xmlns="urn:hl7-org:v3">'
            'before <content styleCode="Bold">bold</content> after</paragraph>'
        )
        result = format_xml_document_for_display(original)
        # the space before <content> and after </content> must survive
        assert "before <content" in result
        assert "</content> after" in result
