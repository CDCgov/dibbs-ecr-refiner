"""
Turn raw TES ValueSet bundles into flat rows the seeder can COPY.

This is the only step that understands FHIR. It runs once per TES release, in
dev or CI, where it can afford to be slow and thorough. Everything downstream --
the seeder, the ops container, CI -- reads the gzipped CSV this writes and needs
no FHIR knowledge at all.

Output lands in `tes/data/processed/`:

    conditions.csv.gz    one row per condition grouper per release
    valuesets.csv.gz     one row per leaf grouper per condition per release
    codes.csv.gz         distinct (system, code, display)
    memberships.csv.gz   the junction: condition x code x leaf grouper
    summary.csv          per-grouper code count and content hash, uncompressed
                         and committed so data PRs show what changed
    manifest.json        row counts, output hashes, and the source file hashes
                         these were derived from

`summary.csv` is the review artifact. A data PR that bumps a release shows up as
a handful of changed lines there rather than several million lines of JSON, and
the content hash catches a grouper that swapped codes without changing its count.
"""

import argparse
import csv
import gzip
import hashlib
import io
import json
import sys
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .groupers import (
    category_for,
    child_references,
    condition_identity,
    coverage_completeness,
    coverage_level,
    is_condition_grouper,
    resolve_children,
    rsg_display_name,
    snomed_from_rsg_url,
    source_name,
)
from .model import SNOMED_OID, SYSTEM_URL_TO_OID, ValueSetDict, ValueSetKey
from .readers import reader_for_version

TES_DIR = Path(__file__).parent.parent
RAW_DIR = TES_DIR / "data" / "source-tes-groupers"
PROCESSED_DIR = TES_DIR / "data" / "processed"

MANIFEST_VERSION = 1


@dataclass
class Counts:
    """Row counts per output, reported and recorded in the manifest."""

    conditions: int = 0
    valuesets: int = 0
    codes: int = 0
    memberships: int = 0
    unresolved_references: int = 0
    dropped_unsupported_system: int = 0


def load_raw_valuesets(raw_dir: Path) -> dict[ValueSetKey, ValueSetDict]:
    """
    Load every published ValueSet, keyed by (url, version).

    Resources without both a url and a version are skipped: those are the VSAC
    `valueSet` references 7.x groupers point at, which TES does not publish here.

    Args:
        raw_dir: Directory holding the raw grouper bundles.

    Returns:
        Every ValueSet in the corpus, keyed by its identity.
    """

    valuesets: dict[ValueSetKey, ValueSetDict] = {}
    for path in sorted(raw_dir.glob("*.json")):
        if path.name == "manifest.json":
            continue
        with path.open(encoding="utf-8") as handle:
            bundle = json.load(handle)
        for valueset in bundle.get("valuesets", []):
            url, version = valueset.get("url"), valueset.get("version")
            if url and version:
                valuesets[(url, version)] = valueset
    return valuesets


def _trigger_codes_by_snomed(raw_dir: Path) -> dict[str, set[tuple[str, str, str]]]:
    """
    Index eICR triggering ValueSets by the SNOMED code they trigger on.

    Triggering bundles ship pre-expanded regardless of release, so they are read
    from `expansion.contains` directly rather than through a version reader.
    """

    triggers: dict[str, set[tuple[str, str, str]]] = {}
    for path in sorted(raw_dir.glob("eicr_triggering*.json")):
        with path.open(encoding="utf-8") as handle:
            bundle = json.load(handle)
        for valueset in bundle.get("valuesets", []):
            focus = [
                coding.get("code")
                for context in valueset.get("useContext", [])
                for coding in context.get("valueCodeableConcept", {}).get("coding", [])
                if coding.get("system") == "http://snomed.info/sct"
            ]
            entries = {
                (
                    SYSTEM_URL_TO_OID[entry["system"]],
                    entry["code"],
                    entry.get("display") or "",
                )
                for entry in valueset.get("expansion", {}).get("contains", [])
                if entry.get("system") in SYSTEM_URL_TO_OID and entry.get("code")
            }
            for snomed in filter(None, focus):
                triggers.setdefault(snomed, set()).update(entries)
    return triggers


def normalize(
    valuesets: dict[ValueSetKey, ValueSetDict],
    triggers: dict[str, set[tuple[str, str, str]]],
) -> tuple[
    list[list], list[list], list[list], list[list], list[list], Counts, dict[str, int]
]:
    """
    Project the raw corpus into the five flat tables.

    Args:
        valuesets: Every loaded ValueSet, keyed by (url, version).
        triggers: eICR trigger codes indexed by the SNOMED code they fire on.

    Returns:
        (conditions, valuesets, codes, memberships, summary, counts, dropped_by_system).
    """

    counts = Counts()
    dropped_by_system: Counter[str] = Counter()
    condition_rows: list[list] = []
    valueset_rows: list[list] = []
    membership_rows: list[list] = []
    summary_rows: list[list] = []
    codes: dict[tuple[str, str], str] = {}

    for valueset in valuesets.values():
        if not is_condition_grouper(valueset):
            continue

        identity = condition_identity(valueset)
        if identity is None:
            continue
        condition_url, condition_version = identity

        coverage = coverage_level(valueset)
        condition_rows.append(
            [
                condition_url,
                condition_version,
                valueset.get("title"),
                coverage.level if coverage else None,
                coverage.reason if coverage else None,
                coverage.date if coverage else None,
            ]
        )
        counts.conditions += 1

        rsgs, acgs = resolve_children(valueset, valuesets)
        counts.unresolved_references += sum(
            1 for key in child_references(valueset) if key not in valuesets
        )

        # A condition's own SNOMED codes are the ones naming its RSG children.
        # The flag is scoped to (code, the RSG that names itself with it): the
        # same SNOMED can appear as ordinary context in a sibling grouper, and
        # that membership is not a self-naming one.
        self_naming: set[tuple[str, str, str]] = set()
        for rsg in rsgs:
            snomed = snomed_from_rsg_url(rsg.get("url"))
            rsg_url = rsg.get("url")
            if not snomed or not rsg_url:
                continue
            self_naming.add((rsg_url, SNOMED_OID, snomed))
            codes.setdefault((SNOMED_OID, snomed), rsg_display_name(rsg) or "")

        trigger_keys = {
            (oid, code)
            for snomed in {code for _, _, code in self_naming}
            for oid, code, _ in triggers.get(snomed, set())
        }
        emitted: set[tuple[str, str, str]] = set()

        for leaf in [*rsgs, *acgs]:
            leaf_url = leaf.get("url")
            leaf_version = leaf.get("version")
            if not leaf_url or not leaf_version:
                continue

            name = source_name(leaf)
            leaf_codes = reader_for_version(leaf_version)(leaf, name)

            supported = [
                code for code in leaf_codes if code.system_url in SYSTEM_URL_TO_OID
            ]
            counts.dropped_unsupported_system += len(leaf_codes) - len(supported)
            dropped_by_system.update(
                code.system_url
                for code in leaf_codes
                if code.system_url not in SYSTEM_URL_TO_OID
            )

            for entry in supported:
                oid = SYSTEM_URL_TO_OID[entry.system_url]
                codes.setdefault((oid, entry.code), entry.display or "")
                membership = (leaf_url, oid, entry.code)
                emitted.add(membership)
                membership_rows.append(
                    [
                        condition_url,
                        condition_version,
                        leaf_url,
                        oid,
                        entry.code,
                        membership in self_naming,
                        (oid, entry.code) in trigger_keys,
                    ]
                )

            valueset_rows.append(
                [
                    condition_url,
                    condition_version,
                    leaf_url,
                    name,
                    category_for(name),
                    len(leaf_codes),
                    coverage_completeness(leaf),
                ]
            )
            summary_rows.append(
                [
                    name,
                    leaf_version,
                    "rsg" if leaf in rsgs else "acg",
                    len(supported),
                    _code_set_hash(supported),
                ]
            )
            counts.valuesets += 1

        # An RSG does not always list the SNOMED code it names itself with. The
        # condition still owns that code, so the membership is emitted here even
        # though no grouper published it as a concept.
        for rsg_url, oid, snomed in sorted(self_naming - emitted):
            membership_rows.append(
                [
                    condition_url,
                    condition_version,
                    rsg_url,
                    oid,
                    snomed,
                    True,
                    (oid, snomed) in trigger_keys,
                ]
            )

    code_rows = [[oid, code, display] for (oid, code), display in codes.items()]
    counts.codes = len(code_rows)
    counts.memberships = len(membership_rows)

    return (
        sorted(condition_rows, key=lambda row: (row[0] or "", row[1] or "")),
        sorted(valueset_rows, key=lambda row: (row[0] or "", row[1], row[2])),
        sorted(code_rows, key=lambda row: (row[0], row[1])),
        sorted(
            membership_rows, key=lambda row: (row[0], row[1], row[2], row[3], row[4])
        ),
        sorted(summary_rows, key=lambda row: (row[0] or "", row[1], row[2])),
        counts,
        dict(sorted(dropped_by_system.items())),
    )


def _code_set_hash(entries) -> str:
    """Content hash of a grouper's code set, so a swap shows up even at equal count."""

    digest = hashlib.sha256()
    for system, code in sorted({(e.system_url, e.code) for e in entries}):
        digest.update(f"{system}|{code}\n".encode())
    return digest.hexdigest()[:16]


def _write_csv_gz(path: Path, header: list[str], rows: Iterable[list]) -> str:
    """
    Write rows as gzipped CSV, byte-identically across runs.

    `gzip.open` stamps the current time and the source filename into the gzip
    header, so the same data produces a different file every run. Both are
    suppressed here: these artifacts are committed, and a regenerated file must
    only differ when the data actually did -- otherwise every run looks like a
    change and CI cannot verify processed output against its sources by hash.
    """

    with path.open("wb") as raw:
        with gzip.GzipFile(
            filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6
        ) as compressed:
            with io.TextIOWrapper(
                compressed, encoding="utf-8", newline=""
            ) as text_stream:
                writer = csv.writer(text_stream)
                writer.writerow(header)
                writer.writerows(rows)
    return _file_hash(path)


def _write_csv(path: Path, header: list[str], rows: Iterable[list]) -> str:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)
    return _file_hash(path)


def _file_hash(path: Path) -> str:
    """
    Hash a file's logical content, decompressing first when it is gzipped.

    Deliberately not a hash of the bytes on disk. gzip output depends on the zlib
    build -- Python 3.13 links zlib while 3.14 links zlib-ng, and the two produce
    different compressed bytes for identical input -- so hashing the file would
    make every check fail whenever the interpreter that verifies differs from the
    one that generated. Hashing the content asserts what we actually care about.
    """

    digest = hashlib.sha256()
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_hashes(raw_dir: Path) -> dict[str, str]:
    """
    Hash every raw bundle the outputs were derived from.

    Recorded in the processed manifest so a source file that changes without a
    re-normalize is detectable in CI without shipping the raw bundles anywhere.
    """

    return {
        path.name: _file_hash(path)
        for path in sorted(raw_dir.glob("*.json"))
        if path.name != "manifest.json"
    }


def main(argv: list[str] | None = None) -> int:
    """Read the raw bundles and write the processed tables."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--out-dir", type=Path, default=PROCESSED_DIR)
    args = parser.parse_args(argv)

    args.out_dir.mkdir(parents=True, exist_ok=True)

    print(f"reading {args.raw_dir}")
    valuesets = load_raw_valuesets(args.raw_dir)
    triggers = _trigger_codes_by_snomed(args.raw_dir)
    print(f"  {len(valuesets):,} valuesets, {len(triggers):,} triggering SNOMED codes")

    conditions, leaf_valuesets, codes, memberships, summary, counts, dropped = (
        normalize(valuesets, triggers)
    )

    outputs = {
        "conditions.csv.gz": _write_csv_gz(
            args.out_dir / "conditions.csv.gz",
            [
                "canonical_url",
                "version",
                "display_name",
                "coverage_level",
                "coverage_level_reason",
                "coverage_level_date",
            ],
            conditions,
        ),
        "valuesets.csv.gz": _write_csv_gz(
            args.out_dir / "valuesets.csv.gz",
            [
                "condition_url",
                "condition_version",
                "canonical_url",
                "display_name",
                "category",
                "code_count",
                "completeness",
            ],
            leaf_valuesets,
        ),
        "codes.csv.gz": _write_csv_gz(
            args.out_dir / "codes.csv.gz",
            ["system_oid", "code", "display"],
            codes,
        ),
        "memberships.csv.gz": _write_csv_gz(
            args.out_dir / "memberships.csv.gz",
            [
                "condition_url",
                "condition_version",
                "valueset_url",
                "system_oid",
                "code",
                "is_child_rsg",
                "is_trigger_code",
            ],
            memberships,
        ),
        "summary.csv": _write_csv(
            args.out_dir / "summary.csv",
            ["display_name", "version", "kind", "code_count", "codes_sha256"],
            summary,
        ),
    }

    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "counts": counts.__dict__,
        "dropped_by_system": dropped,
        "files": {name: {"hash": digest} for name, digest in outputs.items()},
        "derived_from": _source_hashes(args.raw_dir),
    }
    (args.out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    for field, value in counts.__dict__.items():
        print(f"  {field:<28} {value:>10,}")
    print(f"wrote {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
