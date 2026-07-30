from lxml import etree


def normalize_xml(xml: str) -> str:
    """
    Normalizes an XML string for consistent comparison in tests.
    """

    parser = etree.XMLParser(remove_blank_text=True)
    return etree.tostring(
        etree.fromstring(xml.encode("utf-8"), parser),
        pretty_print=True,
        encoding="unicode",
    ).strip()
