import json
import logging
from pathlib import Path

from fhir.resources.valueset import ValueSet

# configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_CONDITIONS: list[str] = ["COVID-19", "Influenza"]
DATA_DIR = Path(__file__).parent.parent / "data" / "source-tes-groupers"

# type alias
# a simple tuple for this script's purpose: (system_url, code)
type SimpleCode = tuple[str, str]


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

        # eagerly calculate codes on initialization
        self.child_codes: set[SimpleCode] = self._calculate_child_codes()
        self.sibling_codes: set[SimpleCode] = self._calculate_sibling_codes()
        self.expansion_codes: set[SimpleCode] = get_expansion_codes(self.vs)

    @property
    def name(self) -> str | None:
        """
        The display name of the condition, or 'N/A' if not available.
        """

        return self.vs.title or self.vs.name if self.vs else "N/A"

    @property
    def version(self) -> str | None:
        """
        The version of the condition, or 'N/A' if not available.
        """

        return self.vs.version if self.vs else "N/A"

    @property
    def all_composed_codes(self) -> set[SimpleCode]:
        """
        All codes derived from combining child and sibling ValueSets.
        """

        return self.child_codes | self.sibling_codes

    @property
    def context_only_codes(self) -> set[SimpleCode]:
        """
        Codes that exist only in sibling 'Additional Context' ValueSets.
        """

        return self.sibling_codes - self.child_codes

    @property
    def expansion_matches_composition(self) -> bool:
        """
        Checks if the pre-calculated expansion matches the composed codes.
        """

        if not self.vs or not self.expansion_codes:
            return False
        return self.expansion_codes == self.all_composed_codes

    def _calculate_child_codes(self) -> set[SimpleCode]:
        """
        Calculates the set of codes from all child RSG ValueSets.
        """

        if not self.vs:
            return set()
        codes: set[SimpleCode] = set()
        for child in get_child_rsg_valuesets(self.vs, self.all_valuesets):
            codes.update(get_codes_from_compose(child))
        return codes

    def _calculate_sibling_codes(self) -> set[SimpleCode]:
        """
        Calculates the set of codes from all sibling 'additional context' ValueSets.
        """

        if not self.vs:
            return set()
        codes: set[SimpleCode] = set()
        for sib in get_sibling_context_valuesets(self.vs, self.all_valuesets):
            codes.update(get_codes_from_compose(sib))
        return codes


def load_all_valuesets(data_dir: Path) -> dict[tuple[str, str], ValueSet]:
    """
    Loads all ValueSet resources from JSON files in the specified directory.
    """

    all_valuesets: dict[tuple[str, str], ValueSet] = {}
    for file in data_dir.glob("*.json"):
        if file.name == "manifest.json":
            continue
        with open(file, encoding="utf-8") as f:
            data = json.load(f)

        valuesets_data = data.get("valuesets", []) or [
            entry.get("resource")
            for entry in data.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "ValueSet"
        ]
        for vs_dict in valuesets_data:
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
    return bool(any("conditiongroupervalueset" in str(prof) for prof in profiles))


def is_reporting_spec_grouper(vs: ValueSet) -> bool:
    """
    Checks if a ValueSet is a 'ReportingSpecGrouper' by its URL.
    """

    return bool(vs.url and "rs-grouper" in vs.url.lower())


def is_additional_context_grouper(vs: ValueSet) -> bool:
    """
    Checks if a ValueSet is for 'Additional Context' by its name or title.
    """

    name, title = (vs.name or "").lower(), (vs.title or "").lower()
    return "additional" in name or "additional" in title


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


def get_child_rsg_valuesets(
    parent: ValueSet, all_valuesets: dict[tuple[str, str], ValueSet]
) -> list[ValueSet]:
    """
    Finds all 'ReportingSpecGrouper' children of a parent ValueSet.
    """

    children: list[ValueSet] = []
    if parent.compose:
        for inc in parent.compose.include or []:
            for ref in inc.valueSet or []:
                url, sep, version = str(ref).partition("|")
                if sep and (child_vs := all_valuesets.get((url, version))):
                    if is_reporting_spec_grouper(child_vs):
                        children.append(child_vs)
    return children


def get_sibling_context_valuesets(
    parent: ValueSet, all_valuesets: dict[tuple[str, str], ValueSet]
) -> list[ValueSet]:
    """
    Finds sibling 'Additional Context' ValueSets by matching name and version.
    """

    siblings: list[ValueSet] = []
    parent_name_norm = (parent.name or "").lower().replace("_", "")
    for vs in all_valuesets.values():
        if (
            is_additional_context_grouper(vs)
            and vs.version == parent.version
            and vs.url != parent.url
            and parent_name_norm in (vs.name or "").lower().replace("_", "")
        ):
            siblings.append(vs)
    return siblings


def get_condition_parents_by_version(
    all_vs: dict[tuple[str, str], ValueSet],
) -> dict[str, dict[str, ValueSet]]:
    """
    Groups all 'ConditionGrouper' ValueSets by name and then by version.
    """

    parents: dict[str, dict[str, ValueSet]] = {}
    for vs in all_vs.values():
        if is_condition_grouper(vs):
            if cond_name := (vs.title or vs.name):
                # ensure that vs.version is not None before using it as a key
                if vs.version:
                    if cond_name not in parents:
                        parents[cond_name] = {}
                    parents[cond_name][vs.version] = vs
    return parents


def print_validation_report(v3: ConditionVersion, v4: ConditionVersion):
    """
    Generates and prints a human-readable report comparing two condition versions.
    """

    v3_codes = v3.all_composed_codes
    v4_codes = v4.all_composed_codes
    added = v4_codes - v3_codes
    dropped = v3_codes - v4_codes

    print(f"\n--- Validation Report for [{v4.name}] ---")

    def print_version_details(ver: ConditionVersion, label: str):
        """
        Prints the validation details for a single version.
        """

        print(f"🔷 {label} (Version: {ver.version})")
        if not ver.vs:
            print("  (Version not found)")
            return
        print(f"  🔢 Composed code count: {len(ver.all_composed_codes)}")
        print(f"  🟫 Codes unique to Additional Context: {len(ver.context_only_codes)}")
        print(f"  📦 Expansion code count: {len(ver.expansion_codes)}")
        match_status = (
            "✅ Matches" if ver.expansion_matches_composition else "❌ Mismatch"
        )
        print(f"  ▶️ Assumption Check: Expansion {match_status} composition.")

    print_version_details(v3, "Old Version")
    print_version_details(v4, "New Version")

    print("\n🔄 Code Changes (Informational):")
    print(f"  ➖ Dropped since {v3.version}: {len(dropped)} codes")
    if dropped:
        print(f"    (e.g., {list(dropped)[:3]})")
    print(f"  ➕ Added in {v4.version}: {len(added)} codes")
    if added:
        print(f"    (e.g., {list(added)[:3]})")
    print("=" * 40)


def main() -> None:
    """
    Main script execution.

    Loads all ValueSets, filters for target conditions, and runs a validation
    report comparing v3.0.0 and v4.0.0 of each to verify assumptions
    about code composition and expansion.
    """

    logger.info("Starting ValueSet validation process...")
    all_vs = load_all_valuesets(DATA_DIR)
    parents_by_condition = get_condition_parents_by_version(all_vs)

    logger.info(f"Filtering for target conditions: {TARGET_CONDITIONS}")
    filtered_conditions = {
        name: versions
        for name, versions in parents_by_condition.items()
        if any(targ.lower() in name.lower() for targ in TARGET_CONDITIONS)
    }

    if not filtered_conditions:
        logger.warning("No target conditions found. Exiting.")
        return

    for name, vs_by_ver in filtered_conditions.items():
        logger.info(f"Processing condition: {name}")
        v3 = ConditionVersion(vs_by_ver.get("3.0.0"), all_vs)
        v4 = ConditionVersion(vs_by_ver.get("4.0.0"), all_vs)
        print_validation_report(v3, v4)

    logger.info("Validation process complete.")


if __name__ == "__main__":
    main()
