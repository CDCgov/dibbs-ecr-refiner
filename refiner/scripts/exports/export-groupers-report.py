import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

EXPORTS_DIR = Path(__file__).parent
SCRIPTS_DIR = EXPORTS_DIR.parent
DATA_DIR = SCRIPTS_DIR / "data" / "source-tes-groupers"
OUTFILE = (
    EXPORTS_DIR
    / f"tes-export-grouper-report-{datetime.today().strftime('%Y-%m-%d')}.csv"
)

# the versions we care about, in order; matches validate_tes_valuesets.py
VERSIONS_TO_CHECK = ["6.0.0"]

COVERAGE_LEVEL_URL = (
    "http://hl7.org/fhir/uv/crmi/StructureDefinition/crmi-curationCoverageLevel"
)

# cell delimiter for aggregated RSG/ACG lists
CELL_SEP = " | "

# type aliases
type SimpleCode = tuple[str, str]
type ValueSetKey = tuple[str, str]  # (url, version)


# NOTE:
# CLASSIFICATION HELPERS
# =============================================================================


def is_condition_grouper(vs: dict) -> bool:
    """
    Checks if a ValueSet is a 'ConditionGrouper' via its metadata profile.

    Mirrors validate_tes_valuesets.is_condition_grouper but operates on dicts.
    """

    meta = vs.get("meta") or {}
    profiles = meta.get("profile") or []
    return any("conditiongroupervalueset" in str(p).lower() for p in profiles)


def is_additional_context_grouper(vs: dict) -> bool:
    """
    Checks if a ValueSet is an 'Additional Context' grouper using its useContext coding.

    Mirrors validate_tes_valuesets.is_additional_context_grouper but operates
    on dicts.
    """

    for context in vs.get("useContext") or []:
        vcc = context.get("valueCodeableConcept") or {}
        for coding in vcc.get("coding") or []:
            if coding.get("code") == "additional-context-grouper":
                return True
    return False


def parse_snomed_from_url(url: str | None) -> str | None:
    """
    Extract the RSG SNOMED CT code from its canonical url.
    """

    if not url:
        return None
    if "rs-grouper-" in url:
        return url.split("rs-grouper-")[-1]
    return None


def get_codes_from_compose(vs: dict | None) -> set[SimpleCode]:
    """
    Extracts inline (system, code) pairs from compose.include[].concept[].

    Mirrors validate_tes_valuesets.get_codes_from_compose but on dicts.
    """

    if not vs:
        return set()
    compose = vs.get("compose") or {}
    codes: set[SimpleCode] = set()
    for inc in compose.get("include") or []:
        system = inc.get("system")
        concepts = inc.get("concept") or []
        if not system or not concepts:
            continue
        for concept in concepts:
            code = concept.get("code")
            if code:
                codes.add((system, code))
    return codes


def get_expansion_codes(vs: dict | None) -> set[SimpleCode]:
    """
    Extracts (system, code) pairs from a ValueSet's expansion.contains.
    """

    if not vs:
        return set()
    expansion = vs.get("expansion") or {}
    codes: set[SimpleCode] = set()
    for c in expansion.get("contains") or []:
        system = c.get("system")
        code = c.get("code")
        if system and code:
            codes.add((system, code))
    return codes


def parse_coverage_level(vs: dict) -> dict | None:
    """
    Extracts the crmi-curationCoverageLevel complex extension into a flat dict.

    Returns {"level": str, "reason": str | None, "date": str | None} or None.
    Mirrors validate_tes_valuesets._parse_coverage_level but on dicts.
    """

    for ext in vs.get("extension") or []:
        if ext.get("url") != COVERAGE_LEVEL_URL:
            continue
        sub_exts = ext.get("extension") or []
        level: str | None = None
        reason: str | None = None
        date: str | None = None
        for sub in sub_exts:
            match sub.get("url"):
                case "level":
                    vcc = sub.get("valueCodeableConcept") or {}
                    coding = (vcc.get("coding") or [{}])[0]
                    level = coding.get("code")
                case "levelReason":
                    reason = sub.get("valueMarkdown")
                case "dateTime":
                    date = sub.get("valueDateTime")
        if level is None:
            return None
        return {"level": level, "reason": reason, "date": date}
    return None


# NOTE:
# LOADING
# =============================================================================


def load_all_valuesets(data_dir: Path) -> dict[ValueSetKey, dict]:
    """
    Loads all ValueSets from JSON files in data_dir, keyed by (url, version).

    Supports both the custom 'valuesets' list format and Bundle-like 'entry'
    formats, matching the loader in validate_tes_valuesets.
    """

    all_valuesets: dict[ValueSetKey, dict] = {}
    json_files = [f for f in data_dir.glob("*.json") if f.name != "manifest.json"]
    print(f"🔎 Found {len(json_files)} JSON file(s) in {data_dir}")

    for file_path in json_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                doc = json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to read {file_path.name}: {e}")
            continue

        vs_list = list(doc.get("valuesets", []))
        for entry in doc.get("entry", []) or []:
            resource = entry.get("resource") or {}
            if resource.get("resourceType") == "ValueSet":
                vs_list.append(resource)

        for vs in vs_list:
            if not vs:
                continue
            url = vs.get("url")
            version = vs.get("version")
            if url and version:
                all_valuesets[(url, version)] = vs

    print(f"📚 Loaded {len(all_valuesets)} unique ValueSets")
    return all_valuesets


# NOTE:
# CONDITION GROUPER RESOLUTION
# =============================================================================


def resolve_cg_children(
    cg: dict,
    all_vs: dict[ValueSetKey, dict],
) -> dict:
    """
    Finds all of the referenced ValueSets associated with a Condition Grouper.

    Walks the condition grouper's compose.include[].valueSet[] references,
    resolves each child, and partitions them into RSGs, ACGs, and unresolved.

    Returns a dict with the partitioned children plus the union of all codes
    contributed by resolved children.
    """

    rsgs: list[dict] = []
    acgs: list[dict] = []
    unresolved: list[dict] = []
    rsg_codes: set[SimpleCode] = set()
    acg_codes: set[SimpleCode] = set()

    compose = cg.get("compose") or {}
    for include in compose.get("include") or []:
        for child_ref in include.get("valueSet") or []:
            url, sep, version = str(child_ref).partition("|")
            if not sep:
                unresolved.append(
                    {
                        "ref": str(child_ref),
                        "url": url,
                        "version": "",
                        "reason": "no version",
                    }
                )
                continue

            child_vs = all_vs.get((url, version))
            if child_vs is None:
                unresolved.append(
                    {
                        "ref": str(child_ref),
                        "url": url,
                        "version": version,
                        "reason": "not found",
                    }
                )
                continue

            child_codes = get_codes_from_compose(child_vs)
            child_info = {
                "url": url,
                "version": version,
                "name": child_vs.get("title") or child_vs.get("name"),
                "snomed": parse_snomed_from_url(url),
                "code_count": len(child_codes),
                "codes": child_codes,
            }

            if is_additional_context_grouper(child_vs):
                acgs.append(child_info)
                acg_codes.update(child_codes)
            else:
                rsgs.append(child_info)
                rsg_codes.update(child_codes)

    return {
        "rsgs": rsgs,
        "acgs": acgs,
        "unresolved": unresolved,
        "rsg_codes": rsg_codes,
        "acg_codes": acg_codes,
        "all_codes": rsg_codes | acg_codes,
    }


# NOTE:
# FORMATTING
# =============================================================================


def format_child_cell(children: list[dict], include_snomed: bool = True) -> str:
    """
    Formats a list of child grouper info dicts into a pipe-separated cell.

    Each child renders as `<snomed?> | <name> | <code_count> codes`.
    """

    parts = []
    for c in children:
        name = c.get("name") or c.get("url") or "(unnamed)"
        code_count = c.get("code_count", 0)
        if include_snomed and c.get("snomed"):
            parts.append(f"{c['snomed']} {name} ({code_count} codes)")
        else:
            parts.append(f"{name} ({code_count} codes)")
    return CELL_SEP.join(parts)


def format_unresolved_cell(unresolved: list[dict]) -> str:
    """
    Formats unresolved references for the CSV cell.
    """

    return CELL_SEP.join(
        f"{u['url']}|{u['version']} ({u['reason']})" for u in unresolved
    )


# NOTE:
# MAIN
# =============================================================================


def main() -> None:
    """
    The main function that orchestrates the report.

    Build a per-(condition, version) report CSV showing RSG children, ACG
    children, code completeness, and totals.
    """

    print("🌱 Starting grouper report export...")
    all_vs = load_all_valuesets(DATA_DIR)

    # group condition groupers by name -> version -> vs
    cgs_by_name: dict[str, dict[str, dict]] = defaultdict(dict)
    for vs in all_vs.values():
        if not is_condition_grouper(vs):
            continue
        name = vs.get("title") or vs.get("name")
        version = vs.get("version")
        if name and version:
            cgs_by_name[name][version] = vs

    print(f"🏷️  Found {len(cgs_by_name)} condition groupers")

    rows: list[dict] = []
    grand_total_codes: set[SimpleCode] = set()
    grand_total_rsg_codes: set[SimpleCode] = set()
    cg_version_count = 0

    for name in sorted(cgs_by_name):
        versions_present = cgs_by_name[name]
        for version in VERSIONS_TO_CHECK:
            cg = versions_present.get(version)
            if cg is None:
                continue
            cg_version_count += 1

            resolution = resolve_cg_children(cg, all_vs)
            coverage = parse_coverage_level(cg)
            expansion_codes = get_expansion_codes(cg)

            # expansion-vs-composition sanity check (matches validate logic)
            if cg.get("expansion"):
                expansion_check = (
                    "match"
                    if expansion_codes == resolution["all_codes"]
                    else "mismatch"
                )
            else:
                expansion_check = "no_expansion"

            rows.append(
                {
                    "condition_grouper_name": name,
                    "condition_grouper_canonical_url": cg.get("url"),
                    "condition_grouper_version": version,
                    "coverage_level": (coverage or {}).get("level") or "",
                    "coverage_reason": (coverage or {}).get("reason") or "",
                    "coverage_date": (coverage or {}).get("date") or "",
                    "rsg_count": len(resolution["rsgs"]),
                    "rsgs": format_child_cell(resolution["rsgs"]),
                    "acg_count": len(resolution["acgs"]),
                    "acgs": format_child_cell(resolution["acgs"], include_snomed=False),
                    "unresolved_count": len(resolution["unresolved"]),
                    "unresolved_refs": format_unresolved_cell(resolution["unresolved"]),
                    "total_rsg_codes": len(resolution["rsg_codes"]),
                    "total_acg_codes": len(resolution["acg_codes"]),
                    "total_codes_in_cg": len(resolution["all_codes"]),
                    "expansion_code_count": len(expansion_codes),
                    "expansion_vs_composition": expansion_check,
                }
            )

            grand_total_codes.update(resolution["all_codes"])
            grand_total_rsg_codes.update(resolution["rsg_codes"])

    # write csv
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "condition_grouper_name",
        "condition_grouper_canonical_url",
        "condition_grouper_version",
        "coverage_level",
        "coverage_reason",
        "coverage_date",
        "rsg_count",
        "rsgs",
        "acg_count",
        "acgs",
        "unresolved_count",
        "unresolved_refs",
        "total_rsg_codes",
        "total_acg_codes",
        "total_codes_in_cg",
        "expansion_code_count",
        "expansion_vs_composition",
    ]
    try:
        with open(OUTFILE, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
    except Exception as e:
        print(f"❌ Error writing CSV: {e}")
        return

    # stdout summary
    print()
    print("=" * 20 + " EXPORT SUMMARY " + "=" * 20)
    print(f"  📦 Rows written: {len(rows)}")
    print(f"  🏷️  Distinct condition groupers: {len(cgs_by_name)}")
    print(f"  📚 (CG, version) pairs emitted: {cg_version_count}")
    print(f"  🔢 Grand total unique codes (RSG ∪ ACG): {len(grand_total_codes)}")
    print(f"  🔢 Grand total unique RSG codes: {len(grand_total_rsg_codes)}")
    print(f"  ✅ Wrote {OUTFILE}")
    print("=" * 56)
    print("🎉 Grouper report export complete!")


if __name__ == "__main__":
    main()
