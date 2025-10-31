from lxml.etree import _Element


def remove_element(elem: _Element) -> None:
    """Helper function for removal of elements from the XML tree."""

    parent = elem.getparent()
    if parent is not None:
        parent.remove(elem)
