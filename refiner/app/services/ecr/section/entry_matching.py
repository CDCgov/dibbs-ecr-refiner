from dataclasses import dataclass
from typing import Final, cast

from lxml import etree
from lxml.etree import _Element

from app.core.exceptions import XMLParsingError
from app.services.format import remove_element
from app.services.terminology import CodeSystemSets, Coding

from ..model import (
    HL7_XSI_NS,
    DbNarrativeAction,
    EntryMatchRule,
    NamespaceMap,
    SectionRunResult,
    SectionSpecification,
)
from ..narrative import (
    ReconstructedNarrative,
    reconstruct_narrative,
    remove_all_comments,
    replace_narrative_with_reconstruction,
    replace_narrative_with_removal_notice,
)
from .utils import (
    SDTC_NAMESPACE,
    _enrich_display_name,
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
    augmentation_timestamp: str = "",
    narrative_action: DbNarrativeAction = "retain",
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
    6. Handles narrative <text> based on the `narrative` action

    No UUID swap needed — match rules only search within <entry>
    elements, so the section's own <code> is never at risk of matching.

    If no entries match, all <entry> children are pruned and the
    section's <text> is handled per the `narrative` setting:

      - "retain"           → narrative left intact
      - "remove"           → narrative replaced with the removal notice
      - "keep_on_match"    → narrative replaced with the removal notice
                             (no matches means the negative branch)
      - "reconstruct"      → same as "keep_on_match". There is nothing to
                             rebuild from, and the original narrative
                             describes the entries that were just pruned.

    The orchestrator maps the resulting `SectionRunResult` to
    `REFINED_NO_MATCHES_NARRATIVE_RETAINED`,
    `REFINED_NO_MATCHES_NARRATIVE_REMOVED`,
    `REFINED_RECONSTRUCT_UNAVAILABLE_FALLBACK_RETAINED`, or
    `REFINED_RECONSTRUCT_NO_MATCHES_FALLBACK_RETAINED` — see
    `refine._interpret_run_result`.

    Returns:
        SectionRunResult reporting whether matches were found and
        what the engine did with the narrative.
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
            # no entries matched: prune them all and resolve the
            # narrative according to the configured setting. the
            # previous hard-coded `create_minimal_section` call (which
            # also overwrote the narrative with a stub table) has been
            # replaced by narrative-driven behavior so that
            # jurisdictions can choose to keep the original narrative
            # even when the coded entries don't survive filtering.
            #
            # nullFlavor="NI" is still applied at the section level so
            # the document satisfies CDA schematron rules that require
            # `SHALL contain at least one entry` for refinable sections.
            # the narrative remains the source of clinical information.
            for entry in section.findall("hl7:entry", namespaces):
                remove_element(entry)
            section.attrib["nullFlavor"] = "NI"

            if narrative_action in ("remove", "keep_on_match", "reconstruct"):
                # all three are negative branches when NOTHING matched:
                #
                #   "remove"        — unconditional
                #   "keep_on_match" — keep on match, and there was none
                #   "reconstruct"   — reconstruct falls back to keep-on-match
                #
                # reconstruct used to retain the original narrative here, on
                # the reasoning that a stale narrative is more informative
                # than a removal notice. That reasoning ignored what the
                # retained narrative actually contains. Nothing matched, so
                # every entry in this section was just pruned — and the
                # original narrative still describes all of them, in full
                # clinical prose. Retaining it ships exactly the content the
                # jurisdiction's configuration said should not be here, with
                # the structured entries stripped so a receiver cannot even
                # process it. Choosing "reconstruct" grants the refiner broad
                # licence to rewrite the section; keep-on-match is far closer
                # to the spirit of that grant than handing back the
                # unrefined original.
                replace_narrative_with_removal_notice(section, namespaces)
                return SectionRunResult(
                    matches_found=False,
                    narrative_disposition="removed",
                )

            # "retain": leave the original narrative in place
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

        # STEP 6: handle narrative <text> reconstruction runs HERE,
        # after STEP 4 enrichment, because it reads displayName off the
        # surviving entries it rebuilds the table from
        match narrative_action:
            case "remove":
                replace_narrative_with_removal_notice(section, namespaces)
                return SectionRunResult(
                    matches_found=True,
                    narrative_disposition="removed",
                )
            case "reconstruct":
                match reconstruct_narrative(
                    section, augmentation_timestamp=augmentation_timestamp
                ):
                    case ReconstructedNarrative() as rebuilt:
                        replace_narrative_with_reconstruction(
                            section, rebuilt.text, namespaces
                        )
                        # entries the section's reconstructor could not
                        # cover are present in reduced form; say so
                        # rather than reporting a clean rebuild
                        return SectionRunResult(
                            matches_found=True,
                            narrative_disposition=(
                                "reconstructed_reduced"
                                if rebuilt.reduced_entry_count
                                else "reconstructed"
                            ),
                        )
                    # these two branches DID match — the surviving entries
                    # are real content, they just could not be rendered as
                    # rows (or the section has no registered reconstructor).
                    # keep-on-match keeps on a match, so the original
                    # narrative stays; removing it would leave real entries
                    # with no readable representation. the footnote says the
                    # narrative may describe entries the refinement removed
                    case "no_matching_entries":
                        return SectionRunResult(
                            matches_found=False,
                            narrative_disposition="reconstruct_no_entries",
                        )
                    case "reconstruction_unavailable":
                        return SectionRunResult(
                            matches_found=True,
                            narrative_disposition="reconstruct_unavailable",
                        )

            case _:
                # "retain" or "keep_on_match" (matches found):
                # leave the original narrative in place
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


def _match_codes(
    entry: _Element,
    code_system_sets: CodeSystemSets,
    rule: EntryMatchRule,
    namespaces: NamespaceMap,
    *,
    xpath: str,
    code_system_oid: str | None,
) -> tuple[list[EntryMatch], bool]:
    """
    Evaluate ONE code location of a rule against the configured code sets.

    Shared by the rule's primary `code_xpath` and its optional
    `translation_xpath` — the two differ only in where they look and
    which code system they are scoped to.

    Args:
        entry: The <entry> being evaluated.
        code_system_sets: The jurisdiction's per-system code lookup.
        rule: The rule these matches are attributed to.
        namespaces: XML namespaces for xpath evaluation.
        xpath: The code location to evaluate, relative to `entry`.
        code_system_oid: OID scoping the lookup, or None for all systems.

    Returns:
        Tuple of `(matches, candidates_found)`. `candidates_found` reports
        whether the location held any code-bearing element at all, which is
        what drives structural precedence — independent of whether any of
        those codes matched.
    """

    elements = cast(list[_Element], entry.xpath(xpath, namespaces=namespaces))
    candidates_found = any((el.get("code") or "").strip() for el in elements)

    matches: list[EntryMatch] = []
    for element in elements:
        code = (element.get("code") or "").strip()
        if not code:
            continue

        if rule.require_value_set_attr and not element.get(
            f"{{{SDTC_NAMESPACE}}}valueSet"
        ):
            continue

        coding = code_system_sets.find_match(code, code_system_oid)
        if coding is not None:
            _enrich_display_name(element, coding)
            matches.append(
                EntryMatch(
                    entry=entry,
                    matched_code_element=element,
                    matched_coding=coding,
                    rule=rule,
                )
            )

    return matches, candidates_found


def _apply_rule(
    entry: _Element,
    code_system_sets: CodeSystemSets,
    rule: EntryMatchRule,
    namespaces: NamespaceMap,
) -> tuple[list[EntryMatch], bool]:
    """
    Evaluate a single rule against an entry: primary codes, then translations.

    The translation location is only consulted when the rule's own primary
    location produced no match — a translation is the sender's alternate
    coding of the same concept, so matching it after the primary already
    matched would double-count one concept.

    Returns:
        Tuple of `(matches, candidates_found)` for this rule alone.
    """

    matches, candidates_found = _match_codes(
        entry,
        code_system_sets,
        rule,
        namespaces,
        xpath=rule.code_xpath,
        code_system_oid=rule.code_system_oid,
    )

    if not matches and rule.translation_xpath:
        translation_matches, translation_candidates = _match_codes(
            entry,
            code_system_sets,
            rule,
            namespaces,
            xpath=rule.translation_xpath,
            code_system_oid=rule.translation_code_system_oid,
        )
        matches.extend(translation_matches)
        candidates_found = candidates_found or translation_candidates

    return matches, candidates_found


def _precedence_key(rule: EntryMatchRule) -> str:
    """
    Return the key that decides which precedence unit a rule belongs to.

    An explicit `precedence_group` wins; otherwise the rule's own
    `code_xpath` is the key, so rules reading the identical location are
    one unit without needing to be annotated.
    """

    return rule.precedence_group or rule.code_xpath


def _group_rules_by_precedence(
    match_rules: list[EntryMatchRule],
) -> list[list[EntryMatchRule]]:
    """
    Group **consecutive** rules that describe the same statement into one unit.

    Structural precedence exists to stop a rule describing a DIFFERENT
    structure from re-claiming an entry a higher-tier rule already spoke for.
    It is NOT meant to stop the alternative codings of one statement from
    being tried. Two rules belong to the same unit when they read the same
    location (identical `code_xpath` — the diagnosis sections' reversed-code
    pairs) or when they say so (`precedence_group` — the Results rules, which
    read one Result Observation at three different locations).

    Grouping is by adjacency rather than by collecting every rule with a
    matching key document-wide: the rule lists are ordered by tier, and a
    rule separated from its twin by a rule at another location is making a
    deliberate ordering statement that regrouping would silently rewrite.

    Args:
        match_rules: The section's rules, in tier order.

    Returns:
        The rules partitioned into consecutive same-statement groups.
    """

    groups: list[list[EntryMatchRule]] = []
    for rule in match_rules:
        if groups and _precedence_key(groups[-1][0]) == _precedence_key(rule):
            groups[-1].append(rule)
        else:
            groups.append([rule])
    return groups


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

    Structural precedence: rules are evaluated in tier order and grouped by
    the **statement** they describe (see `_group_rules_by_precedence`). The first
    group whose xpath finds any code-bearing element claims the entry,
    regardless of whether those candidates produced actual code set matches;
    later groups are not evaluated.

    Precedence is decided per GROUP, not per rule, because a section's rules
    are frequently alternative codings of ONE statement rather than
    descriptions of different ones. The diagnosis sections pair a tier-1 rule
    with a tier-3 rule at the SAME location under the reversed code system;
    Results reads one Result Observation at three DIFFERENT locations (test
    name, local-code translation, organism value). Breaking after the first
    rule in either shape makes the rest unreachable for every entry carrying
    a code at all, silently dropping content the jurisdiction configured.

    The require_value_set_attr guard: when set on a rule, a candidate
    element is only eligible for code matching if it also carries
    sdtc:valueSet. Elements without it still count as candidates for
    structural precedence — the rule claims the entry, it just may not
    produce a match.
    """

    entry_matches: list[EntryMatch] = []

    for group in _group_rules_by_precedence(match_rules):
        candidates_found = False
        for rule in group:
            rule_matches, rule_candidates = _apply_rule(
                entry, code_system_sets, rule, namespaces
            )
            entry_matches.extend(rule_matches)
            candidates_found = candidates_found or rule_candidates

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
       panel sub-observation should be independently evaluated. A rule may
       also carry prune_container_guard_xpath to exempt sibling containers
       that are shared, entry-scoped context (e.g. the Results Specimen
       Collection Procedure) from pruning.

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
    3. Matched with prune_container_xpath — remove non-matching containers,
       except containers exempted by prune_container_guard_xpath (shared,
       organizer-scoped context such as the Specimen Collection Procedure).
    4. Matched, no prune_container_xpath, preserve_whole_entry=False — keep whole.

    Invariant: a matched entry is never removed. An entry whose containers were
    all pruned away is deleted; an entry that never had containers at
    prune_container_xpath is kept, since the rule's container model simply does
    not describe it.
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
        guard_xpath: str | None = None
        for em in entry_matches:
            if em.rule.prune_container_xpath:
                prune_xpath = em.rule.prune_container_xpath
                guard_xpath = em.rule.prune_container_guard_xpath
                break

        if not prune_xpath:
            continue

        containers = cast(
            list[_Element],
            entry.xpath(prune_xpath, namespaces=namespaces),
        )
        had_containers = bool(containers)

        for container in containers:
            # a guarded container that does not itself contain a match
            # candidate is shared, organizer-scoped context (e.g. the
            # Specimen Collection Procedure) — retain it alongside any
            # surviving sibling rather than pruning it as non-matching
            if guard_xpath and not container.xpath(guard_xpath, namespaces=namespaces):
                continue

            if not _container_has_matched_descendant(
                container, matched_code_element_ids
            ):
                remove_element(container)

        # only an entry we actually pruned down to nothing is empty; an entry
        # that never had containers at this path (a Result Observation sitting
        # directly under <entry> with no organizer, or a Problems act whose
        # entryRelationship carries a non-SUBJ typeCode) still holds the match
        # that retained it. without this guard a MATCHED entry is deleted
        if had_containers:
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
