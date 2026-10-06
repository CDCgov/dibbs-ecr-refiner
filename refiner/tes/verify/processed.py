"""
Verify the processed tables against the raw bundles they came from.

Three properties, cheapest first:

1. **The processed files are intact.** Each file's hash matches the manifest.
2. **The processed files are current.** The raw bundle hashes recorded in
   `derived_from` -- the TES bundles and the current eRSD release -- still match
   the files on disk, so nobody changed a raw file without re-running normalize.
3. **The processed files are what normalize produces.** Regenerating into a
   scratch directory yields byte-identical output. This catches a hand-edited
   artifact, and a normalize change that was never applied to the committed data.

Property 3 subsumes 2, but 2 is nearly free and names the failure precisely, so
both run. Only this module needs the raw bundles, which is why it runs in dev and
CI rather than anywhere the ops container reaches.

Usage:
    python -m tes.verify.processed [--quick]
"""

import argparse
import contextlib
import csv
import gzip
import io
import json
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from tes.normalize.ersd import (
    ERSD_DIR,
    bundle_valuesets,
    current_release,
    focus_snomeds,
)
from tes.normalize.groupers import (
    is_additional_context_grouper,
    is_condition_grouper,
    is_reporting_spec_grouper,
)
from tes.normalize.model import KNOWN_CATEGORIES, KNOWN_UNSUPPORTED_SYSTEMS
from tes.normalize.readers import leaf_may_omit_concepts, release_has_expansion
from tes.normalize.run import (
    PROCESSED_DIR,
    RAW_DIR,
    file_hash,
    load_raw_valuesets,
    source_hashes,
)
from tes.normalize.run import (
    main as normalize_main,
)
from tes.verify.report import Result, render


def read_manifest(processed_dir: Path) -> dict | None:
    """
    Parse the processed manifest, or None when it is absent.

    Absence is a reportable failure rather than an exception so every check still
    runs and the report names what is wrong.
    """

    manifest_path = processed_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text())


def check_manifest_hashes(manifest: dict | None, processed_dir: Path) -> Result:
    """
    Every file the manifest names exists and still hashes to what it recorded.
    """

    if manifest is None:
        return Result(
            "Processed files match their manifest hashes",
            False,
            f"{processed_dir / 'manifest.json'} not found -- run `just tes normalize`",
        )

    failures = []
    for name, entry in manifest["files"].items():
        path = processed_dir / name
        if not path.exists():
            failures.append(f"{name}: missing")
        elif (actual := file_hash(path)) != entry["hash"]:
            failures.append(f"{name}: {actual[:12]} != {entry['hash'][:12]}")

    return Result(
        "Processed files match their manifest hashes",
        not failures,
        f"{len(manifest['files'])} files checked, {len(failures)} mismatched",
        failures,
    )


def check_derived_from(manifest: dict | None, raw_dir: Path, ersd_dir: Path) -> Result:
    """
    The raw bundles still hash to what normalize recorded when it last ran.

    Takes the parsed manifest rather than re-reading it: a missing manifest is a
    clean failure in `check_manifest_hashes`, and this reading the file again
    turned that into a crash that killed the rest of the run.
    """

    if manifest is None:
        return Result(
            "Processed data was built from the raw bundles on disk",
            False,
            "no manifest to compare against -- run `just tes normalize`",
        )

    recorded = manifest["derived_from"]
    actual = source_hashes(raw_dir, ersd_dir)

    failures = [
        f"{name}: added to raw, not in processed"
        for name in actual.keys() - recorded.keys()
    ]
    failures += [
        f"{name}: removed from raw, still in processed"
        for name in recorded.keys() - actual.keys()
    ]
    failures += [
        f"{name}: changed since normalize last ran"
        for name in recorded.keys() & actual.keys()
        if recorded[name] != actual[name]
    ]

    return Result(
        "Processed data was built from the raw bundles on disk",
        not failures,
        f"{len(recorded)} source files recorded, {len(failures)} out of date",
        failures,
    )


def check_regenerates_identically(
    processed_dir: Path, raw_dir: Path, ersd_dir: Path
) -> Result:
    """
    Re-running normalize into a scratch directory reproduces the committed files.
    """

    with tempfile.TemporaryDirectory() as scratch:
        scratch_dir = Path(scratch)
        # normalize narrates its own progress; this is a check, not a run
        with contextlib.redirect_stdout(io.StringIO()):
            normalize_main(
                [
                    "--raw-dir",
                    str(raw_dir),
                    "--ersd-dir",
                    str(ersd_dir),
                    "--out-dir",
                    str(scratch_dir),
                ]
            )

        failures = []
        for path in sorted(scratch_dir.iterdir()):
            committed = processed_dir / path.name
            if not committed.exists():
                failures.append(
                    f"{path.name}: normalize produced it, repo does not have it"
                )
            elif file_hash(committed) != file_hash(path):
                failures.append(f"{path.name}: committed copy differs from a fresh run")

        regenerated = {path.name for path in scratch_dir.iterdir()}
        failures += [
            f"{path.name}: in the repo, normalize does not produce it"
            for path in sorted(processed_dir.iterdir())
            if path.name not in regenerated
        ]

    return Result(
        "Committed processed data is exactly what normalize produces",
        not failures,
        f"{len(regenerated)} outputs regenerated and compared",
        failures,
    )


@dataclass
class MembershipFacts:
    """
    What the data-quality checks need from a single pass over the memberships.

    The membership table is two million rows; reading it once and answering
    several questions from that pass keeps verification a few seconds rather
    than a few minutes.

    Attributes:
        conditions_with_codes: (url, version) of every condition holding at
            least one membership.
        conditions_by_self_naming_code: for each SNOMED code flagged
            `is_child_rsg`, the set of condition urls claiming it.
    """

    conditions_with_codes: set[tuple[str, str]]
    conditions_by_self_naming_code: dict[tuple[str, str], set[str]]


def _is_true(value: str) -> bool:
    """
    Parse a boolean out of CSV without depending on how it was written.

    `csv.writer` renders Python's True as "True"; Postgres, pandas and polars all
    write something different. Matching one spelling means a writer change makes
    every row read as False and `check_self_naming_codes_are_unique` passes on an
    empty set.
    """

    return value.strip().lower() in {"true", "t", "1", "yes"}


def read_membership_facts(processed_dir: Path) -> MembershipFacts:
    """
    Make one pass over memberships.csv.gz and collect what the checks need.
    """

    with_codes: set[tuple[str, str]] = set()
    by_code: dict[tuple[str, str], set[str]] = defaultdict(set)

    with gzip.open(
        processed_dir / "memberships.csv.gz", "rt", encoding="utf-8", newline=""
    ) as handle:
        for row in csv.DictReader(handle):
            with_codes.add((row["condition_url"], row["condition_version"]))
            if _is_true(row["is_child_rsg"]):
                by_code[(row["system_oid"], row["code"])].add(row["condition_url"])

    return MembershipFacts(with_codes, dict(by_code))


def check_every_condition_has_codes(
    processed_dir: Path, facts: MembershipFacts
) -> Result:
    """
    Every condition resolves to at least one code.

    A condition with none means its children failed to resolve, or resolved to
    groupers that published nothing -- either way it would seed as a condition
    nobody can configure.
    """

    conditions = _read_rows(processed_dir / "conditions.csv.gz")
    empty = [
        f"{row['display_name']} ({row['version']})"
        for row in conditions
        if (row["canonical_url"], row["version"]) not in facts.conditions_with_codes
    ]

    return Result(
        "Every condition resolves to at least one code",
        not empty,
        f"{len(conditions):,} conditions, {len(empty)} with no codes",
        empty,
    )


def check_self_naming_codes_are_unique(facts: MembershipFacts) -> Result:
    """
    No SNOMED code names more than one condition's reporting specification grouper.

    `is_child_rsg` means "this code is the SNOMED that names its own RSG", so a
    code claimed by two conditions means two conditions believe they are the same
    reportable condition.
    """

    shared = [
        f"{code}: claimed by {len(urls)} conditions"
        for (_, code), urls in sorted(facts.conditions_by_self_naming_code.items())
        if len(urls) > 1
    ]

    return Result(
        "Each self-naming SNOMED code belongs to one condition",
        not shared,
        f"{len(facts.conditions_by_self_naming_code):,} self-naming codes checked",
        shared,
    )


def check_categories_are_known(valuesets: list[dict[str, str]]) -> Result:
    """
    Every valueset category is one the application understands.

    `category_for` falls back to a snake_case slug rather than failing, so a
    category TES adds mid-release lands in the data silently. This is where that
    surfaces -- the app's filters and grouping are built around the known set.
    """

    unknown = sorted({row["category"] for row in valuesets} - KNOWN_CATEGORIES)

    return Result(
        "Every valueset category is a known slug",
        not unknown,
        f"{len(valuesets):,} valuesets across "
        f"{len({row['category'] for row in valuesets})} categories",
        [f"{category}: not in KNOWN_CATEGORIES" for category in unknown],
    )


def check_no_empty_valuesets(valuesets: list[dict[str, str]]) -> Result:
    """
    No leaf grouper projected zero codes.
    """

    empty = [
        f"{row['display_name']} ({row['canonical_url']})"
        for row in valuesets
        if row["code_count"] == "0"
    ]

    return Result(
        "No valueset projected zero codes",
        not empty,
        f"{len(valuesets):,} valuesets, {len(empty)} empty",
        empty,
    )


def check_text_outputs_use_lf(processed_dir: Path) -> Result:
    """
    Committed text output uses LF line endings.

    `.gitattributes` declares `*.csv text eol=lf`, so git normalizes CRLF on the
    way in and hands LF back on checkout. A writer emitting CRLF therefore hashes
    one way locally and another after a fresh clone, which surfaces as an opaque
    manifest mismatch in CI. This names the cause directly instead.
    """

    offenders = []
    for path in sorted(processed_dir.glob("*.csv")):
        carriage_returns = path.read_bytes().count(b"\r")
        if carriage_returns:
            offenders.append(f"{path.name}: {carriage_returns:,} CR bytes, expected 0")

    return Result(
        "Committed text output uses LF line endings",
        not offenders,
        f"{len(list(processed_dir.glob('*.csv')))} plain-text outputs checked",
        offenders,
    )


def check_dropped_systems_are_expected(manifest: dict | None) -> Result:
    """
    The set of unsupported code systems is exactly the one we decided to drop.

    A new entry means TES started publishing a system the refiner ignores, and
    somebody has to decide whether it belongs in CODE_SYSTEMS -- rather than
    discovering months later that codes were being discarded.
    """

    if manifest is None:
        return Result(
            "Dropped code systems are all expected",
            False,
            "no manifest to read the drop set from -- run `just tes normalize`",
        )

    dropped = manifest.get("dropped_by_system", {})
    unexpected = sorted(set(dropped) - KNOWN_UNSUPPORTED_SYSTEMS)

    return Result(
        "Dropped code systems are all expected",
        not unexpected,
        f"{len(dropped)} unsupported systems, {sum(dropped.values()):,} codes dropped",
        [
            f"{url}: {dropped[url]:,} codes, not in KNOWN_UNSUPPORTED_SYSTEMS"
            for url in unexpected
        ],
    )


def _read_rows(path: Path) -> list[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def check_schema_era_assumptions(raw_dir: Path) -> Result:
    """
    The raw bundles still have the shape their release is documented to have.

    `tes/normalize/readers.py` records when `expansion.contains` appeared and when
    `concept[]` became optional. Those are claims about TES, measured from the
    bundles, and TES has moved both before. Asserting them is what turns the
    release table from a comment into something that fails when the next release
    moves the data again -- which is how the 4.0.0 expansion boundary was found
    in the first place.
    """

    failures = []
    bundles = load_raw_valuesets(raw_dir)

    for (_, version), valueset in bundles.items():
        has_expansion = bool((valueset.get("expansion") or {}).get("contains"))
        has_concepts = any(
            include.get("concept")
            for include in (valueset.get("compose") or {}).get("include", [])
        )
        title = valueset.get("title") or valueset.get("url", "?")

        expected_expansion = release_has_expansion(version)
        if has_expansion is not expected_expansion:
            failures.append(
                f"{title} ({version}): expansion is "
                f"{'present' if has_expansion else 'absent'}, release table says "
                f"{'present' if expected_expansion else 'absent'}"
            )

        is_leaf = is_reporting_spec_grouper(valueset) or is_additional_context_grouper(
            valueset
        )
        if is_leaf:
            if not has_concepts and not leaf_may_omit_concepts(version):
                failures.append(
                    f"{title} ({version}): leaf grouper has no concept[], which this "
                    "release is not documented to allow"
                )
            if not has_concepts and not has_expansion:
                failures.append(
                    f"{title} ({version}): leaf grouper publishes no codes at all"
                )
        elif is_condition_grouper(valueset) and has_concepts:
            failures.append(
                f"{title} ({version}): condition grouper declares codes inline; "
                "it is supposed to be a manifest"
            )

    return Result(
        "Raw bundles match the shape their release is documented to have",
        not failures,
        f"{len(bundles):,} valuesets checked against the release table",
        failures,
    )


def check_ersd_shape(ersd_dir: Path) -> Result:
    """
    The current eRSD release still has the v3 shape `tes/normalize/ersd.py` reads.

    The reader relies on a clean split: groupers name members and carry no
    `focus`, while every member names at least one condition and publishes its
    codes in `expansion.contains`. A member with no `focus` would have its codes
    silently dropped, which is the failure worth catching before it reaches the
    flags.
    """

    release = current_release(ersd_dir)
    valuesets = bundle_valuesets(json.loads(release.read_text(encoding="utf-8")))

    failures = []
    for valueset in valuesets:
        is_grouper = any(
            include.get("valueSet")
            for include in (valueset.get("compose") or {}).get("include", [])
        )
        has_focus = bool(focus_snomeds(valueset))
        has_codes = bool((valueset.get("expansion") or {}).get("contains"))
        title = valueset.get("title") or valueset.get("url", "?")

        if is_grouper and has_focus:
            failures.append(f"{title}: grouper names a focus condition")
        elif not is_grouper and not has_focus:
            failures.append(f"{title}: member names no focus condition")
        elif not is_grouper and not has_codes:
            failures.append(f"{title}: member has no expansion.contains")

    return Result(
        "Current eRSD release has the shape the trigger-code reader expects",
        not failures,
        f"{len(valuesets):,} valuesets in {release.name} checked",
        failures,
    )


def main(argv: list[str] | None = None) -> int:
    """
    Run the raw-to-processed checks.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--ersd-dir", type=Path, default=ERSD_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument(
        "--quick",
        action="store_true",
        help=(
            "skip the checks that re-read every raw bundle (~25s); the "
            "cheaper raw hash comparison still runs"
        ),
    )
    parser.add_argument(
        "--integrity-only",
        action="store_true",
        help=(
            "only check the processed files against their own manifest. This is "
            "the one mode needing nothing but data/processed, so it is what the "
            "ops container runs before seeding."
        ),
    )
    args = parser.parse_args(argv)

    manifest = read_manifest(args.processed_dir)

    if args.integrity_only:
        return render(
            [
                check_manifest_hashes(manifest, args.processed_dir),
                check_text_outputs_use_lf(args.processed_dir),
            ]
        )

    facts = read_membership_facts(args.processed_dir)
    valuesets = _read_rows(args.processed_dir / "valuesets.csv.gz")
    results = [
        check_manifest_hashes(manifest, args.processed_dir),
        check_derived_from(manifest, args.raw_dir, args.ersd_dir),
        check_every_condition_has_codes(args.processed_dir, facts),
        check_self_naming_codes_are_unique(facts),
        check_categories_are_known(valuesets),
        check_no_empty_valuesets(valuesets),
        check_text_outputs_use_lf(args.processed_dir),
        check_dropped_systems_are_expected(manifest),
    ]
    # these re-read every raw bundle and are the slowest, so they run last
    if not args.quick:
        results.append(check_schema_era_assumptions(args.raw_dir))
        results.append(check_ersd_shape(args.ersd_dir))
        results.append(
            check_regenerates_identically(
                args.processed_dir, args.raw_dir, args.ersd_dir
            )
        )

    return render(results)


if __name__ == "__main__":
    sys.exit(main())
