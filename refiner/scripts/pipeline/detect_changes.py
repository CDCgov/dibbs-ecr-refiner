import datetime as dtlib
import hashlib
import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from fetch_api_data import run_fetch_pipeline


def _convert_datetimes_to_iso(obj):
    """
    Recursively convert all datetime objects to ISO strings.
    """
    if isinstance(obj, dict):
        return {k: _convert_datetimes_to_iso(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_datetimes_to_iso(i) for i in obj]
    if isinstance(obj, datetime | dtlib.datetime):
        return obj.isoformat()
    return obj


# configuration
load_dotenv()


# build paths relative to this script's location
# PIPELINE_DIR is dibbs-ecr-refiner/refiner/scripts/pipeline/
# SCRIPTS_DIR is dibbs-ecr-refiner/refiner/scripts
PIPELINE_DIR = Path(__file__).parent
SCRIPTS_DIR = PIPELINE_DIR.parent
TES_DATA_DIR = SCRIPTS_DIR / "data" / "source-tes-groupers"
TES_DATA_STAGING_DIR = TES_DATA_DIR / "staging"
MANIFEST_PATH = TES_DATA_DIR / "manifest.json"

API_KEY = os.getenv("TES_API_KEY")
API_SLEEP_INTERVAL = float(os.getenv("API_SLEEP_INTERVAL", "1.0"))
TES_VALIDATE = os.getenv("TES_VALIDATE", "true").lower() in ("1", "true", "yes")


def calculate_sha256(filepath: Path) -> str:
    """
    Calculates the SHA256 hash of a file.

    Args:
        filepath: The path to the file to be hashed.

    Returns:
        The hex digest of the file's SHA256 hash.

    Note:
        The file is read in chunks (8192 bytes at a time) rather than all at once.
        This allows the function to handle large files efficiently without using
        excessive memory. The chunk size (8192) is a commonly used buffer size
        for file operations and does not affect the hash result. It is *not* a
        salt or security parameter—it's just a performance consideration.
    """

    sha256 = hashlib.sha256()
    # read the file in 8kb chunks:
    # * this is for memory efficiency—especially for large files
    # * the hash is computed over the file's actual contents; no salt is involved
    with open(filepath, "rb") as file:
        while chunk := file.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def _validate_valuesets_file(filepath: Path) -> tuple[int, int]:
    """
    Validate each resource in a staged valueset file using fhir.resources.ValueSet.

    Overwrites the file with only the validated ValueSet dicts.

    Returns (valid_count, invalid_count).
    """
    # lazy import so this script can still run if not validating
    try:
        from fhir.resources.valueset import ValueSet
    except Exception as e:
        raise ImportError(
            "fhir.resources is required for TES validation. Install it (pip install fhir.resources)."
        ) from e

    with open(filepath, encoding="utf-8") as fh:
        data = json.load(fh)

    valuesets = data.get("valuesets", []) or []
    valid_vs: list[dict] = []
    invalid_count = 0

    for idx, vs in enumerate(valuesets, start=1):
        try:
            # support pydantic v2 and v1 usage in fhir.resources
            if hasattr(ValueSet, "model_validate"):
                validated = ValueSet.model_validate(vs)
                vs_dict = validated.model_dump()
            else:
                validated = ValueSet.parse_obj(vs)
                vs_dict = validated.dict()
            valid_vs.append(_convert_datetimes_to_iso(vs_dict))
        except Exception as e:
            invalid_count += 1
            print(
                f"    ⚠️  Validation failed for resource #{idx} in {filepath.name}: {e}"
            )

    # rewrite file with validated valuesets (preserve metadata)
    data["valuesets"] = valid_vs
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")

    return len(valid_vs), invalid_count


def main() -> None:
    """
    Orchestrates the data fetching and change detection pipeline.

    This script sets up a staging area, runs the API fetch pipeline,
    compares the newly generated files against a manifest of the previous
    run, synchronizes any changes, and updates the manifest.
    """

    if not API_KEY:
        raise ValueError("TES_API_KEY not found in .env file.")

    # 1: setup
    print(
        f"🧹 Setting up staging area at: {TES_DATA_STAGING_DIR.relative_to(SCRIPTS_DIR)}"
    )
    shutil.rmtree(TES_DATA_STAGING_DIR, ignore_errors=True)
    TES_DATA_STAGING_DIR.mkdir(parents=True)

    old_manifest = {}
    if MANIFEST_PATH.exists():
        print(
            f"🔎 Found existing manifest at: {MANIFEST_PATH.relative_to(SCRIPTS_DIR)}"
        )
        with open(MANIFEST_PATH, encoding="utf-8") as manifest_file:
            old_manifest = json.load(manifest_file)

    # 2: run the fetch pipeline
    print("🚀 Running API fetch and classification pipeline...")
    record_counts = run_fetch_pipeline(
        output_dir=TES_DATA_STAGING_DIR,
        api_key=API_KEY,
        sleep_interval=API_SLEEP_INTERVAL,
        log_dir_base=SCRIPTS_DIR,
    )

    # 3: analyze new files and add a safety check
    new_files_in_staging = list(TES_DATA_STAGING_DIR.glob("*.json"))

    # safety check
    if not new_files_in_staging:
        print(
            "🚨 WARNING: Staging directory is empty after fetch. Aborting to prevent data loss."
        )
        shutil.rmtree(TES_DATA_STAGING_DIR)
        print("✅ Pipeline finished with no changes.")
        return

    print("🧐 Analyzing new files and generating new manifest...")

    # Validate staged files (optional toggle)
    validated_summary: dict[str, dict] = {}
    for json_file in list(new_files_in_staging):
        if TES_VALIDATE:
            print(f"🔬 Validating staged file: {json_file.name}")
            try:
                valid_count, invalid_count = _validate_valuesets_file(json_file)
            except ImportError as ie:
                print(f"❌ Validation failed (missing dependency): {ie}")
                raise
            except Exception:
                print(
                    f"❌ Unexpected error validating {json_file.name}. See traceback."
                )
                raise

            if valid_count == 0:
                # nothing valid — remove staged file to avoid polluting data dir
                json_file.unlink()
                print(
                    f"    ❌ {json_file.name} contained 0 valid valuesets; removed from staging."
                )
                continue

            validated_summary[json_file.name] = {
                "valid": valid_count,
                "invalid": invalid_count,
            }
        else:
            # validation disabled — trust counts from fetch pipeline
            validated_summary[json_file.name] = {
                "valid": record_counts.get(json_file.name.replace(".json", ""), 0),
                "invalid": 0,
            }

    # recompute list of staged files (some may have been removed)
    new_files_in_staging = list(TES_DATA_STAGING_DIR.glob("*.json"))

    new_manifest_files = {}
    for json_file in new_files_in_staging:
        # compute hash of the (possibly rewritten) file
        file_hash = calculate_sha256(json_file)
        rec_count = validated_summary.get(json_file.name, {}).get("valid", 0)
        new_manifest_files[json_file.name] = {
            "hash": file_hash,
            "record_count": rec_count,
        }

    # 4: compare using set operations for clarity
    old_filenames = set(old_manifest.get("files", {}).keys())
    new_filenames = set(new_manifest_files.keys())

    new_files = new_filenames - old_filenames
    deleted_files = old_filenames - new_filenames
    common_files = old_filenames & new_filenames

    updated_files = {
        filename
        for filename in common_files
        if new_manifest_files[filename]["hash"]
        != old_manifest.get("files", {}).get(filename, {}).get("hash")
    }

    # 5: act on results
    if not any([new_files, updated_files, deleted_files]):
        print("  🎉 No changes detected. Nothing to do.")
    else:
        print("  🔄 Changes detected! Synchronizing files...")

        for filename in new_files | updated_files:
            shutil.move(TES_DATA_STAGING_DIR / filename, TES_DATA_DIR / filename)
            status = "NEW" if filename in new_files else "UPDATED"
            print(f"    🚚 {status}: {filename}")

        for filename in deleted_files:
            (TES_DATA_DIR / filename).unlink()
            print(f"    💥 DELETED: {filename}")

        # 6: write new manifest
        final_manifest = {
            "last_updated_utc": datetime.now(UTC).isoformat(),
            "files": new_manifest_files,
        }
        with open(MANIFEST_PATH, "w", encoding="utf-8") as manifest_file:
            json.dump(final_manifest, manifest_file, indent=2)
            # write \n to conform with pre-commit
            manifest_file.write("\n")
        print(
            f"\n✨ Manifest file updated at: {MANIFEST_PATH.relative_to(SCRIPTS_DIR)}"
        )

    # 7: cleanup
    shutil.rmtree(TES_DATA_STAGING_DIR)
    print("✅ Pipeline finished.")


if __name__ == "__main__":
    main()
