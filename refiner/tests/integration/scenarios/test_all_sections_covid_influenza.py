import json
from pathlib import Path

import pytest

from ...unit.conftest import normalize_xml
from .conftest import SCENARIOS, Scenario, load_scenario_xml_files
from .harness import refine_one

# NOTE:
# SNAPSHOT PATHS
# =============================================================================
# snapshots live alongside the tests, not alongside the fixtures: a fixture is
# a static input but the snapshot is an output of refinement, and a single
# fixture may be exercised by multiple tests

SNAPSHOT_ROOT: Path = Path(__file__).parent / "snapshots"


def _snapshot_dir(scenario: Scenario) -> Path:
    return SNAPSHOT_ROOT / Path(scenario.fixture_dir).name / scenario.name


# NOTE:
# SUMMARY DICT (the contents of expected_trace.json)
# =============================================================================
# a small, stable, human-readable dict pulled from the RefinementResult
# * sorted-key json serialization makes diffs trivial to read


def _summary_from_result(result) -> dict:  # noqa: ANN001 - RefinementResult, avoid import cycle
    return {
        "refinement_outcome": result.trace.refinement_outcome,
        "configuration_resolved": result.trace.configuration_resolved,
        "configuration_version": result.trace.configuration_version,
        "canonical_url": result.trace.canonical_url,
        "skip_reason": result.trace.skip_reason,
        "error_detail": result.trace.error_detail,
        "eicr_size_reduction_percentage": result.trace.eicr_size_reduction_percentage,
        "augmented_eicr_id": result.augmented_eicr_result.augmented_doc_id,
        "augmented_rr_id": result.augmented_rr_result.augmented_doc_id,
        "original_eicr_id": result.augmented_eicr_result.original_doc_id,
        "original_rr_id": result.augmented_rr_result.original_doc_id,
    }


# NOTE:
# THE PARAMETRIZED TEST
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s.name for s in SCENARIOS])
async def test_scenario_matches_snapshot(
    scenario: Scenario,
    setup,
    update_snapshots: bool,
    validate_refined_document,
    build_scenario_configuration,
    test_user_jurisdiction_id,
) -> None:
    """
    Build the scenario's configuration through the API, refine the fixture for
    its condition, validate the refined documents, then compare the result
    against committed snapshots.

    Validation (well-formedness, CDA R2 XSD, schematron) runs first so invalid
    output fails the test loudly rather than getting committed as an "expected"
    snapshot. Pass --update-snapshots to overwrite the committed files with the
    current output instead of comparing; use when refinement behavior
    legitimately changes.
    """

    xml_files = load_scenario_xml_files(scenario)
    processed_configuration, canonical_url = await build_scenario_configuration(
        scenario
    )

    result = refine_one(
        xml_files=xml_files,
        processed_configuration=processed_configuration,
        # augmentation is seeded by the jurisdiction the config was activated
        # under (the live test infra: SDDH), NOT the RR's reportable-to
        # jurisdiction. the fixture RR may be reportable elsewhere; that is
        # intentionally not consulted here--it is not a refinement input, and
        # bypassing it lets us reuse arbitrary test data without standing up
        # matching fake jurisdictions
        jurisdiction_code=test_user_jurisdiction_id,
        rsg_code=scenario.rsg_code,
        canonical_url=canonical_url,
        configuration_version=scenario.configuration_version,
    )

    # VALIDATE FIRST
    # catch invalid refined output before either committing it as a
    # snapshot (update mode) or attempting to compare against a possibly
    # stale snapshot (compare mode)
    validate_refined_document(result.refined_eicr, "eICR", scenario.name)
    validate_refined_document(result.refined_rr, "RR", scenario.name)

    actual_summary = _summary_from_result(result)
    actual_eicr = normalize_xml(result.refined_eicr)
    actual_rr = normalize_xml(result.refined_rr)

    snapshot_dir = _snapshot_dir(scenario)
    trace_path = snapshot_dir / "expected_trace.json"
    eicr_path = snapshot_dir / "expected_eICR.xml"
    rr_path = snapshot_dir / "expected_RR.xml"

    # WRITE PATH
    # update mode: write current output as the new snapshot, then pass
    # * always run a print so the user has visible confirmation of what
    #   was written, even when many scenarios are regenerated at once
    if update_snapshots:
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        trace_path.write_text(
            json.dumps(actual_summary, indent=2, sort_keys=True) + "\n"
        )
        eicr_path.write_text(actual_eicr + "\n")
        rr_path.write_text(actual_rr + "\n")
        print(f"\nSnapshot updated: {snapshot_dir.relative_to(SNAPSHOT_ROOT.parent)}")
        return

    # COMPARE PATH
    # missing snapshots fail with a clear pointer at --update-snapshots
    # rather than a cryptic FileNotFoundError.
    missing = [p for p in (trace_path, eicr_path, rr_path) if not p.exists()]
    if missing:
        listing = "\n".join(f"  - {p}" for p in missing)
        pytest.fail(
            f"Snapshot files missing for scenario '{scenario.name}':\n{listing}\n\n"
            "Run with --update-snapshots to generate them, then commit."
        )

    # Tier 1:
    # summary: read first, fails fast on top-line regressions
    expected_summary = json.loads(trace_path.read_text())
    assert actual_summary == expected_summary, (
        f"Summary snapshot mismatch for '{scenario.name}'.\n"
        "The summary catches top-line regressions:\n"
        "  - refinement_outcome change -> a section's match disposition changed\n"
        "  - eicr_size_reduction_percentage change -> different entries retained\n"
        "  - augmented_*_id change -> identifier derivation changed (UUIDv5 seed)\n"
        "  - original_*_id change -> the source fixture changed\n"
        f"Inspect, decide if intentional, then re-run with --update-snapshots.\n"
        f"File: {trace_path}"
    )

    # Tier 2:
    # structural truth: the refined eICR
    expected_eicr = eicr_path.read_text().rstrip("\n")
    assert actual_eicr == expected_eicr, (
        f"Refined eICR snapshot mismatch for '{scenario.name}'.\n"
        f"File: {eicr_path}\n"
        "If intentional, re-run with --update-snapshots and inspect the diff."
    )

    # Tier 3:
    # the refined RR
    expected_rr = rr_path.read_text().rstrip("\n")
    assert actual_rr == expected_rr, (
        f"Refined RR snapshot mismatch for '{scenario.name}'.\n"
        f"File: {rr_path}\n"
        "If intentional, re-run with --update-snapshots and inspect the diff."
    )
