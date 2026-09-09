import re
from abc import abstractmethod

from ..models import (
    DATETIME_VERSION_REGEX,
    SEMVER_VERSION_REGEX,
    FhirCodeInfo,
    VsDict,
)

VERSION_SIX_CUTOFF_DATETIME = "20260327"

# pattern to extract a category slug from ACG names like:
#   "Pertussis Additional Context Medication Codes"
#   "Syphilis Additional Context Clinical Lab Result Codes"
_ACG_CATEGORY_PATTERN = re.compile(
    r"Additional Context (.+?)(?:\s+Codes?)?\s*$", re.IGNORECASE
)


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


def is_reporting_spec_grouper(vs: dict) -> bool:
    """
    Checks if a ValueSet is a 'ReportingSpecGrouper' by its URL.
    """

    url = vs.get("url", "")
    return "rs-grouper" in url.lower()


def is_additional_context_grouper(vs: dict) -> bool:
    """
    Checks if a ValueSet is for 'Additional Context' by its name or title.
    """

    name = (vs.get("name") or "").lower()
    title = (vs.get("title") or "").lower()
    return "additional" in name or "additional" in title


def get_tes_version(version_string: str | None, regex: str) -> str | None:
    """
    Utility function to find version from a passed in string and regex pattern.
    """
    if not version_string:
        return None
    regex_to_match = re.compile(regex)
    match = regex_to_match.search(version_string)
    return match.group(0) if match else None


def semver_is_less_or_equal(v1_str, v2_str):
    """Utility method to compare semver versions."""
    v1_tuple = tuple(map(int, v1_str.split(".")))
    v2_tuple = tuple(map(int, v2_str.split(".")))

    if v1_tuple <= v2_tuple:
        return True
    elif v1_tuple > v2_tuple:
        return False


class TesParsingStrategy:
    """
    Strategy for parsing / returning the codes from a particular TES version schema.
    """

    @abstractmethod
    def parse_vs_for_codes(
        self, vs: dict, return_as_vs: bool = False
    ) -> set[FhirCodeInfo]:
        """
        Abstract parsing method for valuesets coming from the TES.
        """
        pass

    def get_child_rsg_valuesets(
        self,
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
        self,
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


class TesParsingStrategyVersion6(TesParsingStrategy):
    """
    Strategy for parsing TES files prior to version 6.
    """

    def parse_vs_for_codes(self, vs: dict, return_as_vs: bool = False):
        """
        Parsing method for TES files in versions prior to version 6.
        """
        codes = set()
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
                    if return_as_vs:
                        codes.add(inc)
                    else:
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

    def parse_vs_for_codes(self, vs: dict, return_as_vs: bool = False):
        """
        Parsing method for TES files in versions after to version 7.
        """
        result = set()
        expansion = vs.get("expansion")

        if not expansion:
            return result

        source_name = parse_valueset_source_name(vs)
        source_url = vs.get("url")
        if not source_url:
            return result

        for inc in expansion.get("contains", []):
            system = inc.get("system")
            if not system:
                continue

            code = inc.get("code")
            if code:
                if return_as_vs:
                    result.add(inc)
                else:
                    result.add(
                        FhirCodeInfo(
                            system_url=system,
                            code=code,
                            display=inc.get("display"),
                            source_url=source_url,
                            source_name=source_name,
                        )
                    )

        return result


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

    @property
    def all_vs_map(self) -> dict:
        """Parsing strategy for code context."""
        return self.all_vs_map

    @parsing_strategy.setter
    def parsing_strategy(self, strategy: TesParsingStrategy) -> None:
        self._parsing_strategy = strategy

    def determine_parsing_strategy(self, vs: dict) -> None:
        """Function that reads the version property of the valueset and determines the appropriate parsing strategy."""
        version_string = vs.get("version")

        if not version_string:
            # this shouldn't ever happen since the initial file-load in checks
            # for version, but just in case it's undefined somehow, fallback to
            # default, pre-6 parsing strategy.
            self._parsing_strategy = TesParsingStrategyVersion6()
            return

        semver_formatted_version = get_tes_version(
            version_string=version_string, regex=SEMVER_VERSION_REGEX
        )

        if semver_formatted_version:
            if semver_is_less_or_equal(semver_formatted_version, "6.0.0"):
                self._parsing_strategy = TesParsingStrategyVersion6()
            else:
                self._parsing_strategy = TesParsingStrategyVersion7()

        datetime_formated_version = get_tes_version(
            version_string=version_string, regex=DATETIME_VERSION_REGEX
        )

        if datetime_formated_version:
            if datetime_formated_version <= VERSION_SIX_CUTOFF_DATETIME:
                self._parsing_strategy = TesParsingStrategyVersion6()

            else:
                self._parsing_strategy = TesParsingStrategyVersion7()

    def extract_codes_from_vs(self, vs: dict, return_as_vs=False) -> set[FhirCodeInfo]:
        """
        Extracts all (system, code, display) tuples from a ValueSet's compose section.
        """
        self.determine_parsing_strategy(vs)
        return self._parsing_strategy.parse_vs_for_codes(vs, return_as_vs)

    def get_child_rsg_valuesets(
        self,
        parent: dict,
        all_vs_map: dict[tuple[str, str], dict],
    ) -> list[dict]:
        """
        Passthrough function that determines the extraction parsing strategy and runs the get for child RSGs.
        """
        self.determine_parsing_strategy(parent)
        return self._parsing_strategy.get_child_rsg_valuesets(
            parent=parent, all_vs_map=all_vs_map
        )

    def get_sibling_context_valuesets(
        self,
        parent: dict,
        all_vs_map: dict[tuple[str, str], dict],
    ) -> list[VsDict]:
        """
        Passthrough function that determines the extraction parsing strategy and runs the get for sibling context ACGs.
        """
        self.determine_parsing_strategy(parent)
        return self._parsing_strategy.get_sibling_context_valuesets(
            parent=parent, all_vs_map=all_vs_map
        )


# intialize extractor with default parsing strategy of version 6
code_extractor = CodeExtractionContext(TesParsingStrategyVersion6())
