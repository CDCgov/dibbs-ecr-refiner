import re
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any

from config import logger

from .models import (
    COVERAGE_LEVEL_URL,
    DATETIME_VERSION_REGEX,
    SEMVER_VERSION_REGEX,
    AcgCompleteness,
    ContextGrouperInfo,
    CoverageLevel,
    FhirCodeInfo,
    VsCanonicalUrl,
    VsDict,
    VsVersion,
)

VERSION_SIX_CUTOFF_DATETIME = "20260327"

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


def get_tes_version(version_string: str, regex: str) -> str | None:
    """
    Utility function to find version from a passed in string and regex pattern.
    """
    regex_to_match = re.compile(regex)
    match = regex_to_match.search(version_string)
    return match.group(0) if match else None


def parse_valueset_source_name(vs: dict) -> str:
    """
    Extracts ValueSet TES source from the valueset, if it exists.

    For distinct types of TES valuesets, this function:
        - Checks "title" for ACG since those valuesets have all the relevant data
        in that field
        - Checks useContext.valueCodeableConcept.text for other ValueSets that have the appropriate descriptor
        - Falls back to an empty string if nothing is found.
    """
    # get the condition context that we want to prefix the source from
    title = vs.get("title", "")

    # if the valueset is an ACG, the title has all the information we need, so
    # just return a cleaned version
    match = _ACG_CATEGORY_PATTERN.search(title)
    if match:
        return title.strip()

    # otherwise, we need to find the valueSet text nested in the useContext information
    useContext = vs.get("useContext", [])
    if not useContext:
        return ""

    for context in useContext:
        for key, value in context.items():
            if key == "valueCodeableConcept":
                return f"{title} {value.get('text')}"

    return ""


def semver_is_less_or_equal(v1_str, v2_str):
    """Utility method to compare semver versions."""
    v1_tuple = tuple(map(int, v1_str.split(".")))
    v2_tuple = tuple(map(int, v2_str.split(".")))

    if v1_tuple < v2_tuple:
        return True
    elif v1_tuple > v2_tuple:
        return False
    return True


class TesParsingStrategy:
    """
    Strategy for parsing / returning the codes from a particular TES version schema.
    """

    @abstractmethod
    def parse_vs_for_codes(self, vs: dict) -> set[FhirCodeInfo]:
        """
        Abstract parsing method for valuesets coming from the TES.
        """
        pass


class TesParsingStrategyVersion6(TesParsingStrategy):
    """
    Strategy for parsing TES files prior to version 6.
    """

    def parse_vs_for_codes(self, vs: dict):
        """
        Parsing method for TES files in versions prior to version 6.
        """
        codes: set[FhirCodeInfo] = set()
        compose = vs.get("compose")

        if not compose:
            return codes

        source_name = parse_valueset_source_name(vs)
        source_url = vs.get("url")
        if not source_url:
            return codes

        for inc in compose.get("include", []):
            system = inc.get("system")
            if not system:
                continue

            for concept in inc.get("concept", []):
                code = concept.get("code")
                if code:
                    codes.add(
                        FhirCodeInfo(
                            system_url=system,
                            code=code,
                            display=concept.get("display"),
                            source_url=source_url,
                            source_name=source_name,
                        )
                    )

        return codes


class TesParsingStrategyVersion7(TesParsingStrategy):
    """
    Strategy for parsing TES files prior to version 6.
    """

    def parse_vs_for_codes(self, vs: dict):
        """
        Parsing method for TES files in versions after to version 7.
        """
        codes: set[FhirCodeInfo] = set()
        expansion = vs.get("expansion")

        if not expansion:
            return codes

        source_name = parse_valueset_source_name(vs)
        source_url = vs.get("url")
        if not source_url:
            return codes

        for inc in expansion.get("contains", []):
            system = inc.get("system")
            if not system:
                continue

            code = inc.get("code")
            if code:
                codes.add(
                    FhirCodeInfo(
                        system_url=system,
                        code=code,
                        display=inc.get("display"),
                        source_url=source_url,
                        source_name=source_name,
                    )
                )

        return codes


class CodeExtractionContext:
    """
    Strategy context class for TES valueset parsing.

    Implemented to extensibly handle parsing for different TES schemas.
    """

    def __init__(self, strategy: TesParsingStrategy) -> None:
        """Init function."""
        self._parsing_strategy = strategy

    @property
    def parsing_strategy(self) -> TesParsingStrategy:
        """Parsing strategy for code context."""
        return self._parsing_strategy

    @parsing_strategy.setter
    def parsing_strategy(self, strategy: TesParsingStrategy) -> None:
        self._parsing_strategy = strategy

    def determine_parsing_strategy(self, vs: dict) -> None:
        """Function that reads the version property of the valueset and determines the appropriate parsing strategy."""
        version = vs.get("version")

        if not version:
            # fallback to default, pre-6 parsing strategy.
            self._parsing_strategy = TesParsingStrategyVersion6()
            return

        if ver := get_tes_version(version_string=version, regex=SEMVER_VERSION_REGEX):
            if semver_is_less_or_equal("6.0.0", ver):
                self._parsing_strategy = TesParsingStrategyVersion6()

            else:
                self._parsing_strategy = TesParsingStrategyVersion7()

        elif ver := get_tes_version(
            version_string=version, regex=DATETIME_VERSION_REGEX
        ):
            if ver <= VERSION_SIX_CUTOFF_DATETIME:
                self._parsing_strategy = TesParsingStrategyVersion6()

            if ver > VERSION_SIX_CUTOFF_DATETIME:
                self._parsing_strategy = TesParsingStrategyVersion7()

    def extract_codes_from_vs(self, vs: dict) -> set[FhirCodeInfo]:
        """
        Extracts all (system, code, display) tuples from a ValueSet's compose section.
        """
        self.determine_parsing_strategy(vs)
        return self._parsing_strategy.parse_vs_for_codes(vs)


# intialize extractor with default parsing strategy of version 6
code_extractor = CodeExtractionContext(TesParsingStrategyVersion6())


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


def is_additional_context_grouper(vs: dict) -> bool:
    """
    Checks if a ValueSet is for 'Additional Context' by its name or title.
    """

    name = (vs.get("name") or "").lower()
    title = (vs.get("title") or "").lower()
    return "additional" in name or "additional" in title


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
) -> list[VsDict]:
    """
    Finds the Additional Context Grouper ValueSets referenced by a parent.

    Resolves children via the parent's compose.include[].valueSet references,
    using the same (url, version) lookup pattern as get_child_rsg_valuesets.

    The parent CG's compose section explicitly declares its ACG children, so
    we don't have to reverse-engineer the relationship from naming patterns.
    Earlier versions of this function matched siblings by name substring,
    which had two failure modes:

    * A spelling drift between parent and child silently dropped the ACG.
      E.g. v6.0.0 "Streptoccal_Disease" (parent typo) does not match
      "Streptococcal_Disease_Additional_Context_*" (children spelled
      correctly), so every strep ACG was missed and ~22,000 codes were
      lost from the seeded condition.

    * A parent name that is a strict substring of another condition's name
      silently absorbed that other condition's ACGs. E.g. "Influenza" is
      a substring of "Invasive_Haemophilus_Influenzae_Disease...", so the
      Influenza condition was pulling in H. Influenzae's ACGs as siblings
      and inflating its code count by ~9,000.

    Both failure modes go away once siblings are resolved by the explicit
    reference graph.
    """

    siblings: list[VsDict] = []

    compose = parent.get("compose")
    if not compose:
        return siblings

    for inc in compose.get("include", []):
        for ref in inc.get("valueSet", []):
            url, sep, version = str(ref).partition("|")
            if sep and (child_vs := all_vs_map.get((url, version))):
                if is_additional_context_grouper(child_vs):
                    siblings.append(child_vs)

    return siblings


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

        for child_vs in get_child_rsg_valuesets(self.parent_vs, self.all_vs_map):
            self.child_codes.update(code_extractor.extract_codes_from_vs(child_vs))

    def _aggregate_sibling_codes(self):
        """
        Extracts codes from all sibling 'additional context' ValueSets and collects per-grouper metadata.
        """

        for sibling_vs in get_sibling_context_valuesets(
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
