"""
Print the valueset rows seeding has quarantined.

`_quarantine_stale_valuesets` moves rows the processed tables stopped
declaring into `orphaned_valuesets` instead of deleting them, which is only
useful if the rows can be read back. Deployed environments have no interactive
database access--the ops image is the whole interface--so retrieval is a
command rather than a query:

    ops orphans

Usage:
    python3 ./ops/seeding/report_orphans.py [--version 6.0.0] [--limit 200]

Putting a row back, should that ever be wanted. `valueset_id` is the id the row
held in `valuesets` and is what the membership junction referenced, so a restore
reuses it rather than generating a new one; the next seed quarantines the row
again unless the processed tables have started declaring it:

    INSERT INTO valuesets (
        id, condition_id, display_name, category, canonical_url,
        code_count, completeness, parent_url, created_at, updated_at
    )
    SELECT o.valueset_id, c.id, o.display_name, o.category, o.canonical_url,
           o.code_count, o.completeness, o.parent_url,
           o.valueset_created_at, o.valueset_updated_at
    FROM orphaned_valuesets o
    JOIN tes t ON t.version = o.condition_version
    JOIN conditions c
      ON c.canonical_url = o.condition_canonical_url AND c.tes_id = t.id
    WHERE o.id = '<orphan_id>';
"""

import argparse
import os
import sys

from connection import get_db_connection
from psycopg import Connection
from psycopg.rows import dict_row


def fetch_orphans(
    connection: Connection, version: str | None, limit: int
) -> list[dict]:
    """
    Read quarantined valuesets, most recently removed first.

    Args:
        connection: An open connection to the database.
        version: Restrict to one TES release, or None for every release.
        limit: Maximum rows to return.

    Returns:
        One row per quarantined valueset.
    """

    # keyed rows, not tuples: `render` is a separate function, so a column
    # reordered here would silently misassign there
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            """
            SELECT removed_at, condition_version, display_name, canonical_url,
                   condition_canonical_url, code_count, memberships_at_removal,
                   valueset_created_at, valueset_updated_at, id, valueset_id
            FROM orphaned_valuesets
            -- cast so an omitted --version is an untyped NULL postgres
            -- can still resolve
            WHERE %(version)s::text IS NULL
               OR condition_version = %(version)s::text
            ORDER BY removed_at DESC, condition_version, canonical_url
            LIMIT %(limit)s
            """,
            {"version": version, "limit": limit},
        )
        return cursor.fetchall()


def render(rows: list[dict]) -> None:
    """
    Print one block per quarantined row.

    A block rather than a table: canonical urls are long enough that columns
    wrap into noise in CloudWatch, and these are read one at a time.

    Args:
        rows: Rows from `fetch_orphans`.
    """

    if not rows:
        print("No quarantined valuesets.")
        return

    print(f"{len(rows):,} quarantined valueset rows\n")
    for row in rows:
        # memberships tells you which kind of removal this was: 0 means the row
        # was already stranded when the quarantine first ran, anything higher
        # means that seed is what retired it
        print(f"  {row['display_name'] or '(no title)'}  [{row['condition_version']}]")
        print(f"    valueset    {row['canonical_url']}")
        print(f"    condition   {row['condition_canonical_url']}")
        print(f"    orphan_id   {row['id']}")
        # the id the row held in `valuesets`, and what the membership junction
        # referenced -- a restore that does not reuse it is not a restore
        print(f"    valueset_id {row['valueset_id']}")
        print(
            f"    codes {row['code_count']:,} | "
            f"memberships at removal {row['memberships_at_removal']:,} | "
            f"seeded {row['valueset_created_at']:%Y-%m-%d} | "
            f"last changed {row['valueset_updated_at']:%Y-%m-%d} | "
            f"removed {row['removed_at']:%Y-%m-%d %H:%M}"
        )
        print()


def main(argv: list[str] | None = None) -> int:
    """
    Print quarantined valuesets from the database named by DB_URL.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", help="restrict to one TES release")
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args(argv)

    url = os.getenv("DB_URL")
    password = os.getenv("DB_PASSWORD")
    if not url or not password:
        print("DB_URL and DB_PASSWORD must be set.", file=sys.stderr)
        return 2

    with get_db_connection(url, password) as connection:
        render(fetch_orphans(connection, args.version, args.limit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
