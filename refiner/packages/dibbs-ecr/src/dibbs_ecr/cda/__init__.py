from __future__ import annotations

from typing import Final

type NamespaceMap = dict[str, str]

HL7_NAMESPACE: Final[str] = "urn:hl7-org:v3"

HL7_NS: Final[NamespaceMap] = {"hl7": HL7_NAMESPACE}

HL7_XSI_NS: Final[NamespaceMap] = {
    "hl7": HL7_NAMESPACE,
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

__all__ = [
    "HL7_NAMESPACE",
    "HL7_NS",
    "HL7_XSI_NS",
    "NamespaceMap",
]
