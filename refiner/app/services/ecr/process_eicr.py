import uuid
from dataclasses import dataclass
from typing import Final, Literal, cast

from lxml import etree
from lxml.etree import _Element

from app.services.terminology import CodeSystemSets, Coding

from ...core.exceptions import (
    StructureValidationError,
    XMLParsingError,
)
from ..format import remove_element
from .model import EicrVersion, EntryMatchRule, NamespaceMap, SectionSpecification

# NOTE:
# CONSTANTS AND CONFIGURATION
# =============================================================================

# <text> constants for refined sections
REFINER_OUTPUT_TITLE: Final[str] = (
    "Output from CDC eCR Refiner application by request of jurisdiction."
)
REMOVE_SECTION_MESSAGE: Final[str] = (
    "Section details have been removed as requested by jurisdiction for this condition."
)
MINIMAL_SECTION_MESSAGE: Final[str] = (
    "No clinical information matches the configured code sets for this condition."
)
CLINICAL_DATA_TABLE_HEADERS: Final[list[str]] = [
    "Display Text",
    "Code",
    "Code System",
    "Is Trigger Code",
    "Matching Condition Code",
]

# extended namespace map that includes xsi — needed for Results match rules
# that filter on @xsi:type='CD'
_MATCH_NAMESPACES: Final[NamespaceMap] = {
    "hl7": "urn:hl7-org:v3",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}


# NOTE:
# INTERNAL RESULT TYPES FOR NEW PATH
# =============================================================================


@dataclass
class EntryMatch:
    """
    Result of matching a single entry against the match rules.

    Tracks the entry element, the specific code element that matched,
    the Coding from the configuration, and which rule produced the match
    (needed for prune_container_xpath).
    """

    entry: _Element
    matched_code_element: _Element
    matched_coding: Coding
    rule: EntryMatchRule


# NOTE:
# SECTION PROCESSING (Core refinement logic)
# =============================================================================


def get_section_by_code(
    structured_body: _Element,
    loinc_code: str,
    namespaces: NamespaceMap = {"hl7": "urn:hl7-org:v3"},
) -> _Element | None:
    """
    Get a section from structuredBody by its LOINC code.

    Args:
        structured_body: The HL7 structuredBody element to search within.
        loinc_code: The LOINC code of the section to retrieve.
        namespaces: The namespaces to use for element search. Defaults to hl7.

    Returns:
        _Element: The section element or None if not found

    Raises:
        XMLParsingError: If XPath evaluation fails
    """

    try:
        xpath_query = f'.//hl7:section[hl7:code[@code="{loinc_code}"]]'
        xpath_result = structured_body.xpath(xpath_query, namespaces=namespaces)

        if isinstance(xpath_result, list) and len(xpath_result) == 1:
            section = cast(list[_Element], xpath_result)
            return section[0]
    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message=f"Failed to evaluate XPath for section code {loinc_code}",
            details={"xpath_query": xpath_query, "error": str(e)},
        )
    return None


def get_section_loinc_codes(
    structured_body: _Element,
    namespaces: NamespaceMap = {"hl7": "urn:hl7-org:v3"},
) -> list[str]:
    """
    Parses an eICR's structuredBody to find all top-level section codes.

    This function is used to discover which sections are actually present in a given
    eICR document before applying any refinement logic. It borrows patterns for
    error handling and namespace management from other functions in this module.

    :param structured_body: The <structuredBody> XML element from an eICR.
    :param namespaces: The XML namespaces to use for the XPath query.
    :return: A list of LOINC codes for the sections found in the document.
    """

    if structured_body is None:
        return []

    # this xpath is designed to be specific and efficient:
    # 1. It starts from the current element (structured_body)
    # 2. It finds direct <section> children
    # 3. It then finds the direct <code> child of that section
    # 4. Finally, it extracts the 'code' attribute string
    # This avoids finding codes in nested sections or other parts of the document
    xpath_query = ".//hl7:section/hl7:code/@code"

    try:
        xpath_result = structured_body.xpath(xpath_query, namespaces=namespaces)

        # the result of a query ending in /@attribute is a list of strings.
        if isinstance(xpath_result, list):
            # we can directly return the list of strings.
            return cast(list[str], xpath_result)

        return []
    except etree.XPathError as e:
        raise XMLParsingError(
            message="Failed to evaluate XPath for discovering section LOINC codes.",
            details={"xpath_query": xpath_query, "error": str(e)},
        )


def process_section(
    section: _Element,
    codes_to_match: set[str],
    namespaces: NamespaceMap = {"hl7": "urn:hl7-org:v3"},
    section_specification: SectionSpecification | None = None,
    version: EicrVersion = "1.1",
    code_system_sets: CodeSystemSets | None = None,
) -> None:
    """
    Process a section by filtering its entries based on provided condition codes.

    Routes to one of two paths based on whether the section has entry_match_rules:

    SECTION-AWARE PATH:
        Used when section_specification.has_match_rules is True and code_system_sets
        is provided. This is the primary path for sections where the IG defines
        SHALL or SHOULD constraints on entry code elements and code systems (e.g.,
        Problems, Results, Encounters, Medications, Immunizations, Plan of Treatment).
        Evaluates IG-driven XPaths per entry, matches against the correct code system,
        supports structural precedence for heterogeneous entry types, component-level
        pruning within organizers, and displayName enrichment on matched and surviving
        elements. Does not need the UUID swap since it only searches within <entry>
        elements.

    GENERIC PATH:
        Used for sections without entry match rules. These are sections where either:
        (a) the content is narrative-only with no <entry> elements (History of Present
            Illness, Reason for Visit, Chief Complaint, Review of Systems),
        (b) the entry content is patient-level context rather than condition-specific
            coded findings (Social History, Vital Signs, Pregnancy), or
        (c) the entry structure has not yet been characterized with specific match
            rules (Procedures).
        Uses unscoped code matching against the flat codes_to_match set and entry-level
        pruning only. DisplayName enrichment runs post-prune when code_system_sets is
        available.

    Args:
        section: The XML section element to process.
        codes_to_match: Flat set of all condition codes for the generic path.
        namespaces: XML namespaces for XPath evaluation.
        section_specification: Static specification for this section (match rules,
            trigger code OIDs). None for sections not in the specification.
        version: eICR version being processed.
        code_system_sets: Structured per-system codes for section-aware matching
            and displayName enrichment on both paths.
    """

    # ROUTE: if we have match rules and structured codes, use the new path
    if (
        section_specification is not None
        and section_specification.has_match_rules
        and code_system_sets is not None
    ):
        _process_section_with_match_rules(
            section=section,
            code_system_sets=code_system_sets,
            section_specification=section_specification,
            namespaces=namespaces,
        )
        return

    # FALLBACK: existing generic path (unchanged)
    _process_section_generic(
        section=section,
        codes_to_match=codes_to_match,
        namespaces=namespaces,
        section_specification=section_specification,
        version=version,
        code_system_sets=code_system_sets,
    )


# NOTE:
# NEW PATH: SECTION-AWARE MATCHING
# =============================================================================


def _process_section_with_match_rules(
    section: _Element,
    code_system_sets: CodeSystemSets,
    section_specification: SectionSpecification,
    namespaces: NamespaceMap,
) -> None:
    """
    Process a section using IG-driven entry match rules.

    Todo:
    Update after narrative refinement plan addition

    This is the new section-aware path. It:
    1. Clears the narrative <text> (will be rebuilt)
    2. Iterates <entry> elements and evaluates match rules per entry
    3. Enriches displayName on matched code elements
    4. Prunes non-matching entries (or components within entries for organizers)
    5. Identifies trigger codes among matches
    6. Generates summary text

    No UUID swap needed — match rules only search within <entry> elements,
    so the section's own <code> is never at risk of matching.
    """

    # clear the narrative text — it will be rebuilt from matches
    text_element = section.find("./hl7:text", namespaces=namespaces)
    if text_element is not None:
        text_element.clear()

    try:
        # STEP 1:
        # find matching entries using the section's match rules
        matches = _find_matching_entries(
            section=section,
            code_system_sets=code_system_sets,
            match_rules=section_specification.entry_match_rules,
        )

        if not matches:
            create_minimal_section(section=section, removal_reason="no_match")
            return

        # STEP 2:
        # prune non-matching content
        _prune_section_by_matches(section, matches, namespaces)

        # STEP 3:
        # enrich displayName on **all** surviving code-baring elements
        _enrich_surviving_entries(section, code_system_sets, namespaces)

        # STEP 4:
        # trigger identification among matched elements
        trigger_analysis = _analyze_trigger_codes_in_context(
            [m.matched_code_element for m in matches],
            section_specification,
        )

        # STEP 5:
        # generate summary text
        trigger_code_elements = {
            element_id
            for element_id, is_trigger in trigger_analysis.items()
            if is_trigger
        }

        # clean up comments
        _remove_all_comments(section)

        _update_text_element(
            section,
            [m.matched_code_element for m in matches],
            trigger_code_elements,
        )

    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message="Invalid XPath expression in entry match rule",
            details={"section_details": section.attrib, "error": str(e)},
        )


def _find_matching_entries(
    section: _Element,
    code_system_sets: CodeSystemSets,
    match_rules: list[EntryMatchRule],
) -> list[EntryMatch]:
    """
    Iterate entries in a section and evaluate match rules against each.

    Returns ALL matches within each entry (not just the first), which is
    necessary for container-level pruning — the pruner needs to know every
    matched element to decide which containers to keep.

    Rule evaluation follows "structural precedence": if a rule's XPath finds
    elements in the entry (meaning the entry has the structure that rule targets),
    that rule "claims" the entry. Later rules are only tried if the current rule's
    XPath finds nothing (meaning the entry doesn't have that structure at all).

    This prevents generic fallback rules (like SNOMED on observation/value) from
    matching entries that were already evaluated by a more specific rule (like
    LOINC on observation/code) but didn't have matching codes.
    """

    namespaces = _MATCH_NAMESPACES
    matches: list[EntryMatch] = []

    entries = section.findall("hl7:entry", namespaces)

    for entry in entries:
        entry_matches = _try_match_entry(
            entry, code_system_sets, match_rules, namespaces
        )
        matches.extend(entry_matches)

    return matches


def _try_match_entry(
    entry: _Element,
    code_system_sets: CodeSystemSets,
    match_rules: list[EntryMatchRule],
    namespaces: NamespaceMap,
) -> list[EntryMatch]:
    """
    Try to match a single entry against the match rules.

    Returns all matches found within the entry (for container-level pruning).

    Rule precedence: if a rule's code_xpath finds elements in this entry
    (even if none match the code set), that rule "claims" the entry and
    subsequent rules are NOT evaluated. This prevents fallback rules from
    matching generic codes (like "Detected") on entries that were already
    examined by a more specific rule.

    A rule only "claims" an entry if its XPath returns at least one element
    with a @code attribute. If the XPath returns nothing, or only elements
    without @code, the next rule is tried.
    """

    entry_matches: list[EntryMatch] = []

    for rule in match_rules:
        # evaluate primary code xpath
        code_elements = cast(
            list[_Element],
            entry.xpath(rule.code_xpath, namespaces=namespaces),
        )

        # check if this rule's xpath found code-bearing elements in this entry
        # if so, this rule "claims" the entry regardless of whether codes match
        candidates_found = any(el.get("code") for el in code_elements)

        for code_el in code_elements:
            code_val = code_el.get("code")
            if not code_val:
                continue

            coding = code_system_sets.find_match(code_val, rule.code_system_oid)
            if coding is not None:
                _enrich_display_name(code_el, coding)
                entry_matches.append(
                    EntryMatch(
                        entry=entry,
                        matched_code_element=code_el,
                        matched_coding=coding,
                        rule=rule,
                    )
                )

        # try translation xpath if primary found no matches (but might still claim)
        if not entry_matches and rule.translation_xpath:
            translation_elements = cast(
                list[_Element],
                entry.xpath(rule.translation_xpath, namespaces=namespaces),
            )

            if not candidates_found:
                candidates_found = any(el.get("code") for el in translation_elements)

            for trans_el in translation_elements:
                trans_code = trans_el.get("code")
                if not trans_code:
                    continue

                coding = code_system_sets.find_match(
                    trans_code, rule.translation_code_system_oid
                )
                if coding is not None:
                    _enrich_display_name(trans_el, coding)
                    entry_matches.append(
                        EntryMatch(
                            entry=entry,
                            matched_code_element=trans_el,
                            matched_coding=coding,
                            rule=rule,
                        )
                    )

        # STRUCTURAL PRECEDENCE: if this rule found code-bearing elements
        # in this entry, it "claims" the entry — don't try subsequent rules,
        # regardless of whether any codes actually matched.
        # This prevents the SNOMED-on-value fallback from matching generic
        # qualifiers like "Detected" on entries that were already evaluated
        # by the LOINC-on-code rule.
        if candidates_found:
            break

    return entry_matches


def _enrich_display_name(code_element: _Element, coding: Coding) -> None:
    """
    Enrich a code element's displayName attribute if it's missing or empty.

    This is the displayName enrichment from the RFC — it happens at match time
    because we have both the XML element and the Coding with the display name
    from the configuration.

    Args:
        code_element: The XML element with a @code attribute.
        coding: The matched Coding from the configuration.
    """

    if not coding.display:
        return

    existing = code_element.get("displayName")
    if not existing or not existing.strip():
        code_element.set("displayName", coding.display)


def _enrich_surviving_entries(
    section: _Element,
    code_system_sets: CodeSystemSets,
    namespaces: NamespaceMap,
) -> None:
    """
    Enrich displayName on all code-bearing elements within surviving entries.

    This is a post-prune enrichment pass that fills in missing displayName
    attributes on any element with a @code that exists in the condition
    grouper or custom code sets. It covers elements that the match rules
    didn't directly target (e.g., organizer-level codes, result values
    claimed by structural precedence) but that PHAs still need labeled
    for readability.

    Only adds displayName — never overwrites existing values.

    Runs after pruning so only surviving content is touched, and before
    text generation so enriched displayNames feed into the narrative summary.

    Args:
        section: The section element (already pruned).
        code_system_sets: Structured per-system lookup from the configuration.
        namespaces: XML namespaces for element search.
    """

    CODE_BEARING_TAGS: set[str] = {
        "{urn:hl7-org:v3}code",
        "{urn:hl7-org:v3}value",
        "{urn:hl7-org:v3}translation",
    }

    for entry in section.findall("hl7:entry", namespaces):
        for element in entry.iter():
            if element.tag not in CODE_BEARING_TAGS:
                continue

            code_val = element.get("code")
            if not code_val:
                continue

            # skip if displayName is already present
            existing = element.get("displayName")
            if existing and existing.strip():
                continue

            # use the element's own codeSystem to scope the lookup
            code_system_oid = element.get("codeSystem")

            coding = code_system_sets.find_match(code_val, code_system_oid)
            if coding is not None:
                _enrich_display_name(element, coding)


def _prune_section_by_matches(
    section: _Element,
    matches: list[EntryMatch],
    namespaces: NamespaceMap,
) -> None:
    """
    Remove non-matching content from a section based on the match results.

    Two pruning strategies:
    1. Entry-level (default): Remove entire <entry> elements that didn't match.
    2. Component-level (when prune_container_xpath is set): Within matched entries,
       remove individual containers (e.g., organizer/component) that don't contain
       matched observations. Used for Results section.

    Args:
        section: The section element being processed.
        matches: List of EntryMatch objects from the matching step.
        namespaces: XML namespaces for XPath evaluation.
    """

    # collect all entries in the section
    all_entries = section.findall("hl7:entry", namespaces)
    matched_entries = {id(m.entry) for m in matches}

    # check if any match uses component-level pruning
    prune_rules = {
        m.rule.prune_container_xpath for m in matches if m.rule.prune_container_xpath
    }

    if prune_rules:
        # COMPONENT-LEVEL PRUNING
        # for entries that matched, prune non-matching containers within them
        # for entries that didn't match at all, remove the whole entry
        _prune_at_container_level(section, matches, all_entries, namespaces)
    else:
        # ENTRY-LEVEL PRUNING
        # simple: remove entries not in the matched set
        for entry in all_entries:
            if id(entry) not in matched_entries:
                remove_element(entry)


def _prune_at_container_level(
    section: _Element,
    matches: list[EntryMatch],
    all_entries: list[_Element],
    namespaces: NamespaceMap,
) -> None:
    """
    Prune within containers (panels/organizers) if coded elements do not match.

    Prune non-matching containers within matched entries (e.g., organizer/component in
    the Results section), and remove entirely unmatched entries. For each matched
    entry that has a prune_container_xpath rule:

    1. Find all containers at the specified XPath within the entry
    2. For each container, check if it has a descendant that was a matched code element
    3. Remove containers that don't contain any matched elements
    4. If all containers in an entry are removed, remove the entry too

    For matched entries without prune_container_xpath, the entry is kept as-is.
    For unmatched entries, the entry is removed entirely.
    """

    matched_entry_ids = {id(m.entry) for m in matches}

    # build a set of all matched code element ids for containment checking
    matched_code_element_ids = {id(m.matched_code_element) for m in matches}

    # group matches by entry for container-level logic
    entry_to_matches: dict[int, list[EntryMatch]] = {}
    for m in matches:
        entry_id = id(m.entry)
        if entry_id not in entry_to_matches:
            entry_to_matches[entry_id] = []
        entry_to_matches[entry_id].append(m)

    for entry in all_entries:
        entry_id = id(entry)

        if entry_id not in matched_entry_ids:
            # entry had no matches at all — remove it
            remove_element(entry)
            continue

        # check if this entry's matches have a prune_container_xpath
        entry_matches = entry_to_matches.get(entry_id, [])
        prune_xpath = None
        for em in entry_matches:
            if em.rule.prune_container_xpath:
                prune_xpath = em.rule.prune_container_xpath
                break

        if not prune_xpath:
            # no container pruning for this entry — keep it whole
            continue

        # find all containers at the prune xpath
        containers = cast(
            list[_Element],
            entry.xpath(prune_xpath, namespaces=namespaces),
        )

        for container in containers:
            # check if any descendant of this container was a matched code element
            has_match = _container_has_matched_descendant(
                container, matched_code_element_ids
            )
            if not has_match:
                remove_element(container)

        # if we removed all containers, remove the entry too
        remaining_containers = entry.xpath(prune_xpath, namespaces=namespaces)
        if isinstance(remaining_containers, list) and len(remaining_containers) == 0:
            remove_element(entry)


def _container_has_matched_descendant(
    container: _Element,
    matched_element_ids: set[int],
) -> bool:
    """
    Return True/False for whether or not a container has a match in its entry path.

    Check if a container element has any descendant (including itself) that
    is one of the matched code elements.
    """

    if id(container) in matched_element_ids:
        return True

    for descendant in container.iter():
        if id(descendant) in matched_element_ids:
            return True

    return False


# NOTE:
# GENERIC MATCHING (Fallback for sections without strict entry processing rules)
# =============================================================================


def _process_section_generic(
    section: _Element,
    codes_to_match: set[str],
    namespaces: NamespaceMap,
    section_specification: SectionSpecification | None,
    version: EicrVersion,
    code_system_sets: CodeSystemSets | None = None,
) -> None:
    """
    Process a section using the generic matching logic.

    Used for sections without IG-verified entry match rules. These are
    sections where the entry structure is either narrative-only, contains
    non-condition-specific content (vital signs, social history), or has
    not yet been characterized with specific match rules.

    Matching is unscoped — any code/value/translation element with a @code
    in codes_to_match is considered a hit. Pruning is entry-level only.
    DisplayName enrichment runs post-prune when code_system_sets is available.
    """

    # neutralize section's direct <code> and <text> children to exclude from search
    original_code_value = None

    if (
        section_code_element := section.find("./hl7:code", namespaces=namespaces)
    ) is not None:
        if (
            original_code_value := section_code_element.get("code")
        ) and "code" in section_code_element.attrib:
            section_code_element.set("code", f"TEMP_SWAP_{uuid.uuid4()}")

    if (text_element := section.find("./hl7:text", namespaces=namespaces)) is not None:
        text_element.clear()

    try:
        if not codes_to_match:
            create_minimal_section(section=section, removal_reason="no_match")
            return

        try:
            # STEP 1:
            # CONTEXT FILTERING
            contextual_matches = _find_condition_relevant_elements(
                section, codes_to_match, namespaces
            )

            if not contextual_matches:
                create_minimal_section(section=section, removal_reason="no_match")
                return

            # STEP 2:
            # TRIGGER IDENTIFICATION WITHIN CONTEXT
            trigger_analysis = _analyze_trigger_codes_in_context(
                contextual_matches, section_specification
            )

            # STEP 3:
            # PROCESS ENTRIES AND GENERATE OUTPUT
            _preserve_relevant_entries_and_generate_summary(
                section, contextual_matches, trigger_analysis, namespaces
            )

            # STEP 4:
            # ENRICH displayName on surviving entries
            if code_system_sets is not None:
                _enrich_surviving_entries(section, code_system_sets, namespaces)

        except etree.XPathEvalError as e:
            raise XMLParsingError(
                message="Invalid XPath expression",
                details={"section_details": section.attrib, "error": str(e)},
            )
    finally:
        if section_code_element is not None and original_code_value:
            section_code_element.set("code", original_code_value)


def _find_condition_relevant_elements(
    section: _Element, codes_to_match: set[str], namespaces: NamespaceMap
) -> list[_Element]:
    """
    STEP 1: Find clinical elements matching SNOMED condition codes.

    This is the context filter - only elements relevant to our reportable
    condition should proceed to the next step.

    Args:
        section: The XML section element to search within
        codes_to_match: The list of codes to match for the relevant elements
        namespaces: XML namespaces for XPath evaluation

    Returns:
        list[_Element]: Deduplicated list of contextually relevant clinical elements

    Raises:
        XMLParsingError: If XPath evaluation fails
    """

    # handle empty code matches early
    if not codes_to_match:
        return []

    try:
        codes_to_check = frozenset(codes_to_match)

        # Pattern 1:
        # parent code, translation, and value elements that might have
        # direct codes
        candidates_parents = cast(
            list[_Element],
            section.xpath(
                ".//hl7:*[hl7:code/@code or hl7:translation/@code or hl7:value/@code]",
                namespaces=namespaces,
            ),
        )

        # Pattern 2:
        # elements with code, translation, or value children that might
        # have matching codes
        candidates_children = cast(
            list[_Element],
            section.xpath(
                ".//*[self::hl7:code or self::hl7:translation or self::hl7:value][@code]",
                namespaces=namespaces,
            ),
        )

        matched_parents = [
            el
            for el in candidates_parents
            if any(child.get("code") in codes_to_check for child in el)
        ]

        matched_children = [
            el for el in candidates_children if el.get("code") in codes_to_check
        ]

        xpath_result = matched_children + matched_parents
        if not isinstance(xpath_result, list):
            return []

        clinical_elements = cast(list[_Element], xpath_result)

        # deduplicate hierarchical matches within our SNOMED-filtered set
        return _deduplicate_clinical_elements(clinical_elements)

    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message="Failed to generate candidate elements for code matching",
            details={"section_details": section.attrib, "error": str(e)},
        )


def _analyze_trigger_codes_in_context(
    contextual_matches: list[_Element],
    section_specification: SectionSpecification | None,
) -> dict[int, bool]:
    """
    STEP 2: Identify trigger codes among already-contextually-relevant elements.

    This function performs trigger code identification ONLY within the context
    of elements that have already been deemed relevant to our reportable condition.
    This ensures we don't preserve random trigger codes unrelated to the condition.

    Args:
        contextual_matches: List of clinical elements already filtered for context
        section_specification: Static specification for this section. Contains the
            set of valid trigger code OIDs used for fast lookup.

    Returns:
        dict[int, bool]: Mapping of element_id -> is_trigger_code for each element
    """

    # STEP 1:
    # extract the set of OIDs (or empty set if spec is None)
    trigger_oids = (
        section_specification.trigger_oids if section_specification else set()
    )

    # STEP 2:
    # return early if no trigger code OIDs are defined
    if not section_specification or not section_specification.trigger_codes:
        return {id(elem): False for elem in contextual_matches}

    trigger_analysis = {}
    template_cache: dict[int, bool] = {}

    for clinical_element in contextual_matches:
        element_id = id(clinical_element)

        if (result := template_cache.get(element_id)) is None:
            result = template_cache[element_id] = _has_trigger_template_ancestor(
                clinical_element, trigger_oids
            )

        trigger_analysis[element_id] = result

    return trigger_analysis


def _preserve_relevant_entries_and_generate_summary(
    section: _Element,
    contextual_matches: list[_Element],
    trigger_analysis: dict[int, bool],
    namespaces: NamespaceMap,
) -> None:
    """
    STEP 3: Process entry-level operations and generate final section content.

    This function handles the final processing steps:
    1. Find and preserve entries containing our contextually relevant elements
    2. Remove unwanted entries
    3. Generate summary text showing both regular matches and trigger codes

    Args:
        section: The XML section element being processed
        contextual_matches: List of contextually relevant clinical elements
        trigger_analysis: Mapping of element_id -> is_trigger_code
        namespaces: XML namespaces for XPath evaluation
    """

    # find parent entries for all matching clinical elements
    entry_paths = []
    for clinical_element in contextual_matches:
        entry_path = _find_path_to_entry(clinical_element)
        entry_paths.append(entry_path)

    # deduplicate entry paths to prevent overlapping XML branches
    deduplicated_entry_paths = _deduplicate_entry_paths(entry_paths)

    # remove entries that don't contain our contextually relevant clinical elements
    _prune_unwanted_siblings(deduplicated_entry_paths, section)

    # clean up all comments from processed sections
    _remove_all_comments(section)

    # generate summary text showing both regular matches and trigger codes
    trigger_code_elements = {
        element_id for element_id, is_trigger in trigger_analysis.items() if is_trigger
    }

    _update_text_element(section, contextual_matches, trigger_code_elements)


# NOTE:
# XML TREE MANIPULATION (Entry and element management)
# =============================================================================


def _find_path_to_entry(element: _Element) -> _Element:
    """
    Find the nearest entry ancestor of an element.

    Args:
        element: The element to find the entry for

    Returns:
        The entry element

    Raises:
        StructureValidationError: If no entry ancestor found
    """

    current_element: _Element | None = element

    # walk up the tree until we find an entry element
    while (
        current_element is not None and current_element.tag != "{urn:hl7-org:v3}entry"
    ):
        current_element = current_element.getparent()

    if current_element is None:
        raise StructureValidationError(
            message="Parent <entry> element not found.",
            details={"element_tag": element.tag},
        )

    return current_element


def _prune_unwanted_siblings(
    entry_paths: list[_Element],
    section: _Element,
) -> None:
    """
    Remove entries that don't contain relevant clinical elements.

    Args:
        entry_paths: List of entry elements to preserve
        section: The section being processed
    """

    namespaces: NamespaceMap = {"hl7": "urn:hl7-org:v3"}

    xpath_result = section.xpath(".//hl7:entry", namespaces=namespaces)
    if not isinstance(xpath_result, list):
        return

    all_entries = cast(list[_Element], xpath_result)

    for entry in all_entries:
        if entry not in entry_paths:
            remove_element(entry)


def _deduplicate_entry_paths(entry_paths: list[_Element]) -> list[_Element]:
    """
    Remove duplicate and nested entry paths to prevent overlapping XML branches.

    When XPath matches find nested elements (e.g., both an <act> and an <observation>
    within that <act>), we could end up with duplicate entries or parent/child entries
    both being preserved, leading to duplicate content in the refined eICR.

    Args:
        entry_paths: List of entry elements that may contain duplicates or nested relationships

    Returns:
        list[_Element]: Deduplicated list with no overlapping branches
    """

    if not entry_paths:
        return entry_paths

    # remove exact duplicates first (same entry element referenced multiple times)
    unique_entries = []
    seen_entries = set()

    for entry in entry_paths:
        entry_id = id(entry)
        if entry_id not in seen_entries:
            unique_entries.append(entry)
            seen_entries.add(entry_id)

    # remove nested relationships (parent/child entries)
    final_entries = []

    for current_entry in unique_entries:
        is_nested_within_another = False

        for potential_parent_entry in unique_entries:
            if current_entry is not potential_parent_entry and _is_ancestor(
                potential_parent_entry, current_entry
            ):
                is_nested_within_another = True
                break

        if not is_nested_within_another:
            final_entries.append(current_entry)

    return final_entries


def _deduplicate_clinical_elements(clinical_elements: list[_Element]) -> list[_Element]:
    """
    Remove nested clinical elements that represent the same logical finding.

    When XPath matches both a parent element (like <organizer>) and its child
    elements (like <observation>), we want to keep only the highest-level
    parent that contains the complete clinical context.
    """

    if not clinical_elements:
        return clinical_elements

    code_groups: dict[str, list[_Element]] = {}

    for elem in clinical_elements:
        data = _extract_clinical_data(elem)
        code = data.get("code")

        if isinstance(code, str):
            if code not in code_groups:
                code_groups[code] = []
            code_groups[code].append(elem)

    deduplicated = []

    for code, elements in code_groups.items():
        if len(elements) == 1:
            deduplicated.append(elements[0])
        else:
            ancestors = []

            for elem in elements:
                is_descendant = False
                for other_elem in elements:
                    if elem != other_elem and _is_ancestor(other_elem, elem):
                        is_descendant = True
                        break

                if not is_descendant:
                    ancestors.append(elem)

            deduplicated.extend(ancestors)

    return deduplicated


def _is_ancestor(potential_ancestor: _Element, potential_descendant: _Element) -> bool:
    """
    Check if one element is an ancestor of another in the XML tree.

    Args:
        potential_ancestor: Element that might be the ancestor
        potential_descendant: Element that might be the descendant

    Returns:
        bool: True if potential_ancestor contains potential_descendant
    """

    current = potential_descendant.getparent()

    while current is not None:
        if current is potential_ancestor:
            return True
        current = current.getparent()

    return False


# NOTE:
# CLINICAL DATA EXTRACTION AND ANALYSIS
# =============================================================================


def _extract_clinical_data(
    clinical_element: _Element,
) -> dict[str, str | bool | None]:
    """
    Extract basic data from a clinical element.

    Extracts display text, code, and code system from clinical elements.

    * Note: Trigger code status is handled separately through the trigger_analysis
      dictionary in the section processing pipeline.

    Args:
        clinical_element: The clinical element to extract data from.

    Returns:
        dict[str, str | None]: Dictionary containing the extracted clinical data
                               with display_text, code, and code_system.
    """

    code_element: _Element | None = (
        clinical_element
        if clinical_element.tag.endswith("code")
        else clinical_element.find(".//hl7:code", namespaces={"hl7": "urn:hl7-org:v3"})
    )

    # find the code element — check for code, value, or translation tags
    # that carry @code directly, then fall back to searching for a child code element
    tag_local = (
        clinical_element.tag.split("}")[-1]
        if "}" in clinical_element.tag
        else clinical_element.tag
    )

    if tag_local in ("code", "value", "translation") and clinical_element.get("code"):
        code_element = clinical_element
    else:
        code_element = clinical_element.find(
            ".//hl7:code", namespaces={"hl7": "urn:hl7-org:v3"}
        )

    display_text: str | None = None
    code: str | None = None
    code_system: str | None = None

    if code_element is not None:
        display_text_raw = code_element.get("displayName")
        if isinstance(display_text_raw, str):
            display_text = display_text_raw

        code_raw = code_element.get("code")
        if isinstance(code_raw, str):
            code = code_raw

        code_system_raw = code_element.get("codeSystemName")
        if isinstance(code_system_raw, str):
            code_system = code_system_raw

    return {
        "display_text": display_text,
        "code": code,
        "code_system": code_system,
    }


def _has_trigger_template_ancestor(element: _Element, trigger_oids: set[str]) -> bool:
    """
    Check if element is within a trigger code template.

    This function is called during STEP 2 of the processing pipeline,
    after elements have already been filtered for contextual relevance.

    Args:
        element: The XML element to check
        trigger_oids: Set of template OIDs that indicate trigger codes.

    Returns:
        bool: True if element is within any of the trigger templates
    """

    if not trigger_oids:
        return False

    current: _Element | None = element
    namespaces: NamespaceMap = {"hl7": "urn:hl7-org:v3"}

    while current is not None:
        template_elements = current.xpath(".//hl7:templateId", namespaces=namespaces)

        if isinstance(template_elements, list):
            for template in template_elements:
                if not isinstance(template, _Element):
                    continue
                if (root := template.get("root")) and root in trigger_oids:
                    return True

                if (
                    root
                    and (extension := template.get("extension"))
                    and f"{root}:{extension}" in trigger_oids
                ):
                    return True

        current = current.getparent()

    return False


# NOTE:
# TEXT ELEMENT GENERATION (HTML table creation)
# =============================================================================


def create_minimal_section(
    section: _Element, removal_reason: Literal["no_match", "configured"] = "no_match"
) -> None:
    """
    Create a minimal section with updated text and nullFlavor.

    Updates the text element, removes all entry elements, and adds
    nullFlavor="NI" to the section element. The message displayed in the
    section varies based on why it was made minimal.

    Args:
        section: The section element to update.
        removal_reason: Designates why the section was made minimal:
          - "no_match": No matching clinical information found during refinement.
            Uses MINIMAL_SECTION_MESSAGE constant.
          - "configured": Section was configured to be removed via section processing.
            Uses REMOVE_SECTION_MESSAGE constant.

    Raises:
        XMLParsingError: If XPath evaluation fails
    """

    MESSAGE_MAP: Final[dict[str, str]] = {
        "no_match": MINIMAL_SECTION_MESSAGE,
        "configured": REMOVE_SECTION_MESSAGE,
    }

    _section_message = MESSAGE_MAP[removal_reason]

    namespaces: NamespaceMap = {"hl7": "urn:hl7-org:v3"}
    text_element = section.find(".//hl7:text", namespaces=namespaces)

    if text_element is None:
        text_element = etree.Element("{urn:hl7-org:v3}text")
        section.append(text_element)

    # update the <text> element with the specific message
    text_element.clear()
    title_element = etree.SubElement(text_element, "title")
    title_element.text = REFINER_OUTPUT_TITLE

    table_element = etree.SubElement(text_element, "table", border="1")
    thead_element = etree.SubElement(table_element, "thead")
    tr_element = etree.SubElement(thead_element, "tr")
    td_element = etree.SubElement(tr_element, "td")
    td_element.text = _section_message

    # remove all <entry> elements
    for entry in section.findall(".//hl7:entry", namespaces=namespaces):
        section.remove(entry)

    # clean up all comments from processed sections
    _remove_all_comments(section)

    # add nullFlavor="NI" to the <section> element
    section.attrib["nullFlavor"] = "NI"


def _create_or_update_text_element(
    clinical_elements: list[_Element], trigger_code_elements: set[int]
) -> _Element:
    """
    Create clean, professional text element with trigger code information.

    Args:
        clinical_elements: List of clinical elements to include in the text.
        trigger_code_elements: Set of clinical element IDs that are trigger codes.

    Returns:
        _Element: The created text element with clean formatting.
    """

    text_element = etree.Element("{urn:hl7-org:v3}text")

    title = etree.SubElement(text_element, "title")
    title.text = REFINER_OUTPUT_TITLE

    table_element = etree.SubElement(text_element, "table", border="1")

    thead_row = etree.SubElement(table_element, "thead")
    header_row = etree.SubElement(thead_row, "tr")
    headers = CLINICAL_DATA_TABLE_HEADERS

    for header in headers:
        th = etree.SubElement(header_row, "th")
        th.text = header

    trigger_elements = [
        elem for elem in clinical_elements if id(elem) in trigger_code_elements
    ]
    other_elements = [
        elem for elem in clinical_elements if id(elem) not in trigger_code_elements
    ]

    for clinical_element in trigger_elements:
        _add_clinical_data_row(table_element, clinical_element, is_trigger=True)

    for clinical_element in other_elements:
        _add_clinical_data_row(table_element, clinical_element, is_trigger=False)

    return text_element


def _add_clinical_data_row(
    table_element: _Element, clinical_element: _Element, is_trigger: bool
) -> None:
    """
    Add a single clinical data row to the table.

    Args:
        table_element: The table element to add the row to
        clinical_element: The clinical element
        is_trigger: Whether this is a trigger code
    """

    data = _extract_clinical_data(clinical_element)
    tbody = etree.SubElement(table_element, "tbody")
    row = etree.SubElement(tbody, "tr")

    td = etree.SubElement(row, "td")
    display_text_raw = data["display_text"]
    display_text = display_text_raw if isinstance(display_text_raw, str) else None

    if is_trigger and display_text:
        b = etree.SubElement(td, "b")
        b.text = display_text
    else:
        td.text = display_text or "Not specified"

    td = etree.SubElement(row, "td")
    code_raw = data["code"]
    code = code_raw if isinstance(code_raw, str) else None

    if is_trigger and code:
        b = etree.SubElement(td, "b")
        b.text = code
    else:
        td.text = code or "Not specified"

    td = etree.SubElement(row, "td")
    code_system_raw = data["code_system"]
    code_system = code_system_raw if isinstance(code_system_raw, str) else None
    td.text = code_system or "Not specified"

    td = etree.SubElement(row, "td")
    td.text = "YES" if is_trigger else "NO"

    td = etree.SubElement(row, "td")
    td.text = "YES"


def _update_text_element(
    section: _Element,
    clinical_elements: list[_Element],
    trigger_code_elements: set[int],
) -> None:
    """
    Update a section's text element with clinical data information.

    Args:
        section: The section element containing the text element to update.
        clinical_elements: List of clinical elements to include in the text.
        trigger_code_elements: Set of clinical element IDs that are trigger codes.
    """

    new_text_element = _create_or_update_text_element(
        clinical_elements, trigger_code_elements
    )

    existing_text_element = section.find(
        ".//hl7:text", namespaces={"hl7": "urn:hl7-org:v3"}
    )

    if existing_text_element is not None:
        section.replace(existing_text_element, new_text_element)
    else:
        section.insert(0, new_text_element)


# NOTE:
# XML CLEANUP UTILITIES
# =============================================================================


def _remove_all_comments(section: _Element) -> None:
    """
    Remove all XML comments from a processed section.

    After refining a section, comments may no longer be accurate or relevant.
    This ensures clean output without orphaned or misleading comments.

    Args:
        section: The section element to clean up
    """
    xpath_result = section.xpath(".//comment()")
    if isinstance(xpath_result, list):
        for comment in xpath_result:
            if isinstance(comment, etree._Element):
                remove_element(comment)
