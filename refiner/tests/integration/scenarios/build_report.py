from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from textwrap import dedent

from lxml import etree

# NOTE:
# PATHS
# =============================================================================

SCRIPT_FILE: Path = Path(__file__).resolve()
SCENARIOS_DIR: Path = SCRIPT_FILE.parent
SNAPSHOTS_DIR: Path = SCENARIOS_DIR / "snapshots"
REPORT_PATH: Path = SCENARIOS_DIR / "REPORT.md"


# NOTE:
# REFINER OUTPUT MARKER STRINGS
# =============================================================================
# duplicated from app/services/ecr/narrative/constants.py rather than imported
# * if the production strings change without a corresponding update
# here, the report's "Disposition" column will show outdated labels (e.g.
# "refined or retained" where the section is actually stubbed). that's a
# detectable failure mode in code review of REPORT.md. importing the
# constants would hide the drift

REMOVE_SECTION_MARKER: str = (
    "Section details have been removed as requested by jurisdiction"
)
REMOVE_NARRATIVE_MARKER: str = "Section narrative has been removed"
MINIMAL_SECTION_MARKER: str = "No clinical information matches the configured code sets"


# NOTE:
# ROLLUP COVERAGE DATA
# =============================================================================
# tim's roll-up sheet (May 2026). when adding or removing scenarios, update
# the `scenarios` list per row. coverage status values are conventional:
#   "Direct"               - a scenario directly exercises the behavior
#   "Partial"              - a scenario exercises part of the cited concern
#   "Indirect"             - existing snapshots would shift if the bug returned,
#                            but no scenario directly asserts the behavior
#   "Covered by validation" - the validation layer (XSD + schematron) catches it
#   "Gap"                  - not currently covered; closing it requires a new scenario


@dataclass(frozen=True)
class RollupRow:
    issue: int
    title: str
    status: str
    scenarios: list[str] = field(default_factory=list)
    evidence: str = ""


ROLLUP_COVERAGE: list[RollupRow] = [
    RollupRow(
        issue=1,
        title="Adding code sets removes relevant data",
        status="Direct",
        scenarios=["covid_baseline", "covid_plus_unrelated_condition"],
        evidence=(
            "`covid_plus_unrelated_condition` adds Fertilizer Poisoning to the "
            "COVID configuration — the exact condition Tim cited in the original "
            "Roll-up sheet. The snapshot pins the refined output, which should "
            "track `covid_baseline` because Fertilizer Poisoning codes don't "
            "appear in the fixture. A regression of the bug would manifest as "
            "the size reduction percentage climbing above the baseline's: "
            "adding unrelated codes would once again be removing COVID-relevant "
            "content."
        ),
    ),
    RollupRow(
        issue=2,
        title="Immunization code matching across OID mismatch",
        status="Direct",
        scenarios=["covid_with_custom_codes"],
        evidence=(
            "`covid_with_custom_codes` adds CVX code 2563008 as a custom code. "
            "The fixture tags the same code value with the RxNorm OID. The "
            "snapshot pins whether the matcher accepts the cross-OID match."
        ),
    ),
    RollupRow(
        issue=3,
        title="Schematron validation of refined output",
        status="Covered by validation",
        scenarios=["all scenarios"],
        evidence=(
            "Every refined eICR and RR is validated against CDA R2 XSD and "
            "schematron on every test run, before snapshot comparison. Errors "
            "and fatal severity fail the test; warnings are tolerated. "
            "Enforced by the `validate_refined_document` fixture in "
            "`tests/integration/scenarios/conftest.py`."
        ),
    ),
    RollupRow(
        issue=4,
        title="Custom codes in nested locations (entryRelationship/value, substanceAdministration)",
        status="Direct",
        scenarios=["covid_with_custom_codes", "covid_with_substance_admin_custom_code"],
        evidence=(
            "`covid_with_custom_codes` adds 10628911000119103, which lives in "
            "the fixture's Problem List `entryRelationship/value`, covering the "
            "nested-observation half. `covid_with_substance_admin_custom_code` "
            "adds a custom code targeting a Medications `substanceAdministration` "
            "entry; both medication sections gain an entry "
            "(Medications Administered 1→2, History of Medication Use 1→2)."
        ),
    ),
    RollupRow(
        issue=5,
        title="Procedures retained via unrelated entryRelationship codes",
        status="Direct",
        scenarios=[
            "covid_baseline",
            "covid_with_custom_codes",
            "covid_with_procedure_only_code",
        ],
        evidence=(
            "The concern has two halves.\n\n"
            "**Negative case (procedures not retained via entryRelationship "
            "match):** Nausea (SNOMED 422587007) is in both the COVID and "
            "Influenza condition groupers, so it is a configured matching "
            "code under `covid_baseline`. The fixture's three procedure "
            "entries (Colonic polypectomy, ECMO, Ventilator care) all carry "
            "Nausea in their entryRelationship. Despite both conditions being "
            "true, `covid_baseline` shows the Procedures section stubbed at "
            "0 entries — the matcher correctly does not retain procedures "
            "based on a match found only in entryRelationship. The explicit "
            "assertion `test_covid_baseline_does_not_retain_procedures_via_"
            "entry_relationship_only_match` in "
            "`tests/integration/scenarios/test_explicit_assertions.py` pins this directly "
            "with precondition guards that fail diagnostically if the fixture "
            "or configuration drifts.\n\n"
            "**Positive case (procedures retained when their primary code "
            "matches as a custom code):** `covid_with_custom_codes` adds ECMO "
            "(SNOMED 233573008) as a custom code; `covid_with_procedure_only_code` "
            "adds Ventilator care (SNOMED 385857005). Both snapshots show the "
            "matching procedure surviving whole."
        ),
    ),
    RollupRow(
        issue=6,
        title="Vital sign panel returns whole panel on single match",
        status="Direct",
        scenarios=["covid_with_custom_codes", "covid_with_multi_vital_sign_codes"],
        evidence=(
            "`covid_with_custom_codes` adds Heart Rate (LOINC 8867-4) as a "
            "single custom code. Combined with body temperature (LOINC 8310-5) "
            "-- a member of the COVID condition grouper, matched from the "
            "baseline configuration -- the snapshot pins panel pruning at a "
            "two-of-nine cardinality. `covid_with_multi_vital_sign_codes` adds "
            "three more vital sign codes (8867-4, 8480-6, 9279-1) and pins the "
            "four-of-nine case (those three plus body temperature). The "
            "surviving sub-components are the configured-and-present codes, not "
            "only the custom additions. If the bug returned, both snapshots "
            "would shift to retaining all nine sub-components."
        ),
    ),
]


# NOTE:
# SCENARIO DISCOVERY FROM SNAPSHOTS
# =============================================================================
# The report walks the snapshots/ directory rather than importing from any
# test file. This keeps the report decoupled from any specific test module
# and works correctly if more test files are added later.

HL7_NS: dict[str, str] = {"hl7": "urn:hl7-org:v3"}


@dataclass(frozen=True)
class SectionInfo:
    """
    One section in a refined eICR snapshot, summarized for the report.
    """

    loinc: str
    name: str
    entry_count: int
    disposition: str  # human-readable refiner outcome


@dataclass(frozen=True)
class ScenarioSnapshot:
    """
    All snapshot data for a single scenario, parsed from disk.
    """

    name: str
    fixture: str
    summary: dict
    eicr_sections: list[SectionInfo]
    trace_path: Path
    eicr_path: Path
    rr_path: Path


def _classify_section_disposition(section: etree._Element) -> str:
    """
    Best-effort classification of what the refiner did to this section.

    Pattern-matches the section's text content against the refiner's
    well-known output messages. Not exhaustive (it can't distinguish
    "retained as-is" from "refined with matches" because both can have
    populated narrative), but informative enough for stakeholder review.
    """

    text_el = section.find("hl7:text", HL7_NS)
    if text_el is None:
        return "no <text>"

    full_text = " ".join(text_el.itertext())

    if REMOVE_SECTION_MARKER in full_text:
        return "removed by configuration"
    if MINIMAL_SECTION_MARKER in full_text:
        return "stubbed (no matches)"
    if REMOVE_NARRATIVE_MARKER in full_text:
        return "refined; narrative removed"

    entry_count = len(section.findall("hl7:entry", HL7_NS))
    if entry_count == 0:
        return "narrative-only"
    return "refined or retained"


def _parse_eicr_sections(eicr_path: Path) -> list[SectionInfo]:
    """
    Walk the refined eICR's top-level sections and summarize each in document order.
    """

    tree = etree.parse(str(eicr_path))
    root = tree.getroot()
    structured_body = root.find(".//hl7:structuredBody", HL7_NS)
    if structured_body is None:
        return []

    out: list[SectionInfo] = []
    for section in structured_body.findall("./hl7:component/hl7:section", HL7_NS):
        code_el = section.find("./hl7:code", HL7_NS)
        loinc = (code_el.get("code") if code_el is not None else None) or "?"
        name = (code_el.get("displayName") if code_el is not None else None) or "?"
        entries = section.findall("./hl7:entry", HL7_NS)
        out.append(
            SectionInfo(
                loinc=loinc,
                name=name,
                entry_count=len(entries),
                disposition=_classify_section_disposition(section),
            )
        )
    return out


def discover_scenarios() -> list[ScenarioSnapshot]:
    """
    Find every committed scenario by walking snapshots/<fixture>/<scenario>/.

    Sorted by (fixture, scenario_name) for deterministic output. Fails
    loudly with actionable messages if the snapshots directory is missing
    or any scenario directory is incomplete.
    """

    if not SNAPSHOTS_DIR.is_dir():
        raise SystemExit(
            f"Snapshots directory not found: {SNAPSHOTS_DIR}\n"
            "Run `pytest tests/integration/scenarios/ --update-snapshots` first."
        )

    scenarios: list[ScenarioSnapshot] = []

    for fixture_dir in sorted(SNAPSHOTS_DIR.iterdir()):
        if not fixture_dir.is_dir():
            continue
        for scenario_dir in sorted(fixture_dir.iterdir()):
            if not scenario_dir.is_dir():
                continue

            trace_path = scenario_dir / "expected_trace.json"
            eicr_path = scenario_dir / "expected_eICR.xml"
            rr_path = scenario_dir / "expected_RR.xml"

            missing = [
                p.name for p in (trace_path, eicr_path, rr_path) if not p.exists()
            ]
            if missing:
                raise SystemExit(
                    f"Incomplete snapshot at {fixture_dir.name}/{scenario_dir.name}: "
                    f"missing {', '.join(missing)}.\n"
                    "Run `pytest tests/integration/scenarios/ --update-snapshots`."
                )

            scenarios.append(
                ScenarioSnapshot(
                    name=scenario_dir.name,
                    fixture=fixture_dir.name,
                    summary=json.loads(trace_path.read_text()),
                    eicr_sections=_parse_eicr_sections(eicr_path),
                    trace_path=trace_path,
                    eicr_path=eicr_path,
                    rr_path=rr_path,
                )
            )

    if not scenarios:
        raise SystemExit(
            f"No scenarios found in {SNAPSHOTS_DIR}. "
            "Run `pytest tests/integration/scenarios/ --update-snapshots` first."
        )

    return scenarios


# NOTE:
# RENDERING
# =============================================================================
# plain string-building: the report is small enough that a templating
# library would add more friction than it removes


def _scenario_anchor(name: str) -> str:
    """
    GitHub-flavored Markdown anchor for a scenario header.
    """

    return name.replace("_", "-").lower()


def _relpath_from_report(p: Path) -> str:
    """
    Return a path string suitable for a Markdown link inside REPORT.md.
    """

    return str(p.relative_to(REPORT_PATH.parent))


def _render_header() -> str:
    return (
        dedent("""
            # eCR Refiner — Scenarios Report

            *Auto-generated. To regenerate:*

            ```
            pytest tests/integration/scenarios/ --update-snapshots
            python tests/integration/scenarios/build_report.py
            ```

            This report summarizes the behaviors pinned by the scenarios test suite at `tests/integration/scenarios/`. Each scenario refines a committed eICR/RR pair against a committed configuration JSON and asserts in two layers: validation (well-formedness, CDA R2 XSD, schematron) and snapshot comparison against committed expected files.

            See the [scenarios README](./README.md) for the full mechanics. This document is the high-level summary intended for stakeholder review.
        """).strip()
        + "\n"
    )


def _render_coverage_matrix() -> str:
    lines = [
        "## Roll-up issue coverage",
        "",
        "Mapping of the issues identified during early testing (Roll-up sheet, May 2026) to current suite coverage. Each scenario reference is a link to its detail section below.",
        "",
        "| # | Issue | Status | Scenario(s) |",
        "|---|-------|--------|-------------|",
    ]

    for row in ROLLUP_COVERAGE:
        if not row.scenarios:
            scenarios_cell = "—"
        else:
            scenarios_cell = ", ".join(
                f"[`{s}`](#{_scenario_anchor(s)})"
                if s != "all scenarios"
                else "all scenarios"
                for s in row.scenarios
            )
        lines.append(
            f"| {row.issue} | {row.title} | **{row.status}** | {scenarios_cell} |"
        )

    lines.extend(["", "### Evidence per issue", ""])
    for row in ROLLUP_COVERAGE:
        lines.append(f"**Issue {row.issue} — {row.title}** ({row.status})")
        lines.append("")
        lines.append(row.evidence)
        lines.append("")

    return "\n".join(lines)


def _render_scenario(scenario: ScenarioSnapshot) -> str:
    summary = scenario.summary
    lines = [
        f"### {scenario.name}",
        "",
        f"**Fixture:** `{scenario.fixture}`",
        "",
        (
            "**Snapshot files:** "
            f"[trace JSON]({_relpath_from_report(scenario.trace_path)}) · "
            f"[refined eICR]({_relpath_from_report(scenario.eicr_path)}) · "
            f"[refined RR]({_relpath_from_report(scenario.rr_path)})"
        ),
        "",
        "**Refinement summary**",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Outcome | `{summary['refinement_outcome']}` |",
        f"| Configuration version | `{summary['configuration_version']}` |",
        f"| Configuration resolved | `{summary['configuration_resolved']}` |",
        f"| eICR size reduction | `{summary['eicr_size_reduction_percentage']}%` |",
        f"| Canonical URL | `{summary['canonical_url']}` |",
        f"| Augmented eICR id | `{summary['augmented_eicr_id']}` |",
        f"| Augmented RR id | `{summary['augmented_rr_id']}` |",
        f"| Original eICR id | `{summary['original_eicr_id']}` |",
        f"| Original RR id | `{summary['original_rr_id']}` |",
        "",
        "**Refined eICR — sections retained**",
        "",
        "| LOINC | Section | Entries | Disposition |",
        "|-------|---------|---------|-------------|",
    ]
    for section in scenario.eicr_sections:
        lines.append(
            f"| `{section.loinc}` | {section.name} | {section.entry_count} | "
            f"{section.disposition} |"
        )

    related = [r for r in ROLLUP_COVERAGE if scenario.name in r.scenarios]
    if related:
        lines.extend(
            [
                "",
                "**Pins Roll-up issues:** "
                + ", ".join(f"#{r.issue} ({r.status.lower()})" for r in related),
            ]
        )

    lines.append("")
    return "\n".join(lines)


def _render_scenarios_section(scenarios: list[ScenarioSnapshot]) -> str:
    plural = "s" if len(scenarios) != 1 else ""
    lines = [
        "## Scenarios",
        "",
        f"Total: {len(scenarios)} scenario{plural} across "
        f"{len({s.fixture for s in scenarios})} "
        f"fixture{'s' if len({s.fixture for s in scenarios}) != 1 else ''}.",
        "",
    ]
    for scenario in scenarios:
        lines.append(_render_scenario(scenario))
    return "\n".join(lines)


def _render_appendix() -> str:
    return (
        dedent("""
            ## Appendix — running the suite

            ```
            pytest tests/integration/scenarios/                                  # run all scenarios + smoke tests
            pytest tests/integration/scenarios/test_<fixture>.py -k <scenario>   # one scenario
            pytest tests/integration/scenarios/ --update-snapshots               # regenerate after intentional changes
            python tests/integration/scenarios/build_report.py        # regenerate this report
            ```

            See [`tests/integration/scenarios/README.md`](./README.md) for adding fixtures, configurations, and scenarios.
        """).strip()
        + "\n"
    )


def _compose_report(scenarios: list[ScenarioSnapshot]) -> str:
    """
    Compose the full report from its sections, single trailing newline.
    """

    parts = [
        _render_header(),
        "",
        _render_coverage_matrix(),
        "",
        _render_scenarios_section(scenarios),
        "",
        _render_appendix(),
    ]
    return "\n".join(parts).rstrip() + "\n"


# NOTE:
# CONSISTENCY CHECK + ENTRY POINT
# =============================================================================


def _check_coverage_references_known_scenarios(
    scenarios: list[ScenarioSnapshot],
) -> None:
    """
    Fail if ROLLUP_COVERAGE references scenarios that don't have snapshots.

    Catches the common "added a row to the matrix before authoring the
    scenario" mistake at build time rather than producing broken anchor
    links in the rendered report.
    """

    snapshot_names = {s.name for s in scenarios}
    referenced: set[str] = set()
    for row in ROLLUP_COVERAGE:
        for name in row.scenarios:
            if name != "all scenarios":
                referenced.add(name)

    missing = referenced - snapshot_names
    if missing:
        raise SystemExit(
            "ROLLUP_COVERAGE references scenarios that don't exist as "
            f"snapshots: {sorted(missing)}\n"
            "Either remove the references or generate the missing snapshots "
            "with `pytest tests/integration/scenarios/ --update-snapshots`."
        )


def build_report() -> int:
    scenarios = discover_scenarios()
    _check_coverage_references_known_scenarios(scenarios)
    report = _compose_report(scenarios)
    REPORT_PATH.write_text(report)
    print(f"Wrote {REPORT_PATH.relative_to(SCENARIOS_DIR.parent.parent)}")
    return 0


def main() -> int:
    return build_report()


if __name__ == "__main__":
    raise SystemExit(main())
