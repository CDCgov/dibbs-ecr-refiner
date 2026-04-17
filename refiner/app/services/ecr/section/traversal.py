from typing import cast

from lxml import etree
from lxml.etree import _Element

from app.core.exceptions import XMLParsingError
from app.services.ecr.model import HL7_NS, NamespaceMap

# NOTE:
# SECTION LOOKUP
# =============================================================================


def get_section_by_code(
    structured_body: _Element,
    loinc_code: str,
    namespaces: NamespaceMap = HL7_NS,
) -> _Element | None:
    """
    Get a top-level section from structuredBody by its LOINC code.

    Searches only direct <component>/<section> children of structuredBody,
    not nested sub-sections within other sections. This matches the eICR
    IG's section cardinality semantics: the sections defined by the IG
    are top-level, and repeated occurrences of the same LOINC code at
    deeper levels represent different semantic content that should not
    be conflated with top-level sections.

    If the document has multiple top-level sections with the same LOINC
    code (which should not occur in a Schematron-valid eICR but could
    occur in a malformed document), the first match is returned. Callers
    that need to handle this case should compare against the full list
    produced by `get_section_loinc_codes`.

    Args:
        structured_body: The HL7 structuredBody element to search within.
        loinc_code: The LOINC code of the section to retrieve.
        namespaces: The namespaces to use for element search. Defaults to hl7.

    Returns:
        The section element, or None if no top-level section with that
        LOINC code is present.

    Raises:
        XMLParsingError: If XPath evaluation fails.
    """

    try:
        xpath_query = f'./hl7:component/hl7:section[hl7:code[@code="{loinc_code}"]]'
        xpath_result = structured_body.xpath(xpath_query, namespaces=namespaces)

        if isinstance(xpath_result, list) and len(xpath_result) >= 1:
            sections = cast(list[_Element], xpath_result)
            return sections[0]
    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message=f"Failed to evaluate XPath for section code {loinc_code}",
            details={"xpath_query": xpath_query, "error": str(e)},
        )
    return None


# NOTE:
# SECTION DISCOVERY
# =============================================================================


def get_section_loinc_codes(
    structured_body: _Element,
    namespaces: NamespaceMap = HL7_NS,
) -> list[str]:
    """
    Return LOINC codes for all top-level sections in structuredBody.

    Used to discover which sections are actually present in a given eICR
    document before applying any refinement logic. Only considers direct
    <component>/<section> children of structuredBody; nested sub-sections
    are deliberately excluded to match the eICR IG's section cardinality
    model.

    Args:
        structured_body: The <structuredBody> XML element from an eICR.
        namespaces: The XML namespaces to use for the XPath query.

    Returns:
        A list of LOINC code strings for the top-level sections found
        in the document. Order matches document order. Duplicates are
        preserved; callers that need deduplication should convert to
        a set.

    Raises:
        XMLParsingError: If XPath evaluation fails.
    """

    if structured_body is None:
        return []

    # this xpath is designed to be specific and efficient:
    # 1. it starts from the current element (structured_body)
    # 2. it finds direct <component>/<section> children
    # 3. it then finds the direct <code> child of that section
    # 4. finally, it extracts the 'code' attribute string
    # this avoids finding codes in nested sections or other parts of the
    # document
    xpath_query = "./hl7:component/hl7:section/hl7:code/@code"

    try:
        xpath_result = structured_body.xpath(xpath_query, namespaces=namespaces)

        if isinstance(xpath_result, list):
            return cast(list[str], xpath_result)

        return []
    except etree.XPathError as e:
        raise XMLParsingError(
            message="Failed to evaluate XPath for discovering section LOINC codes.",
            details={"xpath_query": xpath_query, "error": str(e)},
        )
