"""
Asserts that every aggregate over a membership-grain table deduplicates.

`conditions_codes_temp` is keyed `(condition_id, code_id, valueset_id)`, so joining
it multiplies the row set: a code contributed by eight sibling groupers is eight
rows. Any aggregate built on those rows therefore sees duplicates, and an aggregate
that drops `valueset_id` from its output -- which is the only column distinguishing
them -- silently changes grain without changing cardinality.

This is the guard CLAUDE.md's warning needed and did not have. That paragraph named
the trap, named the reference implementation, and even recorded which file was still
wrong; the queries shipped wrong anyway and stayed wrong for two months. Prose does
not fail a build.

It reads the SQL out of the source with `ast` rather than running it, so it costs
nothing and catches the mistake at author time rather than in a data review.
"""

import ast
import re
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[2] / "app"

# tables whose grain is a membership rather than an entity. joining one of these
# fans the row set out, so aggregates in the same query have to collapse it
FAN_OUT_TABLES = ("conditions_codes_temp",)

# `COUNT(*)` over a membership table is a count of memberships, which is sometimes
# exactly what is wanted, and it says so; `COUNT(c.id)` reads like a count of codes,
# so it is held to the same rule as the list builders -- it is how `code_count` went
# wrong
AGGREGATE = re.compile(
    r"\b(?:(?:JSONB_AGG|JSON_AGG|ARRAY_AGG|STRING_AGG)\s*\(|COUNT\s*\((?!\s*\*))",
    re.IGNORECASE,
)
ARRAY_SUBQUERY = re.compile(r"\bARRAY\s*\(\s*SELECT\b", re.IGNORECASE)

# aggregates whose input is already collapsed before they see it, so `DISTINCT` would
# be redundant. each entry is a claim that something upstream -- a `GROUP BY` on the
# code, or a `SELECT DISTINCT` CTE including the code's id -- has already removed the
# valueset fan-out. the key is the aggregate head plus a fragment that pins which one
ALLOWED_WITHOUT_DISTINCT: dict[str, str] = {
    "ARRAY_AGG(code_id) FILTER (WHERE in_cur AND NOT in_prev)": (
        "_get_tes_update_diff_db: the `tes_records` CTE does "
        "`GROUP BY c.canonical_url, c.display_name, cc.code_id`, so one row per code "
        "reaches the aggregate"
    ),
    "ARRAY_AGG(code_id) FILTER (WHERE in_prev AND NOT in_cur)": (
        "_get_tes_update_diff_db: same CTE, same reason"
    ),
    "JSONB_BUILD_OBJECT( 'code', cur.code": (
        "get_tes_update_condition_diff_db: the `cur` CTE is `SELECT DISTINCT` over a "
        "column list that includes `c.id as code_id`, so the fan-out is gone before "
        "the FULL OUTER JOIN pairs rows 1:1 on it"
    ),
    "JSONB_BUILD_OBJECT( 'code', prev.code": (
        "get_tes_update_condition_diff_db: the `prev` CTE, same reason"
    ),
    "COUNT(cur.code_id) FILTER (WHERE prev.code_id IS NULL) > 0": (
        "get_tes_update_condition_diff_db: same `SELECT DISTINCT` CTEs, and the count "
        "is only compared to zero"
    ),
    "COUNT(prev.code_id) FILTER (WHERE cur.code_id IS NULL) > 0": (
        "get_tes_update_condition_diff_db: the `prev` side of the same `HAVING`"
    ),
}


def _sql_literals() -> list[tuple[Path, str]]:
    """Every string literal in `app/db` long enough to be a query."""

    found: list[tuple[Path, str]] = []
    for path in sorted(APP.rglob("*.py")):
        if "__pycache__" in path.parts or ".venv" in path.parts:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                text = node.value
            elif isinstance(node, ast.JoinedStr):
                # an f-string query: join the literal parts, since the
                # interpolated pieces are clause fragments built elsewhere
                text = "".join(
                    v.value
                    for v in node.values
                    if isinstance(v, ast.Constant) and isinstance(v.value, str)
                )
            else:
                continue
            if "SELECT" in text.upper() and len(text) > 40:
                found.append((path, text))
    return found


def _aggregates_missing_distinct(sql: str) -> list[str]:
    """Aggregate heads in `sql` whose argument list does not start with DISTINCT."""

    offenders: list[str] = []
    for pattern in (AGGREGATE, ARRAY_SUBQUERY):
        for match in pattern.finditer(sql):
            # the opening paren is the last character the pattern consumed for an
            # aggregate; for ARRAY(SELECT ...) the SELECT is what DISTINCT follows
            tail = sql[match.end() : match.end() + 40]
            if re.match(r"\s*DISTINCT\b", tail, re.IGNORECASE):
                continue
            snippet = " ".join(sql[match.start() : match.end() + 140].split())
            if any(allowed in snippet for allowed in ALLOWED_WITHOUT_DISTINCT):
                continue
            head = " ".join(match.group(0).split())
            offenders.append(f"{head} ... -> {snippet}")
    return offenders


@pytest.fixture(scope="module")
def fan_out_queries() -> list[tuple[Path, str]]:
    return [
        (path, sql)
        for path, sql in _sql_literals()
        if any(table in sql for table in FAN_OUT_TABLES)
    ]


def test_there_are_fan_out_queries_to_check(fan_out_queries):
    """A rename of the junction must not silently empty this whole module."""

    assert fan_out_queries, (
        f"no query in app/ references any of {FAN_OUT_TABLES} -- if the junction was "
        "renamed, update FAN_OUT_TABLES, because every assertion below just became "
        "vacuous"
    )


def test_aggregates_over_the_junction_deduplicate(fan_out_queries):
    found: list[str] = []
    for path, sql in fan_out_queries:
        rel = path.relative_to(APP.parent)
        for offender in _aggregates_missing_distinct(sql):
            found.append(f"  {rel}\n      {offender}")

    assert not found, (
        "aggregate(s) over a membership-grain table without DISTINCT.\n"
        "a row in conditions_codes_temp is a membership, so these carry one entry\n"
        "per (code, valueset) pair while looking like a list of codes:\n"
        + "\n".join(found)
        + "\n\n  `app/db/configurations/codes/db.py` is the reference implementation."
    )


def test_json_build_object_is_never_aggregated_with_distinct(fan_out_queries):
    """
    `DISTINCT JSON_BUILD_OBJECT(...)` cannot work -- `json` has no equality operator.

    Postgres rejects it outright, so this is really a guard against the half-fix:
    someone adds `DISTINCT` to satisfy the test above without switching the builder,
    and only finds out at runtime.
    """

    found: list[str] = []
    for path, sql in fan_out_queries:
        for match in re.finditer(
            r"DISTINCT\s+JSON_BUILD_OBJECT\s*\(", sql, re.IGNORECASE
        ):
            snippet = " ".join(sql[match.start() : match.start() + 60].split())
            found.append(f"  {path.relative_to(APP.parent)}: {snippet}")

    assert not found, (
        "DISTINCT applied to JSON_BUILD_OBJECT -- `json` has no equality operator, so\n"
        "postgres will reject this at execution time. use JSONB_BUILD_OBJECT:\n"
        + "\n".join(found)
    )
