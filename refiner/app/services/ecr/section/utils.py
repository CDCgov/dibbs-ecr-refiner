from typing import Final

from lxml import etree
from lxml.etree import _Element

from app.services.terminology import CodeSystemSets, Coding

from ..model import EntryMatchRule, NamespaceMap
from ..specification.constants import (
    CVX_OID,
    ICD10_OID,
    LOINC_OID,
    RXNORM_OID,
    SNOMED_OID,
)

# NOTE:
# NAMESPACE CONSTANTS
# =============================================================================

SDTC_NAMESPACE: Final[str] = "urn:hl7-org:sdtc"

CODE_SYSTEM_LABELS: Final[dict[str, str]] = {
    LOINC_OID: "LOINC",
    SNOMED_OID: "SNOMED",
    RXNORM_OID: "RxNorm",
    ICD10_OID: "ICD-10",
    CVX_OID: "CVX",
}


def code_system_label(oid: str | None) -> str:
    """
    Return a human-readable label for a code system OID.

    Falls back to the OID string for unrecognized OIDs, and returns
    "any code system" when the rule accepts any code system (oid=None)
    — a deliberate choice documented at the call site, not a missing
    value.
    """

    if oid is None:
        return "any code system"
    return CODE_SYSTEM_LABELS.get(oid, oid)


# NOTE:
# DISPLAYNAME ENRICHMENT
# =============================================================================


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

    Called by both `entry_matching.process` and
    `generic_matching.process` after pruning and before narrative
    writing.

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

            existing = element.get("displayName")
            if existing and existing.strip():
                continue

            code_system_oid = element.get("codeSystem")
            coding = code_system_sets.find_match(code_val, code_system_oid)
            if coding is not None:
                _enrich_display_name(element, coding)


def _enrich_display_name(code_element: _Element, coding: Coding) -> None:
    """
    Set `displayName` on a code-bearing element from a Coding.

    Only sets the attribute if it is absent or empty; never overwrites
    an existing non-empty value.
    """

    existing = code_element.get("displayName")
    if existing and existing.strip():
        return

    if coding.display:
        code_element.set("displayName", coding.display)


# NOTE:
# COMMENT INJECTION — RULE-MATCHED ENTRIES (entry_matching path)
# =============================================================================


def build_entry_match_comment_text(
    entry_matches: list,  # list[EntryMatch] — typed as list to avoid circular import
    match_rules: list[EntryMatchRule],
) -> str:
    """
    Build the comment text for a rule-matched entry's match provenance.

    Used by `entry_matching._inject_entry_match_comments`. Accepts a
    list of EntryMatch objects (typed as `list` to avoid importing the
    dataclass here; callers are responsible for passing the correct type).

    Comment format (single match):
        eCR Refiner: rule N (TN) [xpath_tail] — element[code] "display" (CodeSystem)

    Comment format (multiple matches):
        eCR Refiner: rule N (TN) [xpath_tail] — element[code] "display" (CodeSystem)
        eCR Refiner: rule N (TN) [xpath_tail] — element[code] "display" (CodeSystem)
        ...

    Returns a string suitable for passing to etree.Comment(). Leading/
    trailing spacing is included for readability.
    """

    lines: list[str] = []

    for m in entry_matches:
        try:
            rule_index = match_rules.index(m.rule) + 1
        except ValueError:
            rule_index = 0

        xpath_tail = m.rule.code_xpath.rsplit("/", 1)[-1]
        predicate_start = xpath_tail.find("[")
        if predicate_start != -1:
            xpath_tail = xpath_tail[:predicate_start]

        tag = etree.QName(m.matched_code_element.tag).localname
        code = m.matched_coding.code
        display = m.matched_coding.display or ""
        sys_label = code_system_label(m.rule.code_system_oid)
        tier = m.rule.tier

        if display:
            lines.append(
                f" eCR Refiner matched: {tag}[{code}] '{display}' ({sys_label})"
                f" Entry match fired for: rule {rule_index} (T{tier}) [{xpath_tail}]"
            )
        else:
            lines.append(
                f" eCR Refiner matched: {tag}[{code}] ({sys_label})"
                f" Entry match fired for: rule {rule_index} (T{tier}) [{xpath_tail}]"
            )

    if len(lines) == 1:
        return lines[0] + " "
    else:
        return "\n" + "\n".join(f"  {line.strip()}" for line in lines) + "\n"


# NOTE:
# COMMENT INJECTION — GENERIC-MATCHED ENTRIES (generic_matching path)
# =============================================================================


def build_generic_match_comment_text(
    matched_code: str,
    matched_display: str,
    matched_tag: str,
    path_from_entry: str,
) -> str:
    """
    Build the comment text for a generic-path matched entry.

    Unlike rule-matched entries, the generic path has no rule index or
    tier — it's a flat code-value scan. The comment attributes the
    match to the generic engine and names the code and where in the
    entry it was found.

    Comment format:
        eCR Refiner: generic match — {tag}[{code}] "{display}" at {path}

    Args:
        matched_code:    The code value that triggered the match.
        matched_display: Display name for the code, or empty string.
        matched_tag:     Local element name (e.g. "code", "value").
        path_from_entry: Slash-separated path from the entry root to
                         the matched element (e.g. "act/observation/value").
                         Used to show where in the entry the match landed.
    """

    if matched_display:
        return (
            f" eCR Refiner: generic match — {matched_tag}[{matched_code}]"
            f' "{matched_display}" at {path_from_entry} '
        )
    else:
        return (
            f" eCR Refiner: generic match — {matched_tag}[{matched_code}]"
            f" at {path_from_entry} "
        )


# NOTE:
# COMMENT INSERTION HELPER
# =============================================================================


def insert_comment_before(entry: _Element, comment_text: str) -> None:
    """
    Insert an XML comment immediately before an <entry> element.

    Used by both matching engines after pruning to annotate surviving
    entries with match provenance. The comment is inserted as the
    previous sibling of the entry in its parent element.

    Args:
        entry:        The <entry> element to annotate.
        comment_text: Text for the comment node. Passed directly to
                      etree.Comment() — callers should include leading/
                      trailing spaces for readability.
    """

    comment = etree.Comment(comment_text)
    comment.tail = "\n"
    parent = entry.getparent()
    if parent is not None:
        idx = list(parent).index(entry)
        parent.insert(idx, comment)
