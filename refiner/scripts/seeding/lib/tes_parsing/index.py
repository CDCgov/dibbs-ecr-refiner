import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypedDict
from uuid import UUID

from config import TES_DATA_DIR, TRIGGER_FILE_PREFIX, logger

from ..models import (
    CODE_SYSTEM_DATA,
    COVERAGE_LEVEL_URL,
    AcgCompleteness,
    ContextGrouperInfo,
    CoverageLevel,
    FhirCodeInfo,
    SystemSortedFhirInfo,
    VsCanonicalUrl,
    VsDict,
    VsVersion,
)
from .code_extraction import (
    _ACG_CATEGORY_PATTERN,
    code_extractor,
    parse_valueset_source_name,
)

# normalize extracted category names to clean, stable slugs
_CATEGORY_SLUG_MAP = {
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


def parse_coverage_level(vs: dict) -> CoverageLevel | None:
    """
    Extracts the crmi-curationCoverageLevel extension from a raw ValueSet dict, if present.

    The extension is complex (has nested sub-extensions rather than a direct value).
    Expected sub-extensions by url:
        - "level": valueCodeableConcept with a single coding
        - "levelReason": valueMarkdown (expected when level is "partial")
        - "dateTime": valueDateTime (expected when level is "complete")
    """

    extensions = vs.get("extension", [])
    if not extensions:
        return None

    for ext in extensions:
        if ext.get("url") != COVERAGE_LEVEL_URL:
            continue

        sub_extensions = ext.get("extension", [])
        if not sub_extensions:
            logger.warning(
                f"Found curationCoverageLevel extension with no sub-extensions "
                f"on {vs.get('title') or vs.get('url')}"
            )
            return None

        level: str | None = None
        reason: str | None = None
        date: str | None = None

        for sub_ext in sub_extensions:
            sub_url = sub_ext.get("url")

            if sub_url == "level":
                codings = sub_ext.get("valueCodeableConcept", {}).get("coding", [])
                if codings:
                    level = codings[0].get("code")

            elif sub_url == "levelReason":
                reason = sub_ext.get("valueMarkdown")

            elif sub_url == "dateTime":
                date = sub_ext.get("valueDateTime")

            else:
                logger.warning(
                    f"Unexpected sub-extension url '{sub_url}' in "
                    f"curationCoverageLevel on {vs.get('title') or vs.get('url')}"
                )

        if level is None:
            logger.warning(
                f"curationCoverageLevel extension present but 'level' "
                f"sub-extension missing on {vs.get('title') or vs.get('url')}"
            )
            return None

        return CoverageLevel(level=level, reason=reason, date=date)

    return None


def map_coverage_level_to_acg_completeness(vs: dict) -> str | None:
    """
    Maps TES CRMI curation coverage level to the app's ACG completeness label.

    Missing coverage returns None so it is stored as NULL.
    """

    coverage = parse_coverage_level(vs)

    if coverage is None:
        return None

    if coverage.level == "complete":
        return AcgCompleteness.FULLY_COMPLETE

    if coverage.level == "partial":
        return AcgCompleteness.PARTIALLY_COMPLETE

    logger.warning(
        f"Unexpected ACG coverage level '{coverage.level}' on "
        f"{vs.get('title') or vs.get('url')}"
    )

    return None


def parse_valueset_category(name: str) -> str:
    """
    Extracts a normalized category slug from an Additional Context Grouper name or a generalized category for Reporting Specification Groupers.

    Examples:
        "Pertussis Additional Context Medication Codes" -> "medication"
        "Syphilis Additional Context Clinical Lab Result Codes" -> "clinical_lab_result"
        "Unknown Format" -> "other"
    """

    acg_match = _ACG_CATEGORY_PATTERN.search(name)
    rsg_match = "reporting specification grouper" in name.lower()
    if rsg_match:
        return "reporting_specification_grouper"

    if not acg_match or rsg_match:
        logger.warning(f"Could not parse category from name: '{name}'")
        return "other"

    raw_category = acg_match.group(1).strip().lower()
    slug = _CATEGORY_SLUG_MAP.get(raw_category)

    if slug is None:
        # normalize to snake_case as a fallback for new categories
        slug = re.sub(r"\s+", "_", raw_category)
        logger.info(f"New ACG category encountered: '{raw_category}' -> '{slug}'")

    return slug


def parse_snomed_from_url(url: str) -> str | None:
    """
    Extracts a SNOMED code from a 'rs-grouper' URL.
    """

    return url.split("rs-grouper-")[-1] if "rs-grouper-" in url else None


def is_condition_grouper(vs: dict) -> bool:
    """
    Checks if a ValueSet is a 'ConditionGrouper' via its metadata profile.
    """

    profiles = vs.get("meta", {}).get("profile", []) or []
    return any("conditiongroupervalueset" in str(prof).lower() for prof in profiles)


@dataclass
class ConditionData:
    """
    Represents a single, processed condition grouper ready for database insertion.
    """

    parent_vs: VsDict
    all_vs_map: dict[tuple[VsCanonicalUrl, VsVersion], VsDict]

    child_codes: set[FhirCodeInfo] = field(init=False, default_factory=set)
    """
    Codes from all child 'Reporting Specification Grouper' (RSG) ValueSets.
    """

    sibling_codes: set[FhirCodeInfo] = field(init=False, default_factory=set)
    """
    Codes from all sibling 'Additional Context Grouper' ValueSets.
    """

    context_groupers: list[ContextGrouperInfo] = field(init=False, default_factory=list)
    """
    Metadata for each resolved Additional Context Grouper.
    """

    coverage: CoverageLevel | None = field(init=False, default=None)
    """
    Parsed coverage level from the crmi-curationCoverageLevel extension, if present.
    """

    def __post_init__(self):
        """
        Populates the code sets after the instance is initialized.
        """

        self._aggregate_child_codes()
        self._aggregate_sibling_codes()
        self.coverage = parse_coverage_level(self.parent_vs)

    def _aggregate_child_codes(self):
        """
        Extracts codes and SNOMED IDs from all child RSG ValueSets.
        """

        for child_vs in code_extractor.get_child_rsg_valuesets(
            self.parent_vs, self.all_vs_map
        ):
            self.child_codes.update(code_extractor.extract_codes_from_vs(child_vs))

    def _aggregate_sibling_codes(self):
        """
        Extracts codes from all sibling 'additional context' ValueSets and collects per-grouper metadata.
        """

        for sibling_vs in code_extractor.get_sibling_context_valuesets(
            self.parent_vs, self.all_vs_map
        ):
            codes = code_extractor.extract_codes_from_vs(sibling_vs)
            self.sibling_codes.update(codes)

    def _sort_codes(self, codes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Normalize and sort the lists of codes.

        This ensures the condition row's `updated_at` won't change due to list order changing.
        """

        return sorted(
            [
                {
                    "code": str(code.get("code", "")).strip(),
                    "display": (code.get("display") or "").strip(),
                }
                for code in codes
                if code.get("code") is not None
            ],
            key=lambda x: (x["code"], x["display"]),
        )

    @property
    def all_codes(self) -> set[FhirCodeInfo]:
        """
        Generates a union of all codes belonging to the condition.
        """
        # combine all codes; the union operator `|` correctly merges the sets
        return self.child_codes | self.sibling_codes

    @property
    def payload(self) -> dict[str, Any]:
        """
        Generates the dictionary payload for database insertion.
        """

        result = {
            "canonical_url": self.parent_vs.get("url"),
            "version": self.parent_vs.get("version"),
            "display_name": self.parent_vs.get("title"),
            "coverage_level": None,
            "coverage_level_reason": None,
            "coverage_level_date": None,
        }

        if self.coverage:
            result["coverage_level"] = self.coverage.level
            result["coverage_level_reason"] = self.coverage.reason
            result["coverage_level_date"] = self.coverage.date

        return result

    @property
    def context_grouper_payloads(self) -> list[dict[str, Any]]:
        """
        Generates the list of context grouper payloads for child table insertion.

        These are inserted separately after the condition row exists,
        since they need the condition's database ID.
        """

        return [
            {
                "name": cg.name,
                "category": cg.category,
                "canonical_url": cg.canonical_url,
                "code_count": cg.code_count,
                "completeness": cg.completeness,
            }
            for cg in self.context_groupers
        ]


class CodeRow(TypedDict):
    """
    A code row to upsert into the DB.

    UUID is generated by Python to help with seeding of the join tables.
    """

    id: UUID
    display: str
    code: str
    system_id: str
    valueset_url: str


def categorize_codes_by_system_oid(
    all_codes: set[FhirCodeInfo],
) -> SystemSortedFhirInfo:
    """
    Categorizes a set of codes into a dictionary based on their system.
    """
    url_to_oid_map = {c["url"]: c["oid"] for c in CODE_SYSTEM_DATA.values()}
    # the key is a "system_name", and the value is an empty list that will hold CodePayloads
    result: SystemSortedFhirInfo = {
        system_oid: [] for system_oid in url_to_oid_map.values()
    }

    for info in all_codes:
        if cur_code_system_oid := url_to_oid_map.get(info.system_url):
            result[cur_code_system_oid].append(info)
    return result


def parse_child_rsg_details_from_use_context(use_context: list[dict[str, dict]]) -> str:
    """
    Traverses the use context block in the valueset dict to get the display context for an RSG code.
    """
    for context in use_context:
        value_codeable_concept = context.get("valueCodeableConcept", "")
        if not isinstance(value_codeable_concept, str):
            vs_description = value_codeable_concept.get("text", None)
            # one of the use contexts in the RSG files is a description of
            # "this code is an RSG code". Skip that one.
            if (
                isinstance(vs_description, str)
                and vs_description != "Reporting Specification Grouper"
            ):
                return vs_description

    raise ValueError("No description found in parsing child RSG display name")


def is_reporting_trigger_valueset(vs: dict) -> bool:
    """
    Checks if a ValueSet is an eICR triggering ValueSet by its meta.profile.

    These carry the 'us-ph-triggering-valueset' profile from the US Public
    Health eCR IG -- they enumerate the codes that would carry a
    trigger-code templateId in an eICR, i.e. the actual reason a case
    report was sent, as opposed to RSG/ACG's broader "codes associated with
    this condition" scope.
    """

    profiles = vs.get("meta", {}).get("profile", []) or []
    return any("us-ph-triggering-valueset" in str(p) for p in profiles)


def parse_snomed_focus_codes(vs: dict) -> list[str]:
    """
    Extracts every SNOMED 'focus' useContext code from a ValueSet.

    A triggering ValueSet's useContext[focus] names the condition(s) it's
    associated with, the same role RSG's useContext[focus] plays -- but
    unlike RSG (one condition per ValueSet), a triggering ValueSet can list
    more than one.
    """

    codes: list[str] = []
    for context in vs.get("useContext", []):
        if context.get("code", {}).get("code") != "focus":
            continue
        for coding in context.get("valueCodeableConcept", {}).get("coding", []):
            if coding.get("system") == "http://snomed.info/sct" and coding.get("code"):
                codes.append(coding["code"])
    return codes


def get_expansion_codes(vs: dict) -> set[FhirCodeInfo]:
    """
    Extracts codes from a ValueSet's expansion.contains.

    Triggering ValueSets ship pre-expanded (expansion.contains) rather than
    as compose.include[].concept[] like RSG/ACG/CG, since they're sourced
    from VSAC rather than authored directly in TES's grouper compose.
    """

    codes: set[FhirCodeInfo] = set()
    source_url = vs.get("url")
    if not source_url:
        return codes

    source_name = parse_valueset_source_name(vs)
    for concept in vs.get("expansion", {}).get("contains", []):
        system = concept.get("system")
        code = concept.get("code")
        if system and code:
            codes.add(
                FhirCodeInfo(
                    system_url=system,
                    code=code,
                    # triggering valuesets ship without displays; the empty
                    # string keeps FhirCodeInfo's contract intact for any
                    # caller that does more than read code/system
                    display=concept.get("display") or "",
                    source_url=source_url,
                    source_name=source_name,
                )
            )
    return codes


def trigger_valueset_files() -> list[Path]:
    """
    Finds the eICR triggering shard set in TES_DATA_DIR.

    There is only ever one set: the triggering valuesets are unversioned, so
    a refetch overwrites them in place rather than landing beside the
    previous release the way the dated/semver groupers do.
    """

    return sorted(TES_DATA_DIR.glob(f"{TRIGGER_FILE_PREFIX}*.json"))


def load_trigger_codes_by_snomed() -> dict[str, set[FhirCodeInfo]]:
    """
    Loads the newest eICR triggering ValueSets, grouped by SNOMED focus code.

    Several triggering ValueSets typically share the same focus condition
    (e.g. separate disorder/lab/organism ValueSets for one condition), so
    codes are unioned per SNOMED code across all of them.
    """

    codes_by_snomed: defaultdict[str, set[FhirCodeInfo]] = defaultdict(set)
    for path in trigger_valueset_files():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for vs in data.get("valuesets", []):
            if not is_reporting_trigger_valueset(vs):
                continue
            codes = get_expansion_codes(vs)
            for snomed_code in parse_snomed_focus_codes(vs):
                codes_by_snomed[snomed_code].update(codes)

    return dict(codes_by_snomed)
