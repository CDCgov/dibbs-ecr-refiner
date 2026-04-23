import json
import re
from dataclasses import dataclass, field
from typing import Any

import psycopg
from config import TES_DATA_DIR, logger
from psycopg.types.json import Jsonb

SYSTEM_MAP = {
    "http://loinc.org": "loinc_codes",
    "http://snomed.info/sct": "snomed_codes",
    "http://hl7.org/fhir/sid/icd-10-cm": "icd10_codes",
    "http://www.nlm.nih.gov/research/umls/rxnorm": "rxnorm_codes",
    "http://hl7.org/fhir/sid/cvx": "cvx_codes",
}

COVERAGE_LEVEL_URL = (
    "http://hl7.org/fhir/uv/crmi/StructureDefinition/crmi-curationCoverageLevel"
)

# pattern to extract a category slug from ACG names like:
#   "Pertussis Additional Context Medication Codes"
#   "Syphilis Additional Context Clinical Lab Result Codes"
_ACG_CATEGORY_PATTERN = re.compile(
    r"Additional Context (.+?)(?:\s+Codes?)?\s*$", re.IGNORECASE
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
}

# type aliases
# a tuple representing a single, raw code: (system, code, display) pulled straight from the fhir ValueSet
# * display **could** be empty
type FhirCodeTuple = tuple[str, str, str | None]

# a dictionary representing a single code prepared for categorization by a code system
# * display **could** be empty
type CodePayload = dict[str, str | None]

# a list of processed codes for a specific system
type SystemCodeList = list[CodePayload]

# the map of all unique codes for a condition + version
type ConditionCodePayload = dict[str, SystemCodeList]


type VsCanonicalUrl = str
type VsVersion = str
type VsDict = dict


@dataclass
class CoverageLevel:
    """
    Parsed representation of the crmi-curationCoverageLevel extension.
    """

    level: str
    reason: str | None = None
    date: str | None = None


@dataclass
class ContextGrouperInfo:
    """
    Metadata for a single Additional Context Grouper ValueSet.
    """

    name: str
    category: str
    canonical_url: str
    code_count: int


@dataclass
class ConditionData:
    """
    Represents a single, processed condition grouper ready for database insertion.
    """

    parent_vs: VsDict
    all_vs_map: dict[tuple[VsCanonicalUrl, VsVersion], VsDict]

    child_codes: set[FhirCodeTuple] = field(init=False, default_factory=set)
    """
    Codes from all child 'Reporting Specification Grouper' (RSG) ValueSets.
    """

    sibling_codes: set[FhirCodeTuple] = field(init=False, default_factory=set)
    """
    Codes from all sibling 'Additional Context Grouper' ValueSets.
    """

    child_rsg_snomed_codes: set[str] = field(init=False, default_factory=set)
    """
    SNOMED codes extracted directly from the URLs of child RSG ValueSets.
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

        for child_vs in get_child_rsg_valuesets(self.parent_vs, self.all_vs_map):
            if snomed_code := parse_snomed_from_url(child_vs.get("url", "")):
                self.child_rsg_snomed_codes.add(snomed_code)

            self.child_codes.update(extract_codes_from_compose(child_vs))

    def _aggregate_sibling_codes(self):
        """
        Extracts codes from all sibling 'additional context' ValueSets and collects per-grouper metadata.
        """

        for sibling_vs in get_sibling_context_valuesets(
            self.parent_vs, self.all_vs_map
        ):
            codes = extract_codes_from_compose(sibling_vs)
            self.sibling_codes.update(codes)

            name = sibling_vs.get("title") or sibling_vs.get("name") or ""
            self.context_groupers.append(
                ContextGrouperInfo(
                    name=name,
                    category=parse_acg_category(name),
                    canonical_url=sibling_vs.get("url", ""),
                    code_count=len(codes),
                )
            )

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
    def payload(self) -> dict[str, Any]:
        """
        Generates the dictionary payload for database insertion.
        """

        # combine all codes; the union operator `|` correctly merges the sets
        all_codes = self.child_codes | self.sibling_codes
        categorized = categorize_codes_by_system(all_codes)

        result = {
            "canonical_url": self.parent_vs.get("url"),
            "version": self.parent_vs.get("version"),
            "display_name": self.parent_vs.get("title"),
            "child_rsg_snomed_codes": sorted(self.child_rsg_snomed_codes),
            "loinc_codes": Jsonb(self._sort_codes(categorized["loinc_codes"])),
            "snomed_codes": Jsonb(self._sort_codes(categorized["snomed_codes"])),
            "icd10_codes": Jsonb(self._sort_codes(categorized["icd10_codes"])),
            "rxnorm_codes": Jsonb(self._sort_codes(categorized["rxnorm_codes"])),
            "cvx_codes": Jsonb(self._sort_codes(categorized["cvx_codes"])),
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
            }
            for cg in self.context_groupers
        ]


def get_db_connection(db_url: str, db_password: str) -> psycopg.Connection:
    """
    Establishes and returns a connection to the PostgreSQL database.
    """

    try:
        return psycopg.connect(db_url, password=db_password)
    except psycopg.OperationalError as error:
        logger.error(f"❌ Database connection failed: {error}")
        raise


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


def parse_acg_category(name: str) -> str:
    """
    Extracts a normalized category slug from an Additional Context Grouper name.

    Examples:
        "Pertussis Additional Context Medication Codes" -> "medication"
        "Syphilis Additional Context Clinical Lab Result Codes" -> "clinical_lab_result"
        "Unknown Format" -> "other"
    """

    match = _ACG_CATEGORY_PATTERN.search(name)
    if not match:
        logger.warning(f"Could not parse ACG category from name: '{name}'")
        return "other"

    raw_category = match.group(1).strip().lower()
    slug = _CATEGORY_SLUG_MAP.get(raw_category)

    if slug is None:
        # normalize to snake_case as a fallback for new categories
        slug = re.sub(r"\s+", "_", raw_category)
        logger.info(f"New ACG category encountered: '{raw_category}' -> '{slug}'")

    return slug


def is_additional_context_grouper(vs: dict) -> bool:
    """
    Checks if a ValueSet is for 'Additional Context' by its name or title.
    """

    name = (vs.get("name") or "").lower()
    title = (vs.get("title") or "").lower()
    return "additional" in name or "additional" in title


def extract_codes_from_compose(vs: dict) -> set[FhirCodeTuple]:
    """
    Extracts all (system, code, display) tuples from a ValueSet's compose section.
    """

    codes: set[FhirCodeTuple] = set()

    compose = vs.get("compose")
    if not compose:
        return codes

    for inc in compose.get("include", []):
        system = inc.get("system")
        if not system:
            continue

        for concept in inc.get("concept", []):
            code = concept.get("code")
            if code:
                codes.add((system, code, concept.get("display")))

    return codes


def is_reporting_spec_grouper(vs: dict) -> bool:
    """
    Checks if a ValueSet is a 'ReportingSpecGrouper' by its URL.
    """

    url = vs.get("url", "")
    return "rs-grouper" in url.lower()


def get_child_rsg_valuesets(
    parent: dict,
    all_vs_map: dict[tuple[str, str], dict],
) -> list[dict]:
    """
    Finds all 'ReportingSpecGrouper' children of a parent ValueSet.
    """

    children: list[dict] = []

    compose = parent.get("compose")
    if not compose:
        return children

    for inc in compose.get("include", []):
        for ref in inc.get("valueSet", []):
            url, sep, version = str(ref).partition("|")
            if sep and (child_vs := all_vs_map.get((url, version))):
                if is_reporting_spec_grouper(child_vs):
                    children.append(child_vs)

    return children


def get_sibling_context_valuesets(
    parent: dict,
    all_vs_map: dict[tuple[str, str], dict],
) -> list[dict]:
    """
    Finds sibling 'Additional Context' ValueSets by matching name and version.
    """

    siblings: list[dict] = []

    parent_name = (parent.get("name") or "").lower().replace("_", "")
    parent_version = parent.get("version")
    parent_url = parent.get("url")

    for vs in all_vs_map.values():
        if (
            is_additional_context_grouper(vs)
            and vs.get("version") == parent_version
            and vs.get("url") != parent_url
            and parent_name in (vs.get("name") or "").lower().replace("_", "")
        ):
            siblings.append(vs)

    return siblings


def categorize_codes_by_system(
    all_codes: set[FhirCodeTuple],
) -> ConditionCodePayload:
    """
    Categorizes a set of codes into a dictionary based on their system.
    """

    # the key is a "system_name", and the value is an empty list that will hold CodePayloads
    result: ConditionCodePayload = {
        system_name: [] for system_name in SYSTEM_MAP.values()
    }

    for system, code, display in all_codes:
        if system_key := SYSTEM_MAP.get(system):
            result[system_key].append({"code": code, "display": display})

    return result


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


def load_valuesets_from_all_files() -> dict[tuple[VsCanonicalUrl, VsVersion], VsDict]:
    """
    Loads all ValueSet resources from JSON files in the TES data directory.
    """

    vs_map: dict[tuple[str, str], dict] = {}
    json_files = [f for f in TES_DATA_DIR.glob("*.json") if f.name != "manifest.json"]

    for idx, file_path in enumerate(json_files, start=1):
        logger.info(f"📝 Loading TES file {idx} / {len(json_files)}: {file_path.name}")

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        for vs_dict in data.get("valuesets", []):
            url = vs_dict.get("url")
            version = vs_dict.get("version")
            if url and version:
                vs_map[(url, version)] = vs_dict
            else:
                logger.warning(f"Failed to parse ValueSet {url}|{version}")

    logger.info(f"📊 Loaded {len(vs_map)} unique ValueSets from all TES files.")
    return vs_map
