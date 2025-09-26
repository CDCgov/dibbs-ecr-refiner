import csv
import json
from datetime import datetime
from pathlib import Path

EXPORTS_DIR = Path(__file__).parent
SCRIPTS_DIR = EXPORTS_DIR.parent
TES_DATA_DIR = SCRIPTS_DIR / "data" / "tes"
OUTFILE = (
    EXPORTS_DIR / f"tes-export-groupers-{datetime.today().strftime('%Y-%m-%d')}.csv"
)


def parse_snomed_from_url(url: str) -> str | None:
    """
    Extract the RSG SNOMED CT code from its canonical url.
    """

    if "rs-grouper-" in url:
        return url.split("rs-grouper-")[-1]
    return None


def main():
    """
    Run the script to export CSV file to show relationship between CGs <-> RSGs.
    """

    print("🌱 Starting grouper CSV export...")

    # load all ValueSets, keyed by (url, version)
    all_valuesets = {}
    json_files = [f for f in TES_DATA_DIR.glob("*.json") if f.name != "manifest.json"]
    print(f"🔎 Found {len(json_files)} JSON file(s) in {TES_DATA_DIR}")
    for file_path in json_files:
        print(f"📖 Reading {file_path.name}...")
        try:
            with open(file_path) as f:
                doc = json.load(f)
                for vs in doc.get("valuesets", []):
                    key = (vs.get("url"), vs.get("version"))
                    all_valuesets[key] = vs
        except Exception as e:
            print(f"⚠️ Failed to read {file_path.name}: {e}")

    rows = []
    parent_count = 0
    relation_count = 0

    # iterate parent ValueSets that reference child ValueSets
    for parent in all_valuesets.values():
        includes = parent.get("compose", {}).get("include", [])
        has_children = any("valueSet" in inc for inc in includes)
        if not has_children:
            continue
        parent_count += 1
        condition_grouper_name = parent.get("name") or parent.get("title")
        condition_grouper_canonical_url = parent.get("url")
        condition_grouper_version = parent.get("version")
        for include in includes:
            for child_ref in include.get("valueSet", []):
                try:
                    (
                        reporting_spec_grouper_canonical_url,
                        reporting_spec_grouper_version,
                    ) = child_ref.split("|", 1)
                except ValueError:
                    print(f"⚠️ Skipping malformed child reference: {child_ref}")
                    continue
                child_vs = all_valuesets.get(
                    (
                        reporting_spec_grouper_canonical_url,
                        reporting_spec_grouper_version,
                    )
                )
                if not child_vs:
                    print(
                        f"⚠️ Could not find child ValueSet: {reporting_spec_grouper_canonical_url}|{reporting_spec_grouper_version}"
                    )
                    continue
                reporting_spec_grouper_snomed = parse_snomed_from_url(
                    child_vs.get("url", "")
                )
                if not reporting_spec_grouper_snomed:
                    # Skip non-reporting-specification groupers (like additional context groupers)
                    continue
                reporting_spec_grouper_name = child_vs.get("title")
                rows.append(
                    {
                        "condition_grouper_name": condition_grouper_name,
                        "condition_grouper_canonical_url": condition_grouper_canonical_url,
                        "condition_grouper_version": condition_grouper_version,
                        "reporting_spec_grouper_snomed": reporting_spec_grouper_snomed,
                        "reporting_spec_grouper_name": reporting_spec_grouper_name,
                        "reporting_spec_grouper_canonical_url": reporting_spec_grouper_canonical_url,
                        "reporting_spec_grouper_version": reporting_spec_grouper_version,
                    }
                )
                relation_count += 1

    print(
        f"🧩 Processed {parent_count} parent groupers with {relation_count} parent-child relationships."
    )

    # write to csv
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(OUTFILE, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "condition_grouper_name",
                "condition_grouper_canonical_url",
                "condition_grouper_version",
                "reporting_spec_grouper_snomed",
                "reporting_spec_grouper_name",
                "reporting_spec_grouper_canonical_url",
                "reporting_spec_grouper_version",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        print(f"✅ Wrote {len(rows)} rows to {OUTFILE}")
        print("🎉 Grouper CSV export complete!")
    except Exception as e:
        print(f"❌ Error writing CSV: {e}")


if __name__ == "__main__":
    main()
