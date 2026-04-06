from typing import cast

from lxml import etree
from lxml.etree import _Element

from app.db.configurations.model import DbConfigurationSectionInstructions
from app.services.ecr.model import EICRRefinementPlan
from app.services.terminology import ProcessedConfiguration

from ...core.exceptions import (
    StructureValidationError,
)
from ...core.models.types import XMLFiles
from ..format import remove_element
from .model import HL7_NS, RRRefinementPlan
from .process_eicr import (
    create_minimal_section,
    get_section_by_code,
    get_section_loinc_codes,
    process_section,
)
from .specification import SECTION_PROCESSING_SKIP, detect_eicr_version, load_spec

# NOTE:
# CONSTANTS
# =============================================================================

# TODO:
# decide on default values for both:
# * SKIP_SECTION_INSTRUCTIONS
#   - if the action is "retain" we should keep (retain) the narrative as-is
# * DEFAULT_SECTION_INSTRUCTIONS
#   - we should match how it shows up in the UI where narrative is set
#     to 'false' and refine is set to 'true'
SKIP_SECTION_INSTRUCTIONS = DbConfigurationSectionInstructions(
    include=True,
    narrative=True,
    action="retain",
)

DEFAULT_SECTION_INSTRUCTIONS = DbConfigurationSectionInstructions(
    include=True,
    narrative=False,
    action="refine",
)


# NOTE:
# PUBLIC API FUNCTIONS
# =============================================================================


def get_file_size_in_bytes(file_content: str) -> int:
    """
    Encodes the string as UTF-8 and determines its size in bytes.

    Args:
        file_content (str): The content of the file as a string

    Returns:
        int: Size in bytes
    """
    return len(file_content.encode("utf-8"))


def get_file_size_in_megabytes(file_content: str) -> int:
    """
    Returns file size in megabytes.
    """

    return round(get_file_size_in_bytes(file_content) / 1_000_000)


def get_file_size_reduction_percentage(unrefined_eicr: str, refined_eicr: str) -> int:
    """
    Given an unrefined document eICR document and a refined eICR document, calculate the percentage in which the file size was reduced post-refinement.

    Args:
        unrefined_eicr (str): An unrefined eICR XML document
        refined_eicr (str): A refined eICR XML document
    Returns:
        int: Integer representing the percentage in which the file size was reduced.
    """

    unrefined_bytes = get_file_size_in_bytes(unrefined_eicr)
    refined_bytes = get_file_size_in_bytes(refined_eicr)

    if unrefined_bytes == 0:
        return 0

    percent_diff = (unrefined_bytes - refined_bytes) / unrefined_bytes * 100
    return round(percent_diff)


# NOTE:
# EICR REFINEMENT PLAN CREATION
# =============================================================================


def _build_section_rules_map(
    processed_configuration: ProcessedConfiguration,
) -> dict[str, DbConfigurationSectionInstructions]:
    """
    Builds a section rules map from a processed configuration.

    The map key is a section LOINC code and the value is a `DbConfigurationSectionInstructions`.

    Args:
        processed_configuration (ProcessedConfiguration): The processed configuration

    Returns:
        dict[str, DbConfigurationSectionInstructions]: The resulting section rules map
    """
    rules_map: dict[str, DbConfigurationSectionInstructions] = {}

    for rule in processed_configuration.section_processing:
        code = rule.get("code")
        if not code:
            continue

        rules_map[code] = DbConfigurationSectionInstructions(
            include=rule.get("include", DEFAULT_SECTION_INSTRUCTIONS.include),
            narrative=rule.get("narrative", DEFAULT_SECTION_INSTRUCTIONS.narrative),
            action=rule.get("action", DEFAULT_SECTION_INSTRUCTIONS.action),
        )

    return rules_map


def _apply_section_skip_rules(
    rules_map: dict[str, DbConfigurationSectionInstructions],
) -> dict[str, DbConfigurationSectionInstructions]:
    """
    Takes a section rules map, copies it, updates it to include skipped sections, and then returns the new map.

    Args:
        rules_map (dict[str, DbConfigurationSectionInstructions]): The original map without skips

    Returns:
        dict[str, DbConfigurationSectionInstructions]: The modified map that includes skipped sections
    """
    modified_map = rules_map.copy()

    for code in SECTION_PROCESSING_SKIP:
        modified_map[code] = SKIP_SECTION_INSTRUCTIONS

    return modified_map


def create_eicr_refinement_plan(
    processed_configuration: ProcessedConfiguration,
    eicr_root: _Element,
) -> EICRRefinementPlan:
    """
    Create an EICRRefinementPlan by combining configuration rules and the sections present in the parsed eICR document.

    Args:
        processed_configuration: The processed configuration containing terminology
                                 and section processing rules.
        eicr_root: The parsed eICR root element.

    Returns:
        An EICRRefinementPlan containing the exact instructions for `refine_eicr`.
    """

    # discover all sections directly from the parsed tree
    structured_body = eicr_root.find(".//hl7:structuredBody", namespaces=HL7_NS)
    present_section_codes = (
        get_section_loinc_codes(structured_body) if structured_body is not None else []
    )

    # create a map of the rules from the configuration for efficient lookup
    rules_map = _build_section_rules_map(processed_configuration)

    # update the rules map with sections to be skipped (include + retain)
    rules_map_with_skips = _apply_section_skip_rules(rules_map)

    section_instructions = {
        # * for each discovered section, use the determined rules from the map
        # * if a code doesn't yet have rules, we'll skip it (include + retain)
        code: rules_map_with_skips.get(code, SKIP_SECTION_INSTRUCTIONS)
        for code in present_section_codes
    }

    return EICRRefinementPlan(
        codes_to_check=processed_configuration.codes,
        code_system_sets=processed_configuration.code_system_sets,
        section_instructions=section_instructions,
    )


# NOTE:
# EICR REFINEMENT EXECUTION
# =============================================================================


def refine_eicr(
    eicr_root: _Element,
    plan: EICRRefinementPlan,
) -> None:
    """
    Refine an eICR by executing a provided RefinementPlan.

    Mutates `eicr_root` in place. The caller is responsible for parsing
    beforehand and serializing afterward.

    This function is a "pure executor." It does not make decisions; it only
    carries out the instructions given to it in the plan.

    Processing behavior:
        - It iterates through the instructions in the plan.
        - For each section, it performs one of three actions:
          - retain: Leaves the section completely unmodified.
          - remove: Replaces the section with a minimal "stub" section.
          - refine: Processes the section using the plan's XPath to filter entries.

    Args:
        eicr_root: The parsed eICR root element.
        plan: A complete, actionable plan for refining the eICR.

    Raises:
        StructureValidationError: If the document structure is invalid.
    """

    structured_body = eicr_root.find(".//hl7:structuredBody", HL7_NS)

    # if we don't have a structuredBody this is a major problem
    if structured_body is None:
        raise StructureValidationError(
            message="No structured body found in eICR",
            details={"document_type": "eICR"},
        )

    # STEP 1:
    # detect version
    version = detect_eicr_version(eicr_root)

    # STEP 2:
    # load specification
    specification = load_spec(version)

    for section_code, section_rules in plan.section_instructions.items():
        section = get_section_by_code(
            structured_body=structured_body,
            loinc_code=section_code,
            namespaces=HL7_NS,
        )

        if section is None:
            continue

        if not section_rules.include:
            # we will just force a minimal section
            create_minimal_section(section=section, removal_reason="configured")
            continue

        if section_rules.action == "retain":
            # retain means that we're not processing this section so we continue
            continue

        section_specification = specification.sections.get(section_code)
        process_section(
            section=section,
            codes_to_match=plan.codes_to_check,
            namespaces=HL7_NS,
            section_specification=section_specification,
            code_system_sets=plan.code_system_sets,
            include_narrative=section_rules.narrative,
        )


# NOTE:
# RR REFINEMENT
# =============================================================================


def create_rr_refinement_plan(
    processed_configuration: ProcessedConfiguration,
) -> RRRefinementPlan:
    """
    Given a ProcessedConfiguration, creates and returns an RRRefinementPlan.

    Args:
        processed_configuration (ProcessedConfiguration): ProcessedConfiguration to build the plan from.

    Returns:
        RRRefinementPlan: The newly created RRRefinement plan.
    """

    return RRRefinementPlan(
        included_condition_child_rsg_snomed_codes_to_retain=processed_configuration.included_condition_rsg_codes
    )


def refine_rr(
    rr_root: _Element,
    plan: RRRefinementPlan,
) -> None:
    """
    Refine an RR by filtering out conditions not reportable to the jurisdiction.

    Mutates `rr_root` in place. The caller is responsible for parsing
    beforehand and serializing afterward.

    Processing behavior:
        - It iterates through the RR and removes information common to all RR's.
        - It loops through all the condition observations in the reportability RC
            - Anything that isn't RRSVS1 reportable is filtered out
            - Of the remaining reportable observations, anything that isn't specified
              in the refinement configurations are filtered out
            - For anything remaining, any codes that aren't specified within the
              in the configuration RSG or custom codes are filtered out.

    Args:
        rr_root: The parsed RR root element.
        plan: The RRRefinementPlan for the corresponding eICR.

    Raises:
        StructureValidationError: If the document structure is invalid.
    """

    # now, move on to processing the actual RR body
    structured_body = rr_root.find(".//hl7:structuredBody", HL7_NS)

    if structured_body is None:
        raise StructureValidationError(
            message="No structured body found in RR",
            details={"document_type": "RR"},
        )
    rr11_organizers = cast(
        list[_Element],
        structured_body.xpath(
            ".//hl7:section[hl7:code/@code='55112-7']//hl7:entry/hl7:organizer[hl7:code/@code='RR11']",
            namespaces=HL7_NS,
        ),
    )

    if not rr11_organizers and not rr11_organizers[0]:
        raise StructureValidationError(
            message="Missing required RR11 Coded Information Organizer",
            details={
                "document_type": "RR",
                "error": "RR11 organizer not found in Summary Section",
            },
        )

    rr_organizer = rr11_organizers[0]

    # Compile the set of conditions the jurisdiction has a configuration
    # for as represented by the child_rsg_snomed codes that exist in the payload
    codes_to_keep: set[str] = set(
        plan.included_condition_child_rsg_snomed_codes_to_retain
    )

    components_to_check = cast(
        list[_Element],
        rr_organizer.xpath(
            ".//hl7:component[hl7:observation[hl7:templateId/@root='2.16.840.1.113883.10.20.15.2.3.12']]",
            namespaces=HL7_NS,
        ),
    )

    for component in components_to_check:
        observation = component.find("hl7:observation", HL7_NS)
        if observation is None:
            continue

        value = observation.find("hl7:value", HL7_NS)
        if value is None:
            continue

        value_to_check = value.get("code")
        if value_to_check not in codes_to_keep:
            # if the payload in question doesn't have that condition in the config,
            # remove that observation
            remove_element(component)
            continue

        organizers = cast(
            list[_Element],
            observation.xpath(
                ".//hl7:entryRelationship/hl7:organizer",
                namespaces=HL7_NS,
            ),
        )

        if not organizers:
            continue

        organizer = organizers[0]

        rr7_roles = cast(
            list[_Element],
            organizer.xpath(
                ".//hl7:participant/hl7:participantRole[hl7:code/@code='RR7']",
                namespaces=HL7_NS,
            ),
        )

        if not rr7_roles:
            continue

        for rr7_role in rr7_roles:
            id_element = rr7_role.find("hl7:id", HL7_NS)

            if id_element is None:
                continue

        # Similarly, if component / observation doesn't have a tagged RRVS1 entry,
        # it's not reportable, so throw out the whole thing
        reportable_observation_tags = cast(
            list[_Element],
            organizer.xpath(
                ".//hl7:component/hl7:observation[hl7:value/@code='RRVS1']",
                namespaces=HL7_NS,
            ),
        )

        if len(reportable_observation_tags) == 0:
            remove_element(component)
            continue


def refine_rr_for_unconfigured_conditions(
    xml_files: XMLFiles,
    condition_codes: set[str],
) -> str:
    """
    Create an RR filtered to only the reportable conditions that were not refined.

    This is a convenience function for callers outside the pipeline (e.g., the
    lambda handler) that need a self-contained parse → filter → serialize path.
    The pipeline itself uses reportability directly on a parsed tree.

    When the RR contains multiple reportable conditions for a jurisdiction but
    only some have active refiner configurations, the conditions that go through
    full refinement get their own refined RR (produced by `refine_for_condition`
    via the pipeline). The remaining conditions — those without active
    configurations — still need their reportability information preserved.

    This function produces that "remainder" RR. It filters the original RR down
    to just the condition observations matching the provided codes, removing
    everything else. This prevents duplication: when the jurisdiction receives
    the full output package (original files + refined outputs), each condition's
    reportability information appears exactly once.

    Example scenario:
        SDDH has two reportable conditions: COVID (840539006) and Influenza (772828001).
        Only COVID has an active configuration.

        - COVID goes through refine_for_condition → produces refined_eICR.xml + refined_RR.xml
        - Influenza has no config → this function produces an RR with only the
          Influenza reportability observation, written to unrefined_rr/refined_RR.xml

        The jurisdiction receives both and can process each condition without
        seeing COVID reported twice.

    Args:
        xml_files: The eICR/RR pair. Only the RR is used.
        condition_codes: The set of RSG SNOMED codes for conditions that
            were NOT refined (i.e., had no active configuration). The
            returned RR will retain only these condition observations.

    Returns:
        str: The filtered RR XML as a string, containing only the
            reportability observations for the specified condition codes.
    """

    plan = RRRefinementPlan(
        included_condition_child_rsg_snomed_codes_to_retain=condition_codes
    )

    rr_root = xml_files.parse_rr()
    refine_rr(rr_root=rr_root, plan=plan)
    return etree.tostring(rr_root, encoding="unicode")
