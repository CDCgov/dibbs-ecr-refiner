from copy import deepcopy
from typing import cast

from lxml import etree
from lxml.etree import _Element

from app.core.exceptions import StructureValidationError, XMLParsingError
from app.services.format import remove_element
from app.services.terminology import CodeSystemSets

from ..model import (
    HL7_NS,
    DbNarrativeAction,
    NamespaceMap,
    SectionRunResult,
    SectionSpecification,
)
from ..narrative import (
    reconstruct_narrative,
    remove_all_comments,
    replace_narrative_with_reconstruction,
    replace_narrative_with_removal_notice,
    restore_narrative,
)
from .utils import (
    _index_narrative_display_ids,
    build_generic_match_comment_text,
    enrich_surviving_entries,
    insert_comment_before,
)

# NOTE:
# PUBLIC ENTRY POINT
# =============================================================================


def process(
    section: _Element,
    codes_to_match: set[str],
    namespaces: NamespaceMap,
    section_specification: SectionSpecification | None,
    augmentation_timestamp: str = "",
    code_system_sets: CodeSystemSets | None = None,
    narrative_action: DbNarrativeAction = "retain",
) -> SectionRunResult:
    """
    Process a section using the generic matching logic.

    Used for sections without IG-verified entry match rules. These are
    sections where the entry structure is either narrative-only,
    contains non-condition-specific content, or has not yet been
    characterized with specific match rules.

    Matching is unscoped — any code/value/translation element with a
    `@code` in `codes_to_match` is considered a hit. Pruning is
    entry-level only. `displayName` enrichment runs post-prune when
    `code_system_sets` is available.

    The generic path neutralizes the section's `<code>` and
    `<text>` elements before searching to prevent false matches.
    Both are saved as deep copies and restored after processing —
    `<code>` unconditionally in the finally block (to avoid
    corrupting the tree on error), and `<text>` whenever the
    `narrative` action may end up preserving the original
    ("retain", "keep_on_match", or the "reconstruct" fallback
    branch — see Step 5 below).

    Source document XML comments are stripped before matching begins.
    Match provenance comments (`eCR Refiner: generic match — ...`)
    are injected above each surviving entry after pruning; these
    survive because they are added after the source comment cleanup.

    If no entries match (or `codes_to_match` is empty), all <entry>
    children are pruned and the section's <text> is handled per the
    `narrative` setting:

      - "retain"           → narrative restored intact
      - "remove"           → narrative replaced with the removal notice
      - "reconstruct"      → falls back to RETAIN the original narrative
                             (nothing to rebuild from)
      - "keep_on_match"    → narrative replaced with the removal notice
                             (no matches means the negative branch)

    `nullFlavor="NI"` is applied at the section level so the document
    continues to satisfy CDA schematron rules that require `SHALL
    contain at least one entry` for refinable sections. See
    `refine._interpret_run_result` for outcome mapping.

    Returns:
        SectionRunResult reporting whether matches were found and
        what the engine did with the narrative.
    """

    # neutralize <code>: remove the @code attribute so the section's
    # own LOINC code doesn't match during the unscoped search
    # the full element is deep-copied and restored in the finally block
    section_code_element = section.find("./hl7:code", namespaces=namespaces)
    original_code = (
        deepcopy(section_code_element) if section_code_element is not None else None
    )
    if section_code_element is not None and section_code_element.get("code"):
        section_code_element.attrib.pop("code")

    # neutralize <text>: clear it so inline codes in the narrative
    # don't produce false matches
    # save a deep copy whenever the narrative may end up preserved —
    # "retain", "keep_on_match" (resolves to retain when matches are
    # found), or "reconstruct" (falls back to retain when the engine
    # cannot rebuild)
    PRESERVE_NARRATIVE_ACTIONS = {"retain", "keep_on_match", "reconstruct"}
    text_element = section.find("./hl7:text", namespaces=namespaces)
    original_text = (
        deepcopy(text_element)
        if text_element is not None and narrative_action in PRESERVE_NARRATIVE_ACTIONS
        else None
    )
    # capture the narrative's ID -> label map BEFORE clearing it. entries
    # point at those labels through <originalText><reference value="#id"/>,
    # and enrich_surviving_entries (STEP 4, far below) needs them to recover a
    # display for codes the jurisdiction sets don't carry. clearing first would
    # leave nothing to resolve against
    narrative_index = _index_narrative_display_ids(section, namespaces)

    if text_element is not None:
        text_element.clear()

    try:
        if not codes_to_match:
            # nothing to match against → treat as no-match. defer to
            # the shared no-match handler below by jumping straight to
            # the empty-matches branch.
            contextual_matches: list[_Element] = []
        else:
            try:
                # STEP 1: strip source document comments before matching
                # so they cannot interfere with candidate gathering.
                # provenance comments injected after pruning (STEP 3) will
                # survive because they are added after this cleanup.
                remove_all_comments(section)

                # STEP 2: CONTEXT FILTERING
                contextual_matches = _find_condition_relevant_elements(
                    section, codes_to_match, namespaces
                )

            except etree.XPathEvalError as e:
                raise XMLParsingError(
                    message="Invalid XPath expression",
                    details={
                        "section_details": dict(section.attrib),
                        "error": str(e),
                    },
                )

        if not contextual_matches:
            # no matches: prune every <entry> and apply the configured
            # narrative behavior. nullFlavor="NI" is set at the section
            # level so the document continues to satisfy CDA
            # schematron rules that require `SHALL contain at least
            # one entry` for refinable sections — the narrative
            # remains the source of clinical information.
            for entry in section.findall("hl7:entry", namespaces=namespaces):
                remove_element(entry)
            section.attrib["nullFlavor"] = "NI"

            if narrative_action == "remove" or narrative_action == "keep_on_match":
                # "keep_on_match" is the negative branch on no-match
                replace_narrative_with_removal_notice(section, namespaces)
                return SectionRunResult(
                    matches_found=False,
                    narrative_disposition="removed",
                )

            if narrative_action == "reconstruct":
                # NOTE: reconstruct + no matches falls back to
                # retaining the original narrative rather than
                # swapping in a removal notice. assumption: when the
                # jurisdiction asked for reconstruction and we can't
                # produce one, the original narrative is the most
                # informative state available — strictly more useful
                # to a reviewer than the removal placeholder.
                if original_text is not None:
                    restore_narrative(section, original_text, namespaces)
                return SectionRunResult(
                    matches_found=False,
                    narrative_disposition="reconstruct_fallback_retained",
                )

            # "retain": restore the original <text> we saved before
            # neutralizing it
            if original_text is not None:
                restore_narrative(section, original_text, namespaces)
            return SectionRunResult(
                matches_found=False,
                narrative_disposition="retained",
            )

        try:
            # STEP 3: PRUNE non-matching entries and inject provenance
            # comments above the surviving ones
            surviving_entries = _preserve_relevant_entries(section, contextual_matches)
            _inject_generic_match_comments(surviving_entries, contextual_matches)

            # STEP 4: ENRICH displayName on surviving entries
            if code_system_sets is not None:
                enrich_surviving_entries(
                    section,
                    code_system_sets,
                    namespaces,
                    narrative_index=narrative_index,
                )

            # STEP 5: handle narrative <text> reconstruction runs HERE,
            # after STEP 4 enrichment, because it reads displayName off
            # the surviving entries it rebuilds the table from
            match narrative_action:
                case "remove":
                    replace_narrative_with_removal_notice(section, namespaces)
                    return SectionRunResult(
                        matches_found=True,
                        narrative_disposition="removed",
                    )
                case "reconstruct":
                    reconstructed = reconstruct_narrative(
                        section, augmentation_timestamp=augmentation_timestamp
                    )
                    if reconstructed is not None:
                        replace_narrative_with_reconstruction(
                            section, reconstructed, namespaces
                        )
                        return SectionRunResult(
                            matches_found=True,
                            narrative_disposition="reconstructed",
                        )
                    # NOTE: no registered reconstructor (or nothing
                    # survived to rebuild) — fall back to RETAIN the
                    # original narrative rather than swap in a
                    # removal notice. assumption: when the
                    # jurisdiction asked for reconstruction and we
                    # can't run it, the original narrative is more
                    # informative to a reviewer than the removal
                    # placeholder, even though it may reference
                    # entries that were pruned.
                    if original_text is not None:
                        restore_narrative(section, original_text, namespaces)
                    return SectionRunResult(
                        matches_found=True,
                        narrative_disposition="reconstruct_fallback_retained",
                    )
                case _:
                    # "retain" or "keep_on_match" (matches found):
                    # restore the saved original when present; a None
                    # original means the source had no <text>
                    if original_text is not None:
                        restore_narrative(section, original_text, namespaces)
                    return SectionRunResult(
                        matches_found=True,
                        narrative_disposition="retained",
                    )

        except etree.XPathEvalError as e:
            raise XMLParsingError(
                message="Invalid XPath expression",
                details={
                    "section_details": dict(section.attrib),
                    "error": str(e),
                },
            )
    finally:
        # always restore <code> — even on error — to avoid leaving
        # the tree in a modified state for the caller
        if section_code_element is not None and original_code is not None:
            section.replace(section_code_element, original_code)


# NOTE:
# CONTEXT FILTERING
# =============================================================================


def _find_condition_relevant_elements(
    section: _Element,
    codes_to_match: set[str],
    namespaces: NamespaceMap,
) -> list[_Element]:
    """
    Find clinical elements matching condition codes.

    This is the context filter — only elements relevant to the
    reportable condition should proceed to the next step.

    Searches for both:

    1. Parent elements that have a `code`/`translation`/`value`
       child carrying a `@code` attribute (the "candidates_parents"
       pattern).
    2. Direct `code`/`translation`/`value` elements with a
       `@code` attribute (the "candidates_children" pattern).

    Both result lists are filtered against `codes_to_match` and
    combined, then deduplicated to remove parent/child overlap.

    Args:
        section: The XML section element to search within.
        codes_to_match: The set of codes to match against.
        namespaces: XML namespaces for XPath evaluation.

    Returns:
        Deduplicated list of contextually relevant clinical elements.

    Raises:
        XMLParsingError: If XPath evaluation fails.
    """

    if not codes_to_match:
        return []

    try:
        codes_to_check = frozenset(codes_to_match)

        # Pattern 1: parent elements with code/translation/value children
        # that might have direct codes
        candidates_parents = cast(
            list[_Element],
            section.xpath(
                ".//hl7:*[hl7:code/@code or hl7:translation/@code or hl7:value/@code]",
                namespaces=namespaces,
            ),
        )

        # Pattern 2: code/translation/value elements that might have
        # matching codes directly
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

        clinical_elements = matched_children + matched_parents

        # deduplicate hierarchical matches within the matched set
        return _deduplicate_clinical_elements(clinical_elements)

    except etree.XPathEvalError as e:
        raise XMLParsingError(
            message="Failed to generate candidate elements for code matching",
            details={
                "section_details": dict(section.attrib),
                "error": str(e),
            },
        )


# NOTE:
# ENTRY PRESERVATION
# =============================================================================


def _preserve_relevant_entries(
    section: _Element,
    contextual_matches: list[_Element],
) -> list[_Element]:
    """
    Preserve entries containing relevant elements; remove the rest.

    For each matched clinical element, walks up the tree to find its
    enclosing `<entry>`, deduplicates the resulting entry list, and
    removes any entry not in the deduplicated set.

    Returns the list of surviving `<entry>` elements so the caller
    can inject match provenance comments above each one.

    Args:
        section: The section element being processed.
        contextual_matches: Clinical elements found by the context
            filter.

    Returns:
        Deduplicated list of preserved entry elements.
    """

    entry_paths = []
    for clinical_element in contextual_matches:
        entry_path = _find_path_to_entry(clinical_element)
        entry_paths.append(entry_path)

    deduplicated_entry_paths = _deduplicate_entry_paths(entry_paths)

    _prune_unwanted_siblings(deduplicated_entry_paths, section)

    return deduplicated_entry_paths


def _inject_generic_match_comments(
    surviving_entries: list[_Element],
    contextual_matches: list[_Element],
) -> None:
    """
    Insert provenance comments above each surviving entry.

    The generic path has no rule index or tier — it's a flat unscoped
    code scan. Comments attribute the match to the generic engine and
    identify the code and element path that triggered retention.

    One comment per entry. When multiple matched elements map to the
    same entry (e.g. two matching codes in one act), only the first
    matched element is cited — the generic path doesn't distinguish
    which element is "primary."

    Args:
        surviving_entries:  Entry elements that survived pruning.
        contextual_matches: Clinical elements that produced matches,
            in the order returned by `_find_condition_relevant_elements`.
    """

    # build a map from entry id → first matching element within it
    entry_id_to_first_match: dict[int, _Element] = {}
    for matched_el in contextual_matches:
        try:
            entry = _find_path_to_entry(matched_el)
        except Exception:
            continue
        eid = id(entry)
        if eid not in entry_id_to_first_match:
            entry_id_to_first_match[eid] = matched_el

    for entry in surviving_entries:
        first_match = entry_id_to_first_match.get(id(entry))
        if first_match is None:
            continue

        code = first_match.get("code") or ""
        display = first_match.get("displayName") or ""
        tag = etree.QName(first_match.tag).localname

        # build a readable path from entry root to the matched element
        path_parts: list[str] = []
        current: _Element | None = first_match
        while current is not None and current is not entry:
            path_parts.append(etree.QName(current.tag).localname)
            current = current.getparent()

        path_from_entry = "/".join(reversed(path_parts)) if path_parts else tag

        comment_text = build_generic_match_comment_text(
            matched_code=code,
            matched_display=display,
            matched_tag=tag,
            path_from_entry=path_from_entry,
        )
        insert_comment_before(entry, comment_text)


def _find_path_to_entry(element: _Element) -> _Element:
    """
    Find the nearest <entry> ancestor of an element.

    Walks up the tree from `element` until it finds an element with
    the `{urn:hl7-org:v3}entry` tag. Used by `_preserve_relevant_entries`
    to map matched clinical elements back to the entries that should
    be kept.

    Raises:
        StructureValidationError: If no <entry> ancestor is found.
    """

    current_element: _Element | None = element

    while (
        current_element is not None and current_element.tag != "{urn:hl7-org:v3}entry"
    ):
        current_element = current_element.getparent()

    if current_element is None:
        raise StructureValidationError(
            message="Parent <entry> element not found.",
            details={"element_tag": element.tag},
        )

    # narrowed: None branch raised above
    # this makes mypy happy
    entry_element: _Element = current_element

    return entry_element


def _prune_unwanted_siblings(
    entry_paths: list[_Element],
    section: _Element,
) -> None:
    """
    Remove top-level <entry> elements not in the preserved set.

    Args:
        entry_paths: Entry elements to keep.
        section: The section being processed.
    """

    preserved_ids = {id(e) for e in entry_paths}
    all_entries = section.findall("./hl7:entry", namespaces=HL7_NS)

    for entry in all_entries:
        if id(entry) not in preserved_ids:
            remove_element(entry)


# NOTE:
# DEDUPLICATION HELPERS
# =============================================================================


def _deduplicate_entry_paths(entry_paths: list[_Element]) -> list[_Element]:
    """
    Remove duplicate and nested entry paths.

    When XPath matches find nested elements (e.g., both an <act> and
    an <observation> inside that <act>), this function ensures we don't
    end up with duplicate or parent/child entries both being preserved,
    which would lead to duplicate content in the refined eICR.

    Args:
        entry_paths: List of entry elements that may contain duplicates
            or nested relationships.

    Returns:
        Deduplicated list with no overlapping branches.
    """

    if not entry_paths:
        return entry_paths

    # remove exact duplicates first (same entry referenced multiple times)
    unique_entries: list[_Element] = []
    seen_entries: set[int] = set()

    for entry in entry_paths:
        entry_id = id(entry)
        if entry_id not in seen_entries:
            unique_entries.append(entry)
            seen_entries.add(entry_id)

    # remove nested relationships (parent/child entries)
    final_entries: list[_Element] = []

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


def _deduplicate_clinical_elements(
    clinical_elements: list[_Element],
) -> list[_Element]:
    """
    Remove nested clinical elements representing the same logical finding.

    When XPath matches both a parent element (like <organizer>) and
    its child elements (like <observation>), we want to keep only the
    highest-level parent that contains the complete clinical context.
    """

    if not clinical_elements:
        return clinical_elements

    code_groups: dict[str, list[_Element]] = {}

    for elem in clinical_elements:
        data = _extract_code_for_grouping(elem)
        code = data.get("code")

        if isinstance(code, str):
            if code not in code_groups:
                code_groups[code] = []
            code_groups[code].append(elem)

    deduplicated: list[_Element] = []

    for code, elements in code_groups.items():
        if len(elements) == 1:
            deduplicated.append(elements[0])
            continue

        ancestors: list[_Element] = []
        for elem in elements:
            is_descendant = False
            for other_elem in elements:
                if elem is not other_elem and _is_ancestor(other_elem, elem):
                    is_descendant = True
                    break

            if not is_descendant:
                ancestors.append(elem)

        deduplicated.extend(ancestors)

    return deduplicated


def _is_ancestor(
    potential_ancestor: _Element,
    potential_descendant: _Element,
) -> bool:
    """
    Check if one element is an ancestor of another in the XML tree.

    Walks up from `potential_descendant` looking for
    `potential_ancestor`. Returns True if found.
    """

    current = potential_descendant.getparent()

    while current is not None:
        if current is potential_ancestor:
            return True
        current = current.getparent()

    return False


def _extract_code_for_grouping(element: _Element) -> dict[str, str | None]:
    """
    Extract a clinical element's code for use in grouping during dedup.

    Used by `_deduplicate_clinical_elements` to identify elements
    representing the same logical finding so that nested duplicates
    can be collapsed to the outermost ancestor.

    Returns:
        Dictionary with a `code` key (string or None).
    """

    tag_local = element.tag.split("}")[-1] if "}" in element.tag else element.tag

    if tag_local in ("code", "value", "translation") and element.get("code"):
        return {"code": element.get("code")}

    code_element = element.find(".//hl7:code", namespaces=HL7_NS)
    if code_element is not None:
        return {"code": code_element.get("code")}

    return {"code": None}
