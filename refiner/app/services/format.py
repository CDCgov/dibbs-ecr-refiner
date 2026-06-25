import re

from lxml import etree
from lxml.etree import _Element

# heal '<tableborder="1">' -> '<table border="1">' (and similar)
# * this is a defensive band-aid for malformed input; if it triggers in practice, the
# real fix belongs upstream at the source of the malformed xml
SPACE_BEFORE_FIRST_ATTR = re.compile(r"<([A-Za-z_:][\w:.-]*)(?=\S+=)")


def minify_xml(text: str) -> str:
    """
    Produces a compact version of an XML file on a single line.

    Args:
        text (str): Original XML as a string

    Returns:
        str: The minified XML string
    """
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(text.encode(), parser)
    return etree.tostring(root, encoding="unicode")


def format_xml_document_for_display(text: str) -> str:
    """
    Pretty-print an XML document for display.

    Does not modify content. Only normalizes inter-element whitespace so
    that the same function can be applied to both sides of a diff (the
    original and the refined document) and have them line up visually
    without introducing semantic drift.

    Specifically:
        - Comments are preserved (eCR Refiner provenance comments are
          part of the audit trail and intentionally part of the output).
        - Element text and tail content is left untouched.
        - Inter-element whitespace is normalized via
          remove_blank_text=True + pretty_print=True so indentation is
          consistent regardless of how the input was originally
          serialized.

    Args:
        text: An XML document as a string.

    Returns:
        The pretty-printed XML as a string.

    Raises:
        etree.XMLSyntaxError: If the input is not well-formed XML.
    """

    # heal '<tableborder="1">' -> '<table border="1">' (and similar)
    healed = SPACE_BEFORE_FIRST_ATTR.sub(r"<\1 ", text)

    parser = etree.XMLParser(remove_blank_text=True)
    root: _Element = etree.fromstring(healed.encode("utf-8"), parser=parser)

    return etree.tostring(
        root,
        pretty_print=True,
        encoding="unicode",
        xml_declaration=False,
        with_tail=False,
        method="xml",
    )


def remove_element(elem: _Element) -> None:
    """
    Helper function for removal of elements from the XML tree.
    """

    parent = elem.getparent()
    if parent is not None:
        parent.remove(elem)
