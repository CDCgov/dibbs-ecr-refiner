import json
import logging
from pathlib import Path
from typing import Any

# configuration
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
DATA_DIR = Path(__file__).parent.parent / "data"

# how many records to print in the dry run?
DRY_RUN_RECORD_LIMIT = 5


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


def dry_run_seeding():
    """
    Performs a 'dry run' of the seeding process.

    Preparing the data and printing a summarized sample of the records
    that would be inserted.
    """

    logging.info("🚀 Starting database seeding DRY RUN...")
    logging.info(
        "This will prepare data and print a sample without touching the database."
    )

    # pass 1: read all ValueSet data into a lookup map
    all_valuesets_map: dict[tuple, dict] = {}
    json_files = [f for f in DATA_DIR.glob("*.json") if f.name != "manifest.json"]
    for file_path in json_files:
        with open(file_path) as f:
            data = json.load(f)
            for valueset in data.get("valuesets", []):
                key = (valueset.get("url"), valueset.get("version"))
                all_valuesets_map[key] = valueset
    logging.info(
        f"  ✅ Found {len(all_valuesets_map)} unique ValueSets (url + version)."
    )

    # pass 2: aggregate data for each parent condition in memory
    logging.info("🧠 PASS 2: Aggregating child data into parent condition records...")
    conditions_to_insert = []
    parent_valuesets = [
        valueset
        for valueset in all_valuesets_map.values()
        if any(
            "valueSet" in item
            for item in valueset.get("compose", {}).get("include", [])
        )
    ]

    for parent in parent_valuesets:
        child_snomed_codes = set()
        aggregated_codes = {
            "loinc_codes": [],
            "snomed_codes": [],
            "icd10_codes": [],
            "rxnorm_codes": [],
        }

        for include_item in parent.get("compose", {}).get("include", []):
            for child_ref in include_item.get("valueSet", []):
                try:
                    child_url, child_version = child_ref.split("|", 1)
                except ValueError:
                    continue

                child_valueset = all_valuesets_map.get((child_url, child_version))
                if not child_valueset:
                    continue

                snomed_code = parse_snomed_from_url(child_valueset.get("url"))
                if snomed_code:
                    child_snomed_codes.add(snomed_code)

                child_extracted_codes = extract_codes_from_valueset(child_valueset)
                for code_type, codes in child_extracted_codes.items():
                    aggregated_codes[code_type].extend(codes)

        conditions_to_insert.append(
            {
                "canonical_url": parent.get("url"),
                "version": parent.get("version"),
                "display_name": parent.get("name") or parent.get("title"),
                "child_rsg_snomed_codes": list(child_snomed_codes),
                "loinc_codes": json.dumps(aggregated_codes["loinc_codes"]),
                "snomed_codes": json.dumps(aggregated_codes["snomed_codes"]),
                "icd10_codes": json.dumps(aggregated_codes["icd10_codes"]),
                "rxnorm_codes": json.dumps(aggregated_codes["rxnorm_codes"]),
            }
        )
    logging.info(
        f"  ✅ Aggregated data for {len(conditions_to_insert)} condition versions."
    )

    # --- pass 3: print a summarized sample of the prepared records
    logging.info("\n" + "=" * 80)
    logging.info(
        f"🖨️  DRY RUN: SUMMARIZING FIRST {DRY_RUN_RECORD_LIMIT} OF {len(conditions_to_insert)} PREPARED RECORDS"
    )
    logging.info("=" * 80)

    if not conditions_to_insert:
        logging.warning("⚠️ No records were prepared for insertion.")

    for index, record in enumerate(conditions_to_insert[:DRY_RUN_RECORD_LIMIT]):
        logging.info(f"\n--- RECORD {index + 1} ---")

        # safely get counts from the json strings to provide a clean summary
        loinc_count = len(json.loads(record["loinc_codes"]))
        snomed_count = len(json.loads(record["snomed_codes"]))
        icd10_count = len(json.loads(record["icd10_codes"]))
        rxnorm_count = len(json.loads(record["rxnorm_codes"]))

        summary = (
            f"  Display Name: {record['display_name']}\n"
            f"  URL: {record['canonical_url']}\n"
            f"  Version: {record['version']}\n"
            f"  Derived Child SNOMEDs: {len(record['child_rsg_snomed_codes'])}\n"
            f"  Aggregated LOINC Codes: {loinc_count}\n"
            f"  Aggregated SNOMED Codes: {snomed_count}\n"
            f"  Aggregated ICD-10 Codes: {icd10_count}\n"
            f"  Aggregated RxNorm Codes: {rxnorm_count}"
        )
        print(summary)

    logging.info("\n✅ Dry run complete.")


if __name__ == "__main__":
    dry_run_seeding()
