"""Compare refinement output with the recorded baseline without rewriting it."""

from difflib import unified_diff
from itertools import islice
from pathlib import Path

import pytest
from lxml import etree

from scripts.snapshot_generator.generate_snapshots import (
    EXPECTED_DIR,
    collect_snapshot_files,
    iter_snapshot_files,
)


def _recorded_paths() -> list[Path]:
    return sorted(
        path.relative_to(EXPECTED_DIR)
        for path in EXPECTED_DIR.rglob("*")
        if path.is_file()
    )


def _xml_diff(expected: bytes, actual: bytes) -> str:
    """Format copies for a bounded text diff after the raw-byte comparison fails."""
    try:
        parser = etree.XMLParser(remove_blank_text=True, resolve_entities=False)
        documents = [
            etree.tostring(
                etree.fromstring(data, parser), encoding="unicode", pretty_print=True
            ).splitlines()
            for data in (expected, actual)
        ]
    except etree.XMLSyntaxError:
        documents = [
            data.decode("utf-8", errors="replace").splitlines()
            for data in (expected, actual)
        ]
    lines = list(
        islice(
            unified_diff(*documents, fromfile="expected", tofile="actual", lineterm=""),
            81,
        )
    )
    if not lines:
        return (
            "Raw XML bytes differ, but the displayed XML is identical.\n"
            "Check trailing newlines, whitespace, or XML serialization."
        )
    diff = "\n".join(lines[:80])
    if len(lines) > 80 or len(diff) > 8000:
        return diff[:8000] + "\n... XML diff truncated (80 lines / 8000 characters)."
    return diff


@pytest.fixture(scope="module")
def actual_outputs() -> dict[Path, bytes]:
    """Run the complete fixture corpus once, keeping actual output in memory."""
    return collect_snapshot_files(iter_snapshot_files())


def test_output_inventory_matches_baseline(actual_outputs: dict[Path, bytes]) -> None:
    """Catch missing baselines, missing generated outputs, and stale files."""
    recorded = set(_recorded_paths())
    assert recorded, f"No recorded baseline files found in {EXPECTED_DIR}"

    generated = set(actual_outputs)
    missing_baselines = sorted(generated - recorded)
    missing_outputs = sorted(recorded - generated)
    failures = [
        f"Missing recorded baseline: {path.as_posix()}" for path in missing_baselines
    ]
    failures.extend(
        f"Missing generated output: {path.as_posix()}" for path in missing_outputs
    )
    if failures:
        pytest.fail(
            "Output inventory differs from the recorded baseline:\n"
            + "\n".join(failures),
            pytrace=False,
        )


@pytest.mark.parametrize(
    "relative_path", _recorded_paths(), ids=lambda path: path.as_posix()
)
def test_refinement_matches_recorded_bytes(
    relative_path: Path, actual_outputs: dict[Path, bytes]
) -> None:
    """Compare raw XML bytes, including whitespace and IDs."""
    name = relative_path.as_posix()
    expected_path = EXPECTED_DIR / relative_path
    if not expected_path.is_file():
        pytest.fail(f"Missing recorded baseline: {name}", pytrace=False)
    if relative_path not in actual_outputs:
        pytest.fail(f"Missing generated output: {name}", pytrace=False)

    expected = expected_path.read_bytes()
    actual = actual_outputs[relative_path]
    if actual != expected:
        pytest.fail(
            f"Output differs from baseline: {name}\n{_xml_diff(expected, actual)}",
            pytrace=False,
        )
