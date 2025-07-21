from lxml import etree
from lxml.etree import _Element


def normalize_xml(xml: str) -> str:
    """
    Normalize XML string for comparison: parse, strip out all comments, then re-serialize with consistent pretty-printing.
    """

    # Parse into an Element
    root: _Element = etree.fromstring(xml)

    # Remove all comment nodes
    for comment in root.xpath("//comment()"):
        parent = comment.getparent()
        if parent is not None:
            parent.remove(comment)

    # Re-serialize with consistent formatting
    normalized = etree.tostring(
        root,
        pretty_print=True,
        encoding="unicode",
        xml_declaration=False,
        with_tail=True,
    ).strip()

    return normalized
