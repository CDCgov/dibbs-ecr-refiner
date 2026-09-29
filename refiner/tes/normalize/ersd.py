"""
Read eICR trigger codes from the current eRSD release.

Trigger codes come from the eRSD API rather than TES, whose copy is a stale
unversioned snapshot. `tes/fetch/ersd.py` keeps every release it has fetched in
`data/source-ersd/` and names the newest in the manifest's `current`; only that
one is read here.

An eRSD v3 specification bundle holds two kinds of ValueSet:

- **Groupers** (`dxtc`, `lrtc`, …) -- one per trigger category, naming their
  members by `compose.include[].valueSet` with no `focus`; they say nothing
  about which condition a code triggers
- **Members** -- the VSAC valuesets themselves, each naming the condition(s) it
  triggers as SNOMED codes in `useContext` `focus`, with codes in both
  `compose.include[].concept` and `expansion.contains`

Stdlib only: this runs in CI with nothing installed.
"""

import json
from pathlib import Path

from .model import CODE_SYSTEMS, SYSTEM_URL_TO_OID, SystemOid, ValueSetDict

ERSD_DIR = Path(__file__).parent.parent / "data" / "source-ersd"

# the specification major this reader understands; a v4 bundle may be shaped
# differently, so it is refused rather than read as if it were v3
ERSD_SPEC_MAJOR = 3

SNOMED_URL = CODE_SYSTEMS["snomed"]["url"]


def current_release(ersd_dir: Path) -> Path:
    """
    Locate the release the eRSD manifest names as `current`.

    Args:
        ersd_dir: Directory holding the eRSD releases and their manifest.

    Returns:
        Path to the current release's bundle.

    Raises:
        ValueError: If the manifest names no single file for `current`, or the
            release is not one this reader understands.
    """

    manifest = json.loads((ersd_dir / "manifest.json").read_text(encoding="utf-8"))
    current = manifest["current"]

    if int(current.split(".")[0]) != ERSD_SPEC_MAJOR:
        raise ValueError(
            f"eRSD release {current} is not v{ERSD_SPEC_MAJOR}; "
            "tes/normalize/ersd.py needs a reader for it"
        )

    match [
        name
        for name, entry in manifest["files"].items()
        if entry["rctc_version"] == current
    ]:
        case [name]:
            return ersd_dir / name
        case names:
            raise ValueError(
                f"eRSD manifest names {len(names)} files for current release {current}"
            )


def bundle_valuesets(bundle: dict) -> list[ValueSetDict]:
    """
    Every ValueSet in a specification bundle.

    Args:
        bundle: The parsed specification bundle.

    Returns:
        The bundle's ValueSet resources, groupers and members alike.
    """

    return [
        resource
        for entry in bundle.get("entry", [])
        if (resource := entry.get("resource", {})).get("resourceType") == "ValueSet"
    ]


def focus_snomeds(valueset: ValueSetDict) -> list[str]:
    """
    The SNOMED codes naming the conditions a ValueSet triggers for.

    Args:
        valueset: One ValueSet from the bundle.

    Returns:
        Its `focus` SNOMED codes; empty for a grouper.
    """

    return [
        coding["code"]
        for context in valueset.get("useContext", [])
        if context.get("code", {}).get("code") == "focus"
        for coding in context.get("valueCodeableConcept", {}).get("coding", [])
        if coding.get("system") == SNOMED_URL and coding.get("code")
    ]


def trigger_codes_by_snomed(bundle: dict) -> dict[str, set[tuple[SystemOid, str]]]:
    """
    Index a release's trigger codes by the SNOMED code of the condition they fire on.

    Args:
        bundle: The parsed specification bundle.

    Returns:
        Supported-system `(oid, code)` pairs per condition SNOMED.
    """

    # NOTE: `retired` members are read like any other; the groupers still pin
    # and expand them, so an EHR on this release still triggers on their codes.
    # groupers carry no `focus` and so contribute nothing here
    triggers: dict[str, set[tuple[SystemOid, str]]] = {}
    for valueset in bundle_valuesets(bundle):
        entries = {
            (SYSTEM_URL_TO_OID[entry["system"]], entry["code"])
            for entry in valueset.get("expansion", {}).get("contains", [])
            if entry.get("system") in SYSTEM_URL_TO_OID and entry.get("code")
        }
        for snomed in focus_snomeds(valueset):
            triggers.setdefault(snomed, set()).update(entries)
    return triggers
