from dataclasses import dataclass
from typing import Final, cast

from lxml import etree
from lxml.etree import _Element

from app.core.exceptions import XMLParsingError
from app.services.format import remove_element
from app.services.terminology import CodeSystemSets, Coding

from ..model import (
    HL7_XSI_NS,
    EntryMatchRule,
    NamespaceMap,
    SectionRunResult,
    SectionSpecification,
)
from .narrative import (
    create_minimal_section,
    remove_all_comments,
    replace_narrative_with_removal_notice,
)

# NOTE:
# INTERNAL CONSTANTS
# =============================================================================
# extended namespace map that includes xsi — needed for Results match
# rules that filter on @xsi:type='CD' to distinguish coded values from
# physical-quantity values

_MATCH_NAMESPACES: Final[NamespaceMap] = HL7_XSI_NS


# NOTE:
# INTERNAL RESULT TYPE
# =============================================================================


@dataclass
class EntryMatch:
    """
    Result of matching a single entry against the match rules.

    Tracks the entry element, the specific code element that matched,
    the Coding from the configuration, and which rule produced the
    match (needed to decide between entry-level and container-level
    pruning via ``rule.prune_container_xpath``).
    """

    entry: _Element
    matched_code_element: _Element
    matched_coding: Coding
    rule: EntryMatchRule


# NOTE:
# PUBLIC ENTRY POINT
# =============================================================================


def process(
    section: _Element,
    code_system_sets: CodeSystemSets,
    section_specification: SectionSpecification,
    namespaces: NamespaceMap,
    include_narrative: bool = True,
) -> SectionRunResult:
    """
    Process a section using IG-driven entry match rules.

    This is the section-aware path. It:

    1. Iterates <entry> elements and evaluates match rules per entry
    2. Enriches displayName on matched code elements
    3. Prunes non-matching entries (or containers within entries)
    4. Enriches displayName on all surviving code-bearing elements
    5. Cleans up comments
    6. Handles narrative <text> based on ``include_narrative``:

       - True: the original <text> is left untouched
       - False: <text> is replaced with a removal notice

    No UUID swap needed — match rules only search within <entry>
    elements, so the section's own <code> is never at risk of matching.

    If no entries match, the section is reduced to a minimal stub
    via `create_minimal_section` (the no-match policy override) and
    the function returns a `SectionRunResult` with
    `matches_found=False`. The orchestrator translates this into
    `SectionOutcome.REFINED_NO_MATCHES_STUBBED` regardless of the
    narrative configuration — see `refine._interpret_run_result`.

    Returns:
        SectionRunResult reporting whether matches were found and
        what the engine did with the narrative. The
        `narrative_disposition` field is meaningful only when
        `matches_found=True`; when no matches are found, the engine
        stubs the entire section and the orchestrator short-circuits
        before reading the narrative disposition.
    """

    try:
        # STEP 1: find matching entries using the section's match rules
        matches = _find_matching_entries(
            section=section,
            code_system_sets=code_system_sets,
            match_rules=section_specification.entry_match_rules,
        )

        if not matches:
            # refiner policy: when no entries match, stub the section.
            # this overrides the configured narrative setting — there's
            # no useful narrative to keep when there's no clinical
            # content left to describe.
            # named as REFINED_NO_MATCHES_STUBBED in
            # refine._interpret_run_result.
            create_minimal_section(section=section, removal_reason="no_match")
            return SectionRunResult(
                matches_found=False,
                # placeholder — the orchestrator short-circuits on
                # matches_found=False and never reads this field.
                narrative_disposition="retained",
            )

        # STEP 2: prune non-matching content (entry or container level)
        _prune_section_by_matches(section, matches, namespaces)

        # STEP 3: enrich displayName on all surviving code-bearing elements
        enrich_surviving_entries(section, code_system_sets, namespaces)

        # STEP 4: clean up any leftover comments
        remove_all_comments(section)

        # STEP 5: handle narrative <text>
        if not include_narrative:
            replace_narrative_with_removal_notice(section, namespaces)
            return SectionRunResult(
                matches_found=True,
                narrative_disposition="removed",
            )

        return SectionRunResult(
            matches_found=True,
            narrative_disposition="retained",
        )

    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message="Invalid XPath expression in entry match rule",
            details={"section_details": dict(section.attrib), "error": str(e)},
        )


# NOTE:
# MATCH EVALUATION
# =============================================================================


def _find_matching_entries(
    section: _Element,
    code_system_sets: CodeSystemSets,
    match_rules: list[EntryMatchRule],
) -> list[EntryMatch]:
    """
    Iterate entries in a section and evaluate match rules against each.

    Returns ALL matches within each entry (not just the first), which
    is necessary for container-level pruning — the pruner needs to know
    every matched element to decide which containers to keep.

    Rule evaluation follows "structural precedence": if a rule's XPath
    finds code-bearing elements in the entry (meaning the entry has the
    structure that rule targets), that rule "claims" the entry. Later
    rules are only tried if the current rule's XPath finds nothing
    (meaning the entry doesn't have that structure at all).

    This prevents generic fallback rules (like SNOMED on observation/value)
    from matching entries that were already evaluated by a more specific
    rule (like LOINC on observation/code) but didn't have matching codes.
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

    Returns all matches found within the entry (for container-level
    pruning).

    Rule precedence: if a rule's code_xpath finds code-bearing elements
    in this entry (even if none match the code set), that rule "claims"
    the entry and subsequent rules are NOT evaluated. This prevents
    fallback rules from matching generic codes (like "Detected") on
    entries that were already examined by a more specific rule.

    A rule only "claims" an entry if its XPath returns at least one
    element with a @code attribute. If the XPath returns nothing, or
    only elements without @code, the next rule is tried.
    """

    entry_matches: list[EntryMatch] = []

    for rule in match_rules:
        # evaluate primary code xpath
        code_elements = cast(
            list[_Element],
            entry.xpath(rule.code_xpath, namespaces=namespaces),
        )

        # does this rule's xpath find code-bearing elements in this entry?
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
        # regardless of whether any codes actually matched. This prevents the
        # SNOMED-on-value fallback from matching generic qualifiers like
        # "Detected" on entries that were already evaluated by the
        # LOINC-on-code rule.
        if candidates_found:
            break

    return entry_matches


# NOTE:
# DISPLAYNAME ENRICHMENT
# =============================================================================


def _enrich_display_name(code_element: _Element, coding: Coding) -> None:
    """
    Set `displayName` on a code-bearing element from a Coding.

    Only sets the attribute if it is absent or empty; never overwrites
    an existing non-empty value. This matters because source documents
    may legitimately carry their own displayNames that differ from the
    configuration's, and we want to preserve what the source said
    wherever it said something.
    """

    existing = code_element.get("displayName")
    if existing and existing.strip():
        return

    if coding.display:
        code_element.set("displayName", coding.display)


def enrich_surviving_entries(
    section: _Element,
    code_system_sets: CodeSystemSets,
    namespaces: NamespaceMap,
) -> None:
    """
    Enrich `displayName` on all surviving code-bearing elements.

    Walks every <entry> in the section after pruning and sets
    `displayName` on any <code>, <value>, or <translation> element
    that has a `@code` attribute but no `@displayName`. The
    enrichment lookup uses the element's own `@codeSystem` attribute
    to scope the search in `code_system_sets`.

    This is how the refiner surfaces human-readable labels on code
    elements that the structural match rules didn't directly target
    (e.g., organizer-level codes, result values claimed by structural
    precedence) but that PHAs still need labeled for readability.

    Called from both matching paths — this module's `process` and
    `generic_matching.process` — after pruning and before narrative
    writing. Promoted to public because `generic_matching` imports
    it as a cross-module helper.

    Args:
        section: The section element (already pruned).
        code_system_sets: Structured per-system lookup from the
            configuration.
        namespaces: XML namespaces for element search.
    """

    code_bearing_tags: set[str] = {
        "{urn:hl7-org:v3}code",
        "{urn:hl7-org:v3}value",
        "{urn:hl7-org:v3}translation",
    }

    for entry in section.findall("hl7:entry", namespaces):
        for element in entry.iter():
            if element.tag not in code_bearing_tags:
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


# NOTE:
# PRUNING
# =============================================================================


def _prune_section_by_matches(
    section: _Element,
    matches: list[EntryMatch],
    namespaces: NamespaceMap,
) -> None:
    """
    Remove non-matching content from a section based on match results.

    Two pruning strategies:

    1. Entry-level (default): Remove entire <entry> elements that
       didn't match.
    2. Component-level (when ``prune_container_xpath`` is set): Within
       matched entries, remove individual containers (e.g.,
       organizer/component) that don't contain matched observations.
       Used for the Results section.

    Args:
        section: The section element being processed.
        matches: List of EntryMatch objects from the matching step.
        namespaces: XML namespaces for XPath evaluation.
    """

    all_entries = section.findall("hl7:entry", namespaces)
    matched_entries = {id(m.entry) for m in matches}

    # check if any match uses container-level pruning
    prune_rules = {
        m.rule.prune_container_xpath for m in matches if m.rule.prune_container_xpath
    }

    if prune_rules:
        # COMPONENT-LEVEL PRUNING:
        # for entries that matched, prune non-matching containers within them
        # for entries that didn't match at all, remove the whole entry
        _prune_at_container_level(matches, all_entries, namespaces)
    else:
        # ENTRY-LEVEL PRUNING:
        # simple — remove entries not in the matched set
        for entry in all_entries:
            if id(entry) not in matched_entries:
                remove_element(entry)


def _prune_at_container_level(
    matches: list[EntryMatch],
    all_entries: list[_Element],
    namespaces: NamespaceMap,
) -> None:
    """
    Prune within containers (panels/organizers) when coded elements don't match.

    Prune non-matching containers within matched entries (e.g.,
    organizer/component in the Results section), and remove entirely
    unmatched entries. For each matched entry that has a
    `prune_container_xpath` rule:

    1. Find all containers at the specified XPath within the entry.
    2. For each container, check if it has a descendant that was a
       matched code element.
    3. Remove containers that don't contain any matched elements.
    4. If all containers in an entry are removed, remove the entry too.

    For matched entries without ``prune_container_xpath``, the entry
    is kept as-is. For unmatched entries, the entry is removed entirely.
    """

    matched_entry_ids = {id(m.entry) for m in matches}
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
        prune_xpath: str | None = None
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
    Check if a container has a matched descendant (including itself).

    Returns True if the container element, or any of its descendants,
    is one of the matched code elements identified during matching.
    Used by container-level pruning to decide which containers to keep.
    """

    if id(container) in matched_element_ids:
        return True

    for descendant in container.iter():
        if id(descendant) in matched_element_ids:
            return True

    return False
