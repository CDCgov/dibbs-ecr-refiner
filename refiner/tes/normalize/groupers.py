"""
Classification and reference resolution for TES groupers.

TES publishes three kinds of ValueSet:

* **Condition grouper (CG)** -- a manifest. Its `compose.include[].valueSet`
  entries name its children by `(url, version)`. From 7.0.0 it also carries its
  own `expansion.contains` union of everything below it; nothing reads that,
  because a condition's codes are defined by resolving its children.
* **Reporting specification grouper (RSG)** -- one per reportable condition,
  identified by `rs-grouper-<SNOMED>` in its url. Carries codes.
* **Additional context grouper (ACG)** -- annotates a condition with a category
  (diagnosis, medication, symptom, ...) parsed from its title. Carries codes.

This module is the single place that answers "what kind of grouper is this" and
"what are its children". Before it existed, three modules each had their own
answer to the first question -- by `meta.profile`, by url substring, and by
`useContext` coding -- and they agreed only by luck.
"""

import re
from dataclasses import dataclass

from .model import CanonicalUrl, ValueSetDict, ValueSetKey, Version

COVERAGE_LEVEL_URL = (
    "http://hl7.org/fhir/uv/crmi/StructureDefinition/crmi-curationCoverageLevel"
)

CG_PROFILE_MARKER = "conditiongroupervalueset"
RSG_PROFILE_MARKER = "reportingspecificationgroupervalueset"
RSG_URL_MARKER = "rs-grouper-"

# TES drops "Additional" on some titles ("Influenza Context Clinical Lab Result
# Codes"), so the category is matched with that word optional.
CATEGORY_PATTERN = re.compile(
    r"(?:Additional )?Context (.+?)(?:\s+Codes?)?\s*$", re.IGNORECASE
)

CATEGORY_SLUGS = {
    "medication": "medication",
    "medications": "medication",
    "immunization": "immunization",
    "immunizations": "immunization",
    "symptom": "symptom",
    "symptoms": "symptom",
    "specimen source": "specimen_source",
    "diagnosis": "diagnosis",
    "clinical lab result": "clinical_lab_result",
    "clinical lab results": "clinical_lab_result",
    "lab result": "clinical_lab_result",
    "lab results": "clinical_lab_result",
}

RSG_CATEGORY = "reporting_specification_grouper"

COMPLETENESS_BY_COVERAGE_LEVEL = {
    "complete": "fully complete",
    "partial": "partially complete",
}


def _profiles(valueset: ValueSetDict) -> list[str]:
    return [str(p).lower() for p in valueset.get("meta", {}).get("profile", []) or []]


def is_condition_grouper(valueset: ValueSetDict) -> bool:
    """Whether this ValueSet is a condition grouper, by its declared profile."""

    return any(CG_PROFILE_MARKER in profile for profile in _profiles(valueset))


def is_reporting_spec_grouper(valueset: ValueSetDict) -> bool:
    """
    Whether this ValueSet is a reporting specification grouper.

    Prefers the declared profile and falls back to the `rs-grouper-` url marker,
    which is how every release before profiles were published identified these.
    """

    if any(RSG_PROFILE_MARKER in profile for profile in _profiles(valueset)):
        return True
    return RSG_URL_MARKER in str(valueset.get("url", "")).lower()


def is_additional_context_grouper(valueset: ValueSetDict) -> bool:
    """
    Whether this ValueSet is an additional context grouper.

    ACGs carry no `meta.profile`, so the `grouper-type` useContext coding is the
    only structural signal. Matching on the title instead is not safe: 6.0.0 and
    7.0.0 both ship "Influenza Context Clinical Lab Result Codes", which drops
    the "Additional" a substring match would depend on.
    """

    for context in valueset.get("useContext", []):
        if context.get("code", {}).get("code") != "grouper-type":
            continue
        codings = context.get("valueCodeableConcept", {}).get("coding", [])
        if any(
            coding.get("code") == "additional-context-grouper" for coding in codings
        ):
            return True
    return False


def source_name(valueset: ValueSetDict) -> str:
    """
    Build the display name used for a grouper.

    ACG titles already carry everything needed. Every other kind gets its title
    joined with the `useContext` free-text descriptor, which is what
    distinguishes sibling RSGs that share a title.
    """

    title = valueset.get("title", "")

    if CATEGORY_PATTERN.search(title):
        return title.strip()

    for context in valueset.get("useContext", []):
        if "valueCodeableConcept" in context:
            return f"{title} {context['valueCodeableConcept'].get('text')}"

    return ""


def category_for(name: str) -> str:
    """
    Derive the category slug a grouper's codes belong to.

    RSGs all share one category. ACG categories come from the title, with new
    ones normalized to snake_case rather than rejected, so a category TES adds
    mid-release lands in the data instead of failing the run.
    """

    if "reporting specification grouper" in name.lower():
        return RSG_CATEGORY

    match = CATEGORY_PATTERN.search(name)
    if not match:
        return "other"

    raw = match.group(1).strip().lower()
    return CATEGORY_SLUGS.get(raw) or re.sub(r"\s+", "_", raw)


def snomed_from_rsg_url(url: str | None) -> str | None:
    """Extract the SNOMED code an RSG names itself with, from its url."""

    if not url or RSG_URL_MARKER not in url:
        return None
    return url.split(RSG_URL_MARKER)[-1]


def rsg_display_name(valueset: ValueSetDict) -> str | None:
    """
    Find the human description for an RSG's own SNOMED code.

    One of the useContext entries on every RSG is the literal string
    "Reporting Specification Grouper", describing the artifact rather than the
    condition; it is skipped in favour of the next descriptor.
    """

    for context in valueset.get("useContext", []):
        concept = context.get("valueCodeableConcept")
        if not isinstance(concept, dict):
            continue
        text = concept.get("text")
        if isinstance(text, str) and text != "Reporting Specification Grouper":
            return text
    return None


@dataclass(frozen=True, slots=True)
class CoverageLevel:
    """
    The parsed crmi-curationCoverageLevel extension.

    `reason` is expected when the level is "partial", `date` when it is
    "complete"; TES does not always supply either, so both stay optional.
    """

    level: str
    reason: str | None = None
    date: str | None = None


def coverage_level(valueset: ValueSetDict) -> CoverageLevel | None:
    """
    Parse the CRMI curation coverage level extension.

    The extension is complex -- the level sits in a nested sub-extension rather
    than carrying a direct value. Absent or malformed coverage returns None so
    it stores as NULL rather than guessing.
    """

    for extension in valueset.get("extension", []) or []:
        if extension.get("url") != COVERAGE_LEVEL_URL:
            continue

        level = reason = date = None
        for sub in extension.get("extension", []) or []:
            match sub.get("url"):
                case "level":
                    codings = sub.get("valueCodeableConcept", {}).get("coding", [])
                    if codings:
                        level = codings[0].get("code")
                case "levelReason":
                    reason = sub.get("valueMarkdown")
                case "dateTime":
                    date = sub.get("valueDateTime")

        return CoverageLevel(level=level, reason=reason, date=date) if level else None

    return None


def coverage_completeness(valueset: ValueSetDict) -> str | None:
    """
    Map the coverage level to the app's ACG completeness label.

    Absent coverage, and any level TES adds that the app has no label for,
    return None so it stores as NULL.
    """

    coverage = coverage_level(valueset)
    return COMPLETENESS_BY_COVERAGE_LEVEL.get(coverage.level) if coverage else None


def child_references(valueset: ValueSetDict) -> list[ValueSetKey]:
    """
    Resolve a condition grouper's declared children to (url, version) keys.

    Children are read from the explicit reference graph rather than matched by
    name. Name matching had two failure modes that both silently lost or gained
    codes: a spelling drift between parent and child dropped every ACG for that
    condition, and a parent name that was a substring of another condition's
    name absorbed that condition's ACGs.

    References without a version are skipped -- those are VSAC `valueSet` entries
    that 7.x groupers point at, which TES does not publish alongside the
    groupers and which the expansion already accounts for.
    """

    compose = valueset.get("compose")
    if not compose:
        return []

    keys: list[ValueSetKey] = []
    for include in compose.get("include", []):
        for reference in include.get("valueSet", []) or []:
            url, separator, version = str(reference).partition("|")
            if separator:
                keys.append((url, version))
    return keys


def resolve_children(
    parent: ValueSetDict,
    all_valuesets: dict[ValueSetKey, ValueSetDict],
) -> tuple[list[ValueSetDict], list[ValueSetDict]]:
    """
    Split a condition grouper's resolvable children into RSGs and ACGs.

    Args:
        parent: The condition grouper.
        all_valuesets: Every loaded ValueSet, keyed by (url, version).

    Returns:
        (reporting specification groupers, additional context groupers). A
        reference that does not resolve is omitted from both; the verify step
        reports unresolved references rather than failing the run here.
    """

    rsgs: list[ValueSetDict] = []
    acgs: list[ValueSetDict] = []

    for key in child_references(parent):
        child = all_valuesets.get(key)
        if child is None:
            continue
        if is_reporting_spec_grouper(child):
            rsgs.append(child)
        elif is_additional_context_grouper(child):
            acgs.append(child)

    return rsgs, acgs


def condition_identity(valueset: ValueSetDict) -> tuple[CanonicalUrl, Version] | None:
    """Return the (url, version) a condition grouper is identified by, if complete."""

    url = valueset.get("url")
    version = valueset.get("version")
    return (url, version) if url and version else None
