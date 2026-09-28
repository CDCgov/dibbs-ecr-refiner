"""
Fetch the current eRSD release from the eRSD API into `data/source-ersd`.

The API serves only the latest release and has retired v1 and v2 outright (410),
so every release we will ever want has to be kept at the moment it is fetched.
Each one is stored byte-for-byte as served, named for the RCTC version it
declares, and never deleted; the manifest's `current` names the one to read.
"""

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from fhir.resources.R4B.bundle import Bundle

# FETCH_DIR is dibbs-ecr-refiner/refiner/tes/fetch/
# TES_DIR is dibbs-ecr-refiner/refiner/tes
FETCH_DIR = Path(__file__).parent
TES_DIR = FETCH_DIR.parent
ERSD_DATA_DIR = TES_DIR / "data" / "source-ersd"
MANIFEST_PATH = ERSD_DATA_DIR / "manifest.json"

# the `v3` in the endpoint is the eRSD specification major -- the bundle's shape,
# not its content release; a v4 means a new reader, so it is a code change here
# rather than something to discover at runtime
ERSD_API_URL = "https://ersd.aimsplatform.org/api/ersd/v3specification"
ERSD_SPEC_MAJOR = 3
RCTC_LIBRARY_URL = "http://ersd.aimsplatform.org/fhir/Library/rctc"

MANIFEST_VERSION = 1
MANIFEST_NAME = "ersd"


def fetch_bundle(api_url: str, api_key: str) -> bytes:
    """
    Download the eRSD specification bundle.

    Args:
        api_url: The eRSD specification endpoint.
        api_key: The eRSD API key.

    Returns:
        The response body exactly as served.

    Raises:
        RuntimeError: If the request fails or the API returns a non-2xx status.
    """

    # NOTE: the key rides in the query string, and `requests` puts the full url in
    # its exception messages, while the API echoes it back in 404 bodies; errors are
    # re-raised without their chain and with the key scrubbed so it never lands in
    # a terminal or ci log
    try:
        response = requests.get(
            api_url, params={"format": "json", "api-key": api_key}, timeout=120
        )
    except requests.RequestException as error:
        raise RuntimeError(
            f"eRSD API request to {api_url} failed: {type(error).__name__}"
        ) from None

    if not response.ok:
        try:
            message = str(response.json().get("message", ""))
        except ValueError:
            message = ""
        raise RuntimeError(
            f"eRSD API returned {response.status_code} for {api_url}: "
            f"{message.replace(api_key, '<redacted>')}"
        )
    return response.content


def version_key(version: str) -> tuple[int, ...]:
    """
    Sort key for a dotted numeric version; `3.10.0` sorts after `3.9.0`.

    Args:
        version: A version like `3.2.0`.

    Returns:
        The version's parts as integers.
    """

    return tuple(int(part) for part in version.split("."))


def rctc_release(bundle: dict[str, Any]) -> tuple[str, str]:
    """
    Read the RCTC release a specification bundle declares.

    Args:
        bundle: The parsed specification bundle.

    Returns:
        The RCTC `Library`'s version and date.

    Raises:
        ValueError: If the bundle is not a v3 release this fetcher can vouch for.
    """

    match [
        resource
        for entry in bundle.get("entry", [])
        if (resource := entry.get("resource", {})).get("url") == RCTC_LIBRARY_URL
    ]:
        case [library]:
            pass
        case libraries:
            raise ValueError(
                f"expected one {RCTC_LIBRARY_URL} in the bundle, found {len(libraries)}"
            )

    version = library.get("version", "")
    if version_key(version)[0] != ERSD_SPEC_MAJOR:
        raise ValueError(
            f"RCTC release {version} is not eRSD v{ERSD_SPEC_MAJOR}; "
            "the reader needs updating before this can be stored"
        )
    # the bundle id is free text, but it names the release too; disagreement
    # means one of them is wrong and we can't tell which
    if version not in bundle.get("id", ""):
        raise ValueError(
            f"RCTC library says {version} but the bundle id is {bundle.get('id')!r}"
        )
    return version, library.get("date", "")


def validate_bundle(bundle: dict[str, Any]) -> int:
    """
    Validate the whole bundle as FHIR R4.

    eRSD publishes R4; the default `fhir.resources` models are R5, whose
    `PlanDefinition` rejects the eRSD one, so this must go through `R4B`.

    Args:
        bundle: The parsed specification bundle.

    Returns:
        The number of ValueSets in the bundle.
    """

    Bundle.model_validate(bundle)
    return sum(
        entry.get("resource", {}).get("resourceType") == "ValueSet"
        for entry in bundle.get("entry", [])
    )


def main() -> None:
    """
    Fetch the current eRSD release and record it in the manifest.

    Only writes when the served bytes differ from what the manifest already
    holds for that release, so a fetch that finds nothing new leaves no diff.
    """

    load_dotenv()
    if not (api_key := os.getenv("ERSD_API_KEY")):
        raise ValueError("ERSD_API_KEY not found in .env file.")

    print(f"📡 Fetching eRSD specification from {ERSD_API_URL}...")
    raw = fetch_bundle(ERSD_API_URL, api_key)
    bundle = json.loads(raw)
    version, release_date = rctc_release(bundle)

    print(f"🔬 Validating RCTC {version} as FHIR R4...")
    valueset_count = validate_bundle(bundle)

    manifest: dict[str, Any] = {"files": {}}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if manifest.get("manifest_version", 0) > MANIFEST_VERSION:
            raise ValueError(
                f"Manifest at {MANIFEST_PATH} has manifest_version="
                f"{manifest['manifest_version']}, which is newer than this script "
                f"supports ({MANIFEST_VERSION}). Upgrade the pipeline before continuing."
            )

    filename = f"ersd_{version}.json"
    digest = hashlib.sha256(raw).hexdigest()
    previous = manifest["files"].get(filename)
    if previous and previous["hash"] == digest:
        print(f"🎉 RCTC {version} is unchanged. Nothing to do.")
        return

    # write-then-rename so an interrupted fetch never leaves a partial file behind
    ERSD_DATA_DIR.mkdir(parents=True, exist_ok=True)
    staged = ERSD_DATA_DIR / f".{filename}.tmp"
    staged.write_bytes(raw)
    staged.replace(ERSD_DATA_DIR / filename)
    print(f"🚚 {'UPDATED' if previous else 'NEW'}: {filename}")

    manifest["files"][filename] = {
        "rctc_version": version,
        "release_date": release_date,
        "hash": digest,
        "valueset_count": valueset_count,
        "fetched_at_utc": datetime.now(UTC).isoformat(),
    }
    final_manifest = {
        "manifest_version": MANIFEST_VERSION,
        "name": MANIFEST_NAME,
        "current": max(
            (entry["rctc_version"] for entry in manifest["files"].values()),
            key=version_key,
        ),
        "files": dict(sorted(manifest["files"].items())),
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as manifest_file:
        json.dump(final_manifest, manifest_file, indent=2)
        # write \n to conform with pre-commit
        manifest_file.write("\n")
    print(f"✨ Manifest updated; current release is {final_manifest['current']}")


if __name__ == "__main__":
    main()
