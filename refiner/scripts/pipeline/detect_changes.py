import hashlib
import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from fetch_api_data import run_fetch_pipeline

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
    new_manifest_files = {
        json_file.name: {
            "hash": calculate_sha256(json_file),
            "record_count": record_counts.get(json_file.name.replace(".json", ""), 0),
        }
        for json_file in new_files_in_staging
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
            print(f"    🚚 {STATUS}: {filename}")

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
