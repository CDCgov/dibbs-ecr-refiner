"""
Verify the seeded database against the processed tables.

This is the check that answers "did this deploy seed correctly". It needs only
the processed CSVs and a connection, both of which the ops container already
has, so it runs anywhere--including against production--unlike the
raw-to-processed check, which needs the bundles.

Properties asserted, for the TES releases actually seeded:

1. Every code system OID in the processed data exists in `systems`. This is what
   keeps `ops/seeding/systems.py` and `tes/normalize/model.py` from drifting
   apart: they are deliberately separate lists, and this is the seam that catches
   it if one changes without the other.
2. Row counts agree for conditions, valuesets, codes, and memberships.
3. The membership sets are equal in both directions -- nothing in the processed
   data failed to land, and nothing in the database came from anywhere else.

Property 3 is the strong one; 1 and 2 run first because they localize a failure
that would otherwise show up as a large unexplained set difference.

Usage:
    python -m tes.verify.database
"""

import argparse
import csv
import gzip
import os
import sys
from pathlib import Path

import psycopg
from psycopg import Connection

from tes.normalize.run import PROCESSED_DIR
from tes.verify.report import Result, render

MEMBERSHIP_COLUMNS = (
    "condition_url",
    "condition_version",
    "valueset_url",
    "system_oid",
    "code",
)


def seeded_versions(connection: Connection) -> list[str]:
    """
    Return the TES releases present in the database.
    """

    with connection.cursor() as cursor:
        cursor.execute("SELECT version FROM tes ORDER BY version")
        return [row[0] for row in cursor.fetchall()]


def _stage_processed_memberships(connection: Connection, processed_dir: Path) -> None:
    """
    Load every processed membership into a temp table.

    The gzip is streamed to the server as bytes rather than parsed in Python --
    parsing two million rows with `csv.DictReader` and `write_row` took ~18s of
    the check's runtime, where `COPY` does it in about two. Releases outside the
    seeding window are filtered in the comparison queries instead of on the way
    in, which is the same trade the seeder makes.

    The table is TEMP and `ON COMMIT DROP`, so this stays safe to point at a live
    database.
    """

    columns = (*MEMBERSHIP_COLUMNS, "is_child_rsg", "is_trigger_code")
    definition = ", ".join(f"{column} TEXT" for column in columns)

    with connection.cursor() as cursor:
        cursor.execute(
            f"CREATE TEMP TABLE expected_memberships ({definition}) ON COMMIT DROP"
        )
        statement = (
            f"COPY expected_memberships ({', '.join(columns)}) "
            "FROM STDIN WITH (FORMAT csv, HEADER true)"
        )
        with (
            cursor.copy(statement) as copy,
            gzip.open(processed_dir / "memberships.csv.gz", "rb") as handle,
        ):
            while chunk := handle.read(1 << 20):
                copy.write(chunk)

        cursor.execute("CREATE INDEX ON expected_memberships (condition_version)")
        cursor.execute("ANALYZE expected_memberships")


def check_systems_present(connection: Connection, versions: list[str]) -> Result:
    """
    Every code system the processed data uses is registered in `systems`.
    """

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT e.system_oid
            FROM expected_memberships e
            LEFT JOIN systems s ON s.oid = e.system_oid
            WHERE s.id IS NULL AND e.condition_version = ANY(%(versions)s)
        """,
            {"versions": versions},
        )
        missing = [row[0] for row in cursor.fetchall()]

        cursor.execute(
            "SELECT count(DISTINCT system_oid) FROM expected_memberships "
            "WHERE condition_version = ANY(%(versions)s)",
            {"versions": versions},
        )
        (used,) = cursor.fetchone()

    return Result(
        "Every code system in the processed data exists in `systems`",
        not missing,
        f"{used} code systems used by the processed data",
        [f"{oid}: no row in systems" for oid in missing],
    )


def check_no_stranded_conditions(connection: Connection) -> Result:
    """
    Every condition in the database resolves to at least one code.

    The general form of the partial-seed failure: a condition row with no
    memberships stays configurable in the UI and activates to an `active.json`
    that matches nothing. `ops/seeding` refuses the specific run that causes it,
    but this catches stranding from any cause -- a failed migration, a manual
    delete, a future loader change -- and it covers every release in the database
    rather than only the ones a given run touched.
    """

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT t.version, c.display_name
            FROM conditions c
            JOIN tes t ON t.id = c.tes_id
            WHERE NOT EXISTS (
                SELECT 1 FROM conditions_codes_temp cct
                WHERE cct.condition_id = c.id
            )
            ORDER BY t.version, c.display_name
        """)
        stranded = cursor.fetchall()

        cursor.execute("SELECT count(*) FROM conditions")
        (total,) = cursor.fetchone()

    by_version: dict[str, int] = {}
    for version, _ in stranded:
        by_version[version] = by_version.get(version, 0) + 1

    return Result(
        "No condition is left without codes",
        not stranded,
        f"{total:,} conditions, {len(stranded):,} with no codes",
        [
            f"{version}: {count:,} conditions have no codes"
            for version, count in sorted(by_version.items())
        ],
    )


def check_row_counts(
    connection: Connection, processed_dir: Path, versions: list[str]
) -> Result:
    """
    Table counts agree between the processed data and the database.
    """

    expected_conditions = _count_csv(
        processed_dir / "conditions.csv.gz", "version", versions
    )
    expected_valuesets = _count_csv(
        processed_dir / "valuesets.csv.gz", "condition_version", versions
    )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                (SELECT count(*) FROM conditions c JOIN tes t ON t.id = c.tes_id),
                (SELECT count(*) FROM valuesets),
                (SELECT count(*) FROM conditions_codes_temp),
                (SELECT count(*) FROM expected_memberships
                 WHERE condition_version = ANY(%(versions)s))
        """,
            {"versions": versions},
        )
        conditions, valuesets, memberships, expected_memberships = cursor.fetchone()

    comparisons = [
        ("conditions", expected_conditions, conditions),
        ("valuesets", expected_valuesets, valuesets),
        ("memberships", expected_memberships, memberships),
    ]
    failures = [
        f"{name}: processed has {want:,}, database has {have:,}"
        for name, want, have in comparisons
        if want != have
    ]

    return Result(
        "Row counts agree between processed data and database",
        not failures,
        ", ".join(f"{name}={have:,}" for name, _, have in comparisons),
        failures,
    )


def check_memberships_match(connection: Connection, versions: list[str]) -> Result:
    """
    The membership sets are equal in both directions.

    A row on only one side means either seeding dropped something or the database
    holds a row the processed data cannot account for. Both matter, so the
    comparison runs both ways.

    The database side is materialized once rather than inlined into each `EXCEPT`:
    it is a six-way join over a million rows, and running it twice (four times
    when reporting a breakdown) was most of this check's cost.
    """

    params = {"versions": versions}
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TEMP TABLE actual_memberships ON COMMIT DROP AS
            SELECT c.canonical_url AS condition_url,
                   t.version       AS condition_version,
                   v.canonical_url AS valueset_url,
                   s.oid           AS system_oid,
                   co.code         AS code
            FROM conditions_codes_temp cct
            JOIN conditions c ON c.id = cct.condition_id
            JOIN tes t ON t.id = c.tes_id
            JOIN valuesets v ON v.id = cct.valueset_id
            JOIN codes co ON co.id = cct.code_id
            JOIN systems s ON s.id = co.system_id
        """)
        cursor.execute("ANALYZE actual_memberships")

        columns = ", ".join(MEMBERSHIP_COLUMNS)
        expected = (
            f"SELECT {columns} FROM expected_memberships "
            "WHERE condition_version = ANY(%(versions)s)"
        )
        actual = f"SELECT {columns} FROM actual_memberships"

        cursor.execute(
            f"SELECT count(*) FROM ({expected} EXCEPT {actual}) missing", params
        )
        (missing,) = cursor.fetchone()

        cursor.execute(
            f"SELECT count(*) FROM ({actual} EXCEPT {expected}) extra", params
        )
        (extra,) = cursor.fetchone()

        failures = []
        if missing or extra:
            cursor.execute(
                f"""
                SELECT system_oid, count(*) FROM ({expected} EXCEPT {actual}) m
                GROUP BY system_oid ORDER BY 2 DESC
                """,
                params,
            )
            failures += [
                f"{oid}: {count:,} in processed, absent from database"
                for oid, count in cursor.fetchall()
            ]
            cursor.execute(
                f"""
                SELECT system_oid, count(*) FROM ({actual} EXCEPT {expected}) e
                GROUP BY system_oid ORDER BY 2 DESC
                """,
                params,
            )
            failures += [
                f"{oid}: {count:,} in database, absent from processed"
                for oid, count in cursor.fetchall()
            ]

    return Result(
        "Membership sets are identical in both directions",
        not (missing or extra),
        f"{missing:,} missing from database, {extra:,} unaccounted for in database",
        failures,
    )


def _count_csv(path: Path, version_column: str, versions: list[str]) -> int:
    wanted = set(versions)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        return sum(1 for row in csv.DictReader(handle) if row[version_column] in wanted)


def run_checks(
    connection: Connection, processed_dir: Path = PROCESSED_DIR
) -> list[Result]:
    """
    Run every processed-to-database check.

    Args:
        connection: An open connection to the seeded database.
        processed_dir: Directory holding the processed tables.

    Returns:
        One Result per check, in the order they ran.
    """

    versions = seeded_versions(connection)
    if not versions:
        return [
            Result(
                "Database has seeded TES releases",
                False,
                "the `tes` table is empty -- nothing has been seeded",
            )
        ]

    _stage_processed_memberships(connection, processed_dir)
    return [
        Result(
            "Database has seeded TES releases",
            True,
            f"seeded releases: {', '.join(versions)}",
        ),
        check_systems_present(connection, versions),
        check_no_stranded_conditions(connection),
        check_row_counts(connection, processed_dir, versions),
        check_memberships_match(connection, versions),
    ]


def main(argv: list[str] | None = None) -> int:
    """
    Run the processed-to-database checks against DB_URL.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    args = parser.parse_args(argv)

    url = os.getenv("DB_URL")
    password = os.getenv("DB_PASSWORD")
    if not url or not password:
        print("DB_URL and DB_PASSWORD must be set.", file=sys.stderr)
        return 2

    with psycopg.connect(url, password=password) as connection:
        return render(run_checks(connection, args.processed_dir))


if __name__ == "__main__":
    sys.exit(main())
