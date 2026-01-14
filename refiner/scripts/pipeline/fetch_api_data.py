import json
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


def dynamic_classify_valueset(valueset: dict[str, Any]) -> str | None:
    """
    Dynamically classifies a ValueSet based on its archetype.

    It does so correctly by identifying all versions of
    additional_context_groupers.

    Args:
        valueset: A dictionary representing a single FHIR ValueSet resource.

    Returns:
        A dynamically generated category name string (e.g.,
        'condition_grouper_4.0.0') or None if the ValueSet should be
        ignored.
    """

    profiles = valueset.get("meta", {}).get("profile", [])
    version = valueset.get("version", "unknown_version")
    archetype = "unclassified"

    # rule 1:
    # ignore ecr triggering valuesets
    if any("us-ph-triggering-valueset" in p for p in profiles):
        return None

    # rule 2:
    # identify by profile first (most reliable)
    if any("vsm-reportingspecificationgroupervalueset" in p for p in profiles):
        archetype = "reporting_spec_grouper"
    elif any("vsm-conditiongroupervalueset" in p for p in profiles):
        archetype = "condition_grouper"

    # rule 3:
    # fallback for additional context groupers (no meta.profile)
    # * they are identifiable by having a `useContext` field with a specific code
    # * this correctly identifies v2.0.0, v3.0.0, **and** v4.0.0.
    elif "useContext" in valueset:
        use_contexts = valueset.get("useContext", [])
        for context in use_contexts:
            codings = context.get("valueCodeableConcept", {}).get("coding", [])
            if any(c.get("code") == "additional-context-grouper" for c in codings):
                archetype = "additional_context_grouper"
                break

    # if no classification was made, we can safely ignore it
    if archetype == "unclassified":
        return None

    return f"{archetype}_{version}"


def run_fetch_pipeline(
    output_dir: Path, api_key: str, sleep_interval: float, log_dir_base: Path
) -> dict[str, int]:
    """
    Fetches, classifies, and saves FHIR ValueSets from the API.

    This function streams all active ValueSet resources from the TES API,
    classifies them into versioned categories, and writes them to separate
    JSON files in the specified output directory. It provides detailed
    logging of the process.

    Args:
        output_dir: The directory where the output JSON files will be saved.
        api_key: The API key for authenticating with the TES API.
        sleep_interval: The number of seconds to wait between API calls.
        log_dir_base: The project root -> scripts/ Path for cleaner cli output.

    Returns:
        A dictionary mapping the generated category names to the number of
        records written for each category.
    """

    load_dotenv()
    API_URL = os.getenv("TES_API_URL", "https://tes.tools.aimsplatform.org/api/fhir")
    BATCH_SIZE = 250

    file_handlers = {}
    record_counts: defaultdict[str, int] = defaultdict(int)
    ignored_count = 0

    try:
        headers = {"X-API-KEY": api_key}
        offset = 0
        while True:
            print(f"  📡 Fetching batch from offset {offset}...")

            # give the api some breathing room
            time.sleep(sleep_interval)

            url = (
                f"{API_URL}/ValueSet?status=active&_count={BATCH_SIZE}"
                f"&_getpagesoffset={offset}"
            )
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            bundle = response.json()
            entries = bundle.get("entry", [])
            if not entries:
                print("  ✅ No more entries found. API fetch complete.")
                break

            for entry in entries:
                resource = entry.get("resource", {})
                if resource.get("resourceType") != "ValueSet":
                    continue

                category = dynamic_classify_valueset(resource)

                if category is None:
                    ignored_count += 1
                    continue

                if category not in file_handlers:
                    filepath = output_dir / f"{category}.json"

                    # relative path for cleaner output in cli
                    log_path = filepath.relative_to(log_dir_base)
                    print(f"    ✨ Discovered new category: '{category}'")
                    print(f"    📝 Creating file: {log_path}")

                    filepath_out = open(filepath, "w", encoding="utf-8")
                    filepath_out.write("{\n")
                    filepath_out.write(
                        f'  "metadata": {{ "category": "{category}" }},\n'
                    )
                    filepath_out.write('  "valuesets": [\n')
                    file_handlers[category] = filepath_out

                filepath_out = file_handlers[category]
                if record_counts[category] > 0:
                    filepath_out.write(",\n")

                json.dump(resource, filepath_out, indent=4)
                filepath_out.write("\n")
                record_counts[category] += 1

            offset += BATCH_SIZE
    finally:
        print("  🏁 Finalizing files...")
        if ignored_count > 0:
            print(f"    🙈 Ignored {ignored_count} triggering-related ValueSets.")

        for category, filepath_out in file_handlers.items():
            count = record_counts[category]
            filepath_out.write("  ]\n}\n")
            filepath_out.close()
            closed_filepath = Path(filepath_out.name)
            log_path = closed_filepath.relative_to(log_dir_base)
            print(f"    🔒 Closed {log_path} (wrote {count} records).")

    return dict(record_counts)
