from lxml import etree
from lxml.etree import _Element

from app.services.format import remove_element

from ..model import (
    HL7_NAMESPACE,
    HL7_NS,
)

# NOTE:
# ELEMENT FACTORY HELPERS
# =============================================================================
# every element emitted into <text> must be qualified with the HL7 v3
# namespace for NarrativeBlock.xsd validation to pass


def _make_element(local_name: str, **attribs: str) -> _Element:
    """
    Create a namespace-qualified narrative element.

    Returns a detached element in the urn:hl7-org:v3 namespace. Use
    `_sub_element` instead when the new element should be appended
    to an existing parent.
    """

    element = etree.Element(f"{{{HL7_NAMESPACE}}}{local_name}")
    for key, value in attribs.items():
        element.set(key, value)
    return element


def _sub_element(parent: _Element, local_name: str, **attribs: str) -> _Element:
    """
    Create a namespace-qualified child element appended to `parent`.

    Thin wrapper around etree.SubElement that applies Clark notation
    for the HL7 v3 namespace, matching the pattern used in augment.py.
    """

    element = etree.SubElement(parent, f"{{{HL7_NAMESPACE}}}{local_name}")
    for key, value in attribs.items():
        element.set(key, value)
    return element


# NOTE:
# TEXT PLACEMENT HELPERS
# =============================================================================


def _ensure_text_element(section: _Element) -> _Element:
    """
    Return the section's <text> element, creating one if absent.

    If the section has no <text>, a new empty <text> is created and
    inserted after <title> per the CDA R2 xs:sequence for
    StrucDoc.Section: templateId -> id -> code -> title -> text ->
    confidentialityCode -> languageCode -> subject -> author ->
    informant -> entry -> component.

    If there is no <title> either, the <text> is inserted after
    <code>, which is the next-earliest required element in the
    sequence. Last resort: append to the section.
    """

    text_element = section.find("hl7:text", namespaces=HL7_NS)
    if text_element is not None:
        return text_element

    text_element = _make_element("text")

    title_element = section.find("hl7:title", namespaces=HL7_NS)
    if title_element is not None:
        title_element.addnext(text_element)
        return text_element

    code_element = section.find("hl7:code", namespaces=HL7_NS)
    if code_element is not None:
        code_element.addnext(text_element)
        return text_element

    section.append(text_element)
    return text_element


# NOTE:
# COMMENT CLEANUP
# =============================================================================


def remove_all_comments(section: _Element) -> None:
    """
    Remove all XML comments from a processed section.

    After refining a section, inline comments left over from the source
    document may no longer be accurate or relevant. This scrubs them
    so the refined output doesn't carry misleading annotations forward.
    """

    xpath_result = section.xpath(".//comment()")
    if isinstance(xpath_result, list):
        for comment in xpath_result:
            if isinstance(comment, etree._Element):
                remove_element(comment)
