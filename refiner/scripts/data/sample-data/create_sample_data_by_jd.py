import csv
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from typing import TypedDict

JURISDICTION_CSV = "eCR_Jurisdictions.csv"
SAMPLE_FILES = Path("../../../assets/demo/mon-mothma-two-conditions.zip")
OUTPUT_DIR = Path("jurisdiction_sample_data")
RR_FILENAME = "CDA_RR.xml"
EICR_FILENAME = "CDA_eICR.xml"
ORIGINAL_TEST_JD = "SDDH"


class GitInfo(TypedDict):
    """Captured git-related information."""

    branch: str
    commit_hash: str


def get_git_info() -> GitInfo:
    """Get the git commit hash and branch name from which the file was run."""
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        return {"branch": branch, "commit_hash": commit}
    except Exception:
        return {"branch": "unknown", "commit_hash": "unknown"}


class Jurisdiction(TypedDict):
    """Jurisdiction row of the processed CSV."""

    RoutingCode: str
    Jurisdiction: str


def read_jurisdictions(csv_path: str) -> list[Jurisdiction]:
    """Read CSV and return a list of {'RoutingCode': 'AK', 'Jurisdiction': 'Alaska'}."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def extract_zip_to_memory(zip_path: Path) -> dict[str, bytes]:
    """Extracts all files from a zip into memory."""
    contents = {}
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            contents[name] = zf.read(name)
    return contents


def modify_rr(rr_bytes: bytes, old_value: str, new_value: str) -> bytes:
    """Replace SDDH JD code with the routing code from the CSV."""
    old_bytes = old_value.encode("utf-8")
    new_bytes = new_value.encode("utf-8")

    if old_bytes not in rr_bytes:
        print(f"⚠️  '{old_value}' not found in document")
    else:
        print(f"🔎 Found {rr_bytes.count(old_bytes)} occurrences of '{old_value}'")

    return rr_bytes.replace(old_bytes, new_bytes)


def create_metadata(git_info: GitInfo, jurisdiction: Jurisdiction) -> bytes:
    """Generates the content of the metadata file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metadata_content = f"""Generated at: {timestamp}
Routing Code: {jurisdiction["RoutingCode"]}
Jurisdiction: {jurisdiction["Jurisdiction"]}
Git branch of script: {git_info["branch"]}
Git hash of script: {git_info["commit_hash"]}
"""
    return metadata_content.encode("utf-8")


def create_output_zip(output_path: Path, files: dict[str, bytes], metadata: bytes):
    """Write given files (name -> bytes) to a zip at output_path."""
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
        zf.writestr("metadata.txt", metadata)


if __name__ == "__main__":
    # Read all JDs
    jurisdictions = read_jurisdictions(JURISDICTION_CSV)
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Add other desired "jurisdictions"
    jurisdictions.extend(
        [
            {"RoutingCode": "APHL", "Jurisdiction": "APHL"},
            {"RoutingCode": "CDC", "Jurisdiction": "CDC"},
            {"RoutingCode": "TEST", "Jurisdiction": "Test Jurisdiction"},
        ]
    )

    # Get the git hash
    git_info = get_git_info()

# Loop through all JD IDs in the doc
for jurisdiction in jurisdictions:
    # Get the current JD ID
    routing_code = jurisdiction["RoutingCode"]
    print(f"Processing for {routing_code}...")

    # Get the RR data
    contents = extract_zip_to_memory(SAMPLE_FILES)
    rr_data = contents.get(RR_FILENAME)

    # Swap "SDDH" with the routing code in the RR
    modified_rr = modify_rr(rr_data, ORIGINAL_TEST_JD, routing_code)

    # Replace RR with modified copy
    new_contents = contents.copy()
    new_contents[RR_FILENAME] = modified_rr

    # Name and write zip file
    output_zip = (
        OUTPUT_DIR / f"{routing_code}_eCR_Refiner_COVID_Influenza_Sample_Files.zip"
    )
    metadata = create_metadata(git_info, jurisdiction)
    create_output_zip(output_zip, new_contents, metadata)
    print(f"✅ Created {output_zip.name}")
