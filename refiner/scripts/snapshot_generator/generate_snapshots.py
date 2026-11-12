"""Create expected XML files for the refinement parity tests.

Run from refiner/:
    python -m scripts.snapshot_generator.generate_snapshots

This script runs fixtures through Refiner using the saved cases and configurations
in tests/fixtures/parity/. It uses the same settings and augmentation time on every
run so the parity tests can check whether changes to eCR specification code affect
Refiner's output.

The XML is saved in tests/fixtures/expected/, overwriting existing snapshots.
"""

import argparse
import json
from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import replace
from fnmatch import fnmatchcase
from pathlib import Path
from zipfile import ZipFile

from lxml import etree

from app.core.models.types import XMLFiles
from app.services.ecr.model import HL7_NS
from app.services.ecr.section import process_section
from app.services.ecr.specification import load_spec
from app.services.ecr.specification.constants import OID_TO_SYSTEM_KEY_MAP
from app.services.pipeline import (
    RefinementContext,
    create_augmentation_run_from_xml_files,
    discover_reportable_conditions,
    refine_for_condition,
)
from app.services.terminology import CodeSystemSets, ProcessedConfiguration
from tests.fixtures.manifest import (
    FIXTURE_DIR,
    IGNORED_ARCHIVE_MEMBER_PATTERNS,
    PAIRS,
    SECTION_FIXTURES,
    FixturePair,
    SectionFixture,
)

PARITY_DIR = FIXTURE_DIR / "parity"
EXPECTED_DIR = FIXTURE_DIR / "expected"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_bytes())


def validate_manifest() -> None:
    """Fail when an input is unlisted, missing, or an archive member is ambiguous."""
    names = [item["name"] for item in [*PAIRS, *SECTION_FIXTURES]]
    if len(names) != len(set(names)):
        raise ValueError("Fixture manifest names must be unique")
    referenced = {item["path"] for item in SECTION_FIXTURES}
    archive_members: dict[str, set[str]] = defaultdict(set)
    for pair in PAIRS:
        if "archive" in pair:
            referenced.add(pair["archive"])
            archive_members[pair["archive"]].update((pair["eicr"], pair["rr"]))
        else:
            referenced.update((pair["eicr"], pair["rr"]))
    discovered = {
        path.relative_to(FIXTURE_DIR).as_posix()
        for path in FIXTURE_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".xml", ".zip"}
        and path.relative_to(FIXTURE_DIR).parts[0] != "expected"
    }
    if referenced != discovered:
        raise ValueError(
            f"Fixture inventory differs from manifest: "
            f"unlisted={sorted(discovered - referenced)}, "
            f"missing={sorted(referenced - discovered)}"
        )
    for archive_path, selected in archive_members.items():
        with ZipFile(FIXTURE_DIR / archive_path) as archive:
            members = [
                item.filename for item in archive.infolist() if not item.is_dir()
            ]
        for member in selected:
            if members.count(member) != 1:
                raise ValueError(
                    f"{archive_path}: expected exactly one member {member}"
                )
        unlisted = [
            member
            for member in members
            if member not in selected
            and not any(
                fnmatchcase(member, pattern)
                for pattern in IGNORED_ARCHIVE_MEMBER_PATTERNS
            )
        ]
        if unlisted:
            raise ValueError(f"{archive_path}: unlisted archive members {unlisted}")


def load_pair(pair: FixturePair) -> XMLFiles:
    """Read exact loose files or archive members without newline translation."""
    if "archive" in pair:
        with ZipFile(FIXTURE_DIR / pair["archive"]) as archive:
            eicr = archive.read(pair["eicr"])
            rr = archive.read(pair["rr"])
    else:
        eicr = (FIXTURE_DIR / pair["eicr"]).read_bytes()
        rr = (FIXTURE_DIR / pair["rr"]).read_bytes()
    return XMLFiles(eicr=eicr.decode("utf-8"), rr=rr.decode("utf-8"))


def _check_case_coverage(cases: list[dict], fixture_names: set[str]) -> None:
    """Require exactly one case definition for every manifest fixture."""
    listed = [case["fixture"] for case in cases]
    if len(listed) != len(set(listed)) or set(listed) != fixture_names:
        raise ValueError(
            "Fixed cases must cover every fixture exactly once: "
            f"missing={sorted(fixture_names - set(listed))}, "
            f"unexpected={sorted(set(listed) - fixture_names)}, "
            f"duplicates={sorted(name for name in set(listed) if listed.count(name) > 1)}"
        )


def _full_document_snapshot_files(
    pair: FixturePair, case: dict, augmentation_time: str
) -> Iterator[tuple[Path, bytes]]:
    """Check RR discovery and replay the pair's recorded configurations."""
    files = load_pair(pair)
    reportable = {
        group.jurisdiction: sorted(condition.code for condition in group.conditions)
        for group in discover_reportable_conditions(files)
    }
    if reportable != case["reportable_conditions"]:
        raise ValueError(
            f"{pair['name']}: RR reportable conditions changed; "
            f"expected {case['reportable_conditions']}, got {reportable}"
        )
    if not case["scenarios"]:
        raise ValueError(f"{pair['name']}: no fixed refinement scenarios")
    run = replace(
        create_augmentation_run_from_xml_files(files),
        augmentation_time=augmentation_time,
    )
    source_directory = Path(pair.get("archive", pair["eicr"])).parts[0]
    for scenario in case["scenarios"]:
        directory = Path(source_directory) / pair["name"] / scenario["name"]
        try:
            payload = _read_json(PARITY_DIR / scenario["configuration"])
            result = refine_for_condition(
                xml_files=files,
                processed_configuration=ProcessedConfiguration.from_dict(payload),
                context=RefinementContext(
                    configuration_version=1,
                    **scenario["context"],
                ),
                run=run,
            )
        except Exception as error:
            raise RuntimeError(f"{directory}: refinement failed") from error
        yield directory / "eICR.xml", result.documents.eicr.encode("utf-8")
        yield directory / "RR.xml", result.documents.rr.encode("utf-8")


def _section_snapshot_files(
    fixture: SectionFixture, case: dict, augmentation_time: str
) -> Iterator[tuple[Path, bytes]]:
    """Refine and reconstruct a fragment under the three fixed specification versions."""
    source = (FIXTURE_DIR / fixture["path"]).read_bytes()
    codes = CodeSystemSets.from_dict(case["code_system_sets"], OID_TO_SYSTEM_KEY_MAP)
    for version in ("1.1", "3.1", "3.1.1"):
        directory = Path("sections") / fixture["name"] / version
        try:
            section = etree.fromstring(source)
            process_section(
                section=section,
                codes_to_match=codes.all_codes,
                namespaces=HL7_NS,
                section_specification=load_spec(version).sections[case["loinc"]],
                code_system_sets=codes,
                augmentation_timestamp=augmentation_time,
                narrative="reconstruct",
            )
        except Exception as error:
            raise RuntimeError(f"{directory}: section refinement failed") from error
        yield directory / "section.xml", etree.tostring(section, encoding="utf-8")


def iter_snapshot_files() -> Iterator[tuple[Path, bytes]]:
    """Replay fixed inputs; yield XML without writing or normalizing it."""
    validate_manifest()
    catalog = _read_json(PARITY_DIR / "cases.json")
    pairs = {pair["name"]: pair for pair in PAIRS}
    sections = {fixture["name"]: fixture for fixture in SECTION_FIXTURES}
    _check_case_coverage(catalog["pairs"], set(pairs))
    _check_case_coverage(catalog["sections"], set(sections))
    for case in catalog["pairs"]:
        yield from _full_document_snapshot_files(
            pairs[case["fixture"]], case, catalog["augmentation_time"]
        )
    for case in catalog["sections"]:
        yield from _section_snapshot_files(
            sections[case["fixture"]], case, catalog["augmentation_time"]
        )


def collect_snapshot_files(files: Iterable[tuple[Path, bytes]]) -> dict[Path, bytes]:
    """Reject duplicate output paths so a case cannot overwrite another case."""
    outputs: dict[Path, bytes] = {}
    for path, data in files:
        if path in outputs:
            raise ValueError(f"Duplicate snapshot output: {path}")
        outputs[path] = data
    return outputs


def generate_snapshots() -> int:
    """Generate all XML before overwriting expected files."""
    outputs = collect_snapshot_files(iter_snapshot_files())
    for path, data in outputs.items():
        destination = EXPECTED_DIR / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    return len(outputs)


def main() -> None:
    """Generate or refresh the snapshots in tests/fixtures/expected."""
    argparse.ArgumentParser(description=__doc__).parse_args()
    count = generate_snapshots()
    print(f"Wrote {count} refined XML documents to {EXPECTED_DIR}")


if __name__ == "__main__":
    main()
