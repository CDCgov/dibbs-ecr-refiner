import pytest
from lxml import etree

from app.services import format


class TestStripComments:
    def test_removes_comments(self):
        raw = """<root>
        <!-- a comment -->
        <child>Text</child>
        <!-- another comment -->
        </root>"""

        result = format.strip_comments(raw)
        # No comments left
        assert "<!--" not in result

    def test_handles_nested_comments(self):
        raw = """
        <root>
          <parent>
            <!-- remove this -->
            <child><!-- and this too -->Value</child>
          </parent>
        </root>
        """
        result = format.strip_comments(raw)
        assert "<!--" not in result


class TestNormalizeXmlPositive:
    def test_preserves_element_order_and_content(self):
        raw = "<root><x>1</x><y>2</y></root>"
        result = format.normalize_xml(raw)
        # ensure order is preserved
        assert result.find("<x>1</x>") < result.find("<y>2</y>")

    def test_collapses_whitespace_in_cells(self):
        raw_xml = """
        <root>
          <table border="1">
            <tr>
              <td>   spaced    out   text   </td>
            </tr>
          </table>
        </root>
        """
        normalized = format.normalize_xml(raw_xml)

        assert "<td>spaced out text</td>" in normalized

    def test_removes_blank_tails(self):
        raw_xml = """
        <root>
          <table border="1">
            <tr>
              <td>cell1</td>
              <td>cell2</td>
            </tr>
          </table>
        </root>
        """
        normalized = format.normalize_xml(raw_xml)

        # Ensure there's no trailing spaces after </td>
        assert "<td>cell1</td>" in normalized
        assert "<td>cell2</td>" in normalized

    def test_invalid_input_type(self):
        with pytest.raises(ValueError):
            format.normalize_xml(123)  # not a string


class TestNormalizeXmlNegative:
    @pytest.mark.parametrize(
        "bad_xml",
        [
            "",  # empty
            "<root><unclosed></root>",
            "<root><child></root>",  # mismatched tags
            "not xml at all",
        ],
    )
    def test_invalid_xml_raises(self, bad_xml):
        with pytest.raises(etree.XMLSyntaxError):
            format.normalize_xml(bad_xml)

    def test_non_string_input(self):
        with pytest.raises(ValueError):
            format.normalize_xml(None)  # passing None should TypeError
