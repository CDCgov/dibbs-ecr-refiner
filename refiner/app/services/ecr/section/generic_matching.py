import logging
from copy import deepcopy
from typing import Final

from lxml import etree
from lxml.etree import _Element

from app.core.exceptions import StructureValidationError, XMLParsingError
from app.services.format import remove_element
from app.services.terminology import CodeSystemSets

from ..model import (
    HL7_NAMESPACE,
    NamespaceMap,
    SectionRunResult,
    SectionSpecification,
)
from .narrative import (
    create_minimal_section,
    remove_all_comments,
    replace_narrative_with_removal_notice,
    restore_narrative,
)

logger = logging.getLogger(__name__)

# NOTE:
# * structural metadata elements that CDA templates almost universally
# require on clinical statements (Act, Procedure, Observation,
# SubstanceAdministration, Encounter, etc.). When a clinical statement
# is preserved as an ancestor of a match, these immediate children are
# preserved alongside it so the resulting statement remains
# structurally valid CDA.
# * this is a generic-CDA approximation. The forward-compatible form
# would be a template-specific lookup keyed by templateId, returning
# the exact required children for each template. That registry doesn't
# exist yet; this set is the intersection of required children across
# the templates the refiner cares about
_CDA_STRUCTURAL_METADATA_NAMES: Final[frozenset[str]] = frozenset(
    {
        "templateId",
        "id",
        "code",
        "statusCode",
        "effectiveTime",
        "value",
    }
)


def _path_from_entry(matched_element: _Element, entry: _Element) -> str:
    """
    Build a slash-separated string of local names from the entry root down to the matched element, for diagnostic logging.

    Returns something like "procedure/participant/participantRole/code"
    so a reader can see at a glance where in the entry's structure the
    match lives. Used only for logging — not part of the matching or
    pruning logic.
    """

    chain: list[str] = []
    current: _Element | None = matched_element

    while current is not None and current is not entry:
        if isinstance(current.tag, str):
            chain.append(etree.QName(current.tag).localname)
        current = current.getparent()

    chain.reverse()
    return "/".join(chain) if chain else "(entry root)"


# NOTE:
# CODE-BEARING ELEMENT TAGS
# =============================================================================
# the three CDA element types whose `@code` attribute can carry a clinical
# concept worth matching against. these are the elements we walk during
# candidate gathering. anything outside this set is structural CDA scaffolding
# that the matcher does not look at
_CODE_BEARING_TAGS: Final[frozenset[str]] = frozenset(
    {
        f"{{{HL7_NAMESPACE}}}code",
        f"{{{HL7_NAMESPACE}}}value",
        f"{{{HL7_NAMESPACE}}}translation",
    }
)


# NOTE:
# MECHANICS-DESCRIBING ELEMENT EXCLUSIONS
# =============================================================================
# * elements that carry SNOMED codes describing the *mechanics* of an
# observation/procedure (how, where, with what device) rather than the
# clinical assertion itself. SNOMED codes appearing on these elements would
# match the configured code set if they happen to overlap, but a PHA
# configuring a condition would not mean to match on "the body site of the
# measurement" or "the device used to perform the procedure"
# * this is the only structural exclusion the matcher applies. all other
# administrative/structural elements (statusCode, interpretationCode,
# routeCode, priorityCode, functionCode, participantRole/code, and so on)
# carry codes from vocabularies outside the five systems the refiner stores
# (LOINC, SNOMED, ICD-10-CM, RxNorm, CVX), so they cannot produce matches
# regardless of grouper contents and require no exclusion.
_EXCLUDED_LOCAL_NAMES: Final[frozenset[str]] = frozenset(
    {
        "methodCode",  # how the observation/procedure was performed
        "targetSiteCode",  # body site of the observation/procedure
        "approachSiteCode",  # approach site, rare but defined in CDA
        "playingDevice",  # device used (parent of <code>)
        "specimenPlayingEntity",  # specimen type (parent of <code>)
        "participantRole",  # role of participating entity (parent of <code>)
    }
)


# NOTE:
# PUBLIC ENTRY POINT
# =============================================================================


def process(
    section: _Element,
    codes_to_match: set[str],
    namespaces: NamespaceMap,
    section_specification: SectionSpecification | None,
    code_system_sets: CodeSystemSets | None = None,
    include_narrative: bool = True,
) -> SectionRunResult:
    """
    Process a section using path-based generic matching.

    Used for sections without IG-verified entry match rules. The matcher
    walks the section, gathers code-bearing elements, checks each one
    against the configured code set by code value, and for every entry
    that contains at least one match preserves the union of paths from
    each match up to the enclosing entry — plus the matched element's
    coding cluster siblings (`<code>`/`<value>`/`<translation>` in the
    same parent). Everything else inside matched entries is pruned.
    Entries with zero matches are removed entirely.

    The matching contract:

      - any code from the configured set that appears on a non-excluded
        candidate element is a match. there is no code system check; the
        configured set already constrains the matchable universe to the
        five systems the refiner stores (LOINC, SNOMED, ICD-10-CM,
        RxNorm, CVX), and the structural mechanics exclusion list covers
        the only places those codes appear non-clinically.
      - preservation is path-based: the chain from a matched element up
        to its enclosing <entry> is preserved, plus any code-bearing
        siblings that travel with the match as a coding cluster. the
        union of these paths across all matches in an entry defines
        what survives pruning.
      - the section's own <code> and <text> are neutralized before
        matching to prevent the section's defining LOINC and any
        narrative-embedded codes from producing false matches. both are
        restored in the finally block.

    If no entries match (or `codes_to_match` is empty), the section is
    reduced to a minimal stub via `create_minimal_section` (the no-match
    policy override) and the function returns a `SectionRunResult` with
    `matches_found=False`. The orchestrator translates this into
    `SectionOutcome.REFINED_NO_MATCHES_STUBBED` regardless of the
    narrative configuration — see `refine._interpret_run_result`.

    Args:
        section: The section element being processed.
        codes_to_match: Flat set of code values from the active
            configuration. Code system is not part of the lookup; see
            the contract notes above for why.
        namespaces: HL7 namespace map for XPath evaluation.
        section_specification: Unused by the generic path; accepted for
            dispatcher signature compatibility.
        code_system_sets: Used for displayName enrichment on surviving
            elements after pruning. Not used during match evaluation.
        include_narrative: Whether to keep the original section
            narrative. When False, narrative is replaced with a removal
            notice. Ignored when matches are zero; the engine stubs the
            section regardless per the no-match policy override.

    Returns:
        SectionRunResult describing what the engine did. Consumed by
        refine_eicr to compute the user-facing SectionOutcome.
    """

    # neutralize the section's own <code>: deep-copy the element so the
    # original can be restored in the finally block, then strip the @code
    # attribute so the section's defining LOINC cannot match. this matters
    # because some configurations carry LOINCs that overlap with section
    # LOINCs (e.g. a Vital Signs panel LOINC that also identifies the
    # section), and we never want a match on the section's own identifier
    section_code_element = section.find("./hl7:code", namespaces=namespaces)
    original_code = (
        deepcopy(section_code_element) if section_code_element is not None else None
    )
    if section_code_element is not None and section_code_element.get("code"):
        section_code_element.attrib.pop("code")

    # neutralize <text>: inline narrative may contain code elements (e.g. in
    # `<content>` references) that would otherwise produce false matches.
    # if the narrative is being kept, deep-copy it so it can be restored
    # after match evaluation. if it's being removed, the deep-copy is
    # unnecessary because the narrative will be replaced by a removal
    # notice rather than restored.
    text_element = section.find("./hl7:text", namespaces=namespaces)
    original_text = (
        deepcopy(text_element)
        if text_element is not None and include_narrative
        else None
    )
    if text_element is not None:
        text_element.clear()

    try:
        if not codes_to_match:
            # no codes to match against → treat as no-match and stub.
            # same override as the "matched nothing" case below; named as
            # REFINED_NO_MATCHES_STUBBED in refine._interpret_run_result
            create_minimal_section(section=section, removal_reason="no_match")
            return SectionRunResult(
                matches_found=False,
                # placeholder — orchestrator short-circuits on
                # matches_found=False and never reads this field
                narrative_disposition="retained",
            )

        try:
            # STEP 1: gather candidate elements and find matches
            matches = _find_matches(section, codes_to_match, namespaces)

            if not matches:
                # refiner policy: when no entries match, stub the section
                # * this overrides the configured narrative setting — there's
                #   no useful narrative to keep when there's no clinical
                #   content left to describe.
                create_minimal_section(section=section, removal_reason="no_match")
                return SectionRunResult(
                    matches_found=False,
                    narrative_disposition="retained",
                )

            # STEP 2: group matches by their enclosing <entry>
            entry_to_matches = _group_matches_by_entry(matches)

            # STEP 3: prune each matched entry to the union of paths from
            # its matches up to itself, plus coding cluster siblings
            for entry, entry_matches in entry_to_matches.items():
                _prune_entry_to_match_paths(entry, entry_matches)

            # STEP 4: remove entries that had zero matches
            _remove_unmatched_entries(section, set(entry_to_matches.keys()), namespaces)

            # STEP 5: enrich displayName on surviving code-bearing elements
            # cross-module helper from entry_matching, used here too so the
            # generic path produces the same kind of human-readable output
            if code_system_sets is not None:
                from .entry_matching import enrich_surviving_entries

                enrich_surviving_entries(section, code_system_sets, namespaces)

            # STEP 6: clean up any leftover comments inside the section
            remove_all_comments(section)

            # STEP 7: handle narrative <text>
            if include_narrative and original_text is not None:
                restore_narrative(section, original_text, namespaces)
                return SectionRunResult(
                    matches_found=True,
                    narrative_disposition="retained",
                )
            elif not include_narrative:
                replace_narrative_with_removal_notice(section, namespaces)
                return SectionRunResult(
                    matches_found=True,
                    narrative_disposition="removed",
                )

            # include_narrative=True but original_text was None — the
            # section had no <text> in the source. nothing to restore,
            # but matches were still found
            return SectionRunResult(
                matches_found=True,
                narrative_disposition="retained",
            )

        except etree.XPathEvalError as e:
            raise XMLParsingError(
                message="Invalid XPath expression in generic matching",
                details={
                    "section_details": dict(section.attrib),
                    "error": str(e),
                },
            )
    finally:
        # always restore <code> — even on error — to avoid leaving the
        # tree in a modified state for the caller. <text> restoration
        # happens in the success path because it depends on the narrative
        # disposition; on error the cleared <text> is left as-is, which
        # matches the existing generic_matching behavior
        if section_code_element is not None and original_code is not None:
            section.replace(section_code_element, original_code)


# NOTE:
# CANDIDATE GATHERING AND MATCH EVALUATION
# =============================================================================


def _find_matches(
    section: _Element,
    codes_to_match: set[str],
    namespaces: NamespaceMap,
) -> list[_Element]:
    """
    Walk the section and return code-bearing elements whose `@code` is in the configured set, skipping mechanics-describing elements.

    Iterates only within `<entry>` children of the section (the section
    code/text were already neutralized by the caller, so there's no
    concern about matching them, but restricting to entries also keeps
    the walk bounded and predictable).
    Whitespace in the @code attribute is stripped before comparison.
    Some EHRs emit codes with leading or trailing whitespace (e.g.
    "94310-0 ") which is well-formed XML but would fail a direct
    string match against the configured set. XSD token-type semantics
    collapse this whitespace for a strictly conformant consumer, so
    stripping is consistent with a correct reading of the underlying
    datatype.
    """

    matches: list[_Element] = []

    for entry in section.findall("hl7:entry", namespaces=namespaces):
        for element in entry.iter():
            if not isinstance(element.tag, str):
                continue

            if element.tag not in _CODE_BEARING_TAGS:
                continue

            # strip whitespace from the @code attribute — handles the
            # "94310-0 " case where some EHRs emit trailing spaces
            code_val = (element.get("code") or "").strip()
            if not code_val:
                continue

            if _is_mechanics_element(element):
                continue

            if code_val in codes_to_match:
                matches.append(element)

    return matches


def _is_mechanics_element(element: _Element) -> bool:
    """
    This is to find out if the element is playing a mechanical role in a pattern within an entry.

    Return True if the element or any of its ancestors up to the
    enclosing `<entry>` is one of the mechanics-describing local names
    in `_EXCLUDED_LOCAL_NAMES`.

    CDA encodes the mechanics exclusion in two shapes depending on the
    template:

      - the element itself (or its immediate parent) carries the
        mechanics name and `@code`, e.g. `<methodCode code="..."/>` or
        `<playingDevice><code code="..."/></playingDevice>`
      - the element is nested several levels deep inside an
        administrative container, e.g.
        `<participant><participantRole><playingEntity><code/></playingEntity></participantRole></participant>`
        — the immediate parent (playingEntity) is not in the exclusion
        list, but a higher ancestor (participantRole, participant) is

    Walking the full ancestor chain catches both shapes from a single
    exclusion entry. The walk stops at the enclosing `<entry>` element
    (exclusive) — anything above that is the section or document
    structure, not the entry's content.
    """

    # check the element itself
    own_local = etree.QName(element.tag).localname
    if own_local in _EXCLUDED_LOCAL_NAMES:
        return True

    # walk ancestors up to (but not including) the enclosing <entry>
    current = element.getparent()
    while current is not None and isinstance(current.tag, str):
        local = etree.QName(current.tag).localname
        if local == "entry":
            return False
        if local in _EXCLUDED_LOCAL_NAMES:
            return True
        current = current.getparent()

    # if we walked all the way to None without hitting <entry>, the
    # element isn't actually inside an entry — fall through as not
    # mechanics. _find_matches only iterates within entries so this
    # branch shouldn't fire in normal use
    return False


# NOTE:
# MATCH GROUPING AND PATH-BASED PRUNING
# =============================================================================


def _group_matches_by_entry(
    matches: list[_Element],
) -> dict[_Element, list[_Element]]:
    """
    Group matched elements by their enclosing `<entry>`.

    Each match is associated with the nearest ancestor `<entry>` element.
    A match that has no `<entry>` ancestor is unexpected (the candidate
    walk in `_find_matches` only descends into entries) and raises a
    `StructureValidationError` to surface the inconsistency rather than
    silently dropping the match.
    """

    grouped: dict[_Element, list[_Element]] = {}

    for matched_element in matches:
        entry = _find_enclosing_entry(matched_element)
        if entry not in grouped:
            grouped[entry] = []
        grouped[entry].append(matched_element)

    return grouped


def _find_enclosing_entry(element: _Element) -> _Element:
    """
    Walk up the tree to find the nearest `<entry>` ancestor.

    This is the brought-forward primitive from the older generic matcher
    (formerly `_find_path_to_entry`). Adapted to return only the entry,
    since the path collection is now done by `_collect_path_to_entry`.
    """

    entry_tag = f"{{{HL7_NAMESPACE}}}entry"
    current: _Element | None = element

    while current is not None and current.tag != entry_tag:
        current = current.getparent()

    if current is None:
        raise StructureValidationError(
            message="No <entry> ancestor found for matched element",
            details={"element_tag": element.tag},
        )

    return current


def _collect_path_to_entry(
    matched_element: _Element, entry: _Element
) -> list[_Element]:
    """
    Return the ancestor chain from a matched element up to its enclosing entry, inclusive of both endpoints.

    Used by `_prune_entry_to_match_paths` to compute the union of nodes
    to preserve when pruning an entry.
    """

    chain: list[_Element] = []
    current: _Element | None = matched_element

    while current is not None:
        chain.append(current)
        if current is entry:
            return chain
        current = current.getparent()

    # this would mean the matched element is not actually inside the
    # entry passed in — a bug in `_group_matches_by_entry` or its caller
    raise StructureValidationError(
        message="Matched element is not a descendant of the given entry",
        details={"element_tag": matched_element.tag, "entry_tag": entry.tag},
    )


def _collect_coding_cluster_siblings(matched_element: _Element) -> list[_Element]:
    """
    Return the matched element's siblings that are also code-bearing elements (`<code>`, `<value>`, or `<translation>`).

    The coding cluster preservation rule: when a match lands on a
    `<code>`, `<value>`, or `<translation>`, the related coding
    elements that share its parent travel with the match. This keeps a
    `<code>`-and-`<value>` pair together when only one of them matched,
    which is almost always what's clinically meaningful — e.g., a
    Result Observation where the test LOINC and the SNOMED result
    value should always survive together.

    Limited to immediate siblings (not descendants) so this rule does
    not accidentally drag nested observations along via
    `entryRelationship`. Path-based pruning handles the structural
    ancestor chain; the cluster rule only handles same-parent code
    grouping.
    """

    parent = matched_element.getparent()
    if parent is None:
        return []

    siblings: list[_Element] = []
    for sibling in parent:
        if sibling is matched_element:
            continue
        if not isinstance(sibling.tag, str):
            continue
        if sibling.tag in _CODE_BEARING_TAGS:
            siblings.append(sibling)

    return siblings


def _prune_entry_to_match_paths(
    entry: _Element,
    matches: list[_Element],
) -> None:
    """
    Prune an entry back to its entry even when multiple matches are present.

    Prune an entry to the union of paths from each match to the entry
    root, plus the coding cluster siblings of each match, plus the
    structurally required immediate children of each preserved
    clinical statement.

    Algorithm:
      1. For each match, collect the ancestor chain from the match
         up to the entry root.
      2. For each match, collect the coding cluster siblings of the
         matched element.
      3. For each preserved ancestor that is a clinical statement
         container, also preserve its structural metadata children
         (id, statusCode, effectiveTime, etc.) so the result is
         structurally valid CDA.
      4. Remove every element in the entry not in the preserve set.
    """

    preserve: set[_Element] = {entry}

    # step 1 + 2: collect path-to-entry and cluster siblings for each match
    for matched_element in matches:
        for ancestor in _collect_path_to_entry(matched_element, entry):
            preserve.add(ancestor)
        for sibling in _collect_coding_cluster_siblings(matched_element):
            preserve.add(sibling)

    # step 3: for every preserved ancestor, also preserve its immediate
    # * structural metadata children (id, statusCode, effectiveTime, etc.)
    #   so the pruned output stays structurally valid CDA. without this,
    #   path-based pruning would correctly preserve the matched code and
    #   its enclosing clinical statement (procedure/act/observation) but
    #   would drop the statement's required children, producing an empty
    #   shell that fails XSD content-model validation
    structural_additions: set[_Element] = set()
    for preserved in preserve:
        if preserved is entry:
            continue
        for child in preserved:
            if not isinstance(child.tag, str):
                continue
            child_local = etree.QName(child.tag).localname
            if child_local in _CDA_STRUCTURAL_METADATA_NAMES:
                structural_additions.add(child)
    preserve.update(structural_additions)

    # step 4: walk the entry and remove anything not in the preserve set
    to_remove: list[_Element] = []
    for descendant in entry.iter():
        if descendant is entry:
            continue
        if not isinstance(descendant.tag, str):
            continue
        if descendant not in preserve:
            to_remove.append(descendant)

    for element in to_remove:
        parent = element.getparent()
        if parent is not None:
            remove_element(element)


def _remove_unmatched_entries(
    section: _Element,
    matched_entries: set[_Element],
    namespaces: NamespaceMap,
) -> None:
    """
    Remove `<entry>` elements that had no matches.

    Entries with at least one match have already been pruned in place
    by `_prune_entry_to_match_paths`. This pass removes the entries
    that contributed nothing.
    """

    for entry in section.findall("hl7:entry", namespaces=namespaces):
        if entry not in matched_entries:
            remove_element(entry)
