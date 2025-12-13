import shutil
from pathlib import Path

# define the single source of truth and the destination
SOURCE_DIR = Path(__file__).parent.parent / "scripts/data/source-ecr-files"
DEST_DIR = Path(__file__).parent / "fixtures"

# a manifest of the files we care about
# * key: the source filename in the scripts directory
# * value: the destination path within the tests/fixtures/ directory
FILE_MANIFEST = {
    "mon-mothma-covid-influenza_CDA_1.1_eICR.xml": "eicr_v1_1/mon_mothma_covid_influenza_eICR.xml",
    "mon-mothma-covid-influenza_CDA_1.1_RR.xml": "eicr_v1_1/mon_mothma_covid_influenza_RR.xml",
    "packaged/mon-mothma-covid-influenza-1.1.zip": "eicr_v1_1/mon_mothma_covid_influenza_1.1.zip",
    "mon-mothma-zika_CDA_3.1.1_eICR.xml": "eicr_v3_1_1/mon_mothma_zika_eICR.xml",
    "mon-mothma-zika_CDA_1.1_RR.xml": "eicr_v3_1_1/mon_mothma_zika_RR.xml",
    "packaged/mon-mothma-zika-3.1.1.zip": "eicr_v3_1_1/mon_mothma_zika_3.1.1.zip",
}


def main():
    """
    Synchronizes curated test data from the source-of-truth directory into the self-contained test fixtures directory.
    """

    print("🚀 Launching test data synchronization...")

    if not SOURCE_DIR.is_dir():
        print(f"❌ ERROR: Source directory not found at {SOURCE_DIR}")
        return 1

    # we only remove and recreate the data subdirectories, not the whole fixtures dir
    # * this leaves loader.py and any other python files untouched
    if (DEST_DIR / "eicr_v1_1").exists():
        shutil.rmtree(DEST_DIR / "eicr_v1_1")
    if (DEST_DIR / "eicr_v3_1_1").exists():
        shutil.rmtree(DEST_DIR / "eicr_v3_1_1")

    print("🌌 Cleaned old data directories")

    for src_name, dest_path_str in FILE_MANIFEST.items():
        source_file = SOURCE_DIR / src_name
        dest_file = DEST_DIR / dest_path_str

        if not source_file.exists():
            print(f"⚠️  WARNING: Source file not found, skipping: {source_file}")
            continue

        # ensure destination subdirectory exists (e.g., tests/fixtures/eicr_v1_1/)
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"📡 Copying {src_name} -> {dest_path_str}")
        shutil.copy(source_file, dest_file)

    print("✨ Synchronization complete. Ready for liftoff!")
    return 0


if __name__ == "__main__":
    exit(main())
