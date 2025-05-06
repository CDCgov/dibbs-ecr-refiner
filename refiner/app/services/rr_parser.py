from typing import Any

from fastapi import Response, status
from lxml import etree

NAMESPACES = {
    "cda": "urn:hl7-org:v3",
    "sdtc": "urn:hl7-org:sdtc",
    "voc": "http://www.lantanagroup.com/voc",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}


def parse_xml(rr_xml: str) -> Any | Response:
    """
    Parses a raw RR XML string and returns the root Element.

    Args:
        rr_xml (str): The raw XML string.

    Returns:
        etree._Element if successful, or FastAPI Response on error.
    """
    try:
        parser = etree.XMLParser(remove_blank_text=True)
        rr_root = etree.fromstring(rr_xml.encode("utf-8"), parser=parser)
        return rr_root
    except etree.ParseError as e:
        return Response(
            content=f"Failed to parse RR XML: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST,
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
