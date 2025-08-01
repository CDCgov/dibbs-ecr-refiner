import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# an empty list means we will process ALL parent conditions found in the data
TARGET_CONDITIONS: list[str] = []

# the directory where the raw json data files are stored
DATA_DIR = Path(__file__).parent.parent / "data"


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
    A container for a parsed Condition Grouper and its children.
    """

    name: str
    url: str
    version: str
    children: list[ReportingSpecGrouper] = field(default_factory=list)


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


def main():
    """
    Main script to read, parse, and validate the logic for specific conditions.
    """

    print("🚀 Starting ValueSet parsing and pre-flight database validation...")
    print(f"📁 Reading data from: {DATA_DIR.resolve()}")
    print("-" * 50)

    # pass 1: read all ValueSet data into a lookup map
    all_valuesets_map: dict[tuple[str, str], dict] = {}
    for file_path in [
        file for file in DATA_DIR.glob("*.json") if file.name != "manifest.json"
    ]:
        with open(file_path) as file:
            data = json.load(file)
            for valueset in data.get("valuesets", []):
                url, version = valueset.get("url"), valueset.get("version")
                if not url or not version:
                    continue
                all_valuesets_map[(url, version)] = valueset

    print(f"✅ Found {len(all_valuesets_map)} unique (url + version) combinations.")

    # pass 1.5: pre-flight check for database integrity
    print("\n" + "=" * 80)
    print("✈️ PRE-FLIGHT CHECK: Validating data against database schema rules...")
    print("=" * 80)

    parent_valuesets = [
        valueset
        for valueset in all_valuesets_map.values()
        if any(
            "valueSet" in item
            for item in valueset.get("compose", {}).get("include", [])
        )
    ]

    print(f"🔎 Found {len(parent_valuesets)} potential 'parent' conditions to check.")

    has_failed_check = False

    # check 1: unique primary key
    seen_primary_keys: set[tuple[str, str]] = set()
    primary_key_check_failed = False
    for valueset in parent_valuesets:
        primary_key = (valueset.get("url"), valueset.get("version"))
        if primary_key in seen_primary_keys:
            print(
                f"  ❌ FAILED [PK]: Duplicate Primary Key found: URL={primary_key[0]}, Version={primary_key[1]}"
            )
            primary_key_check_failed = True
        seen_primary_keys.add(primary_key)
    if not primary_key_check_failed:
        print(
            "  ✅ PASSED [PK]: All parent conditions have a unique (URL, Version) primary key."
        )
    has_failed_check = has_failed_check or primary_key_check_failed

    # check 2: non-empty displayName
    name_check_failed = False
    for valueset in parent_valuesets:
        if not (valueset.get("name") or valueset.get("title")):
            print(
                f"  ❌ FAILED [Name]: Parent condition found with no name or title: URL={valueset.get('url')}"
            )
            name_check_failed = True
    if not name_check_failed:
        print("  ✅ PASSED [Name]: All parent conditions have a valid display name.")
    has_failed_check = has_failed_check or name_check_failed

    # check 3: parent must have at least one valid child
    child_check_failed = False
    for valueset in parent_valuesets:
        child_snomed_codes = set()
        for include_item in valueset.get("compose", {}).get("include", []):
            for child_ref in include_item.get("valueSet", []):
                try:
                    child_url, child_version = child_ref.split("|", 1)
                    if all_valuesets_map.get(
                        (child_url, child_version)
                    ) and parse_snomed_from_url(child_url):
                        child_snomed_codes.add(parse_snomed_from_url(child_url))
                except ValueError:
                    continue
        if not child_snomed_codes:
            print(
                f"  ❌ FAILED [Children]: Parent condition has no valid RS-Grouper children: URL={valueset.get('url')}"
            )
            child_check_failed = True
    if not child_check_failed:
        print(
            "  ✅ PASSED [Children]: All parent conditions have at least one valid child."
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
        # verify the final structure
        if set(aggregated_codes.keys()) != expected_keys:
            print(
                f"  ❌ FAILED [Codes]: Aggregated codes dict has wrong keys for URL={valueset.get('url')}"
            )
            code_structure_failed = True
        for key, value in aggregated_codes.items():
            if not isinstance(value, list):
                print(
                    f"  ❌ FAILED [Codes]: Aggregated code value for '{key}' is not a list for URL={valueset.get('url')}"
                )
                code_structure_failed = True

    if not code_structure_failed:
        print(
            "  ✅ PASSED [Codes]: Aggregated code structures are valid for all parents."
        )
    has_failed_check = has_failed_check or code_structure_failed

    if has_failed_check:
        print(
            "\n🔥 CRITICAL ERROR: One or more pre-flight checks failed. Seeding would fail."
        )
        return

    # pass 2: if all checks pass, we can be confident in the data
    print("\n" + "=" * 80)
    print("📊 PARSING AND AGGREGATING RESULTS (All checks passed)")
    print("=" * 80)
    print(f"✅ Successfully parsed and validated {len(parent_valuesets)} conditions.")
    print("✅ Validation script finished.")


if __name__ == "__main__":
    main()
