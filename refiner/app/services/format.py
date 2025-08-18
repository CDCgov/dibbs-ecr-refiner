import re
from typing import cast

from lxml import etree
from lxml.etree import _Element

SPACE_BEFORE_FIRST_ATTR = re.compile(r"<([A-Za-z_:][\w:.-]*)(?=\S+=)")

def normalize_xml(xml: str) -> str:
    """
    Normalize XML for comparison/reading:
    - heal a common '<tagattr=' -> '<tag attr=' mistake
    - strip comments
    - collapse whitespace in text/tails
    - pretty-print with consistent indentation (good for tables)
    """
    if not isinstance(xml, str):
        raise ValueError(f"Expected XML as str, got {type(xml).__name__!r}")

    # Heal '<tableborder="1">' -> '<table border="1">' (and similar)
    xml = SPACE_BEFORE_FIRST_ATTR.sub(r"<\1 ", xml)

    parser = etree.XMLParser(remove_blank_text=True)
    root: _Element = etree.fromstring(xml, parser=parser)

    # Remove comments
    for comment in cast(list[_Element], root.xpath("//comment()")):
        parent = comment.getparent()
        if parent is not None:
            parent.remove(comment)

    # Normalize whitespace inside text/tails so pretty_print can indent cleanly
    for el in root.iter():
        if el.text is not None:
            t = el.text.strip()
            el.text = " ".join(t.split()) if t else None
        if el.tail is not None:
            t = el.tail.strip()
            # For structural nodes (tr/td/th/etc.), drop tails entirely
            if el.tag in {"table", "thead", "tbody", "tfoot", "tr", "td", "th"}:
                el.tail = None if not t else " ".join(t.split())
            else:
                el.tail = " ".join(t.split()) if t else None

    return etree.tostring(
        root,
        pretty_print=True,
        encoding="unicode",
        xml_declaration=False,
        with_tail=False,
        method="xml",
    )