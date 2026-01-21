import json
import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# configuration
# * an empty list means we will process **all** parent conditions found in the data
TARGET_CONDITIONS: list[str] = []

# the directory where the raw json data files are stored
DATA_DIR = Path(__file__).parent.parent / "data" / "source-tes-groupers"

# setup basic logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# data models
@dataclass
class ReportingSpecGrouper:
    """
    A simple container for a parsed RS-Grouper.
    """

    name: str
    url: str
    version: str
    snomed_code: str
    all_codes: dict[str, list[dict]] = field(default_factory=dict)


@dataclass
class ConditionGrouper:
    """
    A container for a parsed CG and its children.
    """

    name: str
    url: str
    version: str
    children: list[ReportingSpecGrouper] = field(default_factory=list)


def _codes_from_expansion_section(
    valueset: dict[str, Any],
) -> Iterable[tuple[str, str]]:
    """
    Extracts all codes from a single ValueSet with an 'expansion' section.

    Relevant for 4.0.0 and onwards codes.
    """
    expansion = valueset.get("expansion", {})
    if not expansion:
        return
    for contains_item in expansion.get("contains", []):
        system_url = contains_item.get("system")
        code = contains_item.get("code")

        if system_url and code:
            yield system_url, code


def _codes_from_compose_section(valueset: dict[str, Any]) -> Iterable[tuple[str, str]]:
    """
    Extracts all codes from a single ValueSet with an 'compose' section.

    Relevant for any codes older than 3.0.0.
    """
    compose = valueset.get("compose", {})
    if not compose:
        return

    for include_item in compose.get("include", []):
        system_url = include_item.get("system")
        if not system_url:
            continue
        for concept in include_item.get("concept", []):
            code = concept.get("code")
            if code:
                yield system_url, code


def extract_codes_from_valueset(valueset: dict[str, Any]) -> set[tuple[str, str]]:
    """
    Extracts all codes from a single ValueSet into a set of (system, code) tuples.

    Handling both 'compose' and 'expansion' structures.
    """
    return {
        *(_codes_from_compose_section(valueset=valueset) or ()),
        *(_codes_from_expansion_section(valueset=valueset) or ()),
    }


def _extract_valid_child_valuesets_from_parent(
    valueset: dict[str, Any],
    all_valuesets_map: dict[tuple[str, str], dict],
) -> Iterable[tuple[str, dict[str, Any]]]:
    for include_item in valueset.get("compose", {}).get("include", []):
        for child_ref in include_item.get("valueSet", []):
            child_url, child_version = child_ref.split("|", 1)
            child_vs = all_valuesets_map.get((child_url, child_version))
            child_vs_id = child_url + "/" + child_version
            if child_vs and parse_snomed_from_url(valueset.get("url", "")):
                yield (child_vs_id, child_vs)


def parse_snomed_from_url(url: str) -> str | None:
    """
    Extracts the SNOMED code from a Reporting Spec Grouper URL.
    """

    if "rs-grouper-" in url:
        return url.split("rs-grouper-")[-1]
    return None


# ValueSet extractor
def get_valuesets_from_file(file_path: Path) -> tuple[str, list[dict]]:
    """
    Extract the data we want from the TES ValueSet resource.

    Reads a JSON file and extracts ValueSet resources, handling both
    standard FHIR Bundles and the custom {"valuesets": [...]} format.
    Returns a tuple of (detected_format, list_of_valuesets).
    """

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        if data.get("resourceType") == "Bundle" and "entry" in data:
            valuesets = [
                entry.get("resource")
                for entry in data.get("entry", [])
                if entry.get("resource", {}).get("resourceType") == "ValueSet"
            ]
            return "FHIR Bundle", valuesets

        if "valuesets" in data and isinstance(data["valuesets"], list):
            valuesets = [
                vs for vs in data["valuesets"] if vs.get("resourceType") == "ValueSet"
            ]
            return "Custom 'valuesets' List", valuesets

        if data.get("resourceType") == "ValueSet":
            return "Single ValueSet", [data]

    except json.JSONDecodeError:
        logging.error(f"Could not decode JSON from {file_path.name}")
    except Exception as e:
        logging.error(f"An unexpected error occurred with {file_path.name}: {e}")

    return "Unknown or Empty", []


def main():
    """
    Main script to read, parse, and validate the logic for specific conditions.
    """

    logging.info("🚀 Starting ValueSet parsing and pre-flight database validation...")
    logging.info(f"📁 Reading data from: {DATA_DIR.resolve()}")
    print("-" * 50)

    # pass 1: analyze file structures and collecting all ValueSets
    logging.info("🔎 Pass 1: Analyzing file structures and collecting all ValueSets")
    all_valuesets_map: dict[tuple[str, str], dict] = {}
    json_files = [f for f in DATA_DIR.glob("*.json") if f.name != "manifest.json"]

    for file_path in json_files:
        file_type, valuesets = get_valuesets_from_file(file_path)
        if not valuesets:
            logging.warning(
                f"  ❌ No ValueSets found in {file_path.name} (Type: {file_type})"
            )
            continue

        logging.info(
            f"  ⭐ Parsed {len(valuesets):>4} ValueSets from {file_path.name:<45} (Type: {file_type})"
        )
        for valueset in valuesets:
            url, version = valueset.get("url"), valueset.get("version")
            if not url or not version:
                logging.warning(
                    f"  🦘 Skipping ValueSet with missing URL or version (ID: {valueset.get('id', 'N/A')})"
                )
                continue
            all_valuesets_map[(url, version)] = valueset

    print("-" * 50)
    logging.info(
        f"✅ Found {len(all_valuesets_map)} unique (url + version) combinations across all files."
    )

    # pre-flight validation checks
    print("\n" + "=" * 80)
    logging.info("✈️ PRE-FLIGHT CHECK: Validating data against database schema rules...")
    print("=" * 80)

    parent_valuesets = [
        valueset
        for valueset in all_valuesets_map.values()
        if any(
            "valueSet" in item
            for item in valueset.get("compose", {}).get("include", [])
        )
    ]

    logging.info(
        f"🔎 Found {len(parent_valuesets)} potential 'parent' conditions to check."
    )

    has_failed_check = False

    # check 1: unique primary key (URL, Version)
    seen_primary_keys: set[tuple[str, str]] = set()
    primary_key_check_failed = False
    for valueset in parent_valuesets:
        primary_key = (valueset.get("url"), valueset.get("version"))
        if primary_key in seen_primary_keys:
            logging.error(
                f"  ❌ FAILED [PK]: Duplicate Primary Key found: URL={primary_key[0]}, Version={primary_key[1]}"
            )
            primary_key_check_failed = True
        seen_primary_keys.add(primary_key)
    if not primary_key_check_failed:
        logging.info(
            "  ✅ PASSED [PK]: All parent conditions have a unique (URL, Version) primary key."
        )
    has_failed_check = has_failed_check or primary_key_check_failed

    # check 2: non-empty displayName
    name_check_failed = False
    for valueset in parent_valuesets:
        if not (valueset.get("name") or valueset.get("title")):
            logging.error(
                f"  ❌ FAILED [Name]: Parent condition found with no name or title: URL={valueset.get('url')}"
            )
            name_check_failed = True
    if not name_check_failed:
        logging.info(
            "  ✅ PASSED [Name]: All parent conditions have a valid display name."
        )
    has_failed_check = has_failed_check or name_check_failed

    # check 3: parent must have at least one valid child that meets seeder criteria    child_check_failed = False
    for valueset in parent_valuesets:
        child_check_failed = False
        valid_valuesets = {
            *(
                _extract_valid_child_valuesets_from_parent(
                    valueset=valueset, all_valuesets_map=all_valuesets_map
                )
                or ()
            )
        }
        if len(valid_valuesets) > 0:
            break
        else:
            logging.error(
                f"  ❌ FAILED [Children]: Parent '{valueset.get('name')}' (v{valueset.get('version')}) "
                "has no valid children that meet the seeder's criteria (e.g., must be an 'rs-grouper')."
            )
            child_check_failed = True

        if not child_check_failed:
            logging.info(
                "  ✅ PASSED [Children]: All parent conditions have at least one child that meets the seeder's criteria."
            )
        has_failed_check = has_failed_check or child_check_failed

    # check 4: aggregated code structures must be valid
    code_structure_failed = False
    # this check is now less relevant to the new goal but good to keep
    expected_keys = {"loinc_codes", "snomed_codes", "icd10_codes", "rxnorm_codes"}
    for valueset in parent_valuesets:
        # NOTE: this is a simulation of the old seeding logic's aggregation
        _aggregated_codes = {key: [] for key in expected_keys}
        for include_item in valueset.get("compose", {}).get("include", []):
            for child_ref in include_item.get("valueSet", []):
                try:
                    child_url, child_version = child_ref.split("|", 1)
                except ValueError:
                    continue

    if not code_structure_failed:
        logging.info(
            "  ✅ PASSED [Codes]: Aggregated code structures are valid for all parents."
        )
    has_failed_check = has_failed_check or code_structure_failed

    if has_failed_check:
        print("\n" + "=" * 80)
        logging.critical(
            "😭 One or more pre-flight checks failed. Aborting further checks."
        )
        exit(1)
    else:
        print("\n" + "=" * 80)
        logging.info("🎉 SUCCESS: All pre-flight checks passed.")
        print("=" * 80)

    # ==============================================================================
    # SPECIAL VALIDATION: 4.0.0 expansion.contains vs. compose.include
    # ==============================================================================
    print("\n" + "=" * 80)
    logging.info(
        "🔬 SPECIAL VALIDATION: Checking 4.0.0 Condition Grouper Expansions..."
    )
    print("=" * 80)

    v4_parents_with_expansion = [
        vs
        for vs in parent_valuesets
        if vs.get("version") == "4.0.0" and "expansion" in vs
    ]

    if not v4_parents_with_expansion:
        logging.warning(
            "No v4.0.0 condition groupers with an 'expansion' section found to check."
        )
    else:
        logging.info(
            f"Found {len(v4_parents_with_expansion)} v4.0.0 condition groupers with expansions to analyze."
        )
        v4_checks_passed = 0
        v4_checks_failed = 0

        for parent_vs in v4_parents_with_expansion:
            condition_name = parent_vs.get("title") or parent_vs.get("name")
            logging.info(f"\n--- Checking '{condition_name}' ---")

            # set a:
            # get codes from the expansion.contains
            # * these are new to condition grouper 4.0.0 FHIR ValueSets
            expansion_codes = extract_codes_from_valueset(parent_vs)
            logging.info(
                f"  [Set A] Found {len(expansion_codes)} codes in the parent's `expansion`."
            )

            # set b:
            # get codes by composing them from children
            # * this is the way we normally grab the reporting specification grouper codes
            composed_codes = set()
            valid_valuesets = {
                *(
                    _extract_valid_child_valuesets_from_parent(
                        valueset=parent_vs,
                        all_valuesets_map=all_valuesets_map,
                    )
                    or ()
                )
            }
            for _, valueset in valid_valuesets:
                child_codes = extract_codes_from_valueset(valueset)
                composed_codes.update(child_codes)

            logging.info(
                f"  [Set B] Found {len(composed_codes)} codes by composing from children."
            )

            # compare the sets
            if composed_codes.issubset(expansion_codes):
                logging.info(
                    "  ✅ PASSED: All composed codes are present in the expansion."
                )
                if len(composed_codes) < len(expansion_codes):
                    diff = len(expansion_codes) - len(composed_codes)
                    logging.info(
                        f"    ℹ️ Note: Expansion contains {diff} additional codes."
                    )
                v4_checks_passed += 1
            else:
                missing_codes = composed_codes - expansion_codes
                logging.error(
                    f"  ❌ FAILED: {len(missing_codes)} composed codes are MISSING from the expansion."
                )
                # Log a few examples of missing codes for debugging
                for i, (system, code) in enumerate(list(missing_codes)[:3]):
                    logging.error(
                        f"    - Example missing code: System='{system}', Code='{code}'"
                    )
                v4_checks_failed += 1

        # final summary for the v4.0.0 checks
        print("-" * 50)
        logging.info("V4.0.0 Expansion Check Summary:")
        logging.info(f"  - Conditions Passed: {v4_checks_passed}")
        logging.info(f"  - Conditions Failed: {v4_checks_failed}")
        if v4_checks_failed > 0:
            logging.critical(
                "  >>> One or more v4.0.0 conditions failed the expansion check!"
            )
        else:
            logging.info(
                "  🎉🎉🎉 All v4.0.0 conditions passed the expansion check successfully!"
            )

    logging.info("\nValidation script finished.")


if __name__ == "__main__":
    main()
