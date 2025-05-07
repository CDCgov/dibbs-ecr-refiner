from lxml import etree

from ..core.exceptions import XMLProcessingError, XMLValidationError

NAMESPACES = {
    "cda": "urn:hl7-org:v3",
    "sdtc": "urn:hl7-org:sdtc",
    "voc": "http://www.lantanagroup.com/voc",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}


def parse_xml(rr_xml: str) -> etree._Element:
    """
    Parses a raw RR XML string and returns the root Element.

    Args:
        rr_xml (str): The raw XML string.

    Returns:
        etree._Element: The parsed XML element tree

    Raises:
        XMLValidationError: If the XML is invalid
        XMLProcessingError: If XML processing fails
    """
    if not rr_xml:
        raise XMLValidationError("XML content cannot be empty")

    try:
        parser = etree.XMLParser(remove_blank_text=True)
        rr_root = etree.fromstring(rr_xml.encode("utf-8"), parser=parser)
        return rr_root
    except etree.ParseError as e:
        raise XMLProcessingError(
            message="Failed to parse XML content",
            details={
                "error": str(e),
                "line": getattr(e, "line", None),
                "column": getattr(e, "column", None),
            },
        )


def get_reportable_conditions(root) -> str | None:
    """
    Scan the Report Summary section for SNOMED CT codes and return
    them as a comma-separated string, or None if none found.
    """
    codes = []

    # find sections with loinc code 55112-7
    for section in root.xpath(
        ".//cda:section[cda:code/@code='55112-7']", namespaces=NAMESPACES
    ):
        # find all values with the specified codeSystem
        values = section.xpath(
            ".//cda:value[@codeSystem='2.16.840.1.113883.6.96']/@code",
            namespaces=NAMESPACES,
        )
        codes.extend(values)

    return ",".join(codes) if codes else None
