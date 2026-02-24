import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Literal

from fhir.resources.valueset import ValueSet

# configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# to check against specific conditions then pass them to this list like ["covid-19", "influenza"]
TARGET_CONDITIONS: list[str] = []
DATA_DIR = Path(__file__).parent.parent / "data" / "source-tes-groupers"

# type aliases
type SimpleCode = tuple[str, str]
type MatchStatus = Literal["match", "mismatch"]


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

        # eagerly calculate codes on initialization
        self.all_composed_codes: set[SimpleCode] = self._calculate_all_composed_codes()
        self.expansion_codes: set[SimpleCode] = get_expansion_codes(self.vs)

    def _calculate_all_composed_codes(self) -> set[SimpleCode]:
        """
        Resolves all codes by following the parent ValueSet's compose references.

        This follows each compose.include[].valueSet reference one level deep,
        resolving the target from the loaded dictionary and extracting its inline
        codes. This is the local equivalent of what the TES server computes for
        the expansion block, and serves as the ground truth for validation.
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

                if child_vs := self.all_valuesets.get((url, version)):
                    if is_additional_context_grouper(child_vs):
                        self.has_additional_context = True
                    codes.update(get_codes_from_compose(child_vs))
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
            for coding in context.valueCodeableConcept.coding:
                if coding.code == "additional-context-grouper":
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


def print_validation_report(
    v3: ConditionVersion, v4: ConditionVersion
) -> MatchStatus | None:
    """
    Prints a human-readable comparison of two condition versions and returns the v4 expansion match status.

    Returns 'match' or 'mismatch' if v4 has an expansion block, or None if
    there is no expansion to validate against.
    """

    v3_codes = v3.all_composed_codes
    v4_codes = v4.all_composed_codes
    added = v4_codes - v3_codes
    dropped = v3_codes - v4_codes
    v4_match_status: MatchStatus | None = None

    print(f"\n--- Validation Report for [{v4.name if v4.vs else v3.name}] ---")

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
            return "match" if is_match else "mismatch"
        else:
            print("  🔎 Assumption Check: N/A (No expansion provided).")
            return None

    print_version_details(v3, "Old Version")
    v4_match_status = print_version_details(v4, "New Version")

    print("\n🔀 Code Changes (Informational):")
    print(f"  ➖ Dropped since {v3.version}: {len(dropped)} codes")
    if dropped:
        print(f"    (e.g., {list(dropped)[:3]})")
    print(f"  ➕ Added in {v4.version}: {len(added)} codes")
    if added:
        print(f"    (e.g., {list(added)[:3]})")
    print("=" * 40)

    return v4_match_status


def main() -> None:
    """
    Main script execution.

    Loads all ValueSets, filters for target conditions, and runs a validation
    report comparing v3.0.0 and v4.0.0 of each to verify that the v4.0.0
    expansion block accurately represents the full set of codes from all
    referenced child ValueSets.
    """

    logger.info("Starting ValueSet validation process...")
    all_vs = load_all_valuesets(DATA_DIR)
    parents_by_condition = get_condition_parents_by_version(all_vs)

    conditions_to_process = get_filtered_conditions(
        parents_by_condition, TARGET_CONDITIONS
    )
    logger.info(f"Processing {len(conditions_to_process)} conditions...")

    summary: dict[str, int] = {
        "match": 0,
        "mismatch": 0,
        "no_v4_expansion": 0,
        "no_v4": 0,
    }

    for name, vs_by_ver in sorted(conditions_to_process.items()):
        logger.info(f"Processing condition: {name}")
        v3 = ConditionVersion(vs_by_ver.get("3.0.0"), all_vs)
        v4 = ConditionVersion(vs_by_ver.get("4.0.0"), all_vs)

        status = print_validation_report(v3, v4)
        if status:
            summary[status] += 1
        elif v4.vs is None:
            summary["no_v4"] += 1
        elif not v4.vs.expansion:
            summary["no_v4_expansion"] += 1

    # final summary report
    total = len(conditions_to_process)
    print("\n\n" + "=" * 20 + " FINAL SUMMARY " + "=" * 20)
    print(f"Total Conditions Processed: {total}")
    print(f"  ✅ Matches: {summary['match']}")
    print(f"  ❌ Mismatches: {summary['mismatch']}")
    if summary["no_v4_expansion"] > 0:
        print(f"  🚧 No v4.0.0 Expansion to Check: {summary['no_v4_expansion']}")
    if summary["no_v4"] > 0:
        print(f"  🚧 No v4.0.0 ValueSet Found: {summary['no_v4']}")
    print("=" * 55)

    logger.info("Validation process complete.")


if __name__ == "__main__":
    main()
