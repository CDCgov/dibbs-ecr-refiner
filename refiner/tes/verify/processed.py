"""
Verify the processed tables against the raw bundles they came from.

Three properties, cheapest first:

1. **The processed files are intact.** Each file's hash matches the manifest.
2. **The processed files are current.** The raw bundle hashes recorded in
   `derived_from` still match the bundles on disk, so nobody changed a raw file
   without re-running normalize.
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
    _file_hash,
    _source_hashes,
    load_raw_valuesets,
)
from tes.normalize.run import (
    main as normalize_main,
)
from tes.verify.report import Result, render


def check_manifest_hashes(processed_dir: Path) -> Result:
    """Every file the manifest names exists and still hashes to what it recorded."""

    manifest_path = processed_dir / "manifest.json"
    if not manifest_path.exists():
        return Result(
            "Processed files match their manifest hashes",
            False,
            f"{manifest_path} not found -- run `just tes normalize`",
        )

    manifest = json.loads(manifest_path.read_text())
    failures = []
    for name, entry in manifest["files"].items():
        path = processed_dir / name
        if not path.exists():
            failures.append(f"{name}: missing")
        elif (actual := _file_hash(path)) != entry["hash"]:
            failures.append(f"{name}: {actual[:12]} != {entry['hash'][:12]}")

    return Result(
        "Processed files match their manifest hashes",
        not failures,
        f"{len(manifest['files'])} files checked, {len(failures)} mismatched",
        failures,
    )


def check_derived_from(processed_dir: Path, raw_dir: Path) -> Result:
    """The raw bundles still hash to what normalize recorded when it last ran."""

    manifest = json.loads((processed_dir / "manifest.json").read_text())
    recorded = manifest["derived_from"]
    actual = _source_hashes(raw_dir)

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


def check_regenerates_identically(processed_dir: Path, raw_dir: Path) -> Result:
    """Re-running normalize into a scratch directory reproduces the committed files."""

    with tempfile.TemporaryDirectory() as scratch:
        scratch_dir = Path(scratch)
        # normalize narrates its own progress; this is a check, not a run
        with contextlib.redirect_stdout(io.StringIO()):
            normalize_main(["--raw-dir", str(raw_dir), "--out-dir", str(scratch_dir)])

        failures = []
        for path in sorted(scratch_dir.iterdir()):
            committed = processed_dir / path.name
            if not committed.exists():
                failures.append(
                    f"{path.name}: normalize produced it, repo does not have it"
                )
            elif _file_hash(committed) != _file_hash(path):
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


def read_membership_facts(processed_dir: Path) -> MembershipFacts:
    """Make one pass over memberships.csv.gz and collect what the checks need."""

    with_codes: set[tuple[str, str]] = set()
    by_code: dict[tuple[str, str], set[str]] = defaultdict(set)

    with gzip.open(
        processed_dir / "memberships.csv.gz", "rt", encoding="utf-8", newline=""
    ) as handle:
        for row in csv.DictReader(handle):
            with_codes.add((row["condition_url"], row["condition_version"]))
            if row["is_child_rsg"] == "True":
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


def check_categories_are_known(processed_dir: Path) -> Result:
    """
    Every valueset category is one the application understands.

    `category_for` falls back to a snake_case slug rather than failing, so a
    category TES adds mid-release lands in the data silently. This is where that
    surfaces -- the app's filters and grouping are built around the known set.
    """

    rows = _read_rows(processed_dir / "valuesets.csv.gz")
    unknown = sorted({row["category"] for row in rows} - KNOWN_CATEGORIES)

    return Result(
        "Every valueset category is a known slug",
        not unknown,
        f"{len(rows):,} valuesets across {len({r['category'] for r in rows})} categories",
        [f"{category}: not in KNOWN_CATEGORIES" for category in unknown],
    )


def check_no_empty_valuesets(processed_dir: Path) -> Result:
    """No leaf grouper projected zero codes."""

    rows = _read_rows(processed_dir / "valuesets.csv.gz")
    empty = [
        f"{row['display_name']} ({row['canonical_url']})"
        for row in rows
        if row["code_count"] == "0"
    ]

    return Result(
        "No valueset projected zero codes",
        not empty,
        f"{len(rows):,} valuesets, {len(empty)} empty",
        empty,
    )


def check_dropped_systems_are_expected(processed_dir: Path) -> Result:
    """
    The set of unsupported code systems is exactly the one we decided to drop.

    A new entry means TES started publishing a system the refiner ignores, and
    somebody has to decide whether it belongs in CODE_SYSTEMS -- rather than
    discovering months later that codes were being discarded.
    """

    manifest = json.loads((processed_dir / "manifest.json").read_text())
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
    checked = 0

    for (_, version), valueset in load_raw_valuesets(raw_dir).items():
        has_expansion = bool((valueset.get("expansion") or {}).get("contains"))
        has_concepts = any(
            include.get("concept")
            for include in (valueset.get("compose") or {}).get("include", [])
        )
        title = valueset.get("title") or valueset.get("url", "?")
        checked += 1

        if has_expansion is not release_has_expansion(version):
            failures.append(
                f"{title} ({version}): expansion is "
                f"{'present' if has_expansion else 'absent'}, release table says "
                f"{'present' if not has_expansion else 'absent'}"
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
        f"{checked:,} valuesets checked against the release table",
        failures,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the raw-to-processed checks."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="skip the checks that re-read the raw bundles (~25s)",
    )
    parser.add_argument(
        "--integrity-only",
        action="store_true",
        help=(
            "only verify the processed files against their own manifest. This is "
            "the one check that needs nothing but data/processed, so it is what "
            "the ops container can run before seeding."
        ),
    )
    args = parser.parse_args(argv)

    if args.integrity_only:
        return render([check_manifest_hashes(args.processed_dir)])

    facts = read_membership_facts(args.processed_dir)
    results = [
        check_manifest_hashes(args.processed_dir),
        check_derived_from(args.processed_dir, args.raw_dir),
        check_every_condition_has_codes(args.processed_dir, facts),
        check_self_naming_codes_are_unique(facts),
        check_categories_are_known(args.processed_dir),
        check_no_empty_valuesets(args.processed_dir),
        check_dropped_systems_are_expected(args.processed_dir),
    ]
    # these two need the raw bundles and are the slowest, so they run last
    if not args.quick:
        results.append(check_schema_era_assumptions(args.raw_dir))
        results.append(check_regenerates_identically(args.processed_dir, args.raw_dir))

    return render(results)


if __name__ == "__main__":
    sys.exit(main())
