r"""
Generate `template_oids.py` from the eICR STU 3.1.1 IG Volume 2 markdown.

Usage:
    python generate_template_oids.py \\
        --ig-md path/to/CDAR2_IG_PHCASERPT_R2_STU3_1_1_Vol2.md \\
        --out   path/to/template_oids.py

Rationale (why root-only, why STU 3.1.1, etc.) lives in the rendered
output file's header so it's visible where readers actually look.
"""

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path

# heading pattern:
# * section 2.* and 3.* with the IG's anchor span
# * italic asterisk wrapping is inconsistent in the converted markdown, so we
# tolerate optional asterisks around the heading text
# * heading depth (#) also varies: most top-level templates use `#`, but some sub-templates
# (e.g. trigger code specialisations under their base template) use `##`
#
# Examples we need to match:
#   # <span id="page-394-0"></span>*3.41 Problem Observation (V3)*
#   # <span id="page-126-0"></span>2.6.1 Encounters Section (entries required) (V3)
#   ## <span id="page-419-0"></span>3.43.1 Initial Case Report Trigger Code Procedure Activity Act
_HEADING_RE = re.compile(
    r'^#+\s<span id="page-\d+-\d+"></span>'
    r"\*?"
    r"(?P<section>[23](?:\.\d+)+)\s+"
    r"(?P<name>[^\n*]+?)"
    r"\*?\s*$"
)

# identifier line
# * accepts both versioned (urn:hl7ii:OID:DATE) and
# bare (urn:oid:OID) forms
# * the converted markdown sometimes wraps the date
# across two lines inside the code fence; we glue lines first, so this
# regex sees one continuous string
_IDENTIFIER_RE = re.compile(
    r"\[[a-zA-Z]+:\s+identifier\s+"
    r"urn:(?:hl7ii|oid):"
    r"(?P<oid>[0-9.]+)"
    r"(?::(?P<ext>\d{4}-\d{2}-\d{2}))?"
)

# contexts table row: starts with `|`, first column holds the parent name
_TABLE_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|")

# any heading line: used as the "stop" sentinel when looking ahead from
# one heading into the body that follows it
_HEADING_START_RE = re.compile(r'^#+\s<span id="page-')


# templates referenced by the eICR IG but DEFINED in C-CDA (and therefore
# not present as standalone headings in the eICR IG markdown). they show
# up in eICR conformance statements as required child templates
#
# hand curated; verified against the C-CDA R2.1 IG. When adding more:
# include a comment with the C-CDA section reference for future verification.
_CCDA_SUPPLEMENT: list[tuple[str, str, str, str]] = [
    # (group, display_name, root, extension)
    # C-CDA R2.1 §3.31 Indication (V2) - referenced from Encounter
    # Diagnosis (V3) and other entry templates, but only mentioned as a
    # SHALL constraint in the eICR IG, not defined with its own heading.
    (
        "Cross-cutting / infrastructure",
        "Indication (V2)",
        "2.16.840.1.113883.10.20.22.4.19",
        "2014-06-09",
    ),
]

# max hops when walking _contained by_ edges to find a containing section
# * entries can be a few hops from a section through intermediate entry-level
# templates; 5 is generous and well within the IG's actual depth
_MAX_CONTAINMENT_HOPS = 5

_CROSS_CUTTING = "Cross-cutting / infrastructure"


@dataclass
class Template:
    """
    One IG template extracted from the markdown.
    """

    section_number: str  # e.g. "2.14", "3.41", or "ccda" for supplement entries
    display_name: str
    root: str
    extension: str | None
    contained_by: list[str] = field(default_factory=list)


def slugify(name: str) -> str:
    """
    Convert an IG display name to a Python constant name.

    Rules:
      "Problem Observation (V3)"                       -> PROBLEM_OBSERVATION_V3
      "Encounters Section (entries optional) (V3)"     -> ENCOUNTERS_SECTION_ENTRIES_OPTIONAL_V3
      "Encounters Section (entries required) (V3)"     -> ENCOUNTERS_SECTION_ENTRIES_REQUIRED_V3
      "Initial Case Report Trigger Code Problem
       Observation (V3)"                               -> TRIGGER_CODE_PROBLEM_OBSERVATION_V3
      "Author Participation"                           -> AUTHOR_PARTICIPATION

    The "(entries optional)" vs "(entries required)" variants have
    DIFFERENT root OIDs in the IG (e.g. 22.2.5 vs 22.2.5.1), so they
    must produce different constants.

    The "Initial Case Report" prefix on trigger templates is dropped
    because every template with root 2.16.840.1.113883.10.20.15.2.3.* is
    by definition an Initial Case Report trigger code template.
    """

    # drop the verbose IG prefix on trigger code templates
    name = re.sub(r"^Initial Case Report\s+", "", name)

    # turn "(entries optional/required)" into bare words so they survive
    # slugification instead of being dropped as parenthesised content
    name = re.sub(r"\s*\(entries optional\)", " entries optional", name)
    name = re.sub(r"\s*\(entries required\)", " entries required", name)

    # pull out trailing version marker so it becomes a clean suffix
    version_match = re.search(r"\((V\d+)\)\s*$", name)
    version_suffix = ""
    if version_match:
        version_suffix = "_" + version_match.group(1)
        name = name[: version_match.start()].strip()

    slug = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").upper()
    return slug + version_suffix


def glue_wrapped_identifier_lines(lines: list[str]) -> list[str]:
    """
    Glue wrapped identifier lines inside fenced code blocks.

    The IG markdown wraps long identifier lines inside fenced code blocks.
    Glue them so the regex sees `urn:hl7ii:...:2018-04-01 (open)` on one
    line rather than something split across two.

    Two wrap patterns observed in the converted output:
      1. The date wraps mid-string:
            urn:hl7ii:2.16.840.1.113883.10.20.22.4.200:2016-06-
            01 (open)
      2. The identifier prefix wraps before the urn:
            [manufacturedProduct: identifier
            urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.38:2019-04-01 (open)

    Both are conservatively detected and joined only inside ``` fences.
    """

    out: list[str] = []
    in_fence = False
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue

        if in_fence and out:
            prev = out[-1].rstrip()
            curr = line.lstrip()
            # pattern 1: previous ends with '-' and current starts with digits
            if prev.endswith("-") and re.match(r"^\d", curr):
                out[-1] = prev + curr
                continue
            # pattern 2: previous ends with 'identifier' and current starts with 'urn:'
            if prev.endswith("identifier") and curr.startswith("urn:"):
                out[-1] = prev + " " + curr
                continue

        out.append(line)
    return out


def parse_ig(md_path: Path) -> list[Template]:
    """
    Walk the markdown and return all templates from sections 2 and 3.
    """

    lines = glue_wrapped_identifier_lines(md_path.read_text().splitlines())
    templates: list[Template] = []

    for i, line in enumerate(lines):
        heading = _HEADING_RE.match(line)
        if not heading:
            continue

        identifier = _find_next_identifier(lines, i + 1, max_lookahead=20)
        if identifier is None:
            # heading without an identifier (e.g. a divider like
            # "ENTRY-LEVEL TEMPLATES"); skip
            continue

        root, ext = identifier
        templates.append(
            Template(
                section_number=heading.group("section"),
                display_name=heading.group("name").strip(),
                root=root,
                extension=ext,
                contained_by=_find_contained_by(lines, i + 1, max_lookahead=80),
            )
        )

    return templates


def _find_next_identifier(
    lines: list[str], start: int, max_lookahead: int
) -> tuple[str, str | None] | None:
    """
    Return (root, extension) for the next identifier line, or None.
    """

    end = min(start + max_lookahead, len(lines))
    for j in range(start, end):
        if _HEADING_START_RE.match(lines[j]):
            return None
        m = _IDENTIFIER_RE.search(lines[j])
        if m:
            return m.group("oid"), m.group("ext")
    return None


def _find_contained_by(lines: list[str], start: int, max_lookahead: int) -> list[str]:
    """
    Extract "Contained By:" out of its table.

    Pull the "Contained By:" column from the Contexts table that follows
    the identifier line. Returns a list of parent template names.
    """

    end = min(start + max_lookahead, len(lines))
    parents: list[str] = []
    in_table = False
    contained_by_col_seen = False

    for j in range(start, end):
        line = lines[j]

        if _HEADING_START_RE.match(line):
            break

        if "Contained By:" in line:
            in_table = True
            contained_by_col_seen = True
            continue

        if not in_table:
            continue

        # skip the table separator row (|----|---|)
        if re.match(r"^\|[\s\-|:]+\|$", line):
            continue

        m = _TABLE_ROW_RE.match(line)
        if not m:
            # blank line or end of table
            if not line.strip().startswith("|"):
                break
            continue

        cell = m.group(1).strip()
        if not cell or cell == "Contained By:":
            continue

        # strip "(required)" / "(optional)" / "(optional [0..*])" suffix
        cell = re.sub(r"\s*\((?:required|optional)[^)]*\)\s*$", "", cell)
        if cell:
            parents.append(cell)

    return parents if contained_by_col_seen else []


def _section_group_key(section_display_name: str) -> str:
    """
    Normalize a section name for use as a group key.

    "Encounters Section (entries optional) (V3)"  -> "Encounters Section (V3)"
    "Encounters Section (entries required) (V3)"  -> "Encounters Section (V3)"

    Both variants share a group header even though they have different
    root OIDs; both constants still appear in the group.
    """

    return re.sub(r"\s*\(entries (?:optional|required)\)", "", section_display_name)


def group_templates(templates: list[Template]) -> dict[str, list[Template]]:
    """
    Group entry-level templates under their containing section.

    Algorithm:
      1. Sections (2.*) are their own groups. Entries-optional and
         entries-required variants of the same section share one group.
      2. For each entry (3.*), walk Contained By up to _MAX_CONTAINMENT_HOPS
         hops. If any reachable parent is a section, group under it.
      3. If no path leads to a section, group as "Cross-cutting".

    First section reached wins (Contained By order is the IG drafters'
    primary-container hint).
    """

    by_name = {t.display_name: t for t in templates}
    groups: dict[str, list[Template]] = {}

    # seed with section groups in IG order
    for t in templates:
        if t.section_number.startswith("2."):
            groups.setdefault(_section_group_key(t.display_name), []).append(t)

    groups[_CROSS_CUTTING] = []

    for t in templates:
        if not t.section_number.startswith("3."):
            continue
        section_name = _walk_to_section(t, by_name)
        if section_name is None:
            groups[_CROSS_CUTTING].append(t)
        else:
            groups.setdefault(_section_group_key(section_name), []).append(t)

    # append C-CDA supplement entries to their declared groups
    for group, display_name, root, extension in _CCDA_SUPPLEMENT:
        supplement = Template(
            section_number="ccda",
            display_name=display_name,
            root=root,
            extension=extension,
        )
        groups.setdefault(group, []).append(supplement)

    return groups


def _walk_to_section(template: Template, by_name: dict[str, Template]) -> str | None:
    """
    Breadth-First Search Contained By edges until we hit a section-level template.

    Returns the section's display name, or None if no path leads to one.
    """

    visited: set[str] = set()
    frontier: list[tuple[Template, int]] = [(template, 0)]

    while frontier:
        current, hops = frontier.pop(0)
        if hops > _MAX_CONTAINMENT_HOPS:
            continue
        for parent_name in current.contained_by:
            if parent_name in visited:
                continue
            visited.add(parent_name)
            parent = by_name.get(parent_name)
            if parent is None:
                continue
            if parent.section_number.startswith("2."):
                return parent.display_name
            frontier.append((parent, hops + 1))

    return None


_OUTPUT_HEADER = '''"""\
DO NOT EDIT BY HAND--change the source IG or the generator and regenerate.

Generated from the eICR STU 3.1.1 IG Volume 2 markdown by
`refiner/scripts/oid_catalog_builder/generate_template_oids.py`.

Template OIDs for the eCR Refiner entry matching engine.

use the shell script to run the python script and place the output in the
`specification` module.

Matching uses @root only; @extension dates are documented in trailing
comments because vendor variance on @extension is high enough that
strict extension matching produces false negatives in real documents.
"""

from typing import Final
'''


def render(groups: dict[str, list[Template]]) -> str:
    """
    Emit the final template_oids.py contents.
    """

    out: list[str] = [_OUTPUT_HEADER]
    seen: dict[str, str] = {}  # constant_name -> root, for conflict detection

    for group_name, members in groups.items():
        if not members:
            continue
        out.append("")
        out.append("# " + "=" * 75)
        out.append(f"# {group_name}")
        out.append("# " + "=" * 75)
        out.append("")

        for t in members:
            constant = slugify(t.display_name)
            if constant in seen and seen[constant] != t.root:
                raise ValueError(
                    f"Constant {constant} maps to two different roots: "
                    f"{seen[constant]} and {t.root} (from {t.display_name!r})"
                )
            seen[constant] = t.root

            ext_note = f"  # ext {t.extension}" if t.extension else ""
            out.append(f"# {t.display_name}")
            out.append(f'{constant}: Final[str] = "{t.root}"{ext_note}')
            out.append("")

    return "\n".join(out) + "\n"


def main() -> None:
    """
    Main orchestration of the `template_oid.py` generation.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ig-md",
        type=Path,
        required=True,
        help="Path to the eICR 3.1.1 IG Vol 2 markdown",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Path to write the generated template_oids.py",
    )
    args = parser.parse_args()

    templates = parse_ig(args.ig_md)
    groups = group_templates(templates)
    args.out.write_text(render(groups))

    sections = sum(1 for t in templates if t.section_number.startswith("2."))
    entries = sum(1 for t in templates if t.section_number.startswith("3."))
    cross_cutting = len(groups.get(_CROSS_CUTTING, []))

    print(f"Wrote {args.out}")
    print(f"  {sections} section-level + {entries} entry-level templates")
    print(f"  {cross_cutting} entries in {_CROSS_CUTTING}")


if __name__ == "__main__":
    main()
