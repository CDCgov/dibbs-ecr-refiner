from typing import cast

from lxml.etree import _Element

from ...core.exceptions import StructureValidationError
from .models import JurisdictionReportableConditions, ReportableCondition

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
# INTERNAL HELPERS
# =============================================================================


def get_reportable_conditions_by_jurisdiction(
    root: _Element,
) -> list[JurisdictionReportableConditions]:
    """
    Traverse the RR11 Coded Information Organizer in a Reportability Response (RR) CDA document to extract all SNOMED-coded reportable conditions, grouped by jurisdiction/routing agency.

    Steps performed:
        1. Locate the single RR11 Coded Information Organizer within the Summary Section
           (LOINC code 55112-7). This organizer contains the context for routing and conditions.
        2. Prepare a mapping from jurisdiction code (RR7 Routing Entity extension) to a dictionary
           of unique SNOMED-coded reportable conditions.
        3. For each SNOMED-coded condition observation (templateId 2.16.840.1.113883.10.20.15.2.3.12):
            A. Extract the SNOMED code and display name from its <value> element.
            B. For each entryRelationship/component/organizer beneath the condition:
                i. Identify RR7 Routing Entity participantRole and extract its jurisdiction code (extension attribute).
                ii. Confirm this context contains a reportability determination (RR1 observation with value RRVS1).
                iii. If reportable, associate the SNOMED code with the jurisdiction in the mapping, deduplicating by code.
        4. Build and return a list of JurisdictionReportableConditions instances, each containing the jurisdiction code and its unique list of reportable conditions.

    Args:
        root (_Element): Parsed lxml root of the RR CDA document.

    Returns:
        list[JurisdictionReportableConditions]: List of jurisdiction → reportable condition groupings.
    """

    namespaces = {
        "cda": "urn:hl7-org:v3",
        "sdtc": "urn:hl7-org:sdtc",
        "voc": "http://www.lantanagroup.com/voc",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }

    # STEP 1.
    # locate RR11 organizer (should be only one per RR document)
    rr11_organizers = cast(
        list[_Element],
        root.xpath(
            ".//cda:section[cda:code/@code='55112-7']//cda:entry/cda:organizer[cda:code/@code='RR11']",
            namespaces=namespaces,
        ),
    )
    if not rr11_organizers:
        raise StructureValidationError(
            message="Missing required RR11 Coded Information Organizer",
            details={
                "document_type": "RR",
                "error": "RR11 organizer not found in Summary Section",
            },
        )
    rr11_organizer = rr11_organizers[0]

    # STEP 2.
    # prepare jurisdiction → condition mapping
    jurisdiction_to_conditions: dict[str, dict[str, ReportableCondition]] = {}

    # STEP 3.
    # traverse condition observations in RR11
    condition_observations = cast(
        list[_Element],
        rr11_organizer.xpath(
            ".//cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12']]",
            namespaces=namespaces,
        ),
    )
    for condition_observation in condition_observations:
        # A.
        # get SNOMED code + display name
        value_element = condition_observation.find("cda:value", namespaces)
        if value_element is None:
            continue
        snomed_code = value_element.get("code")
        display_name = value_element.get(
            "displayName", "Condition display name not found"
        )
        if not snomed_code:
            continue
        condition_object = ReportableCondition(code=snomed_code, display=display_name)

        # B.
        # for each entryRelationship/component/organizer under this observation
        entry_relationships = condition_observation.findall(
            "cda:entryRelationship", namespaces
        )
        for entry_relationship in entry_relationships:
            organizer = entry_relationship.find("cda:organizer", namespaces)
            if organizer is None:
                continue

            # i.
            # find RR7 Routing Entity participantRole
            rr7_roles = organizer.xpath(
                ".//cda:participantRole[cda:code/@code='RR7']", namespaces=namespaces
            )
            if not rr7_roles:
                continue
            rr7_role = rr7_roles[0]
            id_element = rr7_role.find("cda:id", namespaces)
            if id_element is None or not id_element.get("extension"):
                continue
            jurisdiction_code = id_element.get("extension")

            # ii.
            # confirm RR1/RRVS1 "reportable" determination exists in this organizer
            rr1_reportable = organizer.xpath(
                ".//cda:observation[cda:code/@code='RR1']/cda:value[@code='RRVS1']",
                namespaces=namespaces,
            )
            if not rr1_reportable:
                continue

            # iii.
            # add to jurisdiction mapping, deduping SNOMED code
            if jurisdiction_code not in jurisdiction_to_conditions:
                jurisdiction_to_conditions[jurisdiction_code] = {}
            jurisdiction_to_conditions[jurisdiction_code][snomed_code] = (
                condition_object
            )

    # STEP 4.
    # build output: List of JurisdictionReportableConditions
    jurisdiction_groups = [
        JurisdictionReportableConditions(
            jurisdiction=jurisdiction,
            conditions=list(cond_map.values()),
        )
        for jurisdiction, cond_map in jurisdiction_to_conditions.items()
    ]

    return jurisdiction_groups
