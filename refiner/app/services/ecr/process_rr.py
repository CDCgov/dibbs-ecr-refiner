from typing import cast

from lxml import etree
from lxml.etree import _Element

from ...core.exceptions import StructureValidationError, XMLParsingError
from ...core.models.types import XMLFiles
from .models import ProcessedRR, ReportableCondition

# NOTE:
# =============================================================================
# In lxml, use _Element for type hints and etree.Element in code.
# -> _Element (from lxml.etree) is the actual type of xml element objects, suitable for
#    type annotations and for static type checkers
# -> etree.Element is a factory function that creates and returns _Element instances; use
#    it in code to create nodes.
# * Do not use etree.Element for type hints; it's not a class, but a function.
#   See: https://lxml.de/api/lxml.etree._Element-class.html
# * this will change in lxml 6.0
#   See: on this PR: https://github.com/lxml/lxml/pull/405


# NOTE:
# PUBLIC API FUNCTIONS
# =============================================================================


def process_rr(xml_files: XMLFiles) -> ProcessedRR:
    """
    Process the RR XML document to extract relevant information.

    Args:
        xml_files: Container with both eICR and RR XML content
                  (currently only using RR)

    Returns:
        dict: Extracted information from the RR document

    Raises:
        XMLParsingError
    """

    try:
        rr_root = xml_files.parse_rr()
        return {"reportable_conditions": _get_reportable_conditions(rr_root)}
    except etree.XMLSyntaxError as e:
        raise XMLParsingError(
            message="Failed to parse RR document", details={"error": str(e)}
        )


# NOTE:
# INTERNAL HELPERS
# =============================================================================


def _get_reportable_conditions(root: _Element) -> list[ReportableCondition]:
    """
    Get reportable conditions from the Report Summary section.

    Following RR spec 1.1 structure:
    - Summary Section (55112-7) contains exactly one RR11 organizer
    - RR11 Coded Information Organizer contains condition observations
    - Each observation must have:
      - Template ID 2.16.840.1.113883.10.20.15.2.3.12
      - RR1 determination code with RRVS1 value for reportable conditions
      - SNOMED CT code in value element (codeSystem 2.16.840.1.113883.6.96)

    Args:
        root: The root element of the XML document to parse.

    Returns:
        list[ReportableCondition]

    Raises:
        StructureValidationError: If RR11 Coded Information Organizer is missing (invalid RR)
        XMLParsingError: If XPath evaluation fails
    """

    conditions = []

    # standard CDA namespace declarations required for RR documents
    namespaces = {
        "cda": "urn:hl7-org:v3",
        "sdtc": "urn:hl7-org:sdtc",
        "voc": "http://www.lantanagroup.com/voc",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }

    try:
        # the summary section (55112-7) must contain exactly one RR11 organizer
        # this is specified in the RR IG
        coded_info_organizers = cast(
            list[_Element],
            root.xpath(
                ".//cda:section[cda:code/@code='55112-7']"
                "//cda:entry/cda:organizer[cda:code/@code='RR11']",
                namespaces=namespaces,
            ),
        )

        # if there is no coded information organizer then the RR is not valid
        # this would be a major problem
        if not coded_info_organizers:
            raise StructureValidationError(
                message="Missing required RR11 Coded Information Organizer",
                details={
                    "document_type": "RR",
                    "error": "RR11 organizer with cardinality 1..1 not found in Summary Section",
                },
            )

        # we can safely take [0] because cardinality is 1..1
        coded_info_organizer = coded_info_organizers[0]

        # find all condition observations using the specified templateId
        # This templateId is fixed in the RR spec and identifies condition observations
        observations = cast(
            list[_Element],
            coded_info_organizer.xpath(
                ".//cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12']]",
                namespaces=namespaces,
            ),
        )

        for observation in observations:
            # RR1 with value RRVS1 indicates a "reportable" condition
            # this is how the RR explicitly marks conditions that should be reported
            # other values like "not reportable" or "may be reportable" are filtered out
            determination = observation.xpath(
                ".//cda:observation[cda:code/@code='RR1']/cda:value[@code='RRVS1']",
                namespaces=namespaces,
            )
            if not determination:
                continue

            # per RR spec, each reportable condition observation MUST contain
            # a valid SNOMED CT code (CONF:3315-552) in its value element
            # codeSystem 2.16.840.1.113883.6.96 is required for SNOMED CT
            value = cast(
                list[_Element],
                observation.xpath(
                    ".//cda:value[@codeSystem='2.16.840.1.113883.6.96']",
                    namespaces=namespaces,
                ),
            )
            if not value:
                continue

            code = value[0].get("code")
            display_name = value[0].get(
                "displayName", "Condition display name not found"
            )
            if not code:
                continue

            # when a condition is reportable, we must capture its
            # required SNOMED CT code and display name and build the
            # condition object and ensure uniqueness--duplicate conditions
            # should not be reported multiple times
            condition = ReportableCondition(code=code, display_name=display_name)
            if condition not in conditions:
                conditions.append(condition)

    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message="Failed to evaluate XPath expression in RR document",
            details={"xpath_error": str(e)},
        )

    return conditions
