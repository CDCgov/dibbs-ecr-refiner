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
from .utils import (
    SDTC_NAMESPACE,
    build_entry_match_comment_text,
    enrich_surviving_entries,
    insert_comment_before,
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
    pruning via `rule.prune_container_xpath`, and to build the
    per-entry match provenance comment).
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

    1. Strips source document comments before matching so they cannot
       interfere with candidate gathering
    2. Finds matching entries using the section's rule list
    3. Prunes non-matching entries (entry-level, container-level, or
       whole-entry preservation depending on rule configuration)
    4. Enriches displayName on all surviving code-bearing elements
    5. Injects per-entry match provenance comments above surviving
       entries — added after source comment cleanup so they survive
    6. Handles narrative <text> based on `include_narrative`

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
        # STEP 1: strip source document comments before matching.
        # this prevents source comments from interfering with candidate
        # gathering and ensures our provenance comments (injected in
        # STEP 5) are the only comments in the output.
        remove_all_comments(section)

        # STEP 2: find matching entries using the section's match rules
        matches = _find_matching_entries(
            section=section,
            code_system_sets=code_system_sets,
            match_rules=section_specification.entry_match_rules,
        )

        if not matches:
            create_minimal_section(section=section, removal_reason="no_match")
            return SectionRunResult(
                matches_found=False,
                narrative_disposition="retained",
            )

        # STEP 3: prune non-matching content
        _prune_section_by_matches(section, matches, namespaces)

        # STEP 4: enrich displayName on all surviving code-bearing elements
        enrich_surviving_entries(section, code_system_sets, namespaces)

        # STEP 5: inject match provenance comments above surviving entries
        _inject_entry_match_comments(
            section=section,
            matches=matches,
            match_rules=section_specification.entry_match_rules,
            namespaces=namespaces,
        )

        # STEP 6: handle narrative <text>
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

    Rule evaluation follows structural precedence: if a rule's XPath
    finds code-bearing elements in the entry (candidates), that rule
    claims the entry regardless of whether any codes actually matched.
    Later rules are only tried if the current rule's XPath finds nothing
    at all (meaning the entry doesn't have that structure).
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

    Returns all matches found within the entry. A rule can contribute
    multiple matches if the entry has multiple code-bearing elements
    at the rule's xpath locations.

    Structural precedence: a rule claims the entry as soon as it finds
    any code-bearing elements (candidates_found=True), regardless of
    whether those candidates produced actual code set matches. Once a
    rule claims an entry, subsequent rules are not evaluated.

    The require_value_set_attr guard: when set on a rule, a candidate
    element is only eligible for code matching if it also carries
    sdtc:valueSet. Elements without it still count as candidates for
    structural precedence — the rule claims the entry, it just may not
    produce a match.
    """

    entry_matches: list[EntryMatch] = []

    for rule in match_rules:
        code_elements = cast(
            list[_Element],
            entry.xpath(rule.code_xpath, namespaces=namespaces),
        )

        candidates_found = any((el.get("code") or "").strip() for el in code_elements)

        for code_el in code_elements:
            code_val = (code_el.get("code") or "").strip()
            if not code_val:
                continue

            if rule.require_value_set_attr:
                sdtc_vs = code_el.get(f"{{{SDTC_NAMESPACE}}}valueSet")
                if not sdtc_vs:
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

        if not entry_matches and rule.translation_xpath:
            translation_elements = cast(
                list[_Element],
                entry.xpath(rule.translation_xpath, namespaces=namespaces),
            )

            if not candidates_found:
                candidates_found = any(
                    (el.get("code") or "").strip() for el in translation_elements
                )

            for trans_el in translation_elements:
                trans_code = (trans_el.get("code") or "").strip()
                if not trans_code:
                    continue

                if rule.require_value_set_attr:
                    sdtc_vs = trans_el.get(f"{{{SDTC_NAMESPACE}}}valueSet")
                    if not sdtc_vs:
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

        if candidates_found:
            break

    return entry_matches


# NOTE:
# MATCH PROVENANCE COMMENT INJECTION
# =============================================================================


def _inject_entry_match_comments(
    section: _Element,
    matches: list[EntryMatch],
    match_rules: list[EntryMatchRule],
    namespaces: NamespaceMap,
) -> None:
    """
    Insert XML comments above each surviving <entry> describing what drove its retention.

    Delegates comment text building to `utils.build_entry_match_comment_text`
    and insertion to `utils.insert_comment_before`.
    """

    entry_id_to_matches: dict[int, list[EntryMatch]] = {}
    for m in matches:
        eid = id(m.entry)
        if eid not in entry_id_to_matches:
            entry_id_to_matches[eid] = []
        entry_id_to_matches[eid].append(m)

    for entry in section.findall("hl7:entry", namespaces):
        entry_matches = entry_id_to_matches.get(id(entry))
        if not entry_matches:
            continue

        comment_text = build_entry_match_comment_text(entry_matches, match_rules)
        insert_comment_before(entry, comment_text)


# NOTE:
# DISPLAYNAME ENRICHMENT (matched code elements only)
# =============================================================================


def _enrich_display_name(code_element: _Element, coding: Coding) -> None:
    """
    Set `displayName` on a code-bearing element from a Coding.

    Only sets if absent or empty. Post-prune enrichment of all surviving
    elements is handled by `utils.enrich_surviving_entries`.
    """

    existing = code_element.get("displayName")
    if existing and existing.strip():
        return

    if coding.display:
        code_element.set("displayName", coding.display)


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

    Three pruning strategies selected per matched rule:

    1. preserve_whole_entry=True — matched entry kept completely intact.
       Used for medications, immunizations, procedures, and social history
       structured entries where entryRelationship chains carry clinically
       essential context (reaction observations, performer details, etc.).

    2. prune_container_xpath set — non-matching containers within matched
       entries are removed. Used for Results and Vital Signs where each
       panel sub-observation should be independently evaluated.

    3. Default — unmatched entries removed, matched entries kept whole.
    """

    all_entries = section.findall("hl7:entry", namespaces)
    matched_entries = {id(m.entry) for m in matches}

    has_container_pruning = any(
        m.rule.prune_container_xpath for m in matches if not m.rule.preserve_whole_entry
    )

    if has_container_pruning:
        _prune_at_container_level(matches, all_entries, namespaces)
    else:
        for entry in all_entries:
            if id(entry) not in matched_entries:
                remove_element(entry)


def _prune_at_container_level(
    matches: list[EntryMatch],
    all_entries: list[_Element],
    namespaces: NamespaceMap,
) -> None:
    """
    Prune at the container level within matched entries.

    Cases:
    1. No match — remove entry entirely.
    2. Matched with preserve_whole_entry=True — keep intact, skip pruning.
    3. Matched with prune_container_xpath — remove non-matching containers.
    4. Matched, no prune_container_xpath, preserve_whole_entry=False — keep whole.
    """

    matched_entry_ids = {id(m.entry) for m in matches}
    matched_code_element_ids = {id(m.matched_code_element) for m in matches}

    entry_to_matches: dict[int, list[EntryMatch]] = {}
    for m in matches:
        entry_id = id(m.entry)
        if entry_id not in entry_to_matches:
            entry_to_matches[entry_id] = []
        entry_to_matches[entry_id].append(m)

    for entry in all_entries:
        entry_id = id(entry)

        if entry_id not in matched_entry_ids:
            remove_element(entry)
            continue

        entry_matches = entry_to_matches.get(entry_id, [])

        # WHOLE-ENTRY PRESERVATION:
        # if any match on this entry used preserve_whole_entry=True,
        # skip all intra-entry pruning
        if any(em.rule.preserve_whole_entry for em in entry_matches):
            continue

        prune_xpath: str | None = None
        for em in entry_matches:
            if em.rule.prune_container_xpath:
                prune_xpath = em.rule.prune_container_xpath
                break

        if not prune_xpath:
            continue

        containers = cast(
            list[_Element],
            entry.xpath(prune_xpath, namespaces=namespaces),
        )

        for container in containers:
            if not _container_has_matched_descendant(
                container, matched_code_element_ids
            ):
                remove_element(container)

        remaining = entry.xpath(prune_xpath, namespaces=namespaces)
        if isinstance(remaining, list) and len(remaining) == 0:
            remove_element(entry)


def _container_has_matched_descendant(
    container: _Element,
    matched_element_ids: set[int],
) -> bool:
    """
    Check if a container or any descendant is a matched code element.
    """

    if id(container) in matched_element_ids:
        return True
    for descendant in container.iter():
        if id(descendant) in matched_element_ids:
            return True
    return False
