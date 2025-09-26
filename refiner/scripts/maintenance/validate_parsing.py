import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# configuration
# * an empty list means we will process **all** parent conditions found in the data
TARGET_CONDITIONS: list[str] = []

# the directory where the raw json data files are stored
DATA_DIR = Path(__file__).parent.parent / "data"

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


# helper functions ---
def extract_codes_from_valueset(valueset: dict[str, Any]) -> dict[str, list[dict]]:
    """
    Extracts all code types from a single ValueSet into structured lists.
    """

    codes = {
        "loinc_codes": [],
        "snomed_codes": [],
        "icd10_codes": [],
        "rxnorm_codes": [],
    }
    system_map = {
        "http://loinc.org": "loinc_codes",
        "http://snomed.info/sct": "snomed_codes",
        "http://hl7.org/fhir/sid/icd-10-cm": "icd10_codes",
        "http://www.nlm.nih.gov/research/umls/rxnorm": "rxnorm_codes",
    }
    compose = valueset.get("compose", {})
    for include_item in compose.get("include", []):
        system_url = include_item.get("system")
        code_key = system_map.get(system_url)
        if code_key and "concept" in include_item:
            for concept in include_item["concept"]:
                codes[code_key].append(
                    {"display": concept.get("display"), "code": concept.get("code")}
                )
    return codes


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

    # validation checks
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

    # check 3: parent must have at least one valid child that meets seeder criteria
    child_check_failed = False
    for valueset in parent_valuesets:
        found_valid_children = False
        for include_item in valueset.get("compose", {}).get("include", []):
            for child_ref in include_item.get("valueSet", []):
                try:
                    child_url, child_version = child_ref.split("|", 1)
                    child_vs = all_valuesets_map.get((child_url, child_version))
                    if child_vs and parse_snomed_from_url(child_vs.get("url", "")):
                        found_valid_children = True
                        break
                except ValueError:
                    continue
            if found_valid_children:
                break

        if not found_valid_children:
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
    expected_keys = {"loinc_codes", "snomed_codes", "icd10_codes", "rxnorm_codes"}
    for valueset in parent_valuesets:
        aggregated_codes = {key: [] for key in expected_keys}
        for include_item in valueset.get("compose", {}).get("include", []):
            for child_ref in include_item.get("valueSet", []):
                try:
                    child_url, child_version = child_ref.split("|", 1)
                    child_vs = all_valuesets_map.get((child_url, child_version))
                    if child_vs:
                        child_codes = extract_codes_from_valueset(child_vs)
                        for code_type, codes in child_codes.items():
                            aggregated_codes[code_type].extend(codes)
                except (ValueError, KeyError):
                    continue

        if set(aggregated_codes.keys()) != expected_keys:
            logging.error(
                f"  ❌ FAILED [Codes]: Aggregated codes dict has wrong keys for URL={valueset.get('url')}"
            )
            code_structure_failed = True
        for key, value in aggregated_codes.items():
            if not isinstance(value, list):
                logging.error(
                    f"  ❌ FAILED [Codes]: Aggregated code value for '{key}' is not a list for URL={valueset.get('url')}"
                )
                code_structure_failed = True

    if not code_structure_failed:
        logging.info(
            "  ✅ PASSED [Codes]: Aggregated code structures are valid for all parents."
        )
    has_failed_check = has_failed_check or code_structure_failed

    # final result
    if has_failed_check:
        print("\n" + "=" * 80)
        logging.critical(
            "😭 One or more pre-flight checks failed. Seeding would likely fail or result in incomplete data."
        )
        exit(1)

    print("\n" + "=" * 80)
    logging.info("🎉 SUCCESS: All pre-flight checks passed.")
    logging.info("Validation script finished.")


if __name__ == "__main__":
    main()
