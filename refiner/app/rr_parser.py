import xml.etree.ElementTree as ET

from fastapi import Response, status

NAMESPACES = {
    "cda": "urn:hl7-org:v3",
    "sdtc": "urn:hl7-org:sdtc",
    "voc": "http://www.lantanagroup.com/voc",
}


def parse_xml(rr_xml: str) -> ET.Element | Response:
    """
    Parses a raw RR XML string and returns the root Element.

    Args:
        rr_xml (str): The raw XML string.

    Returns:
        ElementTree.Element if successful, or FastAPI Response on error.
    """
    try:
        rr_root = ET.fromstring(rr_xml)
        return rr_root
    except ET.ParseError as e:
        return Response(
            content=f"Failed to parse RR XML: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


def get_reportable_conditions(root: ET.Element) -> str | None:
    """
    Scan the Report Summary section for SNOMED CT codes and return
    them as a comma-separated string, or None if none found.
    """
    ns = {"cda": "urn:hl7-org:v3", "xsi": "http://www.w3.org/2001/XMLSchema-instance"}
    codes = []
    for section in root.findall(".//cda:section", namespaces=ns):
        if (c := section.find("cda:code", namespaces=ns)) is not None and c.attrib.get(
            "code"
        ) == "55112-7":
            for ve in section.findall(
                ".//cda:value[@codeSystem='2.16.840.1.113883.6.96']", namespaces=ns
            ):
                code = ve.attrib.get("code")
                if code:
                    codes.append(code)
    return ",".join(codes) if codes else None
