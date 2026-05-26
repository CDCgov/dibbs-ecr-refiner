import json
import math
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

# size threshold per shard, in bytes
# * keeps individual files comfortably under github's 50 mb soft warning
# * gives headroom for category growth between releases
SHARD_THRESHOLD_BYTES = 30 * 1024 * 1024


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


def _serialized_size(obj: Any) -> int:
    """
    Estimate the serialized size of a JSON-encodable object in bytes.

    Matches the format used when writing (indent=4) so the rotation
    threshold is meaningful relative to final file size on disk.
    """

    return len(json.dumps(obj, indent=4).encode("utf-8"))


def _write_category_files(
    category: str,
    valuesets: list[dict[str, Any]],
    output_dir: Path,
    log_dir_base: Path,
) -> dict[str, int]:
    """
    Writes a category's ValueSets to one or more shard files.

    A category that fits under SHARD_THRESHOLD_BYTES is written as a single
    file: `<category>.json`. A category that exceeds the threshold is sorted
    by canonical url and split into roughly equal-sized chunks by record count,
    written as `<category>.partNN.json`.

    Args:
        category: The category name (e.g., 'condition_grouper_6.0.0').
        valuesets: The category's ValueSets.
        output_dir: Where to write the files.
        log_dir_base: For cleaner cli output paths.

    Returns:
        A mapping of written filename stem (without .json suffix) to record
        count. For sharded categories, each part is its own key (e.g.,
        'condition_grouper_6.0.0.part01').

    Raises:
        ValueError: If any single ValueSet exceeds SHARD_THRESHOLD_BYTES. A
            single resource larger than the shard ceiling can't be safely
            split, so the human needs to decide between raising the ceiling
            or handling that resource specially.
    """

    # sort by url so shard membership is stable as long as the set of urls
    # in this category doesn't change
    # * if a vs is added or removed, downstream shard boundaries shift, which
    #   is the right behavior: new content means new shards to seed
    sorted_vses = sorted(valuesets, key=lambda v: v.get("url", ""))

    # defensive check: no single vs can exceed the shard ceiling
    # * if this ever fires, raise the ceiling or carve out that vs explicitly;
    #   the alternative is silently breaking github file-size limits
    for vs in sorted_vses:
        vs_size = _serialized_size(vs)
        if vs_size > SHARD_THRESHOLD_BYTES:
            raise ValueError(
                f"ValueSet {vs.get('url', '<no url>')} (version "
                f"{vs.get('version', '<no version>')}) is {vs_size:,} bytes, "
                f"which exceeds the per-shard ceiling of "
                f"{SHARD_THRESHOLD_BYTES:,} bytes. Raise SHARD_THRESHOLD_BYTES "
                f"or handle this resource specially."
            )

    # work out how many shards we need
    # * build the full payload once, see if it fits as a single file
    # * if not, split into ceil(total_size / threshold) chunks by record count
    single_payload = {"metadata": {"category": category}, "valuesets": sorted_vses}
    total_size = _serialized_size(single_payload)

    if total_size <= SHARD_THRESHOLD_BYTES:
        n_shards = 1
    else:
        n_shards = math.ceil(total_size / SHARD_THRESHOLD_BYTES)

    # split records evenly across shards by count
    # * this is approximate by-size since vses within a category have similar
    #   sizes; if that assumption ever breaks (one vs is 10x bigger than its
    #   peers), the resulting shards may still be uneven but will still fit
    #   under the ceiling as long as the single-vs check above passes
    chunk_size = math.ceil(len(sorted_vses) / n_shards)
    chunks = [
        sorted_vses[i : i + chunk_size] for i in range(0, len(sorted_vses), chunk_size)
    ]

    # math.ceil can sometimes produce one fewer chunk than n_shards if the
    # division comes out exact; recompute n_shards from the actual chunks
    n_shards = len(chunks)

    written: dict[str, int] = {}

    for idx, chunk in enumerate(chunks, start=1):
        if n_shards == 1:
            filename = f"{category}.json"
            stem = category
            metadata = {"category": category}
        else:
            filename = f"{category}.part{idx:02d}.json"
            stem = f"{category}.part{idx:02d}"
            metadata = {
                "category": category,
                "part": idx,
                "total_parts": n_shards,
            }

        filepath = output_dir / filename
        log_path = filepath.relative_to(log_dir_base)

        if n_shards == 1:
            print(f"    📝 Writing {log_path} ({len(chunk)} records)")
        else:
            print(
                f"    📝 Writing {log_path} ({len(chunk)} records, "
                f"part {idx}/{n_shards})"
            )

        payload = {"metadata": metadata, "valuesets": chunk}
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=4)
            fh.write("\n")

        written[stem] = len(chunk)

    return written


def run_fetch_pipeline(
    output_dir: Path, api_key: str, sleep_interval: float, log_dir_base: Path
) -> dict[str, int]:
    """
    Fetches, classifies, and saves FHIR ValueSets from the API.

    This function streams all active ValueSet resources from the TES API,
    classifies them into versioned categories, sorts each category by canonical
    url, and writes them to one or more shard files per category. Categories
    that fit under SHARD_THRESHOLD_BYTES are written as a single file;
    larger categories are split into multiple `.partNN.json` files.

    Args:
        output_dir: The directory where the output JSON files will be saved.
        api_key: The API key for authenticating with the TES API.
        sleep_interval: The number of seconds to wait between API calls.
        log_dir_base: The project root -> scripts/ Path for cleaner cli output.

    Returns:
        A dictionary mapping output filename stems (without .json) to the
        number of records written. For sharded categories, each part is its
        own key (e.g., 'condition_grouper_6.0.0.part01').
    """

    load_dotenv()
    API_URL = os.getenv("TES_API_URL", "https://tes.tools.aimsplatform.org/api/fhir")
    BATCH_SIZE = 250

    # buffer per-category in memory so we can sort and split at the end
    # * peak memory is bounded by the size of the full active tes dataset
    # * the previous version of this script streamed straight to disk, which
    #   was lighter on memory but made size-based sharding impossible without
    #   reading files back; given the dataset size, buffering is the simpler
    #   tradeoff
    buffered: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    ignored_count = 0

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

            if category not in buffered:
                print(f"    ✨ Discovered new category: '{category}'")

            buffered[category].append(resource)

        offset += BATCH_SIZE

    print("  🏁 Finalizing files...")
    if ignored_count > 0:
        print(f"    🙈 Ignored {ignored_count} triggering-related ValueSets.")

    record_counts: dict[str, int] = {}
    for category in sorted(buffered.keys()):
        written = _write_category_files(
            category=category,
            valuesets=buffered[category],
            output_dir=output_dir,
            log_dir_base=log_dir_base,
        )
        record_counts.update(written)

    return record_counts
