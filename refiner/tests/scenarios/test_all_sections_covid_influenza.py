import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from app.core.models.types import XMLFiles
from app.services.terminology import ProcessedConfiguration

from ..fixtures.loader import load_fixture_str
from ..unit.conftest import normalize_xml
from .harness import refine_one

# NOTE:
# SCENARIO DEFINITIONS
# =============================================================================
# each Scenario identifies one (fixture, configuration, condition) triple:
# * to add a scenario, append an entry below; the parametrized test picks it
# up automatically


@dataclass(frozen=True)
class Scenario:
    """
    One refinement scenario: fixture + configuration + condition to refine for.

    Fields fall into three groups by snapshot impact:

    Filesystem paths — no snapshot impact:
      `name` — parametrize id and snapshot subdirectory name.
      `fixture_dir` — directory under tests/fixtures/.
      `config_filename` — file under <fixture_dir>/configurations/.

    Augmentation seeds: changing these regenerates ALL snapshots (trace,
    eICR, RR) because they thread into the deterministic UUIDv5 derivation
    that produces the augmented document identifiers, which appear in the
    trace JSON and in the augmentation headers of the refined eICR/RR:
      `jurisdiction_code` — not checked against the RR's jurisdiction; an
        arbitrary stable label.
      `canonical_url` — connected to the Condition Grouper of the
        `rsg_code`; its trailing UUID is the condition_grouper_uuid in
        the seed.

    Recorded metadata: appears in expected_trace.json but doesn't affect
    refinement or the XML snapshots; changing these regenerates only the
    trace JSON:
      `configuration_version` — arbitrary discriminator; incremented per
        scenario.

    Pure metadata — no snapshot impact at all:
      `rsg_code` — the reportable SNOMED code we declare as the condition
        being refined for. Recorded on the internal RefinementTrace for
        observability but does not drive refinement (the
        ProcessedConfiguration does) and does not seed augmentation.
    """

    name: str
    fixture_dir: str
    config_filename: str
    jurisdiction_code: str
    rsg_code: str
    canonical_url: str
    configuration_version: int


SCENARIOS: list[Scenario] = [
    Scenario(
        name="covid_baseline",
        fixture_dir="all_sections_COVID_INFLUENZA",
        config_filename="covid_baseline.json",
        jurisdiction_code="TEST-JD",
        rsg_code="840539006",  # covid-19 disorder
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "07221093-b8a1-4b1d-8678-259277bfba64"
        ),
        configuration_version=1,
    ),
    Scenario(
        name="influenza_baseline",
        fixture_dir="all_sections_COVID_INFLUENZA",
        config_filename="influenza_baseline.json",
        jurisdiction_code="TEST-JD",
        rsg_code="541131000124102",  # infection caused by novel Influenza A variant
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "38475891-387a-4fa2-bbe9-1dc97ce415d1"
        ),
        configuration_version=2,
    ),
    Scenario(
        name="covid_with_custom_codes",
        fixture_dir="all_sections_COVID_INFLUENZA",
        config_filename="covid_with_custom_codes.json",
        jurisdiction_code="TEST-JD",
        rsg_code="840539006",
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "07221093-b8a1-4b1d-8678-259277bfba64"
        ),
        configuration_version=3,
    ),
    Scenario(
        name="covid_with_section_overrides",
        fixture_dir="all_sections_COVID_INFLUENZA",
        config_filename="covid_with_section_overrides.json",
        jurisdiction_code="TEST-JD",
        rsg_code="840539006",
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "07221093-b8a1-4b1d-8678-259277bfba64"
        ),
        configuration_version=4,
    ),
    Scenario(
        name="covid_plus_unrelated_condition",
        fixture_dir="all_sections_COVID_INFLUENZA",
        config_filename="covid_plus_unrelated_condition.json",
        jurisdiction_code="TEST-JD",
        rsg_code="840539006",
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "07221093-b8a1-4b1d-8678-259277bfba64"
        ),
        configuration_version=5,
    ),
    Scenario(
        name="covid_with_substance_admin_custom_code",
        fixture_dir="all_sections_COVID_INFLUENZA",
        config_filename="covid_with_substance_admin_custom_code.json",
        jurisdiction_code="TEST-JD",
        rsg_code="840539006",
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "07221093-b8a1-4b1d-8678-259277bfba64"
        ),
        configuration_version=6,
    ),
    Scenario(
        name="covid_with_multi_vital_sign_codes",
        fixture_dir="all_sections_COVID_INFLUENZA",
        config_filename="covid_with_multi_vital_sign_codes.json",
        jurisdiction_code="TEST-JD",
        rsg_code="840539006",
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "07221093-b8a1-4b1d-8678-259277bfba64"
        ),
        configuration_version=7,
    ),
    Scenario(
        name="covid_with_procedure_only_code",
        fixture_dir="all_sections_COVID_INFLUENZA",
        config_filename="covid_with_procedure_only_code.json",
        jurisdiction_code="TEST-JD",
        rsg_code="840539006",
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "07221093-b8a1-4b1d-8678-259277bfba64"
        ),
        configuration_version=8,
    ),
]


# NOTE:
# SNAPSHOT PATHS
# =============================================================================
# snapshots live alongside the tests, not alongside the fixtures: a
# fixture is a static input but the snapshot is an output of refinement,
# and a single fixture may be exercised by multiple tests in the future

SNAPSHOT_ROOT: Path = Path(__file__).parent / "snapshots"


def _snapshot_dir(scenario: Scenario) -> Path:
    return SNAPSHOT_ROOT / scenario.fixture_dir / scenario.name


# NOTE:
# FIXTURE LOADING
# =============================================================================


def _load_xml_files(scenario: Scenario) -> XMLFiles:
    return XMLFiles(
        eicr=load_fixture_str(f"{scenario.fixture_dir}/eICR.xml"),
        rr=load_fixture_str(f"{scenario.fixture_dir}/RR.xml"),
    )


def _load_processed_configuration(scenario: Scenario) -> ProcessedConfiguration:
    raw = load_fixture_str(
        f"{scenario.fixture_dir}/configurations/{scenario.config_filename}"
    )
    return ProcessedConfiguration.from_dict(json.loads(raw))


# NOTE:
# SUMMARY DICT (the contents of expected_trace.json)
# =============================================================================
# a small, stable, human-readable dict pulled from the RefinementResult
# * sorted-key JSON serialization makes diffs trivial to read


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


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s.name for s in SCENARIOS])
def test_scenario_matches_snapshot(
    scenario: Scenario,
    update_snapshots: bool,
    validate_refined_document,
) -> None:
    """
    Refine the fixture for the scenario's condition, validate the refined
    documents, then compare the result against committed snapshots.

    Validation (well-formedness, CDA R2 XSD, schematron) runs first so
    invalid output fails the test loudly rather than getting committed as
    an "expected" snapshot. Pass --update-snapshots to overwrite the
    committed files with the current output instead of comparing; use
    when refinement behavior legitimately changes.
    """

    xml_files = _load_xml_files(scenario)
    processed_configuration = _load_processed_configuration(scenario)

    result = refine_one(
        xml_files=xml_files,
        processed_configuration=processed_configuration,
        jurisdiction_code=scenario.jurisdiction_code,
        rsg_code=scenario.rsg_code,
        canonical_url=scenario.canonical_url,
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
    # update mode: write current output as the new snapshot, then pass.
    # always run a print so the user has visible confirmation of what
    # was written, even when many scenarios are regenerated at once.
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
