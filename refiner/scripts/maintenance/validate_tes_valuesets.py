import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from fhir.resources.valueset import ValueSet

# configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# to check against specific conditions then pass them to this list like ["covid-19", "influenza"]
TARGET_CONDITIONS: list[str] = []
DATA_DIR = Path(__file__).parent.parent / "data" / "source-tes-groupers"

COVERAGE_LEVEL_URL = (
    "http://hl7.org/fhir/uv/crmi/StructureDefinition/crmi-curationCoverageLevel"
)

# type aliases
type SimpleCode = tuple[str, str]
type MatchStatus = Literal["match", "mismatch"]


@dataclass
class CoverageLevel:
    """
    Parsed representation of the crmi-curationCoverageLevel extension on a condition grouper ValueSet.

    Fields:
        level: The coverage level code (e.g. "complete", "partial").
        reason: The markdown reason text, expected when level is "partial".
        date: The dateTime string, expected when level is "complete".
    """

    level: str
    reason: str | None = None
    date: str | None = None


@dataclass
class ChildGrouperInfo:
    """
    Tracks the resolution status and metadata of a single child ValueSet referenced from a condition grouper's compose block.
    """

    ref: str
    url: str
    version: str
    resolved: bool
    is_additional_context: bool = False
    name: str | None = None
    code_count: int = 0


@dataclass
class GrouperResolutionSummary:
    """
    Aggregated resolution summary for a condition version's child grouper references.
    """

    rsg_children: list[ChildGrouperInfo] = field(default_factory=list)
    additional_context_children: list[ChildGrouperInfo] = field(default_factory=list)
    unresolved_refs: list[ChildGrouperInfo] = field(default_factory=list)

    @property
    def total_referenced(self) -> int:
        """
        Returns a count of all references in the compose.includes for the condition grouper.

        This includes all of the reporting specification groupers and additional context groupers.
        """

        return (
            len(self.rsg_children)
            + len(self.additional_context_children)
            + len(self.unresolved_refs)
        )

    @property
    def has_acgs(self) -> bool:
        """
        Returns True/False if a condition references an additional context grouper in its compose.includes.
        """

        return len(self.additional_context_children) > 0


class ConditionVersion:
    """
    Represents a single version of a condition, holding its ValueSet and derived code sets for analysis.
    """

    def __init__(
        self,
        valueset: ValueSet | None,
        all_valuesets: dict[tuple[str, str], ValueSet],
    ):
        """
        Initializes the ConditionVersion and eagerly calculates all relevant code sets.
        """

        self.vs = valueset
        self.all_valuesets = all_valuesets
        self.has_additional_context = False

        # eagerly calculate codes and track child grouper resolution
        self.grouper_resolution = GrouperResolutionSummary()
        self.all_composed_codes: set[SimpleCode] = self._calculate_all_composed_codes()
        self.expansion_codes: set[SimpleCode] = get_expansion_codes(self.vs)

        # parse coverage level extension (condition grouper level only)
        self.coverage: CoverageLevel | None = _parse_coverage_level(self.vs)

    def _calculate_all_composed_codes(self) -> set[SimpleCode]:
        """
        Resolves all codes by following the parent ValueSet's compose references.

        This follows each compose.include[].valueSet reference one level deep,
        resolving the target from the loaded dictionary and extracting its inline
        codes. This is the local equivalent of what the TES server computes for
        the expansion block, and serves as the ground truth for validation.

        Also populates self.grouper_resolution with per-child tracking info.
        """

        if not self.vs or not self.vs.compose:
            return set()

        codes: set[SimpleCode] = set()
        if not self.vs.compose.include:
            return codes

        for include_group in self.vs.compose.include:
            if not include_group.valueSet:
                continue
            for vs_ref in include_group.valueSet:
                url, sep, version = str(vs_ref).partition("|")
                if not sep:
                    logger.warning(
                        f"No version in ValueSet reference '{vs_ref}' in {self.name}"
                    )
                    continue

                child_vs = self.all_valuesets.get((url, version))

                if child_vs is None:
                    self.grouper_resolution.unresolved_refs.append(
                        ChildGrouperInfo(
                            ref=str(vs_ref),
                            url=url,
                            version=version,
                            resolved=False,
                        )
                    )
                    continue

                child_codes = get_codes_from_compose(child_vs)
                codes.update(child_codes)
                is_acg = is_additional_context_grouper(child_vs)

                if is_acg:
                    self.has_additional_context = True

                info = ChildGrouperInfo(
                    ref=str(vs_ref),
                    url=url,
                    version=version,
                    resolved=True,
                    is_additional_context=is_acg,
                    name=child_vs.title or child_vs.name,
                    code_count=len(child_codes),
                )

                if is_acg:
                    self.grouper_resolution.additional_context_children.append(info)
                else:
                    self.grouper_resolution.rsg_children.append(info)

        return codes

    @property
    def name(self) -> str:
        """
        The display name of the condition.
        """

        if not self.vs:
            return "N/A"
        return self.vs.title or self.vs.name or "N/A"

    @property
    def version(self) -> str:
        """
        The version of the condition.
        """

        if not self.vs:
            return "N/A"
        return self.vs.version or "N/A"

    @property
    def expansion_matches_composition(self) -> bool:
        """
        Checks if the pre-calculated expansion matches the composed codes.
        """

        if not self.vs or not self.vs.expansion:
            return False
        return self.expansion_codes == self.all_composed_codes


def _parse_coverage_level(vs: ValueSet | None) -> CoverageLevel | None:
    """
    Extracts the crmi-curationCoverageLevel extension from a condition grouper ValueSet, if present.

    Coverage level is only declared at the condition grouper level, not on
    individual child ValueSets (RSG or ACG).

    The extension is complex (has nested sub-extensions rather than a direct value).
    Expected sub-extensions by url:
        - "level": valueCodeableConcept with a single coding
        - "levelReason": valueMarkdown (expected when level is "partial")
        - "dateTime": valueDateTime (expected when level is "complete")
    """

    if not vs or not vs.extension:
        return None

    for ext in vs.extension:
        if ext.url != COVERAGE_LEVEL_URL:
            continue

        # this is a complex extension; its data lives in nested sub-extensions
        if not ext.extension:
            logger.warning(
                f"Found curationCoverageLevel extension with no sub-extensions "
                f"on {vs.title or vs.url}"
            )
            return None

        level: str | None = None
        reason: str | None = None
        date: str | None = None

        for sub_ext in ext.extension:
            match sub_ext.url:
                case "level":
                    if (
                        sub_ext.valueCodeableConcept
                        and sub_ext.valueCodeableConcept.coding
                    ):
                        level = sub_ext.valueCodeableConcept.coding[0].code
                case "levelReason":
                    reason = sub_ext.valueMarkdown
                case "dateTime":
                    date = sub_ext.valueDateTime
                case _:
                    logger.warning(
                        f"Unexpected sub-extension url '{sub_ext.url}' in "
                        f"curationCoverageLevel on {vs.title or vs.url}"
                    )

        if level is None:
            logger.warning(
                f"curationCoverageLevel extension present but 'level' "
                f"sub-extension missing on {vs.title or vs.url}"
            )
            return None

        return CoverageLevel(level=level, reason=reason, date=date)

    return None


def load_all_valuesets(data_dir: Path) -> dict[tuple[str, str], ValueSet]:
    """
    Loads all ValueSet resources from JSON files in the specified directory.

    Supports both the custom 'valuesets' list format used by the fetch pipeline
    and Bundle-like 'entry' formats.
    """

    all_valuesets: dict[tuple[str, str], ValueSet] = {}
    for file in data_dir.glob("*.json"):
        if file.name == "manifest.json":
            continue
        with open(file, encoding="utf-8") as f:
            data = json.load(f)

        vs_data_list = data.get("valuesets", []) + [
            entry.get("resource")
            for entry in data.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "ValueSet"
        ]

        for vs_dict in vs_data_list:
            if not vs_dict:
                continue
            try:
                vs_obj = ValueSet.model_validate(vs_dict)
                if vs_obj.url and vs_obj.version:
                    all_valuesets[(vs_obj.url, vs_obj.version)] = vs_obj
            except Exception as e:
                logger.warning(f"Failed to parse ValueSet in {file.name}: {e}")
    logger.info(f"Loaded {len(all_valuesets)} unique ValueSets from {data_dir}")
    return all_valuesets


def is_condition_grouper(vs: ValueSet) -> bool:
    """
    Checks if a ValueSet is a 'ConditionGrouper' via its metadata profile.
    """

    profiles = getattr(getattr(vs, "meta", None), "profile", []) or []
    return bool(any("conditiongroupervalueset" in str(p) for p in profiles))


def is_additional_context_grouper(vs: ValueSet) -> bool:
    """
    Checks if a ValueSet is an 'Additional Context' grouper using its useContext coding.

    This mirrors the classification logic in the fetch pipeline
    (fetch_api_data.py, Rule 3) to ensure consistency between how data
    is categorized at fetch time and how it is identified during validation.
    """

    if not vs.useContext:
        return False
    for context in vs.useContext:
        if context.valueCodeableConcept and context.valueCodeableConcept.coding:
            if any(
                coding.code == "additional-context-grouper"
                for coding in context.valueCodeableConcept.coding
            ):
                return True
    return False


def get_codes_from_compose(vs: ValueSet | None) -> set[SimpleCode]:
    """
    Extracts codes from the 'compose' section of a ValueSet.
    """

    if not vs or not vs.compose:
        return set()
    codes: set[SimpleCode] = set()
    for inc in vs.compose.include or []:
        if inc.system and inc.concept:
            for concept in inc.concept:
                if concept.code:
                    codes.add((inc.system, concept.code))
    return codes


def get_expansion_codes(vs: ValueSet | None) -> set[SimpleCode]:
    """
    Extracts codes from the 'expansion' section of a ValueSet.
    """

    if not vs or not vs.expansion or not vs.expansion.contains:
        return set()
    codes: set[SimpleCode] = set()
    for c in vs.expansion.contains:
        if c.system and c.code:
            codes.add((c.system, c.code))
    return codes


def get_condition_parents_by_version(
    all_vs: dict[tuple[str, str], ValueSet],
) -> dict[str, dict[str, ValueSet]]:
    """
    Groups all ConditionGrouper ValueSets by condition name, then by version.
    """

    parents: defaultdict[str, dict[str, ValueSet]] = defaultdict(dict)
    for vs in all_vs.values():
        if is_condition_grouper(vs):
            if cond_name := (vs.title or vs.name):
                if vs.version:
                    parents[cond_name][vs.version] = vs
    return dict(parents)


def get_filtered_conditions(
    parents_by_condition: dict[str, dict[str, ValueSet]],
    targets: list[str],
) -> dict[str, dict[str, ValueSet]]:
    """
    Filters conditions by target names. Returns all conditions if no targets match or none are specified.
    """

    if not targets:
        return parents_by_condition

    filtered = {
        name: versions
        for name, versions in parents_by_condition.items()
        if name.lower() in (t.lower() for t in targets)
    }
    if not filtered:
        logger.warning("No target conditions matched. Processing all conditions.")
        return parents_by_condition
    return filtered


def print_version_details(ver: ConditionVersion, label: str) -> MatchStatus | None:
    """
    Prints the validation details for a single version and returns its match status if an expansion is present.
    """

    print(f"📋 {label} (Version: {ver.version})")
    if not ver.vs:
        print("  (Version not found)")
        return None

    print(f"  📊 Composed code count: {len(ver.all_composed_codes)}")
    if not ver.has_additional_context:
        print("  💬 No Additional Context codes found.")

    print(f"  📦 Expansion code count: {len(ver.expansion_codes)}")

    if ver.vs.expansion:
        is_match = ver.expansion_matches_composition
        match_label = "✅ Matches" if is_match else "❌ Mismatch"
        print(f"  🔎 Assumption Check: Expansion {match_label} composition.")
    else:
        print("  🔎 Assumption Check: N/A (No expansion provided).")

    # coverage level (condition grouper level only)
    if ver.coverage:
        print(f"  🏷️  Coverage Level: {ver.coverage.level}")
        if ver.coverage.reason:
            print(f"     Reason: {ver.coverage.reason}")
        if ver.coverage.date:
            print(f"     Date: {ver.coverage.date}")
    else:
        print("  🏷️  Coverage Level: (not present)")

    # child grouper resolution detail
    res = ver.grouper_resolution
    if res.total_referenced > 0:
        print(f"  📂 Child Grouper References: {res.total_referenced} total")

        if res.rsg_children:
            print(f"     RSG children: {len(res.rsg_children)} resolved")

        if res.additional_context_children:
            print(
                f"     Additional Context children: "
                f"{len(res.additional_context_children)} resolved"
            )
            for acg in res.additional_context_children:
                print(f"       📦 {acg.name or acg.url} — {acg.code_count} codes")

        if res.unresolved_refs:
            print(f"     ❌ Unresolved references: {len(res.unresolved_refs)}")
            for unresolved in res.unresolved_refs:
                print(f"       ❌ {unresolved.url} | {unresolved.version}")

    if ver.vs.expansion:
        return "match" if ver.expansion_matches_composition else "mismatch"
    return None


def print_pairwise_diff(old: ConditionVersion, new: ConditionVersion) -> None:
    """
    Prints a code diff between two adjacent versions.
    """

    old_codes = old.all_composed_codes
    new_codes = new.all_composed_codes
    added = new_codes - old_codes
    dropped = old_codes - new_codes

    print(f"\n  🔀 Code Changes ({old.version} → {new.version}):")
    print(f"    ➖ Dropped: {len(dropped)} codes")
    if dropped:
        print(f"      (e.g., {list(dropped)[:3]})")
    print(f"    ➕ Added: {len(added)} codes")
    if added:
        print(f"      (e.g., {list(added)[:3]})")


def print_validation_report(
    versions: list[ConditionVersion],
) -> MatchStatus | None:
    """
    Prints a human-readable report for all available versions of a condition and returns the newest version's expansion match status.

    Compares each adjacent pair of versions and reports coverage level info
    for every version.
    """

    # use the last available version's name as the condition label
    condition_name = next((v.name for v in reversed(versions) if v.vs), "N/A")
    print(f"\n--- Validation Report for [{condition_name}] ---")

    latest_match_status: MatchStatus | None = None

    # NOTE:
    # for "oldest" we're starting with 3.0.0 rather than going back to 1.0.0 or 2.0.0
    for idx, ver in enumerate(versions):
        label = (
            "Oldest version checked"
            if idx == 0
            else (
                "Newest version checked"
                if idx == len(versions) - 1
                else f"Version {idx + 1}"
            )
        )
        status = print_version_details(ver, label)

        # always keep the most recent non-None status
        if status is not None:
            latest_match_status = status

        # pairwise diff against the previous version
        if idx > 0:
            prev = versions[idx - 1]
            if prev.vs and ver.vs:
                print_pairwise_diff(prev, ver)

    print("=" * 40)
    return latest_match_status


def print_coverage_summary(
    coverage_summary: dict[str, int],
    not_present_with_acgs: int,
    not_present_without_acgs: int,
) -> None:
    """
    Prints the final coverage level distribution.
    """

    print("\n📊 Coverage Level Distribution (newest version per condition):")
    for level, count in sorted(coverage_summary.items()):
        if level == "not_present":
            print(f"  🔇 Not present: {count}")
            print(f"       With ACGs: {not_present_with_acgs}")
            print(f"       Without ACGs: {not_present_without_acgs}")
        elif level == "complete":
            print(f"  ✅ Complete: {count}")
        elif level == "partial":
            print(f"  🔶 Partial: {count}")
        else:
            print(f"  ⚠️  Unexpected value '{level}': {count}")


def print_invariant_violations(violations: list[str]) -> None:
    """
    Prints any coverage level invariant violations.

    Expected invariants:
        - "partial" level → reason must be present
        - "complete" level → reason must be absent
    """

    if not violations:
        print("✅ No coverage level invariant violations detected.")
        return

    print(f"⚠️  Coverage Level Invariant Violations ({len(violations)}):")
    for v in violations:
        print(f"  - {v}")


def check_coverage_invariants(name: str, ver: ConditionVersion) -> list[str]:
    """
    Checks the coverage level invariants for a single ConditionVersion.

    Returns a list of violation descriptions (empty if clean).
    """

    violations: list[str] = []
    cov = ver.coverage
    if cov is None:
        return violations

    if cov.level == "partial" and not cov.reason:
        violations.append(
            f"[{name}] v{ver.version}: level is 'partial' but no reason provided"
        )
    if cov.level == "complete" and cov.reason:
        violations.append(
            f"[{name}] v{ver.version}: level is 'complete' but reason is present "
            f"('{cov.reason[:80]}...')"
        )

    return violations


def print_acg_summary(
    total_acgs: int,
    conditions_with_unresolved: list[str],
) -> None:
    """
    Prints the aggregate ACG resolution summary across all conditions.
    """

    if total_acgs > 0:
        print(f"\n📂 Total Additional Context Groupers (newest version): {total_acgs}")

    if conditions_with_unresolved:
        print(
            f"\n⚠️  Conditions with unresolved child references: "
            f"{len(conditions_with_unresolved)}"
        )
        for name in conditions_with_unresolved:
            print(f"  - {name}")


# the versions we care about, in order
VERSIONS_TO_CHECK = ["3.0.0", "4.0.0", "5.0.0"]


def main() -> None:
    """
    Main script execution.

    Loads all ValueSets, filters for target conditions, and runs a validation
    report comparing all available versions pairwise. Also validates the
    crmi-curationCoverageLevel extension data for invariant correctness and
    prints a distribution summary with ACG presence breakdown.
    """

    logger.info("Starting ValueSet validation process...")
    all_vs = load_all_valuesets(DATA_DIR)
    parents_by_condition = get_condition_parents_by_version(all_vs)

    conditions_to_process = get_filtered_conditions(
        parents_by_condition, TARGET_CONDITIONS
    )
    logger.info(f"Processing {len(conditions_to_process)} conditions...")

    expansion_summary: dict[str, int] = {
        "match": 0,
        "mismatch": 0,
        "no_newest_expansion": 0,
        "no_newest_vs": 0,
    }

    coverage_summary: dict[str, int] = defaultdict(int)
    all_invariant_violations: list[str] = []
    total_acgs = 0
    not_present_with_acgs = 0
    not_present_without_acgs = 0
    conditions_with_unresolved: list[str] = []

    for name, vs_by_ver in sorted(conditions_to_process.items()):
        logger.info(f"Processing condition: {name}")

        versions = [
            ConditionVersion(vs_by_ver.get(v), all_vs) for v in VERSIONS_TO_CHECK
        ]

        # filter to versions that actually exist
        present_versions = [v for v in versions if v.vs is not None]

        if not present_versions:
            logger.warning(f"No versions found for {name}, skipping.")
            expansion_summary["no_newest_vs"] += 1
            coverage_summary["not_present"] += 1
            not_present_without_acgs += 1
            continue

        status = print_validation_report(present_versions)

        if status:
            expansion_summary[status] += 1
        else:
            newest = present_versions[-1]
            if newest.vs and not newest.vs.expansion:
                expansion_summary["no_newest_expansion"] += 1
            else:
                expansion_summary["no_newest_vs"] += 1

        # coverage level tracking: use the newest present version
        newest = present_versions[-1]
        has_acgs = newest.grouper_resolution.has_acgs

        if newest.coverage:
            coverage_summary[newest.coverage.level] += 1
        else:
            coverage_summary["not_present"] += 1
            if has_acgs:
                not_present_with_acgs += 1
            else:
                not_present_without_acgs += 1

        # invariant checks across all present versions
        for ver in present_versions:
            all_invariant_violations.extend(check_coverage_invariants(name, ver))

        # count total ACGs from newest version
        total_acgs += len(newest.grouper_resolution.additional_context_children)

        if newest.grouper_resolution.unresolved_refs:
            conditions_with_unresolved.append(f"{name} (v{newest.version})")

    # final summary report
    total = len(conditions_to_process)
    print("\n\n" + "=" * 20 + " FINAL SUMMARY " + "=" * 20)
    print(f"Total Conditions Processed: {total}")
    print(f"  ✅ Expansion Matches: {expansion_summary['match']}")
    print(f"  ❌ Expansion Mismatches: {expansion_summary['mismatch']}")
    if expansion_summary["no_newest_expansion"] > 0:
        print(
            f"  🚧 No Newest Expansion to Check: {expansion_summary['no_newest_expansion']}"
        )
    if expansion_summary["no_newest_vs"] > 0:
        print(f"  🚧 No Newest ValueSet Found: {expansion_summary['no_newest_vs']}")

    print_coverage_summary(
        dict(coverage_summary), not_present_with_acgs, not_present_without_acgs
    )
    print()
    print_invariant_violations(all_invariant_violations)
    print_acg_summary(total_acgs, conditions_with_unresolved)
    print("=" * 55)

    logger.info("Validation process complete.")


if __name__ == "__main__":
    main()
