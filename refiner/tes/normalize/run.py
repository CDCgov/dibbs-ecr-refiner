"""
Turn raw TES ValueSet bundles into flat rows the seeder can COPY.

Trigger codes are the one input from outside TES: `is_trigger_code` comes from the
current eRSD release, read by `ersd.py`.

This is the only step that understands FHIR. It runs once per TES release, in
dev or CI, where it can afford to be slow and thorough. Everything downstream--
the seeder, the ops container, CI -- reads the gzipped CSV this writes and needs
no FHIR knowledge at all.

Output lands in `tes/data/processed/`:

    conditions.csv.gz    one row per condition grouper per release
    valuesets.csv.gz     one row per leaf grouper per condition per release
    codes.csv.gz         distinct (system, code, display)
    memberships.csv.gz   the junction: condition x code x leaf grouper
    summary.csv          per-grouper code count, trigger count and content hash,
                         uncompressed and committed so data PRs show what changed
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
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import NamedTuple

from .ersd import ERSD_DIR, current_release, trigger_codes_by_snomed
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
from .model import (
    SNOMED_OID,
    SYSTEM_URL_TO_OID,
    FhirCodeInfo,
    ValueSetDict,
    ValueSetKey,
)
from .readers import reader_for_version

TES_DIR = Path(__file__).parent.parent
RAW_DIR = TES_DIR / "data" / "source-tes-groupers"
PROCESSED_DIR = TES_DIR / "data" / "processed"

MANIFEST_VERSION = 1


@dataclass
class Counts:
    """
    Row counts per output, reported and recorded in the manifest.
    """

    conditions: int = 0
    valuesets: int = 0
    codes: int = 0
    memberships: int = 0
    unresolved_references: int = 0
    dropped_unsupported_system: int = 0


class ConditionRow(NamedTuple):
    """One condition grouper, per release."""

    canonical_url: str
    version: str
    display_name: str | None
    coverage_level: str | None
    coverage_level_reason: str | None
    coverage_level_date: str | None


class ValuesetRow(NamedTuple):
    """One leaf grouper, scoped to the condition that resolved it."""

    condition_url: str
    condition_version: str
    canonical_url: str
    display_name: str
    category: str
    code_count: int
    completeness: str | None


class CodeRow(NamedTuple):
    """One distinct (system, code), with the display that won."""

    system_oid: str
    code: str
    display: str


class MembershipRow(NamedTuple):
    """The junction grain: a condition owning a code via one leaf grouper."""

    condition_url: str
    condition_version: str
    valueset_url: str
    system_oid: str
    code: str
    is_child_rsg: bool
    is_trigger_code: bool


class SummaryRow(NamedTuple):
    """The committed review artifact: per-grouper counts and a content hash."""

    display_name: str
    version: str
    kind: str
    code_count: int
    trigger_count: int
    codes_sha256: str


@dataclass
class NormalizedTables:
    """
    Everything `normalize` produces, named rather than positional.

    The five row lists were previously returned as identically-typed tuple
    elements, so transposing two of them was a silent error the call site had to
    avoid from memory. `codes` is a dict rather than a list because it
    deduplicates across the whole corpus, not per condition.
    """

    counts: Counts = field(default_factory=Counts)
    dropped_by_system: Counter[str] = field(default_factory=Counter)
    conditions: list[ConditionRow] = field(default_factory=list)
    valuesets: list[ValuesetRow] = field(default_factory=list)
    memberships: list[MembershipRow] = field(default_factory=list)
    summary: list[SummaryRow] = field(default_factory=list)
    codes: dict[tuple[str, str], str] = field(default_factory=dict)


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


def normalize(
    valuesets: dict[ValueSetKey, ValueSetDict],
    triggers: dict[str, set[tuple[str, str]]],
) -> NormalizedTables:
    """
    Project the raw corpus into the flat tables.

    Args:
        valuesets: Every loaded ValueSet, keyed by (url, version).
        triggers: eICR trigger codes indexed by the SNOMED code they fire on.

    Returns:
        Every table, sorted deterministically so regenerating the same inputs
        produces the same bytes.
    """

    tables = NormalizedTables()

    for valueset in valuesets.values():
        if is_condition_grouper(valueset):
            _normalize_condition(valueset, valuesets, triggers, tables)

    tables.counts.codes = len(tables.codes)
    tables.counts.memberships = len(tables.memberships)

    tables.conditions.sort(key=lambda row: (row.canonical_url or "", row.version))
    tables.valuesets.sort(
        key=lambda row: (row.condition_url, row.condition_version, row.canonical_url)
    )
    tables.memberships.sort(
        key=lambda row: (
            row.condition_url,
            row.condition_version,
            row.valueset_url,
            row.system_oid,
            row.code,
        )
    )
    tables.summary.sort(key=lambda row: (row.display_name or "", row.version, row.kind))
    return tables


def _normalize_condition(
    condition: ValueSetDict,
    valuesets: dict[ValueSetKey, ValueSetDict],
    triggers: dict[str, set[tuple[str, str]]],
    tables: NormalizedTables,
) -> None:
    """
    Project one condition grouper and its resolved children into `tables`.

    Appends rather than returning: `tables.codes` deduplicates across the whole
    corpus, so per-condition results would have to be merged by the caller
    anyway.

    Args:
        condition: The condition grouper being projected.
        valuesets: Every loaded ValueSet, for resolving children.
        triggers: eICR trigger codes indexed by the SNOMED code they fire on.
        tables: Accumulator every row is appended to.
    """

    identity = condition_identity(condition)
    if identity is None:
        return
    condition_url, condition_version = identity

    coverage = coverage_level(condition)
    tables.conditions.append(
        ConditionRow(
            canonical_url=condition_url,
            version=condition_version,
            display_name=condition.get("title"),
            coverage_level=coverage.level if coverage else None,
            coverage_level_reason=coverage.reason if coverage else None,
            coverage_level_date=coverage.date if coverage else None,
        )
    )
    tables.counts.conditions += 1

    rsgs, acgs = resolve_children(condition, valuesets)
    tables.counts.unresolved_references += sum(
        1 for key in child_references(condition) if key not in valuesets
    )

    # a condition's own SNOMED codes are the ones naming its RSG children. the
    # flag is scoped to (code, the RSG that names itself with it): the same
    # SNOMED can appear as ordinary context in a sibling grouper, and that
    # membership is not a self-naming one
    self_naming: set[tuple[str, str, str]] = set()
    for rsg in rsgs:
        snomed = snomed_from_rsg_url(rsg.get("url"))
        rsg_url = rsg.get("url")
        if not snomed or not rsg_url:
            continue
        self_naming.add((rsg_url, SNOMED_OID, snomed))
        tables.codes.setdefault((SNOMED_OID, snomed), rsg_display_name(rsg) or "")

    trigger_keys = {
        key
        for snomed in {code for _, _, code in self_naming}
        for key in triggers.get(snomed, set())
    }
    emitted: set[tuple[str, str, str]] = set()

    for kind, leaf in [*(("rsg", r) for r in rsgs), *(("acg", a) for a in acgs)]:
        leaf_url = leaf.get("url")
        leaf_version = leaf.get("version")
        if not leaf_url or not leaf_version:
            continue

        name = source_name(leaf)
        leaf_codes = reader_for_version(leaf_version)(leaf, name)
        supported = [
            code for code in leaf_codes if code.system_url in SYSTEM_URL_TO_OID
        ]
        tables.counts.dropped_unsupported_system += len(leaf_codes) - len(supported)
        tables.dropped_by_system.update(
            code.system_url
            for code in leaf_codes
            if code.system_url not in SYSTEM_URL_TO_OID
        )

        for entry in supported:
            oid = SYSTEM_URL_TO_OID[entry.system_url]
            tables.codes.setdefault((oid, entry.code), entry.display or "")
            membership = (leaf_url, oid, entry.code)
            emitted.add(membership)
            tables.memberships.append(
                MembershipRow(
                    condition_url=condition_url,
                    condition_version=condition_version,
                    valueset_url=leaf_url,
                    system_oid=oid,
                    code=entry.code,
                    is_child_rsg=membership in self_naming,
                    is_trigger_code=(oid, entry.code) in trigger_keys,
                )
            )

        tables.valuesets.append(
            ValuesetRow(
                condition_url=condition_url,
                condition_version=condition_version,
                canonical_url=leaf_url,
                display_name=name,
                category=category_for(name, is_rsg=kind == "rsg"),
                code_count=len(leaf_codes),
                completeness=coverage_completeness(leaf),
            )
        )
        tables.summary.append(
            SummaryRow(
                display_name=name,
                version=leaf_version,
                kind=kind,
                code_count=len(supported),
                trigger_count=sum(
                    (SYSTEM_URL_TO_OID[code.system_url], code.code) in trigger_keys
                    for code in supported
                ),
                codes_sha256=_code_set_hash(supported),
            )
        )
        tables.counts.valuesets += 1

    # an RSG does not always list the SNOMED code it names itself with. the
    # condition still owns that code, so the membership is emitted here even
    # though no grouper published it as a concept
    for rsg_url, oid, snomed in sorted(self_naming - emitted):
        tables.memberships.append(
            MembershipRow(
                condition_url=condition_url,
                condition_version=condition_version,
                valueset_url=rsg_url,
                system_oid=oid,
                code=snomed,
                is_child_rsg=True,
                is_trigger_code=(oid, snomed) in trigger_keys,
            )
        )


def _code_set_hash(entries: Iterable[FhirCodeInfo]) -> str:
    """
    Content hash of a grouper's code set, so a swap shows up even at equal count.
    """

    digest = hashlib.sha256()
    for system, code in sorted({(e.system_url, e.code) for e in entries}):
        digest.update(f"{system}|{code}\n".encode())
    return digest.hexdigest()[:16]


def _write_csv_gz(path: Path, header: Sequence[str], rows: Iterable[Sequence]) -> str:
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
                writer = csv.writer(text_stream, lineterminator="\n")
                writer.writerow(header)
                writer.writerows(rows)
    return file_hash(path)


def _write_csv(path: Path, header: Sequence[str], rows: Iterable[Sequence]) -> str:
    """
    Write rows as plain CSV with LF line endings.

    `csv.writer` defaults to CRLF per RFC 4180, but `.gitattributes` declares
    `*.csv text eol=lf`, so git stores LF and hands LF back on checkout. Writing
    CRLF makes the committed file hash differently after a fresh clone -- which is
    exactly how this broke CI the first time.
    """

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    return file_hash(path)


def file_hash(path: Path) -> str:
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


def source_hashes(raw_dir: Path, ersd_dir: Path) -> dict[str, str]:
    """
    Hash every raw bundle the outputs were derived from.

    Recorded in the processed manifest so a source file that changes without a
    re-normalize is detectable in CI without shipping the raw bundles anywhere.
    Only the current eRSD release is included, since it is the only one read; a
    new release then shows up as one file removed and another added.
    """

    ersd_release = current_release(ersd_dir)
    return {
        **{
            path.name: file_hash(path)
            for path in sorted(raw_dir.glob("*.json"))
            if path.name != "manifest.json"
        },
        ersd_release.name: file_hash(ersd_release),
    }


def main(argv: list[str] | None = None) -> int:
    """Read the raw bundles and write the processed tables."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--ersd-dir", type=Path, default=ERSD_DIR)
    parser.add_argument("--out-dir", type=Path, default=PROCESSED_DIR)
    args = parser.parse_args(argv)

    args.out_dir.mkdir(parents=True, exist_ok=True)

    print(f"reading {args.raw_dir}")
    valuesets = load_raw_valuesets(args.raw_dir)
    ersd_release = current_release(args.ersd_dir)
    triggers = trigger_codes_by_snomed(
        json.loads(ersd_release.read_text(encoding="utf-8"))
    )
    print(
        f"  {len(valuesets):,} valuesets, {len(triggers):,} triggering SNOMED codes "
        f"from {ersd_release.name}"
    )

    tables = normalize(valuesets, triggers)
    code_rows = sorted(
        CodeRow(system_oid=oid, code=code, display=display)
        for (oid, code), display in tables.codes.items()
    )

    # headers come from the row types rather than being restated here: the two
    # used to be declared ~150 lines apart, so adding a column to one and not the
    # other shifted every value silently past every DictReader downstream
    outputs = {
        "conditions.csv.gz": _write_csv_gz(
            args.out_dir / "conditions.csv.gz", ConditionRow._fields, tables.conditions
        ),
        "valuesets.csv.gz": _write_csv_gz(
            args.out_dir / "valuesets.csv.gz", ValuesetRow._fields, tables.valuesets
        ),
        "codes.csv.gz": _write_csv_gz(
            args.out_dir / "codes.csv.gz", CodeRow._fields, code_rows
        ),
        "memberships.csv.gz": _write_csv_gz(
            args.out_dir / "memberships.csv.gz",
            MembershipRow._fields,
            tables.memberships,
        ),
        "summary.csv": _write_csv(
            args.out_dir / "summary.csv", SummaryRow._fields, tables.summary
        ),
    }

    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "counts": asdict(tables.counts),
        "dropped_by_system": dict(sorted(tables.dropped_by_system.items())),
        "files": {name: {"hash": digest} for name, digest in outputs.items()},
        "derived_from": source_hashes(args.raw_dir, args.ersd_dir),
    }
    (args.out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    for name, value in asdict(tables.counts).items():
        print(f"  {name:<28} {value:>10,}")
    print(f"wrote {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
