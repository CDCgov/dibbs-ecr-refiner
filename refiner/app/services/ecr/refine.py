import dataclasses
from typing import cast

from lxml import etree
from lxml.etree import _Element

from app.core.exceptions import StructureValidationError
from app.core.models.types import XMLFiles
from app.db.configurations.model import DbConfigurationSectionInstructions
from app.services.ecr.model import (
    HL7_NS,
    EICRRefinementPlan,
    EICRSpecification,
    RRRefinementPlan,
    SectionOutcome,
    SectionProvenanceRecord,
    SectionRunResult,
    SectionSource,
)
from app.services.ecr.policy import SECTION_PROCESSING_SKIP
from app.services.ecr.section import (
    append_section_provenance_footnote,
    create_minimal_section,
    get_section_by_code,
    get_section_loinc_codes,
    process_section,
)
from app.services.ecr.section.narrative import replace_narrative_with_removal_notice
from app.services.ecr.specification import detect_eicr_version, load_spec
from app.services.format import remove_element
from app.services.terminology import ProcessedConfiguration

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


def get_file_size_in_mib(file_content: str) -> float:
    """
    Returns file size in mebibytes (MiB).
    """

    size_mb = get_file_size_in_bytes(file_content) / (1024 * 1024)
    return round(size_mb, 3)


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


def _build_section_name_lookup(
    processed_configuration: ProcessedConfiguration,
) -> dict[str, str]:
    """
    Build a LOINC code → section name lookup from the processed configuration.

    The name comes from the jurisdiction's configuration (what they see in the
    UI), not the IG canonical display name. This is the authoritative name for
    provenance since we're documenting their configuration choices.

    Args:
        processed_configuration: The processed configuration.

    Returns:
        dict[str, str]: Map of LOINC code to section name.
    """

    return {
        rule["code"]: rule.get("name", rule["code"])
        for rule in processed_configuration.section_processing
        if rule.get("code")
    }


def _build_section_provenance(
    present_section_codes: list[str],
    rules_map: dict[str, DbConfigurationSectionInstructions],
    rules_map_with_skips: dict[str, DbConfigurationSectionInstructions],
    specification: EICRSpecification,
    section_name_lookup: dict[str, str],
    config_version: int | None,
) -> dict[str, SectionProvenanceRecord]:
    """
    Build a provenance record for every section present in this document.

    Classifies each section by source — configured by the jurisdiction,
    held by a system skip rule, or not in the jurisdiction's configuration
    at all — so downstream rendering can explain why a section looks the
    way it does in the refined output.

    Source classification (evaluated in priority order):
        - "system_skip": code is in SECTION_PROCESSING_SKIP (always retain,
          regardless of configuration)
        - "configured": code is in the jurisdiction's configuration rules_map
        - "unconfigured": code is present in the document but absent from both
          of the above; falls back to SKIP_SECTION_INSTRUCTIONS at refinement time

    Display name priority:
        - configured sections: jurisdiction's name from section_name_lookup
          (what they see and set in the UI)
        - system_skip / unconfigured sections: IG canonical display name from
          specification, falling back to the LOINC code if not in the catalog

    The `outcome` field on each record is left at its default value
    here. refine_eicr finalizes it via `dataclasses.replace` after
    section processing completes — see `_interpret_run_result`.

    Args:
        present_section_codes: LOINC codes of sections found in the document.
        rules_map: Pre-skip configuration rules (configured sections only).
        rules_map_with_skips: Merged map including system skip rules.
        specification: The eICR spec for this document's version.
        section_name_lookup: LOINC → jurisdiction-configured name.
        config_version: The version of the activated configuration, or None
            if not available (e.g., legacy S3 configs without version).

    Returns:
        dict[str, SectionProvenanceRecord]: One record per present section,
            keyed by LOINC code.
    """

    provenance: dict[str, SectionProvenanceRecord] = {}

    for code in present_section_codes:
        # classify source before the merged map loses the distinction
        if code in SECTION_PROCESSING_SKIP:
            source = SectionSource.SYSTEM_SKIP
        elif code in rules_map:
            source = SectionSource.CONFIGURED
        else:
            source = SectionSource.UNCONFIGURED

        # resolve display name: jurisdiction name for configured sections,
        # IG canonical name for everything else
        if source == SectionSource.CONFIGURED:
            display_name = section_name_lookup.get(code, code)
        else:
            spec_entry = specification.sections.get(code)
            display_name = spec_entry.display_name if spec_entry else code

        # resolve instructions from the merged map (same fallback as refine_eicr)
        instructions = rules_map_with_skips.get(code, SKIP_SECTION_INSTRUCTIONS)

        provenance[code] = SectionProvenanceRecord(
            loinc_code=code,
            display_name=display_name,
            include=instructions.include,
            action=instructions.action,
            narrative=instructions.narrative,
            config_version=config_version,
            source=source,
        )

    return provenance


def create_eicr_refinement_plan(
    processed_configuration: ProcessedConfiguration,
    eicr_root: _Element,
    augmentation_timestamp: str,
    config_version: int | None = None,
) -> EICRRefinementPlan:
    """
    Create an EICRRefinementPlan by combining configuration rules and the sections present in the parsed eICR document.

    Detects the eICR version and loads the specification once here so that
    refine_eicr receives a fully resolved plan and does not need to
    re-inspect the document. The specification is also used by
    _build_section_provenance to resolve display names for sections not
    present in the jurisdiction's configuration.

    Args:
        processed_configuration: The processed configuration containing terminology
                                 and section processing rules.
        eicr_root: The parsed eICR root element.
        augmentation_timestamp: The HL7 V3 timestamp from the
            AugmentationContext shared across this refinement run. Used
            to stamp the IDs on per-section provenance footnotes so they
            tie back to the augmentation author's <time> value.
        config_version: The version number of the activated configuration.
            Passed through to each SectionProvenanceRecord for audit trail.
            Optional for backward compatibility with callers that do not yet
            supply it (defaults to None).

    Returns:
        An EICRRefinementPlan containing the exact instructions for `refine_eicr`.
    """

    # detect version and load spec once — result is carried on the plan so
    # refine_eicr does not need to re-detect or re-load
    version = detect_eicr_version(eicr_root)
    specification = load_spec(version)

    # discover all sections directly from the parsed tree
    structured_body = eicr_root.find(".//hl7:structuredBody", namespaces=HL7_NS)
    present_section_codes = (
        get_section_loinc_codes(structured_body) if structured_body is not None else []
    )

    # build the rules map from the configuration, then overlay system skip rules
    rules_map = _build_section_rules_map(processed_configuration)
    rules_map_with_skips = _apply_section_skip_rules(rules_map)

    section_instructions = {
        # * for each discovered section, use the determined rules from the map
        # * if a code doesn't yet have rules, we'll skip it (include + retain)
        code: rules_map_with_skips.get(code, SKIP_SECTION_INSTRUCTIONS)
        for code in present_section_codes
    }

    # build provenance before the maps are discarded — source classification
    # requires the pre-merge rules_map to distinguish configured from unconfigured
    section_name_lookup = _build_section_name_lookup(processed_configuration)
    section_provenance = _build_section_provenance(
        present_section_codes=present_section_codes,
        rules_map=rules_map,
        rules_map_with_skips=rules_map_with_skips,
        specification=specification,
        section_name_lookup=section_name_lookup,
        config_version=config_version,
    )

    return EICRRefinementPlan(
        codes_to_check=processed_configuration.codes,
        code_system_sets=processed_configuration.code_system_sets,
        section_instructions=section_instructions,
        section_provenance=section_provenance,
        specification=specification,
        augmentation_timestamp=augmentation_timestamp,
        config_version=config_version,
    )


# NOTE:
# OUTCOME INTERPRETATION
# =============================================================================


def _interpret_run_result(
    section_rules: DbConfigurationSectionInstructions,
    run_result: SectionRunResult,
) -> SectionOutcome:
    """
    Map (configuration, run result) to a user-facing SectionOutcome.

    Most of this function is mechanical: the configured action and
    narrative disposition determine the outcome name. The one
    exception is the no-match override on the first branch — that's
    a refiner *policy* decision, not a configuration translation.

    The no-match override: when a section is configured for refinement
    (action="refine") but the matching engine finds no entries that
    match the configured codes, the section is stubbed regardless of
    the narrative configuration. This applies uniformly to all three
    refine variants (narrative retained, removed, or reconstructed).
    The justification is that preserving an empty section with an
    orphaned narrative would mislead reviewers — better to surface
    the empty result clearly than to imply there was content here.

    If this policy ever needs to vary (per-section overrides,
    thresholds, conditional stubbing based on document context, etc.),
    the right place for that logic is ecr/policy.py — that's where
    refiner-behavior decisions live, separate from the IG-derived
    specification and the structural matching engines. For now, the
    policy is a single condition in this function and adding
    indirection would obscure rather than clarify it.

    Args:
        section_rules: The jurisdiction's configured instructions for
            this section. Currently only used for documentation
            symmetry — the run result alone is sufficient to determine
            the outcome — but reserved for future policy variations
            that need to consult the configuration.
        run_result: What the matching engine reported about the run.

    Returns:
        The SectionOutcome describing what happened to this section.
    """

    # policy override: no matches always produces a stub, regardless
    # of what the narrative configuration said. see the docstring
    # above for the rationale.
    if not run_result.matches_found:
        return SectionOutcome.REFINED_NO_MATCHES_STUBBED

    # matches were found; outcome reflects what happened to the narrative
    if run_result.narrative_disposition == "removed":
        return SectionOutcome.REFINED_NARRATIVE_REMOVED
    if run_result.narrative_disposition == "reconstructed":
        return SectionOutcome.REFINED_NARRATIVE_RECONSTRUCTED
    return SectionOutcome.REFINED_WITH_MATCHES


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
    carries out the instructions given to it in the plan. Version detection
    and specification loading are performed during plan creation, so this
    function receives a fully resolved plan with no document introspection.

    Processing behavior:
        - It iterates through the instructions in the plan.
        - For each section, it executes one of four branches based on the
          configured (include, action, narrative) combination:

            - include=False                              -> remove (stub)
            - include=True, action="retain", narrative   -> retain branch
            - include=True, action="refine"              -> refine via process_section

        - The retain branch honors the narrative setting: when the
          jurisdiction has configured narrative removal on a retained
          section, the narrative is replaced with the removal notice
          while the entries are left untouched.
        - The refine branch delegates to process_section, which dispatches
          to the section-aware or generic matching engine based on the
          section specification. The engine returns a SectionRunResult
          which is then interpreted into a SectionOutcome via
          _interpret_run_result.
        - After each branch, the section's provenance record is finalized
          with the runtime outcome via dataclasses.replace, and an
          unanchored provenance footnote is appended to the section's
          <text> element. The footnote ID is built from the section's
          LOINC code and the plan's augmentation_timestamp, tying it to
          the augmentation author's <time> value for forensic
          traceability.

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

    for section_code, section_rules in plan.section_instructions.items():
        section = get_section_by_code(
            structured_body=structured_body,
            loinc_code=section_code,
            namespaces=HL7_NS,
        )

        if section is None:
            continue

        provenance = plan.section_provenance.get(section_code)
        outcome: SectionOutcome

        if not section_rules.include:
            # BRANCH 1: wholesale removal
            create_minimal_section(section=section, removal_reason="configured")
            outcome = SectionOutcome.REMOVED_BY_CONFIG

        elif section_rules.action == "retain":
            # BRANCH 2: retain entries; honor the narrative setting.
            # the narrative=False case used to be a silent no-op (the old
            # `retain` branch was a literal `pass`); it now correctly
            # replaces the narrative with the removal notice while
            # leaving the entries untouched
            if not section_rules.narrative:
                replace_narrative_with_removal_notice(
                    section=section, namespaces=HL7_NS
                )
                outcome = SectionOutcome.RETAINED_NARRATIVE_REMOVED
            else:
                outcome = SectionOutcome.RETAINED

        else:
            # BRANCH 3: refine entries via the matching engines.
            # process_section returns a SectionRunResult describing what
            # actually happened, which _interpret_run_result maps to a
            # user-facing outcome (including the no-match policy override)
            section_specification = plan.specification.sections.get(section_code)
            run_result = process_section(
                section=section,
                codes_to_match=plan.codes_to_check,
                namespaces=HL7_NS,
                section_specification=section_specification,
                code_system_sets=plan.code_system_sets,
                include_narrative=section_rules.narrative,
            )
            outcome = _interpret_run_result(section_rules, run_result)

        if provenance is not None:
            # finalize the provenance record with the runtime outcome
            # before rendering the footnote. SectionProvenanceRecord is
            # frozen, so dataclasses.replace produces a new instance
            # rather than mutating in place
            finalized = dataclasses.replace(provenance, outcome=outcome)
            append_section_provenance_footnote(
                section=section,
                provenance=finalized,
                augmentation_timestamp=plan.augmentation_timestamp,
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
