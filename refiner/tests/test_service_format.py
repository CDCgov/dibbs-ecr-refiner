import pytest
from lxml import etree

from app.services import format


class TestNormalizeXmlPositive:
    def test_removes_comments(self):
        raw = """<root>
    <!-- a comment -->
    <child>Text</child>
    <!-- another comment -->
</root>"""

        result = format.normalize_xml(raw)
        # No comments left
        assert "<!--" not in result

    def test_preserves_element_order_and_content(self):
        raw = "<root><x>1</x><y>2</y></root>"
        result = format.normalize_xml(raw)
        # ensure order is preserved
        assert result.find("<x>1</x>") < result.find("<y>2</y>")

    def test_handles_nested_comments(self):
        raw = """
        <root>
          <parent>
            <!-- remove this -->
            <child><!-- and this too -->Value</child>
          </parent>
        </root>
        """
        result = format.normalize_xml(raw)
        assert "<!--" not in result


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
