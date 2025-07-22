from lxml import etree
from lxml.etree import _Element
from typing import cast, List


def normalize_xml(xml: str) -> str:
    """
    Normalize XML string for comparison: parse, strip out all comments, then re-serialize with consistent pretty-printing.
    """

    # Reject non‐string inputs
    if not isinstance(xml, str):
        raise ValueError(f"Expected XML as str, got {type(xml).__name__!r}")

    # Parse into an Element
    root: _Element = etree.fromstring(xml)

    # Force mypy to treat this as a list of Elements
    comment_nodes: List[_Element] = root.xpath("//comment()")  # type: ignore[assignment]

    for comment in comment_nodes:
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
